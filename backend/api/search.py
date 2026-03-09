"""
/api/search — semantic search endpoint.

Returns top-K chunks from the vector DB ranked by similarity score.
Each result includes: chunk text, score, source doc, section, and confidence flag.

This is also used internally by /api/chat to retrieve context.
"""

import time
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import QueryLog, get_session
from models.api_models import SearchResponse, SearchResult
from retrieval.retriever import RetrieverService, get_retriever

logger = structlog.get_logger()
router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    query: str = Query(..., description="Natural-language search query", min_length=2),
    top_k: int = Query(default=5, ge=1, le=20, description="Number of results to return"),
    source_type: Optional[str] = Query(default=None, description="Filter by source type: markdown | pdf | html | git"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    retriever: RetrieverService = Depends(get_retriever),
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    """
    Semantic search over indexed documentation.

    - Embeds the query using BAAI/bge-base-en-v1.5
    - Searches Chroma vector store (cosine similarity)
    - Filters by confidence threshold (< 0.60 excluded)
    - Results with score 0.60–0.80 are flagged as low_confidence
    - Logs query + results for evaluation and audit
    """
    t0 = time.time()

    # Build optional Chroma metadata filter
    filters = {"source_type": source_type} if source_type else None

    # Run retrieval
    results: list[SearchResult] = retriever.search(
        query=query,
        top_k=top_k + offset,   # Fetch extra for pagination
        filters=filters,
    )

    # Apply pagination offset
    paginated = results[offset : offset + top_k]

    # No results at all (collection empty or no confident matches)
    if not results:
        logger.info("search.no_results", query=query)

    elapsed_ms = round((time.time() - t0) * 1000, 1)

    # Log query + top result metadata for evaluation
    try:
        log_entry = QueryLog(
            session_id  = "api_search",
            query       = query,
            top_chunks  = [r.chunk_id for r in paginated],
            confidence  = paginated[0].score if paginated else None,
            latency_ms  = elapsed_ms,
        )
        session.add(log_entry)
        await session.commit()
    except Exception as e:
        logger.warning("search.log_error", error=str(e))

    logger.info(
        "search.response",
        query=query[:60],
        results=len(paginated),
        top_score=paginated[0].score if paginated else None,
        elapsed_ms=elapsed_ms,
    )

    return SearchResponse(
        results=paginated,
        query=query,
        total=len(results),
    )
