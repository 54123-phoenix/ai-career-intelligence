"""Resume parser — LLM extraction with rule-based fallback."""

from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime
from typing import Literal

from backend.shared.types import Education, Project, StructuredResume, WorkExperience
from backend.shared.llm_client import call_llm

from .exceptions import ParseError, SchemaValidationError
from .pdf_extractor import extract_text_from_pdf
from .schemas import RESUME_PARSE_PROMPT, SECTION_PATTERNS, normalize_skills


async def parse_resume(
    source: bytes | str,
    source_type: Literal["pdf", "markdown", "text"] = "pdf",
) -> StructuredResume:
    """Parse a resume file into StructuredResume.

    Pipeline: raw bytes → text extraction → LLM extraction → Pydantic validation.
    On LLM failure, falls back to regex-based extraction.
    """
    raw_text = _extract_text(source, source_type)

    try:
        result = await _llm_parse(raw_text)
    except Exception:
        result = _rule_parse(raw_text)

    resume = _validate(result, raw_text)
    return resume


def _extract_text(source: bytes | str, source_type: str) -> str:
    if source_type == "pdf":
        if isinstance(source, str):
            source = source.encode("utf-8")
        return extract_text_from_pdf(source)
    if isinstance(source, bytes):
        return source.decode("utf-8", errors="replace")
    return source


async def _llm_parse(raw_text: str) -> dict:
    prompt = RESUME_PARSE_PROMPT.format(resume_text=raw_text[:8000])
    response = await call_llm(prompt, temperature=0.1, max_retries=2)
    return _safe_json(response)


def _rule_parse(raw_text: str) -> dict:
    """Regex fallback when LLM fails. Best-effort field extraction."""
    skills: list[str] = []
    skill_match = SECTION_PATTERNS["skills"].search(raw_text)
    if skill_match:
        chunk = skill_match.group(1)
        skills = [s.strip() for s in re.split(r"[,，、/|]", chunk) if s.strip()]

    email_match = SECTION_PATTERNS["email"].search(raw_text)
    phone_match = SECTION_PATTERNS["phone"].search(raw_text)

    return {
        "name": "",
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "summary": "",
        "skills": skills,
        "projects": [],
        "education": [],
        "experience": [],
        "certifications": [],
    }


def _validate(data: dict, raw_text: str) -> StructuredResume:
    data["skills"] = normalize_skills(data.get("skills") or [])
    data.setdefault("name", "")
    data.setdefault("summary", "")
    data.setdefault("certifications", [])

    # Parse nested models
    for key, model_cls in [
        ("projects", Project),
        ("education", Education),
        ("experience", WorkExperience),
    ]:
        parsed: list = []
        for item in data.get(key) or []:
            if isinstance(item, dict):
                item = _coerce_dates(item)
                try:
                    parsed.append(model_cls(**item))
                except Exception:
                    continue
        data[key] = parsed

    data = _coerce_dates(data)

    try:
        data["resume_id"] = data.get("resume_id") or f"res-{uuid.uuid4().hex[:8]}"
        return StructuredResume(**data)
    except Exception as exc:
        raise SchemaValidationError(f"Pydantic validation failed: {exc}") from exc


def _coerce_dates(item: dict) -> dict:
    """Convert string dates to date objects."""
    for field in ("start_date", "end_date"):
        raw = item.get(field)
        if isinstance(raw, str) and raw.strip():
            try:
                item[field] = datetime.strptime(raw.strip(), "%Y-%m-%d").date()
            except ValueError:
                item[field] = None
        elif raw == "" or raw is None:
            item[field] = None
    return item


def _safe_json(raw: str) -> dict:
    """Extract JSON from LLM output, tolerating markdown fences."""
    raw = raw.strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        raw = m.group(0)
    return json.loads(raw)
