"""End-to-end tests for the L2 match chain: StructuredResume → Qdrant → Top3JobMatch."""

from __future__ import annotations

import asyncio

import pytest

from backend.shared.types import MatchResult, StructuredJob, StructuredResume

# Pre-computed orthogonal vectors (384-dim) to bypass embedding model download
V1 = [1.0] + [0.0] * 383
V2 = [0.0] * 383 + [1.0]
V3 = [0.5] * 384


class TestMatchE2E:
    def test_full_match_flow(self):
        """Index jobs → search with resume → verify top match returned."""
        from backend.retrieval.retriever import Retriever
        from backend.retrieval.matcher import JobMatcher

        r = Retriever()
        r.reset()

        # Index 3 jobs with pre-computed embeddings
        jobs = [
            ("job-py", "Python Backend", ["Python", "FastAPI", "PostgreSQL"], V1),
            ("job-fe", "Frontend Dev", ["React", "TypeScript"], V2),
            ("job-ml", "ML Engineer", ["Python", "TensorFlow"], V3),
        ]
        for jid, title, skills, vec in jobs:
            job = StructuredJob(
                job_id=jid,
                title=title,
                company="ACME",
                required_skills=skills,
                job_embedding=vec,
            )
            asyncio.run(r.index_job(job))

        # Resume with V1 embedding (matches "Python Backend" best)
        resume = StructuredResume(
            resume_id="r1",
            name="Alice",
            skills=["Python", "FastAPI", "Docker"],
            summary="Backend engineer",
            skill_embedding=V1,
        )

        matcher = JobMatcher()
        matches = matcher.match_from_store(resume, top_k=3)

        assert len(matches) >= 1
        # Top match should be job-py because V1 aligns with V1
        assert matches[0].item_id == "job-py"
        assert matches[0].score > 0.9

    def test_empty_store_returns_empty(self):
        """Search before indexing should return empty list."""
        from backend.retrieval.retriever import Retriever
        from backend.retrieval.matcher import JobMatcher

        r = Retriever()
        r.reset()

        resume = StructuredResume(
            resume_id="r-empty",
            name="Test",
            skill_embedding=V1,
        )

        matcher = JobMatcher()
        matches = matcher.match_from_store(resume, top_k=5)
        assert matches == []

    def test_skill_gap_calculation(self):
        """Verify missing_skills in match payload."""
        from backend.retrieval.retriever import Retriever
        from backend.retrieval.matcher import JobMatcher

        r = Retriever()
        r.reset()

        job = StructuredJob(
            job_id="j-gap",
            title="Full Stack",
            company="Co",
            required_skills=["Python", "React", "Go"],
            job_embedding=V3,
        )
        asyncio.run(r.index_job(job))

        # Candidate only has Python, missing React + Go
        resume = StructuredResume(
            resume_id="r-gap",
            name="Bob",
            skills=["Python"],
            skill_embedding=V3,
        )

        matcher = JobMatcher()
        matches = matcher.match_from_store(resume, top_k=1)

        assert len(matches) == 1
        missing = matches[0].payload["missing_skills"]
        assert "React" in missing
        assert "Go" in missing
        assert "Python" not in missing

    def test_score_threshold_filters(self):
        """Verify score_threshold filters low-scoring results."""
        from backend.retrieval.retriever import Retriever
        from backend.retrieval.matcher import JobMatcher

        r = Retriever()
        r.reset()

        job = StructuredJob(
            job_id="j-high",
            title="Top Match",
            company="Co",
            required_skills=["Python"],
            job_embedding=V1,
        )
        asyncio.run(r.index_job(job))

        resume = StructuredResume(
            resume_id="r-filter",
            name="Test",
            skill_embedding=V1,
        )

        matcher = JobMatcher()
        # High threshold should still pass since V1 matches V1
        matches_high = matcher.match_from_store(resume, top_k=5, score_threshold=0.95)
        assert len(matches_high) >= 1

        # With threshold > 1.0, nothing passes
        matches_impossible = matcher.match_from_store(resume, top_k=5, score_threshold=1.01)
        assert len(matches_impossible) == 0

    def test_top_k_limits_results(self):
        """Verify top_k respects result count limit."""
        from backend.retrieval.retriever import Retriever
        from backend.retrieval.matcher import JobMatcher

        r = Retriever()
        r.reset()

        same_vec = [1.0 / (384 ** 0.5)] * 384  # normalized
        for i in range(5):
            job = StructuredJob(
                job_id=f"j{i}",
                title=f"Job {i}",
                company="Co",
                required_skills=["Python"],
                job_embedding=same_vec,
            )
            asyncio.run(r.index_job(job))

        resume = StructuredResume(
            resume_id="r-topk",
            name="Test",
            skill_embedding=same_vec,
        )

        matcher = JobMatcher()
        matches = matcher.match_from_store(resume, top_k=3)
        assert len(matches) == 3
