from fastapi import APIRouter, HTTPException
from models.api_models import SearchRequest, SearchResponse, SearchResult
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/search")
async def search(query: str, top_k: int = 5) -> SearchResponse:
    """
    Semantic search over indexed docs.
    Returns top-K chunks ranked by similarity score.
    Placeholder — full implementation in Phase 5.
    """
    # TODO: wire up RetrieverService in Phase 5
    logger.info("search.request", query=query, top_k=top_k)
    raise HTTPException(status_code=501, detail="Retrieval not yet implemented. Run Phase 5.")
