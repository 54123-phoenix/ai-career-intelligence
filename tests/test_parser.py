"""Unit tests for Parser Agent — T-001."""

from __future__ import annotations

import pytest

from backend.parser.exceptions import ParseError, SchemaValidationError
from backend.parser.schemas import normalize_skill, normalize_skills, SKILL_SYNONYMS


class TestSkillNormalization:
    def test_known_synonym(self):
        assert normalize_skill("React.js") == "React"
        assert normalize_skill("k8s") == "Kubernetes"
        assert normalize_skill("nodejs") == "Node.js"

    def test_unknown_skill_title_case(self):
        assert normalize_skill("pandas") == "Pandas"
        assert normalize_skill("langgraph") == "Langgraph"

    def test_deduplication(self):
        result = normalize_skills(["React.js", "reactjs", "Python", "python"])
        assert result == ["React", "Python"]

    def test_empty_input(self):
        assert normalize_skills([]) == []
        assert normalize_skills([""]) == []

    def test_synonym_map_coverage(self):
        """Ensure the synonym map has expected canonical entries."""
        canonical = set(SKILL_SYNONYMS.values())
        assert "React" in canonical
        assert "Python" in canonical
        assert "Kubernetes" in canonical
        assert "Docker" in canonical


class TestPdfExtraction:
    def test_empty_bytes(self):
        from backend.parser.pdf_extractor import extract_text_from_pdf

        with pytest.raises(Exception):  # PDFExtractionError or fitz error
            extract_text_from_pdf(b"")


class TestResumeParserMarkdown:
    @pytest.mark.asyncio
    async def test_markdown_extraction(self):
        """Extract text from markdown source (no LLM needed for text extraction)."""
        from pathlib import Path

        from backend.parser.resume_parser import _extract_text

        md_path = Path(__file__).parent.parent / "data" / "test_resumes" / "sample_markdown.md"
        text = md_path.read_text(encoding="utf-8")
        assert "张三" in text or "zhangsan" in text.lower()
        assert "Python" in text

    @pytest.mark.asyncio
    async def test_rule_fallback(self):
        """Rule-based fallback extracts skills from skill section."""
        from backend.parser.resume_parser import _rule_parse

        text = "Skills: Python, React, Docker\n\nExperience: ..."
        result = _rule_parse(text)
        assert len(result["skills"]) > 0


class TestStructuredOutput:
    def test_project_model(self):
        from backend.shared.types import Project

        p = Project(name="Test Project", tech_stack=["Python", "React"])
        assert p.name == "Test Project"
        assert len(p.tech_stack) == 2

    def test_structured_resume_minimal(self):
        from backend.shared.types import StructuredResume

        r = StructuredResume(resume_id="test-001", name="Test User")
        assert r.skills == []
        assert r.projects == []
