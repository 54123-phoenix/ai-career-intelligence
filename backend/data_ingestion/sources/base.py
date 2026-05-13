"""SourceAdapter Protocol — all data sources implement this interface."""

from __future__ import annotations

from typing import Protocol

from backend.data_ingestion.schemas import IngestionResult


class SourceAdapter(Protocol):
    """Contract for any job data source (Boss, Lagou, Liepin, GitHub Jobs, etc.).

    Implementations live in backend/data_ingestion/sources/ and are registered
    via the module-level _ADAPTERS registry in normalizer.py.
    """

    source_name: str

    async def fetch(self) -> list[dict]:
        """Retrieve raw job postings from the source. Returns list of raw dicts."""
        ...

    def normalize(self, raw: dict) -> dict:
        """Convert one raw dict into UnifiedJob-compatible dict."""
        ...
