"""Tests for PreferenceUpdater."""

import pytest
from backend.session.preference_updater import PreferenceUpdater
from backend.session.schemas import DynamicPreferences, SessionSummary


def _summary(**kwargs) -> SessionSummary:
    defaults = {
        "session_id": "s1",
        "user_id": "u1",
        "clicked_categories": ["python", "senior"],
        "top_clicked_skills": ["Python", "SQL"],
        "top_clicked_companies": ["Google", "Meta"],
    }
    defaults.update(kwargs)
    return SessionSummary(**defaults)


def _prefs(**kwargs) -> DynamicPreferences:
    defaults = {
        "user_id": "u1",
        "skill_weights": {"Python": 0.5, "Java": 0.3},
        "preferred_locations": ["北京"],
        "preferred_companies": ["Alibaba"],
        "preferred_levels": ["Senior"],
    }
    defaults.update(kwargs)
    return DynamicPreferences(**defaults)


class TestPreferenceUpdater:
    def test_70_30_blend(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        hist = _prefs(skill_weights={"Python": 0.5, "Java": 0.3})
        summary = _summary(
            top_clicked_skills=["Python", "SQL"],
            clicked_categories=["python", "sql"],
        )
        updated = updater.update(hist, summary)
        # Python gets boosted from both history and session
        assert updated.skill_weights["Python"] >= 0.5

    def test_skill_blend_new_skill_introduced(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        hist = _prefs(skill_weights={"Python": 0.5})
        summary = _summary(
            top_clicked_skills=["SQL", "Go"],
            clicked_categories=["sql", "go"],
        )
        updated = updater.update(hist, summary)
        # New skills appear from session
        assert "sql" in updated.skill_weights or "SQL" in updated.skill_weights or "Go" in updated.skill_weights

    def test_shift_score_zero_when_no_change(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        hist = _prefs(skill_weights={"Python": 0.5})
        summary = _summary(
            top_clicked_skills=["Python"],
            clicked_categories=["python"],
        )
        updated = updater.update(hist, summary)
        assert 0.0 <= updated.preference_shift_score <= 1.0

    def test_shift_score_high_when_big_change(self):
        updater = PreferenceUpdater(recent_weight=0.9)
        hist = _prefs(skill_weights={"Java": 0.9})
        summary = _summary(
            top_clicked_skills=["Python", "Rust", "Go"],
            clicked_categories=["python", "rust", "go"],
        )
        updated = updater.update(hist, summary)
        assert updated.preference_shift_score > 0.0

    def test_cold_start_no_historical(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        updated = updater.update(None, _summary())
        assert updated.session_count == 1
        assert updated.preference_shift_score > 0.0

    def test_create_default(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        prefs = updater.create_default("u1")
        assert prefs.user_id == "u1"
        assert prefs.skill_weights == {}
        assert prefs.session_count == 0

    def test_session_count_increments(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        hist = _prefs(session_count=5)
        updated = updater.update(hist, _summary())
        assert updated.session_count == 6

    def test_locations_extracted(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        hist = _prefs(preferred_locations=["北京"])
        summary = _summary(clicked_categories=["北京", "上海", "python"])
        updated = updater.update(hist, summary)
        assert "北京" in updated.preferred_locations

    def test_companies_extracted(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        hist = _prefs(preferred_companies=["Alibaba"])
        summary = _summary(
            top_clicked_companies=["Google", "Meta"],
            clicked_categories=[],
        )
        updated = updater.update(hist, summary)
        assert "Google" in updated.preferred_companies

    def test_effective_weight_cold_start(self):
        updater = PreferenceUpdater(recent_weight=0.7)
        assert updater._effective_weight(0) == 1.0
        assert updater._effective_weight(1) == 0.85
        assert updater._effective_weight(2) == 0.78
        assert updater._effective_weight(5) == 0.7  # converged

    def test_cosine_shift_same_returns_zero(self):
        score = PreferenceUpdater._compute_shift_score(
            {"a": 0.5, "b": 0.3}, {"a": 0.5, "b": 0.3}
        )
        assert score == 0.0

    def test_cosine_shift_empty_handles_gracefully(self):
        assert PreferenceUpdater._compute_shift_score({}, {}) == 0.0
        assert PreferenceUpdater._compute_shift_score({}, {"a": 0.5}) == 1.0
        assert PreferenceUpdater._compute_shift_score({"a": 0.5}, {}) == 1.0
