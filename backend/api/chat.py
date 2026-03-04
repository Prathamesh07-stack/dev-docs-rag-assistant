from fastapi import APIRouter, HTTPException
from models.api_models import ChatRequest, ChatResponse
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Full RAG loop: retrieve top-K chunks → build prompt → call LLM → return answer + citations.
    Placeholder — full implementation in Phase 6.
    """
    # TODO: wire up RetrievalEngine + LLMClient in Phase 6
    logger.info("chat.request", session_id=request.session_id, message=request.message)
    raise HTTPException(status_code=501, detail="Chat not yet implemented. Run Phase 6.")
