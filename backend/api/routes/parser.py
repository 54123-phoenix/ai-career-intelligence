"""L1 Parser API routes — POST /api/v1/parser/resume.

Parses uploaded PDF/text/markdown resumes into StructuredResume.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.parser import parse_resume

from pydantic import BaseModel

router = APIRouter()


class ResumeParseResponse(BaseModel):
    resume_id: str
    name: str
    skills: list[str]
    summary: str
    experience_count: int
    education_count: int


@router.post("/resume", response_model=ResumeParseResponse)
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """Upload a PDF/markdown/text resume, get structured data back."""
    filename = (file.filename or "").lower()
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if filename.endswith(".pdf"):
        source_type = "pdf"
    elif filename.endswith(".md") or filename.endswith(".markdown"):
        source_type = "markdown"
    elif filename.endswith(".txt"):
        source_type = "text"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Accepted: .pdf, .md, .txt",
        )

    content = await file.read()
    try:
        resume = await parse_resume(content, source_type=source_type)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    return ResumeParseResponse(
        resume_id=resume.resume_id,
        name=resume.name,
        skills=resume.skills,
        summary=resume.summary,
        experience_count=len(resume.experience),
        education_count=len(resume.education),
    )
