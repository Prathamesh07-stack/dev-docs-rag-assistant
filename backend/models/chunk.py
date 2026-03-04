from pydantic import BaseModel, Field
from typing import Optional
import uuid


class Chunk(BaseModel):
    """A text chunk derived from a Document, ready for embedding."""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    section_title: Optional[str] = None   # Nearest heading above this chunk
    position: int = 0                      # Order within the parent document
    token_count: Optional[int] = None
    metadata: dict = Field(default_factory=dict)
    # metadata keys: source_type, path_or_url, page_number, headings_path, doc_title
