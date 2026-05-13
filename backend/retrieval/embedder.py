"""Embedding service — text to dense vector via sentence-transformers."""

from __future__ import annotations

from .schemas import BATCH_SIZE, EMBEDDING_DIM, EMBEDDING_MODEL, job_to_text, resume_to_text


class Embedder:
    """Thin wrapper around sentence-transformers. Caches model in instance."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self._model_name = model_name
        self._model = None

    @property
    def dim(self) -> int:
        return EMBEDDING_DIM

    def _lazy_load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)

    def encode_resume(self, resume) -> list[float]:
        """Encode a StructuredResume into a dense vector."""
        text = resume_to_text(resume)
        return self._encode_text(text)

    def encode_job(self, job) -> list[float]:
        """Encode a StructuredJob into a dense vector."""
        text = job_to_text(job)
        return self._encode_text(text)

    def encode_query(self, text: str) -> list[float]:
        """Encode a raw query string into a dense vector (e.g., for search_by_query)."""
        return self._encode_text(text)

    def encode_batch(self, items: list, item_type: str = "resume") -> list[list[float]]:
        """Batch encode for indexing efficiency. item_type ∈ {'resume', 'job'}."""
        self._lazy_load()
        fn = resume_to_text if item_type == "resume" else job_to_text
        texts = [fn(item) for item in items]
        embeddings = self._model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return [vec.tolist() for vec in embeddings]

    def _encode_text(self, text: str) -> list[float]:
        self._lazy_load()
        vec = self._model.encode(
            [text],
            normalize_embeddings=True,
        )
        return vec[0].tolist()


# Module-level singleton — agents share one model instance
embedder = Embedder()
