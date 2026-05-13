"""Semantic matching orchestration — the main public API of the retrieval module."""

from __future__ import annotations

import logging

from backend.shared.types import MatchResult, StructuredJob, StructuredResume

from .embedder import embedder
from .qdrant_client import COLLECTION_JOBS, COLLECTION_RESUMES, store

logger = logging.getLogger(__name__)


class Retriever:
    """Orchestrates embedding + vector search for resume↔job matching.

    Usage:
        retriever = Retriever()
        await retriever.index_resume(resume)
        matches = await retriever.search_jobs(resume, top_k=5)
    """

    def __init__(self):
        self._embedder = embedder
        self._store = store

    # ---- indexing ---------------------------------------------------------

    async def index_resume(self, resume: StructuredResume) -> str:
        """Index a resume into Qdrant. Returns resume_id."""
        vec = resume.skill_embedding or self._embedder.encode_resume(resume)
        self._store.upsert_resume(
            resume_id=resume.resume_id,
            vector=vec,
            payload={
                "name": resume.name,
                "skills": resume.skills,
                "summary": resume.summary,
            },
        )
        return resume.resume_id

    async def index_job(self, job: StructuredJob) -> str:
        """Index a job into Qdrant. Returns job_id."""
        vec = job.job_embedding or self._embedder.encode_job(job)
        self._store.upsert_job(
            job_id=job.job_id,
            vector=vec,
            payload={
                "title": job.title,
                "company": job.company,
                "required_skills": job.required_skills,
                "optional_skills": job.optional_skills,
                "salary_range": list(job.salary_range) if job.salary_range else None,
                "level": job.level,
                "location": job.location,
            },
        )
        return job.job_id

    async def index_jobs_batch(self, jobs: list[StructuredJob]) -> list[str]:
        """Batch-index multiple jobs."""
        ids = [j.job_id for j in jobs]
        vectors = self._embedder.encode_batch(jobs, item_type="job")
        payloads = [
            {
                "title": j.title,
                "company": j.company,
                "required_skills": j.required_skills,
                "optional_skills": j.optional_skills,
                "salary_range": list(j.salary_range) if j.salary_range else None,
                "level": j.level,
                "location": j.location,
            }
            for j in jobs
        ]
        self._store.upsert_batch(COLLECTION_JOBS, ids, vectors, payloads)
        return ids

    # ---- search -----------------------------------------------------------

    async def search_jobs(
        self,
        resume: StructuredResume,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[MatchResult]:
        """Search top-k matching jobs for a given resume."""
        query_vec = resume.skill_embedding or self._embedder.encode_resume(resume)
        hits = self._store.search(
            collection=COLLECTION_JOBS,
            query_vector=query_vec,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        return [
            MatchResult(
                item_id=h["id"],
                score=h["score"],
                payload=h["payload"],
                match_type="resume_to_job",
            )
            for h in hits
        ]

    async def search_resumes(
        self,
        job: StructuredJob,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[MatchResult]:
        """Search top-k matching resumes for a given job (reverse lookup)."""
        query_vec = job.job_embedding or self._embedder.encode_job(job)
        hits = self._store.search(
            collection=COLLECTION_RESUMES,
            query_vector=query_vec,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        return [
            MatchResult(
                item_id=h["id"],
                score=h["score"],
                payload=h["payload"],
                match_type="job_to_resume",
            )
            for h in hits
        ]

    # ---- text-query search ------------------------------------------------

    async def search_by_query(
        self,
        query_text: str,
        top_k: int = 20,
        score_threshold: float = 0.0,
        filters: dict | None = None,
    ) -> list[MatchResult]:
        """Search jobs by raw text query without requiring a StructuredResume.

        Encodes query text via the embedder, then performs vector search.
        No filtering is applied beyond Qdrant score_threshold — caller is
        responsible for post-filtering (location, salary, skills).

        Args:
            query_text: Natural language query (e.g., "Python 后端 北京")
            top_k: Max number of results
            score_threshold: Minimum cosine similarity score
            filters: Reserved for future Qdrant payload filters
        """
        vec = self._embedder.encode_query(query_text)
        hits = self._store.search(
            collection=COLLECTION_JOBS,
            query_vector=vec,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        return [
            MatchResult(
                item_id=h["id"],
                score=h["score"],
                payload=h["payload"],
                match_type="resume_to_job",
            )
            for h in hits
        ]

    # ---- lifecycle --------------------------------------------------------

    def reset(self):
        """Drop all indexed data. For testing / re-indexing."""
        self._store.reset()


# Module-level singleton
retriever = Retriever()
