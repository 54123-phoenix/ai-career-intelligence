"""Integration tests: full T007 career pipeline."""

import pytest
from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer
from backend.career.career_architect import CareerArchitect
from backend.career.career_simulator import CareerSimulator
from backend.career.career_frontend import CareerFrontend


class TestCareerPipeline:
    def _run_full_pipeline(self, events_data: list[dict], user_id: str = "u1"):
        """Execute all 6 steps of the T007 pipeline."""
        # Step 1: Parse
        parser = CareerParser()
        events = parser.parse_batch(events_data, user_id)

        # Step 2: Retrieve
        retriever = CareerRetriever()
        retriever.ingest_batch(events)
        timeline = retriever.retrieve(user_id)

        # Step 3: Review
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)

        # Step 4: Architect
        architect = CareerArchitect()
        strategy = architect.design(timeline, analysis)

        # Step 5: Simulate
        simulator = CareerSimulator()
        simulation = simulator.simulate(strategy, analysis)

        # Step 6: Frontend
        frontend = CareerFrontend()
        viz = frontend.build(
            user_id=user_id,
            timeline=timeline,
            bottleneck=analysis,
            strategy=strategy,
            simulation=simulation,
        )

        return viz

    def test_full_pipeline_produces_visualization(self):
        events = [
            {"type": "application_sent", "company": "Google", "timestamp": "2026-01-01T00:00:00Z"},
            {"type": "application_sent", "company": "Meta", "timestamp": "2026-01-05T00:00:00Z"},
            {"type": "application_sent", "company": "Amazon", "timestamp": "2026-01-10T00:00:00Z"},
            {"type": "application_sent", "company": "Apple", "timestamp": "2026-01-15T00:00:00Z"},
            {"type": "application_sent", "company": "Netflix", "timestamp": "2026-01-20T00:00:00Z"},
            {"type": "interview", "outcome": "failure", "company": "Google",
             "skills_involved": ["Python", "SQL"], "timestamp": "2026-02-01T00:00:00Z"},
            {"type": "interview", "outcome": "failure", "company": "Meta",
             "skills_involved": ["Python", "Java"], "timestamp": "2026-02-15T00:00:00Z"},
            {"type": "skill_acquired", "skills_acquired": ["System Design"],
             "timestamp": "2026-03-01T00:00:00Z"},
            {"type": "interview", "outcome": "success", "company": "Amazon",
             "skills_involved": ["Python", "System Design"], "timestamp": "2026-03-15T00:00:00Z"},
            {"type": "offer_received", "company": "Amazon", "timestamp": "2026-03-20T00:00:00Z"},
        ]
        viz = self._run_full_pipeline(events, "career-user-1")
        assert viz.user_id == "career-user-1"
        assert viz.career_timeline is not None
        assert viz.bottleneck_summary is not None
        assert viz.current_strategy is not None
        assert viz.simulation_result is not None
        assert len(viz.data_sources) == 5

    def test_pipeline_identifies_bottleneck(self):
        events = [
            {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"},
        ]
        viz = self._run_full_pipeline(events)
        assert viz.bottleneck_summary is not None
        assert viz.bottleneck_summary.dominant_bottleneck != ""

    def test_pipeline_generates_actionable_strategy(self):
        events = [
            {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "interview", "outcome": "failure"},
        ]
        viz = self._run_full_pipeline(events)
        assert len(viz.current_strategy.action_plan) > 0
        for action in viz.current_strategy.action_plan:
            assert action.action != ""  # concrete, not empty

    def test_skill_graph_built(self):
        events = [
            {"type": "skill_acquired", "skills_acquired": ["Python"],
             "timestamp": "2026-01-01T00:00:00Z"},
            {"type": "skill_acquired", "skills_acquired": ["SQL"],
             "timestamp": "2026-03-01T00:00:00Z"},
        ]
        viz = self._run_full_pipeline(events)
        assert "dates" in viz.skill_graph
        assert "skills" in viz.skill_graph
        assert len(viz.skill_graph["dates"]) >= 2

    def test_empty_pipeline_handles_gracefully(self):
        """Empty events should not crash — outputs None for analysis/strategy."""
        retriever = CareerRetriever()
        timeline = retriever.retrieve("empty-user")
        assert timeline.total_events == 0

        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
        assert analysis.dominant_bottleneck == "insufficient_data"

        architect = CareerArchitect()
        strategy = architect.design(timeline, analysis)
        assert strategy.focus_skill != ""
        assert len(strategy.action_plan) <= 5
