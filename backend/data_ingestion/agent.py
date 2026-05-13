"""DataIngestionAgent — orchestrates multiple source adapters for job data ingestion.

Delegates normalization to existing normalize() + ingest_batch() in normalizer.py.
Each registered adapter implements the SourceAdapter Protocol from sources/base.py.
"""

from __future__ import annotations

from backend.data_ingestion.normalizer import ingest_batch
from backend.data_ingestion.schemas import IngestionResult, RawJobPosting, UnifiedJob


class DataIngestionAgent:
    """Ingest data from registered adapters and normalize to UnifiedJob.

    Acts as the runtime agent for T005's data_ingestion_agent role.
    Maintains a cache of ingested jobs queryable by source.

    Usage:
        agent = DataIngestionAgent()
        agent.register_adapter(MockJobSource())
        results = await agent.ingest_all()
        jobs = agent.get_jobs(sources=["mock"])
    """

    def __init__(self):
        self._adapters: dict[str, object] = {}
        self._jobs: dict[str, list[UnifiedJob]] = {}  # source_name → cached jobs

    def register_adapter(self, adapter: object) -> None:
        """Register a SourceAdapter implementation.

        The adapter must have:
          - source_name: str attribute
          - async fetch() → list[dict]
          - normalize(raw: dict) → dict
        """
        name = getattr(adapter, "source_name", None)
        if not name:
            raise ValueError(f"Adapter {adapter!r} missing 'source_name' attribute")
        self._adapters[name] = adapter

    def unregister_adapter(self, source_name: str) -> None:
        """Remove a registered adapter."""
        self._adapters.pop(source_name, None)
        self._jobs.pop(source_name, None)

    async def ingest_from_source(self, source_name: str) -> IngestionResult:
        """Fetch + normalize from one registered source.

        Raises ValueError if source is not registered.
        """
        adapter = self._adapters.get(source_name)
        if adapter is None:
            raise ValueError(
                f"Source '{source_name}' not registered. "
                f"Available: {list(self._adapters.keys())}"
            )

        raw_dicts: list[dict] = await adapter.fetch()  # type: ignore[union-attr]

        # Wrap each raw dict as RawJobPosting
        raw_posts: list[RawJobPosting] = []
        for d in raw_dicts:
            nd = adapter.normalize(d)  # type: ignore[union-attr]
            raw_posts.append(
                RawJobPosting(
                    source=nd.get("source", source_name),
                    raw_id=nd["raw_id"],
                    title=nd.get("title", ""),
                    company=nd.get("company", ""),
                    location=nd.get("location", ""),
                    salary_text=nd.get("salary_text", ""),
                    skills_text=nd.get("skills_text", ""),
                    description=nd.get("description", ""),
                    level=nd.get("level", ""),
                )
            )

        result = ingest_batch(raw_posts)
        self._jobs[source_name] = result.jobs
        return result

    async def ingest_all(self) -> list[IngestionResult]:
        """Fetch + normalize from all registered sources.

        Returns one IngestionResult per source, in registration order.
        """
        results: list[IngestionResult] = []
        for name in list(self._adapters.keys()):
            try:
                r = await self.ingest_from_source(name)
                results.append(r)
            except Exception as e:
                results.append(
                    IngestionResult(
                        source=name,
                        fetched=0,
                        normalized=0,
                        duplicates_skipped=0,
                        errors=1,
                        jobs=[],
                        elapsed_ms=0.0,
                    )
                )
        return results

    def get_jobs(
        self,
        sources: list[str] | None = None,
        limit: int | None = None,
    ) -> list[UnifiedJob]:
        """Retrieve cached UnifiedJobs, optionally filtered by source.

        Args:
            sources: If provided, only return jobs from these sources.
                     If None, return all cached jobs from all sources.
            limit: If provided, return at most this many jobs.
        """
        if sources:
            jobs: list[UnifiedJob] = []
            for s in sources:
                jobs.extend(self._jobs.get(s, []))
        else:
            jobs = []
            for jlist in self._jobs.values():
                jobs.extend(jlist)

        if limit is not None:
            jobs = jobs[:limit]
        return jobs

    def source_names(self) -> list[str]:
        """Return list of registered source names."""
        return list(self._adapters.keys())

    def clear(self) -> None:
        """Reset all caches and remove all adapters."""
        self._adapters.clear()
        self._jobs.clear()
