"""
Chroma vector DB indexer — upserts chunk embeddings and handles re-indexing.

Responsibilities:
  1. Take Chunk objects (from chunker)
  2. Embed their content via EmbeddingClient
  3. Upsert into Chroma with full metadata
  4. Track which docs are indexed in SQLite (IndexedDoc table)
  5. Re-index: detect changed docs by hash → delete old chunks → insert new

Chroma collection layout:
  - One collection per app (rag_docs by default)
  - Each entry: id=chunk_id, embedding, document, metadata
  - Metadata keys: doc_id, doc_title, section_title, source_type, path_or_url, position
"""

import os
import time
from datetime import datetime

import chromadb
import structlog
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal, IndexedDoc, init_db
from ingestion.chunker import chunk_documents
from ingestion.embedder import get_embedder
from ingestion.staging import get_all_staged, init_staging_store
from models.chunk import Chunk
from models.document import Document

logger = structlog.get_logger()

# Resolve project root (parent of backend/) for consistent paths
_PROJECT_ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_CHROMA  = os.path.join(_PROJECT_ROOT, "data", "vectordb")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", _DEFAULT_CHROMA)
CHROMA_COLLECTION  = os.getenv("CHROMA_COLLECTION", "rag_docs")


# ── Chroma client (singleton) ─────────────────────────────────────────────────

_chroma_client = None
_chroma_collection = None


def get_chroma_collection():
    """Return (or create) the Chroma collection. Singleton."""
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _chroma_collection = _chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},   # Use cosine similarity
        )
        logger.info(
            "chroma.collection_ready",
            collection=CHROMA_COLLECTION,
            persist_dir=CHROMA_PERSIST_DIR,
            count=_chroma_collection.count(),
        )
    return _chroma_collection


# ── Core indexing functions ───────────────────────────────────────────────────

def _chunks_to_chroma_payload(chunks: list[Chunk], embeddings: list[list[float]]) -> dict:
    """Convert chunks + embeddings into Chroma-compatible payload."""
    return {
        "ids":        [c.chunk_id for c in chunks],
        "embeddings": embeddings,
        "documents":  [c.content for c in chunks],
        "metadatas":  [
            {
                "doc_id":       c.document_id,
                "doc_title":    c.metadata.get("doc_title", ""),
                "section_title": c.section_title or "",
                "source_type":  c.metadata.get("source_type", ""),
                "path_or_url":  c.metadata.get("path_or_url", ""),
                "position":     c.position,
                "token_count":  c.token_count or 0,
            }
            for c in chunks
        ],
    }


def upsert_chunks(chunks: list[Chunk], batch_size: int = 64):
    """
    Embed chunks and upsert into Chroma in batches.
    Uses upsert (not add) — safe to call multiple times.
    """
    if not chunks:
        logger.info("indexer.no_chunks_to_upsert")
        return

    collection = get_chroma_collection()
    embedder = get_embedder()
    total = len(chunks)

    logger.info("indexer.upserting", total_chunks=total)
    start = time.time()

    for i in range(0, total, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        texts = [c.content for c in batch_chunks]

        embeddings = embedder.embed_texts(texts)
        payload = _chunks_to_chroma_payload(batch_chunks, embeddings)
        collection.upsert(**payload)

        logger.info(
            "indexer.batch_upserted",
            batch=f"{i // batch_size + 1}/{(total + batch_size - 1) // batch_size}",
            size=len(batch_chunks),
        )

    elapsed = round(time.time() - start, 2)
    logger.info("indexer.upsert_done", total=total, elapsed_s=elapsed)


def delete_chunks_for_doc(doc_id: str):
    """Remove all Chroma chunks belonging to a document (for re-indexing)."""
    collection = get_chroma_collection()
    results = collection.get(where={"doc_id": doc_id})
    ids_to_delete = results.get("ids", [])
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        logger.info("indexer.chunks_deleted", doc_id=doc_id, count=len(ids_to_delete))


# ── SQLite tracking ───────────────────────────────────────────────────────────

async def get_indexed_hash(doc_id: str, session: AsyncSession) -> str | None:
    """Return the stored content_hash for a doc, or None if not indexed."""
    row = await session.get(IndexedDoc, doc_id)
    return row.content_hash if row else None


async def save_indexed_doc(doc: Document, chunk_count: int, session: AsyncSession):
    """Record that a document has been indexed."""
    tracked = IndexedDoc(
        id=doc.id,
        source_type=doc.source_type,
        title=doc.title,
        path_or_url=doc.path_or_url,
        content_hash=doc.content_hash,
        chunk_count=chunk_count,
        indexed_at=datetime.utcnow(),
    )
    await session.merge(tracked)
    await session.commit()


# ── Full re-index pipeline ────────────────────────────────────────────────────

async def index_all_docs(
    chunk_size: int = 512,
    overlap: int = 64,
    force: bool = False,
):
    """
    Full indexing pipeline:
      1. Load all staged documents from SQLite
      2. For each doc: check if hash changed since last index
      3. If changed (or forced): delete old chunks, re-chunk, re-embed, upsert
      4. Update IndexedDoc tracking table

    Args:
        chunk_size: Target token count per chunk
        overlap:    Overlap tokens between adjacent chunks
        force:      Re-index everything regardless of hash
    """
    await init_db()
    await init_staging_store()

    stats = {"new": 0, "updated": 0, "skipped": 0, "failed": 0, "total_chunks": 0}
    start = time.time()

    async with AsyncSessionLocal() as session:
        docs = await get_all_staged(session)

        if not docs:
            logger.warning("indexer.no_staged_docs", hint="Run `make ingest` first.")
            return stats

        logger.info("indexer.start", total_docs=len(docs))

        for doc in docs:
            try:
                stored_hash = await get_indexed_hash(doc.id, session)

                # Skip unchanged docs (unless forced)
                if not force and stored_hash == doc.content_hash:
                    logger.debug("indexer.skipped_unchanged", doc_id=doc.id, title=doc.title)
                    stats["skipped"] += 1
                    continue

                is_update = stored_hash is not None

                # Delete old chunks from Chroma before re-inserting
                if is_update:
                    delete_chunks_for_doc(doc.id)

                # Chunk → embed → upsert
                chunks = chunk_documents([doc], chunk_size=chunk_size, overlap=overlap)
                upsert_chunks(chunks)

                # Track in SQLite
                await save_indexed_doc(doc, len(chunks), session)

                if is_update:
                    stats["updated"] += 1
                    logger.info("indexer.doc_updated", title=doc.title, chunks=len(chunks))
                else:
                    stats["new"] += 1
                    logger.info("indexer.doc_indexed", title=doc.title, chunks=len(chunks))

                stats["total_chunks"] += len(chunks)

            except Exception as e:
                logger.error("indexer.doc_failed", doc_id=doc.id, title=doc.title, error=str(e))
                stats["failed"] += 1

    elapsed = round(time.time() - start, 2)
    collection = get_chroma_collection()

    print("\n" + "=" * 52)
    print("  INDEXING COMPLETE")
    print("=" * 52)
    print(f"  ✅ New docs indexed  : {stats['new']}")
    print(f"  🔄 Updated docs      : {stats['updated']}")
    print(f"  ⏭️  Unchanged (skipped): {stats['skipped']}")
    print(f"  ❌ Failed            : {stats['failed']}")
    print(f"  📦 Chunks in Chroma  : {collection.count()}")
    print(f"  ⏱️  Time              : {elapsed}s")
    print("=" * 52)
    print("  Next: `uvicorn main:app` → GET /api/search")
    print("=" * 52 + "\n")

    return stats
