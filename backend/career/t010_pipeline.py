"""T010 Pipeline — Lightweight Career Growth (Core Layer).

Wraps T009 with strict lightweight constraints:
  - 3-5 strategy candidates only
  - Short-term simulation (≤10 rounds, high-confidence priority)
  - Single-user focus with explicit upgrade interface hooks on every agent
  - Every agent output carries UpgradeInterface metadata

Usage:
    pipeline = T010Pipeline()
    output = pipeline.run(user_input, career_dataset)
    # output.upgrade_interfaces["parser"].upgrade_hooks → ["multi_user_ingest", ...]
"""

from __future__ import annotations

import time
import uuid

from backend.career.t009_pipeline import T009Pipeline
from backend.career.t009_schemas import (
    DynamicWeights,
    OffPathFlag,
    ScoredStrategyV2,
    T009ParserOutput,
    T009SimulationFeedback,
    TrendReport,
    UserFeedback,
)
from backend.career.t010_schemas import (
    T010ArchitectOutput,
    T010FrontendData,
    T010ParserOutput,
    T010PipelineOutput,
    T010RetrievalOutput,
    T010ReviewerOutput,
    T010SimulationOutput,
    UpgradeInterface,
)
from backend.career.t008_schemas import (
    CareerPlan,
    JobRecommendation,
    StrategyCandidate,
    UserProfile,
    VisualizationGraph,
)


