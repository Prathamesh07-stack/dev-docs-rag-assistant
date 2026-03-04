"""
Embedding client — converts text into dense vectors using BAAI/bge-base-en-v1.5.

Key design decisions:
  - Same model MUST be used for both indexing and retrieval (critical)
  - Singleton pattern — model loaded once, reused across all calls
  - Batched to avoid memory spikes on large corpora
  - Retries on transient failures (network, GPU OOM, etc.)

Usage:
    embedder = get_embedder()
    vectors = embedder.embed_texts(["How do I deploy?", "What is the SLA?"])
"""

import os
import time
from functools import lru_cache
from typing import Optional

import structlog
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger()

# Model used for BOTH ingestion + retrieval. Never change without re-indexing.
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
DEFAULT_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
DEFAULT_MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))


class EmbeddingClient:
    """
    Wraps sentence-transformers with batching and retries.

    Vectors are normalized (unit length) so cosine similarity == dot product.
    This matches what Chroma uses internally.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_retries = max_retries

        logger.info("embedder.loading_model", model=model_name)
        self._model = SentenceTransformer(model_name)
        self.dimensions = self._model.get_sentence_embedding_dimension()
        logger.info("embedder.model_ready", model=model_name, dimensions=self.dimensions)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts. Returns a list of float vectors.

        - Processes in batches of `batch_size`
        - Retries up to `max_retries` times on failure
        - Normalizes vectors (L2) for consistent cosine similarity
        """
        if not texts:
            return []

        all_vectors: list[list[float]] = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(total_batches):
            batch = texts[batch_idx * self.batch_size : (batch_idx + 1) * self.batch_size]
            vectors = self._embed_with_retry(batch, batch_idx, total_batches)
            all_vectors.extend(vectors)

        return all_vectors

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a single query string.
        bge models recommend prefixing queries with "Represent this sentence:".
        """
        prefixed = f"Represent this sentence: {query}"
        return self.embed_texts([prefixed])[0]

    def _embed_with_retry(
        self,
        batch: list[str],
        batch_idx: int,
        total_batches: int,
    ) -> list[list[float]]:
        """Embed one batch with exponential backoff retries."""
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                vectors = self._model.encode(
                    batch,
                    normalize_embeddings=True,   # L2 normalize for cosine similarity
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                logger.debug(
                    "embedder.batch_done",
                    batch=f"{batch_idx + 1}/{total_batches}",
                    size=len(batch),
                )
                return [v.tolist() for v in vectors]

            except Exception as e:
                last_error = e
                wait = 2 ** attempt          # 1s, 2s, 4s
                logger.warning(
                    "embedder.retry",
                    attempt=attempt + 1,
                    max=self.max_retries,
                    error=str(e),
                    wait_s=wait,
                )
                time.sleep(wait)

        raise RuntimeError(
            f"Embedding failed after {self.max_retries} attempts: {last_error}"
        )


@lru_cache(maxsize=1)
def get_embedder() -> EmbeddingClient:
    """
    Singleton embedder — model is loaded once and reused.
    Uses lru_cache so multiple callers share the same instance.
    """
    return EmbeddingClient()
