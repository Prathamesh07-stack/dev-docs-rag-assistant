from pydantic import BaseModel
from typing import List, Optional


class Citation(BaseModel):
    """A source reference attached to an LLM answer."""
    chunk_id: str
    doc_id: str
    doc_title: str
    section: Optional[str] = None
    path_or_url: str
    score: float


class ChatRequest(BaseModel):
    session_id: str
    message: str
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float           # Top-1 similarity score
    low_confidence: bool = False


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: dict = {}


class SearchResult(BaseModel):
    chunk_id: str
    content: str
    score: float
    doc_id: str
    doc_title: str
    section: Optional[str]
    path_or_url: str
    low_confidence: bool = False


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total: int
