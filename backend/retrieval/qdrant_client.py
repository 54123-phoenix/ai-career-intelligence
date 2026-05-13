"""Qdrant vector store wrapper — in-memory mode for MVP."""

from __future__ import annotations

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .schemas import (
    COLLECTION_JOBS,
    COLLECTION_RESUMES,
    EMBEDDING_DIM,
)

_POINT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _to_uuid(id_str: str) -> str:
    """Convert arbitrary string ID to a valid UUID for Qdrant local mode."""
    return str(uuid.uuid5(_POINT_NAMESPACE, id_str))


class QdrantStore:
    """Manages Qdrant collections for resume/job vectors.

    MVP: uses in-memory storage (":memory:"). Switch to local/remote
    by passing a different `location` to the constructor.
    """

    def __init__(self, location: str = ":memory:"):
        self._client = QdrantClient(location=location)
        self._id_map: dict[str, str] = {}  # original_id → uuid
        self._reverse_map: dict[str, str] = {}  # uuid → original_id
        self._ensure_collections()

    # ---- collection lifecycle ------------------------------------------------

    def _ensure_collections(self):
        for name in (COLLECTION_RESUMES, COLLECTION_JOBS):
            if not self._client.collection_exists(name):
                self._client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )

    def reset(self):
        """Drop and recreate all collections. Useful for testing."""
        for name in (COLLECTION_RESUMES, COLLECTION_JOBS):
            if self._client.collection_exists(name):
                self._client.delete_collection(name)
        self._id_map.clear()
        self._reverse_map.clear()
        self._ensure_collections()

    # ---- indexing -------------------------------------------------------------

    def _map_id(self, original: str) -> str:
        uid = _to_uuid(original)
        self._id_map[original] = uid
        self._reverse_map[uid] = original
        return uid

    def _original_id(self, uid: str) -> str:
        return self._reverse_map.get(uid, uid)

    def upsert_resume(self, resume_id: str, vector: list[float], payload: dict):
        self._client.upsert(
            collection_name=COLLECTION_RESUMES,
            points=[PointStruct(id=self._map_id(resume_id), vector=vector, payload=payload)],
        )

    def upsert_job(self, job_id: str, vector: list[float], payload: dict):
        self._client.upsert(
            collection_name=COLLECTION_JOBS,
            points=[PointStruct(id=self._map_id(job_id), vector=vector, payload=payload)],
        )

    def upsert_batch(
        self,
        collection: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ):
        points = [
            PointStruct(id=self._map_id(id_), vector=vec, payload=pl)
            for id_, vec, pl in zip(ids, vectors, payloads)
        ]
        self._client.upsert(collection_name=collection, points=points)

    # ---- search ---------------------------------------------------------------

    def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        """Raw vector search. Returns list of {id, score, payload}."""
        results = self._client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        ).points
        return [
            {
                "id": self._original_id(hit.id),
                "score": round(hit.score, 4),
                "payload": hit.payload or {},
            }
            for hit in results
        ]

    @property
    def client(self) -> QdrantClient:
        return self._client


# Module-level singleton
store = QdrantStore()
