"""Semantic job matcher — resume vs job embeddings → top-k MatchResult.

Responsibilities (and nothing else):
  1. Compare resume embedding against job embeddings (cosine similarity)
  2. Return top-k MatchResult[] with missing_skills computed
  3. No reranking beyond raw cosine sort — MVP scope.
"""

from __future__ import annotations

import math

from backend.shared.types import MatchResult, StructuredJob, StructuredResume

from .embedder import embedder
from .qdrant_client import store as default_store


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Raw cosine sim for two vectors of equal dimension (already normalized or not)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _missing_skills(resume_skills: list[str], job_required: list[str]) -> list[str]:
    """Skills the job requires but the candidate does not possess."""
    candidate_set = {s.lower().strip() for s in resume_skills}
    return [s for s in job_required if s.lower().strip() not in candidate_set]


class JobMatcher:
    """Match a resume against a set of jobs via cosine similarity on embeddings.

    Two modes:
      - Direct:  provide a list of StructuredJob → embed on-the-fly, compare, return top-k
      - Indexed: jobs already in JobVectorStore → delegate to vector search
    """

    def __init__(self, store=None):
        self._store = store or default_store

    # ---- direct mode ---------------------------------------------------------

    def match(
        self,
        resume: StructuredResume,
        jobs: list[StructuredJob],
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[MatchResult]:
        """Direct matching: compare resume vs jobs via cosine similarity.

        Uses pre-computed embeddings (job_embedding / skill_embedding) when
        available, falling back to the embedder model only when needed.

        Use this when jobs are NOT already indexed in the vector store.
        """
        if not jobs:
            return []

        query_vec = resume.skill_embedding or embedder.encode_resume(resume)
        job_vecs = self._get_job_vectors(jobs)

        scored: list[tuple[float, int]] = []
        for i, jv in enumerate(job_vecs):
            sim = _cosine_similarity(query_vec, jv)
            if sim >= score_threshold:
                scored.append((sim, i))

        scored.sort(key=lambda x: x[0], reverse=True)
        scored = scored[:top_k]

        return [
            self._build_result(jobs[idx], round(sim, 4), resume.skills)
            for sim, idx in scored
        ]

    def _get_job_vectors(self, jobs: list[StructuredJob]) -> list[list[float]]:
        """Extract job vectors — pre-computed when available, otherwise batch-encode."""
        missing_indices: list[int] = []
        vectors: list[list[float]] = [None] * len(jobs)  # type: ignore[list-item]
        for i, j in enumerate(jobs):
            if j.job_embedding:
                vectors[i] = j.job_embedding
            else:
                missing_indices.append(i)
        if missing_indices:
            missing_jobs = [jobs[i] for i in missing_indices]
            encoded = embedder.encode_batch(missing_jobs, item_type="job")
            for i, vec in zip(missing_indices, encoded):
                vectors[i] = vec
        return vectors

    # ---- indexed mode --------------------------------------------------------

    def match_from_store(
        self,
        resume: StructuredResume,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[MatchResult]:
        """Indexed matching: search pre-indexed jobs via QdrantStore.

        Use this when jobs have been upserted via Retriever.index_job().
        """
        from .schemas import COLLECTION_JOBS

        query_vec = resume.skill_embedding or embedder.encode_resume(resume)
        try:
            hits = self._store.search(
                collection=COLLECTION_JOBS,
                query_vector=query_vec,
                top_k=top_k,
                score_threshold=score_threshold,
            )
        except Exception:
            # Qdrant unreachable — return empty rather than crash
            return []

        results: list[MatchResult] = []
        for h in hits:
            payload = h["payload"]
            required = payload.get("required_skills", [])
            results.append(
                MatchResult(
                    item_id=h["id"],
                    score=h["score"],
                    payload={
                        "title": payload.get("title", ""),
                        "company": payload.get("company", ""),
                        "required_skills": required,
                        "optional_skills": payload.get("optional_skills", []),
                        "salary_range": payload.get("salary_range"),
                        "level": payload.get("level", ""),
                        "location": payload.get("location", ""),
                        "missing_skills": _missing_skills(resume.skills, required),
                    },
                    match_type="resume_to_job",
                )
            )
        return results

    # ---- helpers -------------------------------------------------------------

    def _build_result(self, job: StructuredJob, score: float, resume_skills: list[str]) -> MatchResult:
        return MatchResult(
            item_id=job.job_id,
            score=score,
            payload={
                "title": job.title,
                "company": job.company,
                "required_skills": job.required_skills,
                "optional_skills": job.optional_skills,
                "salary_range": list(job.salary_range) if job.salary_range else None,
                "level": job.level,
                "location": job.location,
                "missing_skills": _missing_skills(resume_skills, job.required_skills),
            },
            match_type="resume_to_job",
        )
