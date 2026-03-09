"""
Retrieval Engine — the core of the RAG query pipeline.

Flow:
  1. Embed the user query (same BAAI/bge-base-en-v1.5 model used at index time)
  2. Run ANN similarity search in Chroma
  3. Apply confidence thresholds:
       score > 0.80  → pass (high confidence)
       score 0.60–0.80 → pass with low_confidence=True flag
       score < 0.60  → exclude (not returned to caller)
  4. Return ranked SearchResult objects with full metadata

Note: Chroma returns L2 distances by default when using cosine space.
We convert to similarity score: similarity = 1 - (distance / 2)
This maps cosine distance [0, 2] → similarity [0, 1].
"""

import os
import time
from typing import Optional

import structlog

from ingestion.embedder import get_embedder
from ingestion.indexer import get_chroma_collection
from models.api_models import SearchResult

logger = structlog.get_logger()

CONFIDENCE_HIGH = float(os.getenv("CONFIDENCE_HIGH", "0.80"))
CONFIDENCE_LOW  = float(os.getenv("CONFIDENCE_LOW",  "0.60"))


class RetrieverService:
    """
    Handles semantic search over the Chroma vector store.

    Usage:
        retriever = RetrieverService()
        results = retriever.search("How do I deploy to staging?", top_k=5)
    """

    def __init__(self):
        self.embedder   = get_embedder()
        self.collection = get_chroma_collection()

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[SearchResult]:
        """
        Embed query → ANN search → apply confidence threshold → return results.

        Args:
            query:   Natural-language question
            top_k:   Max number of results to return
            filters: Optional Chroma where-clause, e.g. {"source_type": "pdf"}

        Returns:
            List of SearchResult sorted by similarity score (highest first).
            Only includes chunks with score >= CONFIDENCE_LOW.
        """
        if not query.strip():
            return []

        t0 = time.time()

        # 1. Embed query
        query_vector = self.embedder.embed_query(query)

        # 2. Build Chroma query kwargs
        query_kwargs = {
            "query_embeddings": [query_vector],
            "n_results": min(top_k * 2, 20),  # Fetch extra — some will be filtered by confidence
            "include": ["documents", "metadatas", "distances"],
        }
        if filters:
            query_kwargs["where"] = filters

        # 3. Run similarity search
        try:
            raw = self.collection.query(**query_kwargs)
        except Exception as e:
            logger.error("retriever.search_error", query=query, error=str(e))
            return []

        # 4. Parse and filter results
        results: list[SearchResult] = []
        ids        = raw["ids"][0]        if raw["ids"]        else []
        documents  = raw["documents"][0]  if raw["documents"]  else []
        metadatas  = raw["metadatas"][0]  if raw["metadatas"]  else []
        distances  = raw["distances"][0]  if raw["distances"]  else []

        for chunk_id, content, meta, distance in zip(ids, documents, metadatas, distances):
            # Convert cosine distance [0,2] → similarity [0,1]
            score = round(1.0 - distance / 2.0, 4)

            # Apply confidence threshold
            if score < CONFIDENCE_LOW:
                continue

            results.append(SearchResult(
                chunk_id     = chunk_id,
                content      = content,
                score        = score,
                doc_id       = meta.get("doc_id", ""),
                doc_title    = meta.get("doc_title", ""),
                section      = meta.get("section_title") or None,
                path_or_url  = meta.get("path_or_url", ""),
                low_confidence = score < CONFIDENCE_HIGH,
            ))

        # Sort by score descending, trim to top_k
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:top_k]

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        logger.info(
            "retriever.search_done",
            query=query[:80],
            top_k=top_k,
            returned=len(results),
            top_score=results[0].score if results else None,
            elapsed_ms=elapsed_ms,
        )

        return results


# Module-level singleton — avoids reloading the model on every request
_retriever: Optional[RetrieverService] = None


def get_retriever() -> RetrieverService:
    """FastAPI dependency — returns the shared RetrieverService instance."""
    global _retriever
    if _retriever is None:
        _retriever = RetrieverService()
    return _retriever
