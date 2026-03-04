"""
Chunking module — splits Document content into overlapping, heading-aware chunks.

Strategy:
  1. Split text on heading boundaries (## headings) first — keeps sections together
  2. Within each section, split further if it exceeds chunk_size tokens
  3. Apply overlap between adjacent chunks to preserve boundary context

Chunk size  : ~512 tokens (configurable)
Overlap     : ~64 tokens  (~12%, configurable)
Token count : tiktoken cl100k_base (same tokenizer as GPT-4 / text-embedding-ada-002)
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

import tiktoken

from models.chunk import Chunk
from models.document import Document

# Default tokenizer — cl100k_base matches OpenAI models and bge embeddings
_TOKENIZER = tiktoken.get_encoding("cl100k_base")

# Heading pattern: lines starting with one or more # characters
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _count_tokens(text: str) -> int:
    return len(_TOKENIZER.encode(text))


def _split_by_tokens(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into token-bounded chunks with overlap.
    Works at the sentence/paragraph level to avoid splitting mid-word.
    """
    tokens = _TOKENIZER.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _TOKENIZER.decode(chunk_tokens).strip()
        if chunk_text:
            chunks.append(chunk_text)
        if end >= len(tokens):
            break
        start += chunk_size - overlap   # Slide forward with overlap

    return chunks


def _extract_sections(text: str) -> list[tuple[Optional[str], str]]:
    """
    Split document text into (section_title, section_content) pairs.

    Example:
      # Intro\nsome text\n## Deploy\nother text
      → [("Intro", "some text"), ("Deploy", "other text")]

    If no headings found → returns one section with title=None.
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [(None, text.strip())]

    sections = []
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        content_start = match.end()
        content_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[content_start:content_end].strip()
        if content:
            sections.append((title, content))

    # Include any content before the first heading
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.insert(0, (None, preamble))

    return sections


class Chunker:
    """
    Heading-aware text chunker.

    Usage:
        chunker = Chunker(chunk_size=512, overlap=64)
        chunks = chunker.chunk(document)
    """

    def __init__(self, chunk_size: int = 512, overlap: int = 64, min_chunk_size: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def chunk(self, doc: Document) -> list[Chunk]:
        sections = _extract_sections(doc.content)
        chunks: list[Chunk] = []
        position = 0

        for section_title, section_content in sections:
            token_count = _count_tokens(section_content)

            if token_count <= self.chunk_size:
                # Section fits in one chunk — keep it whole
                sub_texts = [section_content]
            else:
                # Section is too large — split with overlap
                sub_texts = _split_by_tokens(section_content, self.chunk_size, self.overlap)

            for sub_text in sub_texts:
                sub_text = sub_text.strip()
                if _count_tokens(sub_text) < self.min_chunk_size:
                    continue    # Skip tiny fragments (headers, page numbers, etc.)

                chunk = Chunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=doc.id,
                    content=sub_text,
                    section_title=section_title,
                    position=position,
                    token_count=_count_tokens(sub_text),
                    metadata={
                        "source_type":  doc.source_type,
                        "path_or_url":  doc.path_or_url,
                        "doc_title":    doc.title,
                        "page_number":  doc.metadata.get("page_number"),
                        "headings_path": section_title or "",
                    },
                )
                chunks.append(chunk)
                position += 1

        return chunks


def chunk_document(
    doc: Document,
    chunk_size: int = 512,
    overlap: int = 64,
    min_chunk_size: int = 50,
) -> list[Chunk]:
    """Convenience wrapper — chunk a single document."""
    return Chunker(chunk_size, overlap, min_chunk_size).chunk(doc)


def chunk_documents(
    docs: list[Document],
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[Chunk]:
    """Chunk a list of documents — used by the indexer."""
    chunker = Chunker(chunk_size=chunk_size, overlap=overlap)
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunker.chunk(doc))
    return all_chunks
