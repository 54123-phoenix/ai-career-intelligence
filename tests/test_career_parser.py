"""Tests for CareerParser."""

import pytest
from backend.career.career_parser import CareerParser


class TestCareerParser:
    def test_parse_dict_event(self):
        p = CareerParser()
        e = p.parse({"type": "interview", "company": "Google", "job_title": "SDE"}, "u1")
        assert e.event_type == "interview"
        assert e.company == "Google"
        assert e.user_id == "u1"
        assert e.outcome == "pending"

    def test_parse_rejection_detects_failure(self):
        p = CareerParser()
        e = p.parse({"type": "rejection", "company": "Meta"}, "u1")
        assert e.event_type == "rejection"
        assert e.outcome == "failure"

    def test_parse_text_event(self):
        p = CareerParser()
        e = p.parse("interviewed at Google for SDE role", "u1")
        assert e.event_type == "interview"
        assert e.company == "Google"

    def test_parse_batch_sorts_by_timestamp(self):
        p = CareerParser()
        raw = [
            {"type": "rejection", "timestamp": "2026-05-10T12:00:00Z"},
            {"type": "application_sent", "timestamp": "2026-05-01T10:00:00Z"},
            {"type": "interview", "timestamp": "2026-05-05T14:00:00Z"},
        ]
        events = p.parse_batch(raw, "u1")
        assert events[0].event_type == "application_sent"
        assert events[1].event_type == "interview"
        assert events[2].event_type == "rejection"

    def test_alias_mapping(self):
        p = CareerParser()
        assert p._normalize_event_type("applied") == "application_sent"
        assert p._normalize_event_type("onsite") == "interview"
        assert p._normalize_event_type("tech") == "technical_test"

    def test_skills_parsed(self):
        p = CareerParser()
        e = p.parse({"type": "skill_acquired", "skills_acquired": ["Python", "SQL"]}, "u1")
        assert "Python" in e.skills_acquired
        assert "SQL" in e.skills_acquired

    def test_salary_parsed(self):
        p = CareerParser()
        e = p.parse({"type": "offer_received", "salary": [300, 450]}, "u1")
        assert e.salary_range == (300, 450)

    def test_defaults_applied(self):
        p = CareerParser()
        e = p.parse({}, "u1")
        assert e.event_type == "job_view"
        assert e.outcome == "neutral"
        assert e.user_id == "u1"
