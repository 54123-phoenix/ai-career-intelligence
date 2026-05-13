"""Tests for CareerRetriever."""

import pytest
from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever


class TestCareerRetriever:
    def test_retrieve_empty(self):
        r = CareerRetriever()
        t = r.retrieve("u1")
        assert t.user_id == "u1"
        assert t.total_events == 0
        assert t.recent_events == []

    def test_ingest_and_retrieve(self):
        r = CareerRetriever()
        p = CareerParser()
        events = p.parse_batch([
            {"type": "application_sent", "company": "Google", "timestamp": "2026-05-01T10:00:00Z"},
            {"type": "interview", "company": "Google", "timestamp": "2026-05-10T10:00:00Z"},
        ], "u1")
        r.ingest_batch(events)

        t = r.retrieve("u1")
        assert t.total_events == 2
        assert len(t.recent_events) == 2  # 2 <= 10

    def test_recent_events_limited_to_10(self):
        r = CareerRetriever()
        p = CareerParser()
        events = p.parse_batch([
            {"type": "application_sent", "company": f"C{i}"} for i in range(15)
        ], "u1")
        r.ingest_batch(events)
        t = r.retrieve("u1")
        assert len(t.recent_events) == 10

    def test_interview_success_failure_split(self):
        r = CareerRetriever()
        p = CareerParser()
        events = p.parse_batch([
            {"type": "interview", "outcome": "success", "company": "G"},
            {"type": "interview", "outcome": "failure", "company": "M"},
            {"type": "interview", "outcome": "success", "company": "A"},
        ], "u1")
        r.ingest_batch(events)
        t = r.retrieve("u1")
        assert len(t.interview_successes) == 2
        assert len(t.interview_failures) == 1

    def test_skill_trajectory(self):
        r = CareerRetriever()
        p = CareerParser()
        events = p.parse_batch([
            {"type": "skill_acquired", "skills_acquired": ["Python"], "timestamp": "2026-01-15T00:00:00Z"},
            {"type": "skill_acquired", "skills_acquired": ["SQL"], "timestamp": "2026-02-10T00:00:00Z"},
        ], "u1")
        r.ingest_batch(events)
        t = r.retrieve("u1")
        assert len(t.skill_trajectory) == 2  # 2 months

    def test_application_distribution(self):
        r = CareerRetriever()
        p = CareerParser()
        events = p.parse_batch([
            {"type": "application_sent"},
            {"type": "application_sent"},
            {"type": "application_sent"},
            {"type": "interview"},
        ], "u1")
        r.ingest_batch(events)
        t = r.retrieve("u1")
        assert t.application_distribution["application_sent"] == 3
        assert t.application_distribution["interview"] == 1

    def test_clear(self):
        r = CareerRetriever()
        p = CareerParser()
        r.ingest_batch(p.parse_batch([{"type": "application_sent"}], "u1"))
        r.clear("u1")
        assert r.retrieve("u1").total_events == 0
