"""
/api/chat — the full RAG loop.

Flow for each message:
  1. Load conversation history for session_id (follow-up support)
  2. Retrieve top-K chunks from Chroma via RetrieverService
  3. Check confidence — if all chunks below threshold → canned refusal
  4. Build grounded prompt (system + history + context + question)
  5. Call LLM (Ollama by default, OpenAI-compatible)
  6. Format citations from retrieved chunks
  7. Save this turn to session history (for next follow-up)
  8. Log query + result to QueryLog audit table
  9. Return answer + citations + confidence score
"""

import time

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import QueryLog, get_session, init_db
from generation.citation_formatter import results_to_citations, results_to_prompt_chunks
from generation.llm_client import LLMClient, get_llm_client
from generation.prompt_templates import LOW_CONFIDENCE_RESPONSE, build_full_prompt
from generation.session_store import get_history, init_session_store, save_turn
from models.api_models import ChatRequest, ChatResponse, Citation
from retrieval.retriever import RetrieverService, get_retriever

logger = structlog.get_logger()
router = APIRouter()

CONFIDENCE_LOW = float(__import__("os").getenv("CONFIDENCE_LOW", "0.60"))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    retriever:   RetrieverService = Depends(get_retriever),
    llm:         LLMClient        = Depends(get_llm_client),
    db: AsyncSession              = Depends(get_session),
) -> ChatResponse:
    """
    Full RAG loop:
      retrieve → prompt → LLM → citations → session history → audit log → response
    """
    await init_session_store()
    t0 = time.time()

    session_id = request.session_id
    question   = request.message.strip()
    top_k      = request.top_k

    if not question:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    logger.info("chat.request", session_id=session_id, question=question[:80])

    # ── Step 1: Load conversation history ─────────────────────────────────────
    history = await get_history(session_id, db)
    logger.debug("chat.history_loaded", session_id=session_id, turns=len(history))

    # ── Step 2: Retrieve relevant chunks ─────────────────────────────────────
    results = retriever.search(query=question, top_k=top_k)

    # ── Step 3: Confidence check ──────────────────────────────────────────────
    top_score = results[0].score if results else 0.0
    no_confident_results = not results or top_score < CONFIDENCE_LOW

    if no_confident_results:
        logger.info(
            "chat.low_confidence_fallback",
            session_id=session_id,
            top_score=top_score,
        )
        answer    = LOW_CONFIDENCE_RESPONSE
        citations: list[Citation] = []

        # Still save to session so follow-up context is preserved
        await save_turn(session_id, question, answer, db)

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        _log_query(db, session_id, question, [], top_score, answer, elapsed_ms)

        return ChatResponse(
            answer=answer,
            citations=[],
            confidence=top_score,
            low_confidence=True,
        )

    # ── Step 4: Build grounded prompt ────────────────────────────────────────
    prompt_chunks = results_to_prompt_chunks(results)
    messages      = build_full_prompt(
        question=question,
        chunks=prompt_chunks,
        history=history,
    )

    # ── Step 5: Call LLM ─────────────────────────────────────────────────────
    try:
        answer = await llm.generate(messages)
    except RuntimeError as e:
        logger.error("chat.llm_error", error=str(e))
        raise HTTPException(status_code=503, detail=str(e))

    # ── Step 6: Format citations ──────────────────────────────────────────────
    citations = results_to_citations(results)

    # ── Step 7: Save session turn ─────────────────────────────────────────────
    await save_turn(session_id, question, answer, db)

    # ── Step 8: Audit log ────────────────────────────────────────────────────
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    _log_query(db, session_id, question, [r.chunk_id for r in results], top_score, answer, elapsed_ms)

    logger.info(
        "chat.response",
        session_id=session_id,
        confidence=top_score,
        citations=len(citations),
        elapsed_ms=elapsed_ms,
    )

    # ── Step 9: Return ────────────────────────────────────────────────────────
    return ChatResponse(
        answer=answer,
        citations=citations,
        confidence=top_score,
        low_confidence=top_score < float(__import__("os").getenv("CONFIDENCE_HIGH", "0.80")),
    )


def _log_query(
    db: AsyncSession,
    session_id: str,
    query: str,
    chunk_ids: list[str],
    confidence: float,
    answer: str,
    latency_ms: float,
):
    """Fire-and-forget audit log entry."""
    try:
        entry = QueryLog(
            session_id  = session_id,
            query       = query,
            top_chunks  = chunk_ids,
            answer      = answer[:500],   # Truncate to avoid huge DB entries
            confidence  = confidence,
            latency_ms  = latency_ms,
        )
        db.add(entry)
        # Commit will happen at end of request via dependency cleanup
    except Exception as e:
        logger.warning("chat.audit_log_error", error=str(e))
