"""Normalizer — RawJobPosting → UnifiedJob via rule-based cleaning."""

from __future__ import annotations

import hashlib
import re
import time

from backend.data_ingestion.schemas import IngestionResult, RawJobPosting, UnifiedJob
from backend.parser.schemas import SKILL_SYNONYMS


def normalize(raw: RawJobPosting) -> UnifiedJob:
    """Convert a single RawJobPosting into a UnifiedJob."""
    job_id = _make_id(raw.source, raw.raw_id)
    skills = _extract_skills(raw.skills_text)

    return UnifiedJob(
        job_id=job_id,
        title=raw.title.strip(),
        company=raw.company.strip(),
        salary_range=_normalize_salary(raw.salary_text),
        location=raw.location.strip(),
        skills=skills,
        source=raw.source,
        timestamp=raw.fetched_at,
    )


def ingest_batch(raw_posts: list[RawJobPosting]) -> IngestionResult:
    """Normalize a batch and produce an IngestionResult with dedup stats."""
    t0 = time.perf_counter()
    seen: set[str] = set()
    jobs: list[UnifiedJob] = []
    errors = 0
    dupes = 0

    for raw in raw_posts:
        try:
            job = normalize(raw)
        except Exception:
            errors += 1
            continue

        dedup_key = f"{job.job_id}:{job.title.lower()}:{job.company.lower()}"
        if dedup_key in seen:
            dupes += 1
            continue
        seen.add(dedup_key)
        jobs.append(job)

    return IngestionResult(
        source=raw_posts[0].source if raw_posts else "unknown",
        fetched=len(raw_posts),
        normalized=len(jobs),
        duplicates_skipped=dupes,
        errors=errors,
        jobs=jobs,
        elapsed_ms=round((time.perf_counter() - t0) * 1000, 2),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_id(source: str, raw_id: str) -> str:
    raw = f"{source}:{raw_id}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _extract_skills(skills_text: str) -> list[str]:
    """Split comma/pipe-separated skill text and normalize each token."""
    if not skills_text.strip():
        return []
    parts = re.split(r"[,，、/|;；\s]+", skills_text)
    seen: set[str] = set()
    result: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        key = p.lower()
        canonical = SKILL_SYNONYMS.get(key, p)
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def _normalize_salary(raw: str) -> str:
    """Coerce salary text into a consistent format. Best-effort."""
    raw = raw.strip()
    if not raw or "面议" in raw or "negotiable" in raw.lower():
        return "面议"
    # "30K-50K" → standardize
    raw = raw.replace("k", "K").replace("K/月", "K").replace("K/年", "K")
    # Ensure K suffix
    if re.match(r"^\d+-\d+$", raw):
        return f"{raw}K/年"
    if re.match(r"^\d+K-\d+K$", raw):
        return f"{raw}/年"
    return raw
