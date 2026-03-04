from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_session, QueryLog, IndexedDoc

router = APIRouter()


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Index stats: doc count, chunk count, last indexed."""
    doc_count = await session.scalar(select(func.count()).select_from(IndexedDoc))
    chunk_count = await session.scalar(
        select(func.sum(IndexedDoc.chunk_count)).select_from(IndexedDoc)
    )
    last_indexed = await session.scalar(
        select(func.max(IndexedDoc.indexed_at)).select_from(IndexedDoc)
    )
    return {
        "document_count": doc_count or 0,
        "chunk_count": int(chunk_count or 0),
        "last_indexed_at": last_indexed,
    }


@router.get("/queries")
async def get_recent_queries(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """Return recent queries with retrieved chunk IDs."""
    result = await session.execute(
        select(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "session_id": log.session_id,
            "query": log.query,
            "top_chunks": log.top_chunks,
            "confidence": log.confidence,
            "latency_ms": log.latency_ms,
            "created_at": log.created_at,
        }
        for log in logs
    ]
