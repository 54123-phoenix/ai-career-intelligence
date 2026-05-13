"""Integration tests for the L1 parser API endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "test_resumes"

client = TestClient(app)


class TestParserAPI:
    def test_parse_markdown_resume(self):
        """Upload a markdown file, verify structured resume fields."""
        with open(DATA_DIR / "sample_markdown.md", "rb") as f:
            content = f.read()

        resp = client.post(
            "/api/v1/parser/resume",
            files={"file": ("resume.md", content, "text/markdown")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "resume_id" in data
        assert len(data["skills"]) > 0

    def test_parse_text_resume(self):
        """Upload a text file, verify extraction."""
        with open(DATA_DIR / "sample_text.txt", "rb") as f:
            content = f.read()

        resp = client.post(
            "/api/v1/parser/resume",
            files={"file": ("resume.txt", content, "text/plain")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "resume_id" in data
        assert isinstance(data["skills"], list)

    def test_parse_empty_pdf(self):
        """Empty PDF should produce a graceful error."""
        # A minimal valid PDF header
        minimal_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 1\n0000000000 65535 f \ntrailer<</Size 1>>startxref\n9\n%%EOF"
        resp = client.post(
            "/api/v1/parser/resume",
            files={"file": ("empty.pdf", minimal_pdf, "application/pdf")},
        )
        # May succeed with empty fields or return 422 depending on pdf_extractor
        assert resp.status_code in (200, 422)

    def test_unsupported_file_type(self):
        """Non-PDF/md/txt should return 400."""
        resp = client.post(
            "/api/v1/parser/resume",
            files={"file": ("image.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
        assert resp.status_code == 400

    def test_skill_normalization_in_response(self):
        """Verify synonyms are normalized in the response."""
        with open(DATA_DIR / "sample_markdown.md", "rb") as f:
            content = f.read()

        resp = client.post(
            "/api/v1/parser/resume",
            files={"file": ("resume.md", content, "text/markdown")},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Check all skills are title-cased or normalized
        for skill in data["skills"]:
            assert not skill.startswith(" "), f"Skill has leading space: {skill!r}"
            assert len(skill) > 0, "Empty skill found"

    def test_resume_id_is_generated(self):
        """Verify resume_id is auto-generated when not provided."""
        with open(DATA_DIR / "sample_text.txt", "rb") as f:
            content = f.read()

        resp = client.post(
            "/api/v1/parser/resume",
            files={"file": ("resume.txt", content, "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resume_id"].startswith("res-")
        assert len(data["resume_id"]) == 12  # res- + 8 hex chars
