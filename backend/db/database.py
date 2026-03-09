from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON
from datetime import datetime
import os

# Resolve data dir relative to the project root (parent of backend/)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(_BACKEND_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)   # auto-create on first run

DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/staging.db"

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


class QueryLog(Base):
    """Audit log for every user query."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    top_chunks = Column(JSON, nullable=True)    # List of chunk_ids retrieved
    answer = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IndexedDoc(Base):
    """Tracks which documents have been indexed and their content hashes."""
    __tablename__ = "indexed_docs"

    id = Column(String, primary_key=True)       # document id
    source_type = Column(String)
    title = Column(String)
    path_or_url = Column(String)
    content_hash = Column(String)               # For change detection
    chunk_count = Column(Integer, default=0)
    indexed_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
