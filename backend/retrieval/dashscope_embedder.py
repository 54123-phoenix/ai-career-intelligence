"""DashScope (通义千问) embedding client — primary embedding provider.

Per project Constraint 3: all pre-computed embeddings MUST use Alibaba DashScope.
Local sentence-transformers (embedder.py) serves as fallback when API key is absent.

Models:
  text-embedding-v2  → 1536 dims (recommended, best quality)
  text-embedding-v1  → 1536 dims
  text-embedding-v3  → 1024 dims (newest, supports task_type parameter)
"""

from __future__ import annotations

import os
from typing import Literal

from .schemas import job_to_text, resume_to_text

DASHSCOPE_MODEL = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v2")
DASHSCOPE_DIM = 1536  # text-embedding-v1/v2
DASHSCOPE_DIM_V3 = 1024  # text-embedding-v3
BATCH_SIZE = 25  # DashScope has rate limits; 25 per batch is safe


def _get_dim() -> int:
    return DASHSCOPE_DIM_V3 if "v3" in DASHSCOPE_MODEL else DASHSCOPE_DIM


class DashScopeEmbedder:
    """Embedder backed by Alibaba DashScope TextEmbedding API.

    Usage:
        embedder = DashScopeEmbedder()
        if embedder.available:
            vec = embedder.encode_resume(resume)
        else:
            # fall back to sentence-transformers
            from .embedder import embedder as local_embedder
            vec = local_embedder.encode_resume(resume)
    """

    def __init__(self, model: str | None = None):
        self._model = model or DASHSCOPE_MODEL
        self._api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self._dim = _get_dim()

    # ---- public properties ---------------------------------------------------

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def available(self) -> bool:
        return bool(self._api_key) and len(self._api_key) > 10

    @property
    def model_name(self) -> str:
        return self._model

    # ---- public API (mirrors embedder.Embedder interface) --------------------

    def encode_resume(self, resume) -> list[float]:
        text = resume_to_text(resume)
        return self._call_api(text)

    def encode_job(self, job) -> list[float]:
        text = job_to_text(job)
        return self._call_api(text)

    def encode_query(self, text: str) -> list[float]:
        return self._call_api(text)

    def encode_batch(
        self,
        items: list,
        item_type: Literal["resume", "job"] = "resume",
    ) -> list[list[float]]:
        fn = resume_to_text if item_type == "resume" else job_to_text
        texts = [fn(item) for item in items]
        results: list[list[float]] = []

        for i in range(0, len(texts), BATCH_SIZE):
            chunk = texts[i : i + BATCH_SIZE]
            batch_vectors = self._call_api_batch(chunk)
            results.extend(batch_vectors)

        return results

    # ---- internal ------------------------------------------------------------

    def _call_api(self, text: str) -> list[float]:
        """Single text → vector."""
        vectors = self._call_api_batch([text])
        if not vectors:
            raise RuntimeError("DashScope embedding returned empty result")
        return vectors[0]

    def _call_api_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch texts → vectors via DashScope TextEmbedding API."""
        import dashscope

        if not self.available:
            raise RuntimeError(
                "DashScope API key not configured. Set DASHSCOPE_API_KEY env var."
            )

        resp = dashscope.TextEmbedding.call(
            model=self._model,
            input=texts,
            api_key=self._api_key,
        )

        if resp.status_code != 200:
            raise RuntimeError(
                f"DashScope embedding failed: code={resp.status_code} "
                f"msg={resp.message}"
            )

        # resp.output["embeddings"] is a list of {"text_index": i, "embedding": [...]}
        embeddings = resp.output.get("embeddings", [])
        if not embeddings:
            raise RuntimeError("DashScope returned no embeddings")

        # Sort by text_index to preserve input order
        embeddings.sort(key=lambda e: e.get("text_index", 0))
        return [e["embedding"] for e in embeddings]


# Module-level singleton
dashscope_embedder = DashScopeEmbedder()
