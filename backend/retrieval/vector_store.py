"""Job-embedding vector store — minimal Qdrant wrapper.

Provides exactly two operations:
  upsert_job_embedding  — write a job vector + metadata
  search_similar_jobs   — cosine-search top-k jobs by query vector

No matcher logic. No scoring beyond raw cosine distance.
"""

from __future__ import annotations

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .schemas import COLLECTION_JOBS, EMBEDDING_DIM

_POINT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _to_uuid(id_str: str) -> str:
    return str(uuid.uuid5(_POINT_NAMESPACE, id_str))


class JobVectorStore:
    """Purpose-built store for job embeddings only.

    Usage:
        store = JobVectorStore()
        store.upsert_job_embedding("job-001", [0.1, 0.2, ...], {"title": "BE", ...})
        hits = store.search_similar_jobs([0.15, 0.25, ...], top_k=5)
    """

    def __init__(self, location: str = ":memory:"):
        self._client = QdrantClient(location=location)
        self._id_map: dict[str, str] = {}       # original → uuid
        self._reverse_map: dict[str, str] = {}  # uuid → original
        self._ensure_collection()

    # ---- collection ---------------------------------------------------------

    def _ensure_collection(self):
        if not self._client.collection_exists(COLLECTION_JOBS):
            self._client.create_collection(
                collection_name=COLLECTION_JOBS,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

    def _map_id(self, original: str) -> str:
        uid = _to_uuid(original)
        self._id_map[original] = uid
        self._reverse_map[uid] = original
        return uid

    def reset(self):
        if self._client.collection_exists(COLLECTION_JOBS):
            self._client.delete_collection(COLLECTION_JOBS)
        self._id_map.clear()
        self._reverse_map.clear()
        self._ensure_collection()

    # ---- write --------------------------------------------------------------

    def upsert_job_embedding(
        self,
        job_id: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Index a single job embedding into Qdrant.

        Args:
            job_id:    Original job identifier (e.g., "job-042").
            embedding: Normalized dense vector (dim must match EMBEDDING_DIM).
            metadata:  Arbitrary payload dict stored alongside the vector.
        """
        pts = [
            PointStruct(
                id=self._map_id(job_id),
                vector=embedding,
                payload=metadata or {},
            )
        ]
        self._client.upsert(collection_name=COLLECTION_JOBS, points=pts)

    # ---- read ---------------------------------------------------------------

    def search_similar_jobs(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        """Cosine-similarity search over indexed job embeddings.

        Args:
            query_embedding: Normalized query vector.
            top_k:           Max results to return.
            score_threshold: Minimum cosine similarity (0.0 = no filter).

        Returns:
            List of {job_id, score, metadata}, sorted by score descending.
        """
        results = self._client.query_points(
            collection_name=COLLECTION_JOBS,
            query=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
        ).points

        return [
            {
                "job_id": self._reverse_map.get(hit.id, hit.id),
                "score": round(hit.score, 4),
                "metadata": hit.payload or {},
            }
            for hit in results
        ]
