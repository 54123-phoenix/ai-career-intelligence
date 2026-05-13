"""CareerFrontend — convert T007 outputs to structured visualization JSON (T007 Step 6).

Output: CareerVisualization with timeline, skill_graph, bottleneck_summary,
current_strategy, simulation_result.

Output is pure JSON — designed for frontend rendering.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.career.schemas import (
    BottleneckAnalysis,
    CareerStrategy,
    CareerTimeline,
    CareerVisualization,
    StrategySimulation,
)


class CareerFrontend:
    """Convert T007 multi-agent outputs into frontend-ready visualization data.

    Usage:
        frontend = CareerFrontend()
        viz = frontend.build(
            user_id="u1",
            timeline=timeline,
            bottleneck=analysis,
            strategy=strategy,
            simulation=sim_result,
        )
    """

    def build(
        self,
        user_id: str,
        timeline: CareerTimeline | None = None,
        bottleneck: BottleneckAnalysis | None = None,
        strategy: CareerStrategy | None = None,
        simulation: StrategySimulation | None = None,
    ) -> CareerVisualization:
        """Build a complete CareerVisualization from all T007 agent outputs.

        Args:
            user_id: User identifier
            timeline: CareerTimeline from retrieval_agent (Step 2)
            bottleneck: BottleneckAnalysis from reviewer_agent (Step 3)
            strategy: CareerStrategy from architect_agent (Step 4)
            simulation: StrategySimulation from simulation_agent (Step 5)

        Returns:
            CareerVisualization with all 5 sections populated
        """
        viz = CareerVisualization(
            user_id=user_id,
            last_updated=datetime.now(timezone.utc).isoformat(),
            data_sources=[],
        )

        # 1. Career timeline
        if timeline is not None:
            viz.career_timeline = timeline
            viz.data_sources.append("career_timeline")

        # 2. Skill graph data
        if timeline is not None:
            viz.skill_graph = self._build_skill_graph(timeline)
            viz.data_sources.append("skill_graph")

        # 3. Bottleneck summary
        if bottleneck is not None:
            viz.bottleneck_summary = bottleneck
            viz.data_sources.append("bottleneck_summary")

        # 4. Current strategy
        if strategy is not None:
            viz.current_strategy = strategy
            viz.data_sources.append("current_strategy")

        # 5. Simulation result
        if simulation is not None:
            viz.simulation_result = simulation
            viz.data_sources.append("simulation_result")

        return viz

    def build_minimal(
        self,
        user_id: str,
        timeline: CareerTimeline | None = None,
        bottleneck: BottleneckAnalysis | None = None,
    ) -> CareerVisualization:
        """Build visualization with only timeline + bottleneck (no strategy yet)."""
        return self.build(
            user_id=user_id,
            timeline=timeline,
            bottleneck=bottleneck,
        )

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_skill_graph(timeline: CareerTimeline) -> dict:
        """Build skill graph data for frontend chart rendering.

        Returns:
            {dates: ["2026-01", "2026-02", ...],
             skills: {"Python": [0.3, 0.5, ...], "SQL": [0.5, 0.6, ...]}}
        """
        if not timeline.skill_trajectory:
            return {"dates": [], "skills": {}}

        snapshots = timeline.skill_trajectory
        dates = [s.date for s in snapshots]

        # Collect all skills across all snapshots
        all_skills: set[str] = set()
        for s in snapshots:
            all_skills.update(s.skills.keys())

        # Build per-skill value arrays (fill gaps with previous value or 0)
        skills_data: dict[str, list[float]] = {}
        for skill in sorted(all_skills):
            values: list[float] = []
            last_val = 0.0
            for s in snapshots:
                val = s.skills.get(skill, last_val)
                values.append(val)
                last_val = val
            skills_data[skill] = values

        return {"dates": dates, "skills": skills_data}
