"""Fallback strategies for graceful degradation.

Tier 1: Qdrant fails → local cosine similarity (in-memory brute-force)
Tier 2: LLM timeout → template-based regex extraction
Tier 3: Simulation errors → pre-built dialog samples

All fallbacks return the same response format as the primary path.
The frontend sees no difference.
"""

from __future__ import annotations

import math
import re


# ═══════════════════════════════════════════════════════════════════════════════
# Tier 1: Local Cosine Similarity (Qdrant fallback)
# ═══════════════════════════════════════════════════════════════════════════════


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Pure-Python cosine similarity — no external dependencies."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def local_search(
    query_vec: list[float],
    candidates: list[dict],
    top_k: int = 10,
    score_threshold: float = 0.0,
) -> list[dict]:
    """Brute-force cosine similarity search over in-memory candidates.

    Each candidate dict must have "vector" (list[float]) and "payload" (dict).
    Returns list of {score, payload} sorted by descending similarity.
    """
    scored = []
    for c in candidates:
        sim = cosine_similarity(query_vec, c["vector"])
        if sim >= score_threshold:
            scored.append((sim, c["payload"]))
    scored.sort(key=lambda x: -x[0])
    return [{"score": round(s, 4), "payload": p} for s, p in scored[:top_k]]


# ═══════════════════════════════════════════════════════════════════════════════
# Tier 2: Template-Based Resume Parsing (LLM fallback)
# ═══════════════════════════════════════════════════════════════════════════════


def template_parse(raw_text: str) -> dict:
    """Regex-based resume extraction when LLM is unavailable.

    Returns a dict that satisfies the StructuredResume schema contract.
    Reuses SECTION_PATTERNS from parser schemas for skill/email/phone extraction.
    """
    from backend.parser.schemas import SECTION_PATTERNS

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


# ═══════════════════════════════════════════════════════════════════════════════
# Tier 3: Pre-built Simulation Dialogs
# ═══════════════════════════════════════════════════════════════════════════════

PREBUILT_DIALOGS: list[dict] = [
    {
        "simulation_id": "fallback-001",
        "strategy_name": "balanced",
        "outcome": "accepted",
        "summary": {
            "headline": "Career path viable — balanced strategy recommended",
            "badge": {"label": "Moderate Fit", "color": "amber"},
            "stats": [
                {"label": "Estimated Success", "value": "72%"},
                {"label": "Time to Offer", "value": "~14 days"},
                {"label": "Skill Gaps", "value": "2 skills"},
            ],
        },
        "match_score": {
            "overall": 72,
            "gauge": {"label": "Moderate Fit", "value": 72, "color": "amber"},
        },
        "timeline": [
            {
                "phase": "preparation",
                "title": "Skills assessment & gap analysis",
                "duration_days": 5,
                "status": "pending",
            },
            {
                "phase": "application",
                "title": "Targeted applications to top-3 matches",
                "duration_days": 7,
                "status": "pending",
            },
            {
                "phase": "interview",
                "title": "Interview preparation & execution",
                "duration_days": 14,
                "status": "pending",
            },
        ],
        "skill_gap_chart": {
            "matched": ["Python", "FastAPI"],
            "missing": ["Kubernetes", "System Design"],
        },
        "recommendation_cards": [
            {
                "priority": 1,
                "type": "strategy",
                "title": "Adopt balanced application strategy",
                "description": "Mix skill building with targeted applications for best outcome.",
            },
            {
                "priority": 2,
                "type": "skill",
                "title": "Upskill in Kubernetes",
                "description": "Container orchestration is consistently required across top matches.",
            },
        ],
        "decision_path": [
            {
                "step": "applied",
                "action": "Candidate submitted application",
                "reasoning": "Match score meets balanced strategy threshold",
            },
            {
                "step": "screened",
                "action": "HR screen passed",
                "reasoning": "Core skills match job requirements",
            },
            {
                "step": "interview",
                "action": "Interview completed",
                "reasoning": "Technical assessment satisfactory",
            },
            {"step": "offer", "action": "Offer extended", "reasoning": "Candidate meets role requirements"},
        ],
        "hr_reasoning": "Candidate demonstrates relevant core skills with manageable gaps.",
        "candidate_actions": "Applied with balanced confidence level after skill assessment.",
        "failure_points": [],
        "confidence_score": {"overall": 0.72, "breakdown": {"skill_match": 0.7, "experience": 0.75}},
    }
]


def fallback_simulation_dialog() -> dict:
    """Return a pre-built simulation dialog when SimulationEngine fails."""
    return PREBUILT_DIALOGS[0]
