"""Retrieval-internal schemas — collection configs, embedding params."""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Embedding config
# ---------------------------------------------------------------------------
# Local fallback model (sentence-transformers)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# DashScope (primary for pre-computed embeddings per Constraint 3)
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v2")
DASHSCOPE_DIM = 1536
DASHSCOPE_DIM_V3 = 1024

def get_dashscope_dim() -> int:
    return DASHSCOPE_DIM_V3 if "v3" in DASHSCOPE_MODEL else DASHSCOPE_DIM

BATCH_SIZE = 32

# ---------------------------------------------------------------------------
# Qdrant collection configs
# ---------------------------------------------------------------------------
COLLECTION_RESUMES = "resumes"
COLLECTION_JOBS = "jobs"

VECTOR_PARAMS: dict = {
    "size": EMBEDDING_DIM,
    "distance": "Cosine",
}

# Payload indexing — fields searchable via Qdrant filters
RESUME_PAYLOAD_SCHEMA: dict = {
    "skills": {"type": "keyword", "is_array": True},
    "name": {"type": "text"},
}

JOB_PAYLOAD_SCHEMA: dict = {
    "required_skills": {"type": "keyword", "is_array": True},
    "optional_skills": {"type": "keyword", "is_array": True},
    "level": {"type": "keyword"},
    "title": {"type": "text"},
    "company": {"type": "text"},
    "location": {"type": "keyword"},
}


def resume_to_text(resume) -> str:
    """Flatten StructuredResume to a single searchable text for embedding."""
    from backend.shared.types import StructuredResume

    parts = [resume.summary, " ".join(resume.skills)]
    for proj in resume.projects:
        parts.append(f"{proj.name}: {proj.description}")
    for exp in resume.experience:
        parts.append(f"{exp.title} at {exp.company}: {exp.description}")
    return " ".join(filter(None, parts))


def job_to_text(job) -> str:
    """Flatten StructuredJob to a single searchable text for embedding."""
    from backend.shared.types import StructuredJob

    parts = [
        job.title,
        job.company,
        job.description,
        " ".join(job.required_skills),
        " ".join(job.optional_skills),
        job.level,
    ]
    return " ".join(filter(None, parts))
