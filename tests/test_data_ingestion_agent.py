"""Unit tests for Data Ingestion Agent — T005."""

from __future__ import annotations

import pytest

from backend.data_ingestion.schemas import IngestionResult, RawJobPosting, UnifiedJob


# ---------------------------------------------------------------------------
# MockJobSource
# ---------------------------------------------------------------------------


class TestMockSourceAdapter:
    def test_source_name(self):
        from backend.data_ingestion.sources.mock_source import MockJobSource

        source = MockJobSource()
        assert source.source_name == "mock"

    def test_normalize_returns_required_fields(self):
        from backend.data_ingestion.sources.mock_source import MockJobSource

        source = MockJobSource()
        raw = {"source": "mock", "raw_id": "m001", "title": "Engineer", "company": "ACME"}
        out = source.normalize(raw)
        assert out["source"] == "mock"
        assert out["raw_id"] == "m001"
        assert out["title"] == "Engineer"

    @pytest.mark.asyncio
    async def test_fetch_returns_list(self):
        from backend.data_ingestion.sources.mock_source import MockJobSource

        source = MockJobSource()
        results = await source.fetch()
        assert isinstance(results, list)
        assert len(results) >= 10

    @pytest.mark.asyncio
    async def test_fetch_results_have_required_keys(self):
        from backend.data_ingestion.sources.mock_source import MockJobSource

        source = MockJobSource()
        results = await source.fetch()
        for d in results:
            assert "raw_id" in d
            assert "title" in d
            assert "company" in d


# ---------------------------------------------------------------------------
# DataIngestionAgent
# ---------------------------------------------------------------------------


class TestDataIngestionAgent:
    def test_register_adapter(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        assert "mock" in agent.source_names()

    def test_register_adapter_missing_source_name_raises(self):
        from backend.data_ingestion.agent import DataIngestionAgent

        agent = DataIngestionAgent()

        class BadAdapter:
            pass

        with pytest.raises(ValueError, match="source_name"):
            agent.register_adapter(BadAdapter())

    def test_unregister_adapter(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        agent.unregister_adapter("mock")
        assert "mock" not in agent.source_names()

    def test_get_jobs_empty_initially(self):
        from backend.data_ingestion.agent import DataIngestionAgent

        agent = DataIngestionAgent()
        assert agent.get_jobs() == []

    @pytest.mark.asyncio
    async def test_ingest_from_source_produces_result(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        result = await agent.ingest_from_source("mock")
        assert isinstance(result, IngestionResult)
        assert result.source == "mock"
        assert result.fetched > 0
        assert result.normalized > 0
        assert len(result.jobs) > 0

    @pytest.mark.asyncio
    async def test_ingest_from_unknown_source_raises(self):
        from backend.data_ingestion.agent import DataIngestionAgent

        agent = DataIngestionAgent()
        with pytest.raises(ValueError, match="not registered"):
            await agent.ingest_from_source("nonexistent")

    @pytest.mark.asyncio
    async def test_ingest_all(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        results = await agent.ingest_all()
        assert len(results) == 1
        assert results[0].source == "mock"

    def test_get_jobs_after_ingest(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource
        import asyncio

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        asyncio.run(agent.ingest_all())
        jobs = agent.get_jobs()
        assert len(jobs) > 0
        assert all(isinstance(j, UnifiedJob) for j in jobs)

    def test_get_jobs_filter_by_source(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource
        import asyncio

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        asyncio.run(agent.ingest_all())
        jobs = agent.get_jobs(sources=["mock"])
        assert len(jobs) > 0
        jobs = agent.get_jobs(sources=["nonexistent"])
        assert jobs == []

    def test_get_jobs_limit(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource
        import asyncio

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        asyncio.run(agent.ingest_all())
        jobs = agent.get_jobs(limit=5)
        assert len(jobs) == 5

    def test_clear(self):
        from backend.data_ingestion.agent import DataIngestionAgent
        from backend.data_ingestion.sources.mock_source import MockJobSource

        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        agent.clear()
        assert agent.source_names() == []
        assert agent.get_jobs() == []


# ---------------------------------------------------------------------------
# IngestionResult
# ---------------------------------------------------------------------------


class TestIngestionResult:
    def test_valid_result(self):
        result = IngestionResult(
            source="mock",
            fetched=15,
            normalized=14,
            duplicates_skipped=1,
            errors=0,
            elapsed_ms=42.5,
        )
        assert result.fetched == 15
        assert result.normalized == 14
        assert result.duplicates_skipped == 1

    def test_default_values(self):
        result = IngestionResult(source="test")
        assert result.fetched == 0
        assert result.normalized == 0
        assert result.jobs == []
        assert result.elapsed_ms == 0.0
