"""Unit tests for 3-tier fallback strategies."""

from __future__ import annotations

import pytest

from backend.shared.fallback import (
    PREBUILT_DIALOGS,
    cosine_similarity,
    fallback_simulation_dialog,
    local_search,
    template_parse,
)


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_zero_vector(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


class TestLocalSearch:
    def test_top_k_ranking(self):
        query = [1.0, 0.0, 0.0]
        candidates = [
            {"vector": [1.0, 0.0, 0.0], "payload": {"id": "best"}},
            {"vector": [0.0, 1.0, 0.0], "payload": {"id": "mid"}},
            {"vector": [-1.0, 0.0, 0.0], "payload": {"id": "worst"}},
        ]
        results = local_search(query, candidates, top_k=2)
        assert len(results) == 2
        assert results[0]["payload"]["id"] == "best"

    def test_score_threshold(self):
        query = [1.0, 0.0]
        candidates = [
            {"vector": [1.0, 0.0], "payload": {"id": "a"}},
            {"vector": [0.0, 1.0], "payload": {"id": "b"}},
        ]
        results = local_search(query, candidates, top_k=5, score_threshold=0.5)
        assert len(results) == 1
        assert results[0]["payload"]["id"] == "a"


class TestTemplateParse:
    def test_extracts_skills(self):
        text = "## 技能\nPython, FastAPI, Docker, Kubernetes\n\n## 经历"
        result = template_parse(text)
        assert "Python" in result["skills"]
        assert "FastAPI" in result["skills"]

    def test_extracts_email(self):
        text = "Email: alice@example.com\n技能: Python"
        result = template_parse(text)
        assert result["email"] == "alice@example.com"

    def test_empty_input(self):
        result = template_parse("")
        assert result["skills"] == []
        assert result["email"] is None


class TestFallbackDialog:
    def test_dialog_structure(self):
        dialog = fallback_simulation_dialog()
        assert "simulation_id" in dialog
        assert "summary" in dialog
        assert "match_score" in dialog
        assert "timeline" in dialog
        assert "recommendation_cards" in dialog

    def test_prebuilt_dialogs_not_empty(self):
        assert len(PREBUILT_DIALOGS) >= 1
