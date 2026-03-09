from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Document(BaseModel):
    """Normalized document loaded from any source."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str                   # markdown | html | pdf | git
    title: str
    content: str
    path_or_url: str
    content_hash: Optional[str] = None  # MD5 hash for change detection
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
