"""
Staging store — persists loaded Document objects to SQLite.

This acts as an intermediate layer between loading and chunking.
The indexer reads from here to compute embeddings.
Tracks content_hash per doc to support efficient re-indexing.
"""

import json
from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy import Column, String, Text, DateTime, Integer, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import Base, engine, AsyncSessionLocal
from models.document import Document

logger = structlog.get_logger()


class StagedDocument(Base):
    """Raw normalized documents waiting to be chunked and embedded."""
    __tablename__ = "staged_documents"

    id           = Column(String,   primary_key=True)
    source_type  = Column(String,   nullable=False)
    title        = Column(String,   nullable=False)
    content      = Column(Text,     nullable=False)
    path_or_url  = Column(String,   nullable=False)
    content_hash = Column(String,   nullable=False)
    metadata_    = Column("metadata", Text, default="{}")  # JSON blob
    staged_at    = Column(DateTime, default=datetime.utcnow)


async def init_staging_store():
    """Create staged_documents table if it doesn't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_document(doc: Document, session: AsyncSession) -> bool:
    """
    Persist a Document to the staging store.
    Returns True if new/updated, False if unchanged (same hash).
    """
    existing = await session.get(StagedDocument, doc.id)

    # Skip if content hasn't changed
    if existing and existing.content_hash == doc.content_hash:
        logger.debug("staging.unchanged", doc_id=doc.id, title=doc.title)
        return False

    staged = StagedDocument(
        id=doc.id,
        source_type=doc.source_type,
        title=doc.title,
        content=doc.content,
        path_or_url=doc.path_or_url,
        content_hash=doc.content_hash,
        metadata_=json.dumps(doc.metadata),
        staged_at=datetime.utcnow(),
    )

    await session.merge(staged)   # Insert or update
    await session.commit()

    action = "updated" if existing else "inserted"
    logger.info(f"staging.{action}", doc_id=doc.id, title=doc.title)
    return True


async def get_all_staged(session: AsyncSession) -> list[Document]:
    """Retrieve all staged documents for chunking."""
    result = await session.execute(select(StagedDocument))
    rows = result.scalars().all()
    return [
        Document(
            id=row.id,
            source_type=row.source_type,
            title=row.title,
            content=row.content,
            path_or_url=row.path_or_url,
            content_hash=row.content_hash,
            metadata=json.loads(row.metadata_ or "{}"),
        )
        for row in rows
    ]


async def get_staged_count(session: AsyncSession) -> int:
    from sqlalchemy import func
    return await session.scalar(select(func.count()).select_from(StagedDocument)) or 0