class T010Pipeline:
    """Lightweight single-user career growth pipeline with upgrade interfaces.

    Core constraints:
      - Max 5 strategy candidates
      - Short-term simulation only
      - Single-user profile processing
      - Explicit upgrade hooks documented on every agent output

    Upgrade paths (documented, not implemented):
      - parser: multi_user_ingest, multi_source_aggregation, cross_domain_mapping
      - retrieval: cross_user_strategy_library, multi_industry_retrieval, strategy_graph_search
      - reviewer: group_pattern_scoring, multi_dim_metric_expansion, cohort_benchmark_comparison
      - architect: multi_scenario_simulation, long_term_trend_overlay, group_strategy_overlay
      - simulation: multi_scenario_long_term, multi_user_cohort_sim, market_shock_scenario
      - frontend: multi_user_view, cohort_comparison, trend_overlay_view
    """

    # ── Configuration ───────────────────────────────────────────────────────

    MAX_CANDIDATES = 5
    MIN_CANDIDATES = 3
    MAX_SIM_ROUNDS = 10
    RL_ITERATIONS = 2  # reduced from T009's 3 for lightweight mode
    LEARNING_RATE = 0.03  # reduced for stability

    def __init__(self):
        self._t009 = T009Pipeline(
            simulation_rounds=self.MAX_SIM_ROUNDS,
            rl_iterations=self.RL_ITERATIONS,
            learning_rate=self.LEARNING_RATE,
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def run(
        self,
        user_input: dict | str,
        career_dataset: list[dict] | None = None,
        user_id: str | None = None,
        industry_trends: list[dict] | None = None,
        user_feedback: UserFeedback | None = None,
        privacy_level: str = "basic",
    ) -> T010PipelineOutput:
        """Execute the lightweight T010 pipeline.

        Args:
            user_input: Single user's career goals, skills, experience
            career_dataset: Single-source recruitment/career path data
            user_id: Single user identifier
            industry_trends: Optional industry trend data
            user_feedback: Previous session feedback for回流
            privacy_level: Privacy masking level
        """
        uid = user_id or f"user-{uuid.uuid4().hex[:8]}"
        output = T010PipelineOutput()
        t0 = time.perf_counter()

        try:
            # ── Stage 1: Parser (core layer) ────────────────────────────────
            parser_output = self._t009._stage_parse_v2(user_input, career_dataset, uid)

            # Enforce candidate limit
            profile = parser_output.user_profile
            output.user_profile = profile
            output.career_data = parser_output.career_data
            output.baseline_strategy = parser_output.baseline_strategy
            output.off_path_flags = parser_output.off_path_flags
            output.errors.extend(parser_output.warnings)
            output.upgrade_interfaces["parser"] = T010ParserOutput().upgrade

            # ── Stage 2: Retrieval (core: 3-5 candidates) ───────────────────
            retrieval = self._t009._stage_retrieve_v2(parser_output, user_feedback)

            # Enforce strict 3-5 limit
            candidates = retrieval.strategy_candidates[:self.MAX_CANDIDATES]
            if len(candidates) < self.MIN_CANDIDATES and parser_output.baseline_strategy:
                candidates = self._pad_candidates(
                    candidates, parser_output.baseline_strategy.matched_template_id,
                    parser_output.baseline_strategy.templates,
                    parser_output.baseline_strategy.match_confidence,
                )

            output.job_recommendations = retrieval.job_recommendations[:10]
            output.strategy_candidates = candidates
            output.upgrade_interfaces["retrieval"] = T010RetrievalOutput().upgrade

            # ── Stages 3-5: Reviewer → Architect → Simulation (RL loop) ─────
            output = self._core_loop(output, parser_output, candidates, industry_trends)

            # ── Stage 6: Frontend data (core: privacy-masked) ───────────────
            output.frontend_data = self._build_frontend_core(output, privacy_level)
            output.privacy_mask = self._t009._build_privacy_mask(privacy_level)
            output.upgrade_interfaces["frontend"] = T010FrontendData().upgrade

            output.status = "success"
        except Exception as e:
            output.errors.append(f"T010 pipeline error: {e}")
            output.status = "partial" if output.user_profile is not None else "failed"

        output.elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return output

    # ── Core Loop (Stages 3-5) ──────────────────────────────────────────────

    def _core_loop(
        self,
        output: T010PipelineOutput,
        parser_output: T009ParserOutput,
        candidates: list[StrategyCandidate],
        industry_trends: list[dict] | None,
    ) -> T010PipelineOutput:
        """Run lightweight reviewer → architect → simulation loop."""

        from backend.career.t008_schemas import RetrievalOutput

        retrieval = RetrievalOutput(
            job_recommendations=output.job_recommendations,
            strategy_candidates=candidates,
            total_matches=len(output.job_recommendations),
        )

        trends = self._t009._parse_trends(industry_trends or [])
        trend_report = self._t009._build_trend_report(trends, parser_output.user_profile)

        weights = DynamicWeights(iteration=0, learning_rate=self.LEARNING_RATE)

        best_plan: CareerPlan | None = None
        best_sim: T009SimulationFeedback | None = None
        best_viz: VisualizationGraph | None = None
        best_nodes: dict = {}

        for iteration in range(1, self.RL_ITERATIONS + 1):
            weights.iteration = iteration

            # Reviewer (core: 5-dim single-user scoring)
            reviewer = self._t009._stage_review_v2(retrieval, parser_output, weights)
            output.strategy_list = reviewer.strategy_list
            output.diversity_metric = reviewer.diversity_metric

            # Architect (core: single-user plan)
            architect = self._t009._stage_architect_v2(parser_output, reviewer, trend_report)
            output.career_plan = architect.career_plan
            output.visualization_data = architect.visualization_data
            output.interactive_nodes = architect.interactive_nodes

            # Simulation (core: short-term, high-confidence priority)
            if architect.career_plan:
                sim = self._t009._stage_simulate_v2(
                    architect.career_plan, parser_output, weights, iteration
                )
                output.simulation_feedback = sim

                if best_sim is None or sim.base_feedback.average_success_rate > best_sim.base_feedback.average_success_rate:
                    best_plan = architect.career_plan
                    best_sim = sim
                    best_viz = architect.visualization_data
                    best_nodes = architect.interactive_nodes

                weights = self._t009._update_weights(weights, sim, reviewer)
                output.dynamic_weights = weights

                if weights.convergence_delta < self._t009._convergence_threshold:
                    break

        # Use best iteration
        if best_plan:
            output.career_plan = best_plan
        if best_sim:
            output.simulation_feedback = best_sim
        if best_viz:
            output.visualization_data = best_viz
        if best_nodes:
            output.interactive_nodes = best_nodes

        # Re-rank
        if output.strategy_list and output.simulation_feedback:
            output.refined_strategy_list = self._t009._stage_review_refine_v2(
                output.strategy_list, output.simulation_feedback, weights
            )

        # Mark off-path
        off_path_ids = {f.strategy_id for f in parser_output.off_path_flags}
        for s in (output.refined_strategy_list or output.strategy_list):
            if s.strategy.strategy_id in off_path_ids:
                s.off_path = True

        # Upgrade interface annotations
        output.upgrade_interfaces["reviewer"] = T010ReviewerOutput().upgrade
        output.upgrade_interfaces["architect"] = T010ArchitectOutput(
            career_plan=output.career_plan or CareerPlan(user_id=""),
            visualization_data=output.visualization_data or VisualizationGraph(),
        ).upgrade
        output.upgrade_interfaces["simulation"] = T010SimulationOutput().upgrade

        output.feedback_loop = self._t009._feedback_state

        return output

    # ── Frontend (core layer) ───────────────────────────────────────────────

    def _build_frontend_core(self, output: T010PipelineOutput, privacy_level: str) -> dict:
        """Build lightweight frontend data with privacy masking."""
        # Use T009 frontend builder for base data
        t009_output = self._t009._stage_frontend_v2.__self__  # won't work — just build inline

        summary = {}
        if output.user_profile:
            summary = {
                "headline": f"Career plan — {output.strategy_list[0].strategy.strategy_name if output.strategy_list else 'pending'}",
                "user_skills": output.user_profile.skills[:8],
                "career_goals": output.user_profile.career_goals[:3],
                "top_strategy_score": output.strategy_list[0].overall_score if output.strategy_list else 0.0,
                "simulation_success_rate": output.simulation_feedback.base_feedback.average_success_rate if output.simulation_feedback else 0.0,
                "personal_info_masked": privacy_level != "none",
            }

        strategy_comparison = {
            "strategies": [
                {
                    "name": s.strategy.strategy_name,
                    "overall": s.overall_score,
                    "success_rate": s.scores.get("success_rate", 0),
                    "match_degree": s.scores.get("match_degree", 0),
                    "growth_cycle": s.scores.get("growth_cycle", 0),
                    "skill_adaptability": s.scores.get("skill_adaptability", 0),
                    "diversity": s.scores.get("diversity", 0),
                    "rank": s.rank,
                }
                for s in (output.strategy_list)[:5]
            ],
            "dimensions": ["success_rate", "match_degree", "growth_cycle", "skill_adaptability", "diversity"],
        }

        action_timeline: list[dict] = []
        if output.career_plan:
            cum = 0
            for step in output.career_plan.steps:
                action_timeline.append({
                    "step_number": step.step_number,
                    "phase": step.phase,
                    "title": step.title,
                    "description": step.description,
                    "start_day": cum,
                    "end_day": cum + step.duration_days,
                    "duration_days": step.duration_days,
                    "milestones": step.milestones,
                })
                cum += step.duration_days

        sim_chart: dict = {"rounds": [], "average": 0.0}
        if output.simulation_feedback:
            sim_chart = {
                "rounds": [
                    {"round": r.round_id, "probability": r.success_probability, "success": r.success}
                    for r in output.simulation_feedback.base_feedback.rounds
                ],
                "average": output.simulation_feedback.base_feedback.average_success_rate,
                "successful": output.simulation_feedback.base_feedback.successful_rounds,
                "total": output.simulation_feedback.base_feedback.total_rounds,
            }

        recs: list[dict] = []
        if output.career_plan and output.career_plan.selected_strategy is None and output.strategy_list:
            recs.append({
                "priority": 1,
                "type": "strategy",
                "title": f"Adopt '{output.strategy_list[0].strategy.strategy_name}' strategy",
                "description": output.strategy_list[0].rationale,
            })
        if output.simulation_feedback:
            recs.append({
                "priority": 2,
                "type": "simulation",
                "title": f"Simulation confidence: {output.simulation_feedback.base_feedback.average_success_rate:.0%}",
                "description": output.simulation_feedback.base_feedback.recommendation,
            })
        if output.off_path_flags:
            recs.append({
                "priority": 3,
                "type": "warning",
                "title": f"{len(output.off_path_flags)} off-path deviation(s) detected",
                "description": "Review flagged strategies before adopting",
            })

        data = {
            "summary": summary,
            "career_path_graph": output.visualization_data.model_dump() if output.visualization_data else {},
            "strategy_comparison": strategy_comparison,
            "action_timeline": action_timeline,
            "simulation_chart": sim_chart,
            "recommendations": recs,
            "interactive_nodes": output.interactive_nodes,
            "privacy_mask": output.privacy_mask.model_dump() if output.privacy_mask else {},
            "upgrade_interfaces": {
                k: v.model_dump() for k, v in output.upgrade_interfaces.items()
            },
        }

        return data

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _pad_candidates(
        candidates: list[StrategyCandidate],
        matched_template_id: str | None,
        templates: list,
        confidence: float,
    ) -> list[StrategyCandidate]:
        """Pad candidate list to minimum 3 using baseline template recommendations."""
        if not matched_template_id:
            return candidates

        template = next(
            (t for t in templates if getattr(t, 'template_id', None) == matched_template_id),
            None,
        )
        if not template:
            return candidates

        existing_names = {c.strategy_name for c in candidates}
        for strat_name in getattr(template, 'recommended_strategies', []):
            if len(candidates) >= 3:
                break
            if strat_name not in existing_names:
                candidates.append(
                    StrategyCandidate(
                        strategy_id=f"strat-{strat_name}-pad",
                        strategy_name=strat_name,
                        description=f"Auto-padded baseline strategy for {getattr(template, 'target_role', 'unknown role')}",
                        match_score=confidence,
                        historical_success_rate=0.65,
                        source="baseline_pad",
                    )
                )
        return candidates
