"""Data Ingestion API routes.

Endpoints:
  POST /api/v1/ingestion/ingest/{source_name}  — ingest from one source
  POST /api/v1/ingestion/ingest/all            — ingest from all sources
  GET  /api/v1/ingestion/sources               — list registered sources
  GET  /api/v1/ingestion/jobs                  — get cached jobs
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.data_ingestion.agent import DataIngestionAgent
from backend.data_ingestion.schemas import IngestionResult, UnifiedJob
from backend.data_ingestion.sources.mock_source import MockJobSource

from pydantic import BaseModel, Field

router = APIRouter()

# Module-level singleton — MockJobSource registered at startup
_agent = DataIngestionAgent()
_agent.register_adapter(MockJobSource())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/ingest/{source_name}", response_model=IngestionResult)
async def ingest_source(source_name: str):
    """Trigger ingestion from a single registered source.

    Returns IngestionResult with fetched / normalized / duplicates stats.
    """
    available = _agent.source_names()
    if source_name not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source_name}' not registered. Available: {available}",
        )
    try:
        result = await _agent.ingest_from_source(source_name)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ingestion failed for '{source_name}': {e}"
        )
    return result


@router.post("/ingest/all", response_model=list[IngestionResult])
async def ingest_all():
    """Trigger ingestion from all registered sources.

    Returns one IngestionResult per source.
    """
    return await _agent.ingest_all()


@router.get("/sources")
async def list_sources() -> dict:
    """List all registered data sources."""
    return {
        "sources": _agent.source_names(),
        "total": len(_agent.source_names()),
    }


@router.get("/jobs", response_model=list[UnifiedJob])
async def get_jobs(
    source: str | None = None,
    limit: int = 100,
):
    """Retrieve cached UnifiedJobs, optionally filtered by source."""
    sources = [source] if source else None
    return _agent.get_jobs(sources=sources, limit=limit)
