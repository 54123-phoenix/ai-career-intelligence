"""Unit tests for Retrieval Agent — T-002."""

from __future__ import annotations

import pytest

from backend.shared.types import MatchResult, StructuredJob, StructuredResume

# Orthogonal vectors — normalized [0.1]*384 ≈ normalized [0.9]*384 (same direction),
# so use vectors with weight on different dimensions for meaningful cosine tests.
V1 = [1.0] + [0.0] * 383   # weight on dim 0
V2 = [0.0] * 383 + [1.0]   # weight on dim 383 — orthogonal to V1


# ---------------------------------------------------------------------------
# Text flattening (no embedding model needed)
# ---------------------------------------------------------------------------

class TestTextFlattening:
    def test_resume_to_text_extracts_all_fields(self):
        from backend.retrieval.schemas import resume_to_text

        resume = StructuredResume(
            resume_id="r1",
            name="Test",
            summary="Backend engineer",
            skills=["Python", "FastAPI"],
        )
        text = resume_to_text(resume)
        assert "Backend engineer" in text
        assert "Python" in text
        assert "FastAPI" in text

    def test_resume_to_text_empty(self):
        from backend.retrieval.schemas import resume_to_text

        resume = StructuredResume(resume_id="r1", name="Test")
        text = resume_to_text(resume)
        assert text == "" or text.strip() == ""

    def test_job_to_text(self):
        from backend.retrieval.schemas import job_to_text

        job = StructuredJob(
            job_id="j1",
            title="Senior Backend Engineer",
            company="Acme",
            required_skills=["Python", "Docker"],
            description="Build APIs",
        )
        text = job_to_text(job)
        assert "Senior Backend Engineer" in text
        assert "Python" in text
        assert "Build APIs" in text


# ---------------------------------------------------------------------------
# MatchResult model
# ---------------------------------------------------------------------------

class TestMatchResult:
    def test_valid_result(self):
        r = MatchResult(
            item_id="j1",
            score=0.87,
            payload={"title": "Engineer"},
            match_type="resume_to_job",
        )
        assert r.score == 0.87
        assert r.match_type == "resume_to_job"

    def test_score_bounds(self):
        with pytest.raises(Exception):
            MatchResult(item_id="x", score=1.5, payload={}, match_type="resume_to_job")


# ---------------------------------------------------------------------------
# QdrantStore (in-memory)
# ---------------------------------------------------------------------------

class TestQdrantStore:
    def test_upsert_and_search(self):
        from backend.retrieval.qdrant_client import QdrantStore

        s = QdrantStore(location=":memory:")
        s.upsert_job("j1", V1, {"title": "Engineer"})
        s.upsert_job("j2", V2, {"title": "Designer"})

        results = s.search("jobs", V1, top_k=1)
        assert len(results) == 1
        assert results[0]["id"] == "j1"
        assert results[0]["score"] > 0.99

    def test_score_threshold(self):
        from backend.retrieval.qdrant_client import QdrantStore

        s = QdrantStore(location=":memory:")
        s.upsert_job("j1", V1, {"title": "X"})
        s.upsert_job("j2", V2, {"title": "Y"})

        results = s.search("jobs", V1, top_k=5, score_threshold=0.9)
        assert len(results) == 1
        assert results[0]["id"] == "j1"


# ---------------------------------------------------------------------------
# Embedder (model-dependent — skip in CI without network)
# ---------------------------------------------------------------------------

class TestEmbedderLazyLoad:
    def test_dim_constant(self):
        from backend.retrieval.embedder import Embedder

        e = Embedder()
        assert e.dim == 384


# ---------------------------------------------------------------------------
# Retriever integration (in-memory Qdrant, mock embedding)
# ---------------------------------------------------------------------------

class TestRetriever:
    def test_index_and_search_resume_to_job(self):
        from backend.retrieval.retriever import Retriever

        r = Retriever()
        r.reset()

        # Use pre-computed orthogonal embeddings to bypass model download
        resume = StructuredResume(
            resume_id="r99",
            name="Alice",
            skills=["Python"],
            summary="Backend dev",
            skill_embedding=V1,
        )
        job = StructuredJob(
            job_id="j99",
            title="Python Dev",
            company="Co",
            required_skills=["Python"],
            job_embedding=V1,
        )

        import asyncio

        asyncio.run(r.index_resume(resume))
        asyncio.run(r.index_job(job))

        results = asyncio.run(r.search_jobs(resume, top_k=3))
        assert len(results) >= 1
        assert results[0].match_type == "resume_to_job"
        assert results[0].score > 0.99
