"""
Session store — stores conversation history per session_id in SQLite.

Each session keeps the last MAX_HISTORY messages (alternating user/assistant).
This lets the LLM understand follow-up questions like:
  "What about rollback?" (referring to a deployment answer given previously)

Storage: SQLite (same DB as audit log) — no Redis/external store needed for MVP.
"""

import json
from datetime import datetime

import structlog
from sqlalchemy import Column, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import Base, engine

logger = structlog.get_logger()

MAX_HISTORY = int(__import__("os").getenv("SESSION_MAX_HISTORY", "6"))  # 3 turns


class SessionMessage(Base):
    """One message (user or assistant) in a conversation session."""
    __tablename__ = "session_messages"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String,  nullable=False, index=True)
    role       = Column(String,  nullable=False)   # "user" | "assistant"
    content    = Column(Text,    nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_session_store():
    """Create session_messages table if it doesn't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_history(session_id: str, session: AsyncSession) -> list[dict]:
    """
    Retrieve the last MAX_HISTORY messages for a session.
    Returns OpenAI-format list: [{"role": "user"|"assistant", "content": "..."}]
    """
    result = await session.execute(
        select(SessionMessage)
        .where(SessionMessage.session_id == session_id)
        .order_by(SessionMessage.created_at.desc())
        .limit(MAX_HISTORY)
    )
    rows = result.scalars().all()
    # Reverse to chronological order
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


async def save_turn(
    session_id: str,
    user_message: str,
    assistant_message: str,
    db_session: AsyncSession,
):
    """Save one user+assistant exchange to the session history."""
    db_session.add(SessionMessage(
        session_id=session_id, role="user",      content=user_message
    ))
    db_session.add(SessionMessage(
        session_id=session_id, role="assistant", content=assistant_message
    ))
    await db_session.commit()
    logger.debug("session.turn_saved", session_id=session_id)
