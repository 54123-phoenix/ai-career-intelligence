"""One-shot Qdrant ingestion script — pre-compute embeddings and seed vector DB.

Uses DashScope (通义千问) as primary embedding provider per Constraint 3.
Falls back to local sentence-transformers when DASHSCOPE_API_KEY is absent.

SAFETY (Constraint 5):
  - Only UPSERTs new points; never deletes or drops existing collections
  - If a resume/job ID already exists in Qdrant, it is skipped
  - Run with --force to re-embed existing points (still no deletion)

Usage:
  python -m backend.retrieval.seed_qdrant              # seed with demo data
  python -m backend.retrieval.seed_qdrant --dry-run    # preview only, no writes
  python -m backend.retrieval.seed_qdrant --force      # re-embed existing points
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
QDRANT_PATH = os.getenv("QDRANT_PATH", str(Path(__file__).resolve().parent.parent.parent / "data" / "qdrant_storage"))


def _ensure_qdrant_path():
    Path(QDRANT_PATH).mkdir(parents=True, exist_ok=True)


# ── Embedder selection ───────────────────────────────────────────────────────


def _get_embedder():
    """Return (embedder, provider_name). Tries DashScope first, falls back to local."""
    from .dashscope_embedder import dashscope_embedder

    if dashscope_embedder.available:
        print(f"[embedder] Using DashScope {dashscope_embedder.model_name} ({dashscope_embedder.dim}d)")
        return dashscope_embedder, "dashscope"

    from .embedder import embedder as local_embedder

    print(f"[embedder] Using local {local_embedder._model_name} ({local_embedder.dim}d)")
    print("[embedder] Set DASHSCOPE_API_KEY to use DashScope (通义千问) for production quality.")
    return local_embedder, "local"


# ── Qdrant store with dimension awareness ────────────────────────────────────


def _get_store(embedding_dim: int):
    """Create Qdrant store with file persistence and the given vector dimension."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    from .schemas import COLLECTION_JOBS, COLLECTION_RESUMES

    _ensure_qdrant_path()
    client = QdrantClient(path=QDRANT_PATH)

    for name in (COLLECTION_RESUMES, COLLECTION_JOBS):
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )
            print(f"[qdrant] Created collection '{name}' (dim={embedding_dim})")
        else:
            # Verify dimension matches
            info = client.get_collection(name)
            existing_dim = info.config.params.vectors.size
            if existing_dim != embedding_dim:
                print(
                    f"[qdrant] WARNING: Collection '{name}' has dim={existing_dim}, "
                    f"but embedder produces dim={embedding_dim}. "
                    f"Embedding mismatch will cause errors."
                )

    return client


# ── Main ingestion logic ─────────────────────────────────────────────────────


def seed(dry_run: bool = False, force: bool = False) -> dict:
    """Seed Qdrant with demo resume and job embeddings.

    Returns summary dict with counts.
    """
    _ensure_qdrant_path()

    # Lazy import demo data — only when actually seeding
    from backend.simulation.demo_data import JOBS, RESUMES

    embedder, provider = _get_embedder()
    store = _get_store(embedder.dim)

    from .schemas import COLLECTION_JOBS, COLLECTION_RESUMES
    from .qdrant_client import _to_uuid

    # ── Check existing points ──────────────────────────────────────────────
    existing_resumes = _existing_ids(store, COLLECTION_RESUMES)
    existing_jobs = _existing_ids(store, COLLECTION_JOBS)

    # ── Embed + upsert resumes ─────────────────────────────────────────────
    resume_count = 0
    for rid, resume in RESUMES.items():
        uid = _to_uuid(rid)
        if uid in existing_resumes and not force:
            print(f"[skip] Resume '{rid}' ({resume.name}) already indexed")
            continue

        print(f"[embed] Resume '{rid}' ({resume.name})...", end=" ")
        start = time.time()
        vector = embedder.encode_resume(resume)
        elapsed = (time.time() - start) * 1000
        print(f"{elapsed:.0f}ms")

        if not dry_run:
            store.upsert(
                collection_name=COLLECTION_RESUMES,
                points=[_make_point(rid, vector, _resume_payload(resume))],
            )
        resume_count += 1

    # ── Embed + upsert jobs ────────────────────────────────────────────────
    job_count = 0
    for jid, job in JOBS.items():
        uid = _to_uuid(jid)
        if uid in existing_jobs and not force:
            print(f"[skip] Job '{jid}' ({job.title} @ {job.company}) already indexed")
            continue

        print(f"[embed] Job '{jid}' ({job.title} @ {job.company})...", end=" ")
        start = time.time()
        vector = embedder.encode_job(job)
        elapsed = (time.time() - start) * 1000
        print(f"{elapsed:.0f}ms")

        if not dry_run:
            store.upsert(
                collection_name=COLLECTION_JOBS,
                points=[_make_point(jid, vector, _job_payload(job))],
            )
        job_count += 1

    summary = {
        "provider": provider,
        "dimension": embedder.dim,
        "resumes_indexed": resume_count,
        "resumes_skipped": len(RESUMES) - resume_count,
        "jobs_indexed": job_count,
        "jobs_skipped": len(JOBS) - job_count,
        "total_new": resume_count + job_count,
        "dry_run": dry_run,
        "storage_path": QDRANT_PATH,
    }

    return summary


# ── Helpers ──────────────────────────────────────────────────────────────────


def _existing_ids(store, collection: str) -> set[str]:
    """Get all point IDs already in a collection (as UUIDs). Returns empty set on error."""
    try:
        result = store.scroll(collection_name=collection, limit=10_000)
        return {pt.id for pt in result[0]}
    except Exception:
        return set()


def _make_point(id_str: str, vector: list[float], payload: dict):
    """Create a Qdrant PointStruct, mapping string ID to UUID."""
    from qdrant_client.models import PointStruct

    from .qdrant_client import _to_uuid

    return PointStruct(id=_to_uuid(id_str), vector=vector, payload=payload)


def _resume_payload(resume) -> dict:
    """Extract searchable payload from StructuredResume."""
    return {
        "resume_id": resume.resume_id,
        "name": resume.name,
        "skills": resume.skills,
        "summary": resume.summary,
        "experience_companies": [e.company for e in resume.experience],
        "experience_titles": [e.title for e in resume.experience],
        "education_schools": [e.school for e in resume.education],
    }


def _job_payload(job) -> dict:
    """Extract searchable payload from StructuredJob."""
    return {
        "job_id": job.job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "level": job.level,
        "required_skills": job.required_skills,
        "optional_skills": job.optional_skills,
        "salary_range": job.salary_range,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def _print_summary(s: dict):
    print()
    print("=" * 60)
    print("  Qdrant Seeding Summary")
    print("=" * 60)
    print(f"  Provider:       {s['provider']}")
    print(f"  Dimension:      {s['dimension']}")
    print(f"  Resumes:        {s['resumes_indexed']} indexed, {s['resumes_skipped']} skipped")
    print(f"  Jobs:           {s['jobs_indexed']} indexed, {s['jobs_skipped']} skipped")
    print(f"  Total new:      {s['total_new']}")
    print(f"  Dry run:        {s['dry_run']}")
    print(f"  Storage:        {s['storage_path']}")
    print("=" * 60)
    if s["dry_run"]:
        print("  DRY RUN — no data was written.")
    print()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    s = seed(dry_run=dry_run, force=force)
    _print_summary(s)
