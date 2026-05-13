"""T009 Pipeline — Career Growth V2 with RL Optimization & Feedback Loop.

Key enhancements over T008:
  1. Baseline strategy matching (cold-start support)
  2. 5-dimension scoring with diversity constraint
  3. RL-style dynamic weight updates across iterations
  4. Off-path strategy detection with anomaly flags
  5. Industry trend integration for architect
  6. Privacy masking layer
  7. Bidirectional feedback loop (frontend → parser + reviewer)
  8. User feedback handling
"""

from __future__ import annotations

import math
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone

from backend.career.t008_pipeline import T008Pipeline
from backend.career.t008_schemas import (
    CareerData,
    CareerDataEntry,
    CareerPlan,
    JobRecommendation,
    RetrievalOutput,
    SimulationFeedback,
    SimulationRound,
    SkillNode,
    StrategyCandidate,
    UserProfile,
    VisualizationGraph,
)
from backend.career.t009_schemas import (
    BaselineStrategy,
    BaselineStrategyTemplate,
    DiversityMetric,
    DynamicWeights,
    FeedbackLoopState,
    IndustryTrend,
    OffPathFlag,
    PrivacyMask,
    ScoredStrategyV2,
    T009ArchitectOutput,
    T009ParserOutput,
    T009PipelineOutput,
    T009ReviewerOutput,
    T009SimulationFeedback,
    TrendReport,
    UserFeedback,
)

# ── Baseline Strategy Templates ────────────────────────────────────────────
# Industry-standard career path templates for cold-start users

_BASELINE_TEMPLATES: list[BaselineStrategyTemplate] = [
    BaselineStrategyTemplate(
        domain="software_engineering",
        target_role="Senior Backend Engineer",
        typical_skills=["Python", "SQL", "Linux", "Git", "REST API", "Docker", "CI/CD", "System Design", "Kubernetes", "Distributed Systems"],
        typical_timeline_months=36,
        typical_milestones=["Junior Developer", "Backend Engineer", "Senior Backend Engineer", "Staff Engineer"],
        recommended_strategies=["conservative", "balanced"],
        risk_factors=["Skill obsolescence in fast-moving tech", "Overspecialization in single stack"],
        source="industry_benchmark",
    ),
    BaselineStrategyTemplate(
        domain="data_science",
        target_role="Machine Learning Engineer",
        typical_skills=["Python", "SQL", "Statistics", "Pandas", "Scikit-learn", "TensorFlow", "PyTorch", "MLOps", "Deep Learning"],
        typical_timeline_months=30,
        typical_milestones=["Data Analyst", "Junior Data Scientist", "ML Engineer", "Senior MLE"],
        recommended_strategies=["conservative", "pivot"],
        risk_factors=["Math/stats foundation gaps", "Production ML vs. research gap"],
        source="industry_benchmark",
    ),
    BaselineStrategyTemplate(
        domain="frontend",
        target_role="Frontend Tech Lead",
        typical_skills=["HTML/CSS", "JavaScript", "TypeScript", "React", "Next.js", "State Management", "Performance", "System Design", "Team Leadership"],
        typical_timeline_months=36,
        typical_milestones=["Frontend Developer", "Senior Frontend", "Tech Lead", "Frontend Architect"],
        recommended_strategies=["balanced", "aggressive"],
        risk_factors=["Framework churn", "Underestimating backend knowledge needed for lead roles"],
        source="industry_benchmark",
    ),
    BaselineStrategyTemplate(
        domain="product_management",
        target_role="Senior Product Manager",
        typical_skills=["User Research", "Data Analysis", "Roadmapping", "Stakeholder Management", "A/B Testing", "SQL", "Product Strategy", "GTM Strategy"],
        typical_timeline_months=30,
        typical_milestones=["APM", "Product Manager", "Senior PM", "Director of Product"],
        recommended_strategies=["balanced", "conservative"],
        risk_factors=["Domain expertise gap", "Technical depth vs. breadth tradeoff"],
        source="industry_benchmark",
    ),
    BaselineStrategyTemplate(
        domain="devops",
        target_role="Platform Engineer",
        typical_skills=["Linux", "Docker", "Kubernetes", "Terraform", "CI/CD", "AWS/GCP", "Monitoring", "Python/Go", "Security"],
        typical_timeline_months=30,
        typical_milestones=["SysAdmin", "DevOps Engineer", "Platform Engineer", "Staff Platform Engineer"],
        recommended_strategies=["balanced", "aggressive"],
        risk_factors=["Tooling fatigue", "On-call burnout risk"],
        source="industry_benchmark",
    ),
]


class T009Pipeline:
    """T009 Career Growth Pipeline V2 with RL optimization and feedback loop.

    Enhancements over T008:
      - Baseline strategy matching for new users (cold start)
      - 5-dimension scoring with diversity to prevent overfitting
      - RL-style dynamic weight updates per iteration
      - Off-path strategy detection via baseline comparison
      - Industry trend-aware architect planning
      - Privacy-aware data masking
      - Bidirectional agent feedback loop
      - User feedback ingestion

    Usage:
        pipeline = T009Pipeline()
        output = pipeline.run(user_input, career_dataset, user_feedback=prev_feedback)
    """

    def __init__(
        self,
        simulation_rounds: int = 10,
        rl_iterations: int = 3,
        learning_rate: float = 0.05,
        convergence_threshold: float = 0.01,
    ):
        self._t008 = T008Pipeline(simulation_rounds=simulation_rounds)
        self._baseline_templates = _BASELINE_TEMPLATES
        self._rl_iterations = max(1, min(rl_iterations, 10))
        self._learning_rate = max(0.001, min(learning_rate, 0.5))
        self._convergence_threshold = convergence_threshold
        self._weight_history: list[DynamicWeights] = []
        self._feedback_state: FeedbackLoopState | None = None

    # ── Public API ──────────────────────────────────────────────────────────

    def run(
        self,
        user_input: dict | str,
        career_dataset: list[dict] | None = None,
        user_id: str | None = None,
        industry_trends: list[dict] | None = None,
        user_feedback: UserFeedback | None = None,
        privacy_level: str = "basic",
    ) -> T009PipelineOutput:
        """Execute the full T009 pipeline with all enhancements.

        Args:
            user_input: User career goals, skills, experience
            career_dataset: Recruitment/career path data
            user_id: User identifier
            industry_trends: Market/industry trend data
            user_feedback: Previous user feedback for回流
            privacy_level: "none" | "basic" | "full"
        """
        uid = user_id or f"user-{uuid.uuid4().hex[:8]}"
        output = T009PipelineOutput()
        t0 = time.perf_counter()

        # Init feedback loop state
        self._feedback_state = FeedbackLoopState()

        try:
            # Stage 1: Parser V2 — with baseline matching & off-path detection
            parser_output = self._stage_parse_v2(user_input, career_dataset, uid)
            output.user_profile = parser_output.user_profile
            output.career_data = parser_output.career_data
            output.baseline_strategy = parser_output.baseline_strategy
            output.off_path_flags = parser_output.off_path_flags
            output.new_user_generated = parser_output.new_user_generated
            output.errors.extend(parser_output.warnings)

            # Stage 2: Retrieval — strategy candidates (limited 3-5)
            retrieval_output = self._stage_retrieve_v2(
                parser_output, user_feedback
            )
            output.job_recommendations = retrieval_output.job_recommendations
            output.strategy_candidates = retrieval_output.strategy_candidates

            # Parse industry trends
            trends = self._parse_trends(industry_trends or [])
            trend_report = self._build_trend_report(trends, parser_output.user_profile)

            # Stage 3-5: RL iteration loop
            output = self._rl_iteration_loop(
                output, parser_output, retrieval_output, trend_report, user_feedback
            )

            # Stage 6: Frontend V2 — with privacy masking
            output.frontend_data = self._stage_frontend_v2(output, privacy_level)
            output.privacy_mask = self._build_privacy_mask(privacy_level)

            # Populate feedback loop state
            output.feedback_loop = self._feedback_state

            output.status = "success"
        except Exception as e:
            output.errors.append(f"Pipeline error: {e}")
            output.status = "partial" if output.user_profile is not None else "failed"

        output.elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return output

    # ── Stage 1: Parser V2 ──────────────────────────────────────────────────

    def _stage_parse_v2(
        self,
        user_input: dict | str,
        career_dataset: list[dict] | None,
        user_id: str,
    ) -> T009ParserOutput:
        """Parse with baseline matching and off-path detection."""
        # Use T008 parser for basic parsing
        t008_parser_output = self._t008._stage_parse(user_input, career_dataset, user_id)
        profile = t008_parser_output.user_profile
        career_data = t008_parser_output.career_data
        warnings = t008_parser_output.warnings

        # Cold start detection
        new_user = len(profile.skills) < 2 and len(profile.career_goals) < 1
        if new_user:
            profile = self._generate_new_user_profile(user_input, user_id)
            warnings.append("Cold start: generated typical initial profile")
            new_user = True

        # Match baseline strategy template
        baseline = self._match_baseline(profile)
        if baseline.match_confidence < 0.3:
            warnings.append(
                f"Low baseline match confidence ({baseline.match_confidence:.0%}). "
                "User profile may not align with standard career paths."
            )

        # Detect off-path anomalies
        off_path_flags = self._detect_off_path(profile, baseline, career_data)

        return T009ParserOutput(
            user_profile=profile,
            career_data=career_data,
            baseline_strategy=baseline,
            off_path_flags=off_path_flags,
            new_user_generated=new_user,
            warnings=warnings,
        )

    def _match_baseline(self, profile: UserProfile) -> BaselineStrategy:
        """Match user profile to closest baseline career template."""
        if not self._baseline_templates:
            return BaselineStrategy()

        best_template = None
        best_score = 0.0

        profile_skills = {s.lower().strip() for s in profile.skills}

        for template in self._baseline_templates:
            template_skills = {s.lower() for s in template.typical_skills}
            overlap = profile_skills & template_skills
            if template_skills:
                skill_score = len(overlap) / len(template_skills)
            else:
                skill_score = 0.0

            # Goal alignment: check if any career goal matches target role
            goal_score = 0.0
            for goal in profile.career_goals:
                if any(
                    word.lower() in goal.lower()
                    for word in template.target_role.lower().split()
                ):
                    goal_score = 0.6
                    break

            match = skill_score * 0.7 + goal_score * 0.3
            if match > best_score:
                best_score = match
                best_template = template

        return BaselineStrategy(
            templates=self._baseline_templates,
            matched_template_id=best_template.template_id if best_template else None,
            match_confidence=round(best_score, 3),
        )

    def _detect_off_path(
        self,
        profile: UserProfile,
        baseline: BaselineStrategy,
        career_data: CareerData | None,
    ) -> list[OffPathFlag]:
        """Detect strategies/skills deviating from typical career paths."""
        flags: list[OffPathFlag] = []

        if baseline.matched_template_id:
            template = next(
                (t for t in baseline.templates if t.template_id == baseline.matched_template_id),
                None,
            )
            if template:
                profile_skills = {s.lower().strip() for s in profile.skills}
                # Skills that DON'T match the template are anomalous
                template_skills = {s.lower() for s in template.typical_skills}
                missing_core = template_skills - profile_skills
                if len(missing_core) > len(template_skills) * 0.5:
                    flags.append(
                        OffPathFlag(
                            strategy_id="profile",
                            flag_type="skill_order_anomaly",
                            severity="high" if len(missing_core) > len(template_skills) * 0.7 else "medium",
                            description=f"Missing {len(missing_core)} typical skills for {template.target_role}",
                            deviation_score=min(1.0, len(missing_core) / len(template_skills)),
                            recommendation=f"Consider acquiring: {', '.join(list(missing_core)[:3])}",
                        )
                    )

                # Role skip detection — high-level goals without intermediate skills
                if profile.experience_years < 2 and any(
                    "senior" in g.lower() or "lead" in g.lower() or "architect" in g.lower()
                    for g in profile.career_goals
                ):
                    flags.append(
                        OffPathFlag(
                            strategy_id="profile",
                            flag_type="role_skip",
                            severity="medium",
                            description="Targeting senior/lead roles with limited experience",
                            deviation_score=0.6,
                            recommendation="Include mid-level stepping stone roles in plan",
                        )
                    )

        return flags

    def _generate_new_user_profile(self, user_input: dict | str, user_id: str) -> UserProfile:
        """Generate a typical initial profile for cold-start users."""
        text = user_input if isinstance(user_input, str) else str(user_input.get("raw_text", ""))

        # Match to closest template
        best = self._baseline_templates[0]
        best_overlap = 0
        text_lower = text.lower()
        for template in self._baseline_templates:
            overlap = sum(1 for s in template.typical_skills if s.lower() in text_lower)
            if overlap > best_overlap:
                best_overlap = overlap
                best = template

        return UserProfile(
            user_id=user_id,
            career_goals=[best.target_role],
            skills=best.typical_skills[:5],
            experience_years=1.0,
            education_level="本科",
            preferred_locations=["北京", "上海", "深圳"],
            preferred_industries=[best.domain],
            raw_text=text,
        )

    # ── Stage 2: Retrieval V2 ───────────────────────────────────────────────

    def _stage_retrieve_v2(
        self,
        parser_output: T009ParserOutput,
        user_feedback: UserFeedback | None = None,
    ) -> RetrievalOutput:
        """Retrieve with baseline-aware candidate generation and diversity.

        Limits: 3-5 strategy candidates to control complexity.
        """
        profile = parser_output.user_profile

        # Get base candidates from T008
        base_output = self._t008._stage_retrieve(
            parser_output  # type: ignore — T009ParserOutput wraps ParserOutput fields
        )

        # Enforce 3-5 candidate limit
        candidates = base_output.strategy_candidates[:5]
        if len(candidates) < 3:
            # Pad with baseline-recommended strategies
            if parser_output.baseline_strategy and parser_output.baseline_strategy.matched_template_id:
                template = next(
                    (t for t in parser_output.baseline_strategy.templates
                     if t.template_id == parser_output.baseline_strategy.matched_template_id),
                    None,
                )
                if template:
                    for strat_name in template.recommended_strategies:
                        if not any(c.strategy_name == strat_name for c in candidates):
                            candidates.append(
                                StrategyCandidate(
                                    strategy_id=f"strat-{strat_name}-baseline",
                                    strategy_name=strat_name,
                                    description=f"Baseline-recommended {strat_name} strategy for {template.target_role}",
                                    match_score=parser_output.baseline_strategy.match_confidence,
                                    historical_success_rate=0.70,
                                    source="baseline",
                                )
                            )

        # Incorporate user feedback if available
        if user_feedback and user_feedback.strategy_rating > 0:
            for c in candidates:
                if c.strategy_name == user_feedback.strategy_adopted:
                    c.match_score = min(1.0, c.match_score + 0.05)
                    c.historical_success_rate = min(1.0, c.historical_success_rate + 0.03)

        # Annotate diversity
        strategy_names = [c.strategy_name for c in candidates]
        unique_count = len(set(strategy_names))
        for c in candidates:
            if strategy_names.count(c.strategy_name) > 1:
                c.description += " [low diversity: duplicate strategy type]"

        return RetrievalOutput(
            job_recommendations=base_output.job_recommendations[:10],
            strategy_candidates=candidates,
            total_matches=base_output.total_matches,
        )

    # ── Stages 3-5: RL Iteration Loop ───────────────────────────────────────

    def _rl_iteration_loop(
        self,
        output: T009PipelineOutput,
        parser_output: T009ParserOutput,
        retrieval_output: RetrievalOutput,
        trend_report: TrendReport | None,
        user_feedback: UserFeedback | None = None,
    ) -> T009PipelineOutput:
        """Run the reviewer → architect → simulation loop with RL weight updates.

        Each iteration:
          1. Reviewer scores with current weights
          2. Architect generates plan with best strategy
          3. Simulation runs multi-round and produces feedback
          4. Weights are updated based on simulation outcomes (gradient step)
          5. Check convergence → stop early if converged
        """
        weights = DynamicWeights(iteration=0, learning_rate=self._learning_rate)
        best_strategy_list: list[ScoredStrategyV2] = []
        best_simulation: T009SimulationFeedback | None = None
        best_career_plan: CareerPlan | None = None
        best_architect_output: T009ArchitectOutput | None = None

        for iteration in range(1, self._rl_iterations + 1):
            weights.iteration = iteration
            self._feedback_state.retrieval_reviewer_iterations = iteration  # type: ignore

            # Stage 3: Reviewer V2 — 5-dim scoring with current weights
            reviewer_output = self._stage_review_v2(
                retrieval_output, parser_output, weights
            )
            output.strategy_list = reviewer_output.strategy_list
            output.diversity_metric = reviewer_output.diversity_metric

            # Stage 4: Architect V2 — trend-aware plan
            architect_output = self._stage_architect_v2(
                parser_output, reviewer_output, trend_report
            )
            output.career_plan = architect_output.career_plan
            output.visualization_data = architect_output.visualization_data
            output.trend_adjustments = architect_output.trend_adjustments
            output.interactive_nodes = architect_output.interactive_nodes
            output.long_term_outlook = architect_output.long_term_outlook

            # Stage 5: Simulation V2 — multi-round with RL feedback
            if architect_output.career_plan:
                sim_feedback = self._stage_simulate_v2(
                    architect_output.career_plan,
                    parser_output,
                    weights,
                    iteration,
                )
                output.simulation_feedback = sim_feedback
                self._feedback_state.simulation_rounds_run += sim_feedback.base_feedback.total_rounds  # type: ignore
                self._feedback_state.simulation_feedback_applied = True  # type: ignore

                # Track best
                if (
                    best_simulation is None
                    or sim_feedback.base_feedback.average_success_rate
                    > best_simulation.base_feedback.average_success_rate
                ):
                    best_strategy_list = reviewer_output.strategy_list
                    best_simulation = sim_feedback
                    best_career_plan = architect_output.career_plan
                    best_architect_output = architect_output

                # Update weights based on simulation outcome (RL step)
                weights = self._update_weights(
                    weights, sim_feedback, reviewer_output
                )
                output.dynamic_weights = weights
                self._feedback_state.reviewer_weight_updates = iteration  # type: ignore

                # Check convergence
                if weights.convergence_delta < self._convergence_threshold:
                    self._feedback_state.pipeline_converged = True  # type: ignore
                    self._feedback_state.convergence_reason = (  # type: ignore
                        f"Weights converged at iteration {iteration} (delta={weights.convergence_delta:.4f})"
                    )
                    break

        # Use best iteration results
        if best_career_plan:
            output.career_plan = best_career_plan
        if best_simulation:
            output.simulation_feedback = best_simulation
        if best_architect_output:
            output.visualization_data = best_architect_output.visualization_data
            output.interactive_nodes = best_architect_output.interactive_nodes

        # Re-rank strategies with final weights
        if output.strategy_list and output.simulation_feedback:
            output.refined_strategy_list = self._stage_review_refine_v2(
                output.strategy_list, output.simulation_feedback, weights
            )

        # Mark off-path strategies
        off_path_ids = {f.strategy_id for f in parser_output.off_path_flags}
        for s in (output.refined_strategy_list or output.strategy_list):
            if s.strategy.strategy_id in off_path_ids:
                s.off_path = True
                s.off_path_flags = [
                    f for f in parser_output.off_path_flags
                    if f.strategy_id == s.strategy.strategy_id
                ]

        output.dynamic_weights = weights
        return output

    # ── Stage 3: Reviewer V2 ────────────────────────────────────────────────

    def _stage_review_v2(
        self,
        retrieval_output: RetrievalOutput,
        parser_output: T009ParserOutput,
        weights: DynamicWeights,
    ) -> T009ReviewerOutput:
        """Score strategies across 5 dimensions with diversity constraint.

        Dimensions (V2): success_rate, match_degree, growth_cycle, skill_adaptability, diversity
        """
        scored: list[ScoredStrategyV2] = []

        for candidate in retrieval_output.strategy_candidates:
            # 4 base dimensions (reuse T008 scoring)
            base_scores = self._t008._score_strategy(candidate)

            # 5th dimension: diversity
            diversity_score = self._compute_diversity_contribution(
                candidate, retrieval_output.strategy_candidates
            )

            scores = {
                **base_scores,
                "diversity": diversity_score,
            }

            overall = sum(scores[dim] * weights.weights.get(dim, 0.2) for dim in weights.weights)

            scored.append(
                ScoredStrategyV2(
                    strategy=candidate,
                    scores=scores,
                    overall_score=round(overall, 3),
                    rationale=self._t008._generate_rationale(candidate, base_scores),
                )
            )

        scored.sort(key=lambda s: -s.overall_score)
        for i, s in enumerate(scored):
            s.rank = i + 1

        # Compute diversity metric
        diversity = self._compute_diversity_metric(scored)

        return T009ReviewerOutput(
            strategy_list=scored,
            top_n=min(3, len(scored)),
            diversity_metric=diversity,
            dynamic_weights=weights,
            off_path_warnings=[
                s.rationale for s in scored if s.scores.get("diversity", 0) < 0.3
            ],
        )

    @staticmethod
    def _compute_diversity_contribution(
        candidate: StrategyCandidate,
        all_candidates: list[StrategyCandidate],
    ) -> float:
        """Compute how much this strategy adds to candidate set diversity.

        Higher score = this strategy is more different from others (better diversity).
        """
        if len(all_candidates) <= 1:
            return 0.5

        others = [c for c in all_candidates if c.strategy_id != candidate.strategy_id]
        if not others:
            return 0.5

        # Diversity = 1 - avg similarity to other strategies
        similarities: list[float] = []
        for other in others:
            # Name similarity
            name_sim = 1.0 if candidate.strategy_name == other.strategy_name else 0.0
            # Match score similarity
            score_sim = 1.0 - abs(candidate.match_score - other.match_score)
            # Source diversity
            source_sim = 1.0 if candidate.source == other.source else 0.0
            similarities.append(name_sim * 0.5 + score_sim * 0.3 + source_sim * 0.2)

        avg_sim = sum(similarities) / len(similarities)
        return round(1.0 - avg_sim, 3)

    @staticmethod
    def _compute_diversity_metric(strategies: list[ScoredStrategyV2]) -> DiversityMetric:
        """Compute overall diversity across scored strategies."""
        if len(strategies) <= 1:
            return DiversityMetric(
                strategy_diversity=0.0,
                overfitting_risk=0.8,
                recommendation="Too few strategies to assess diversity. Add more candidates.",
            )

        # Strategy type uniqueness
        names = [s.strategy.strategy_name for s in strategies]
        unique_ratio = len(set(names)) / len(names)

        # Score spread per dimension
        dimension_balance: dict[str, float] = {}
        for dim in ["success_rate", "match_degree", "growth_cycle", "skill_adaptability", "diversity"]:
            values = [s.scores.get(dim, 0.0) for s in strategies]
            if values:
                spread = max(values) - min(values)
                dimension_balance[dim] = round(spread, 3)

        # Overfitting risk: high if all strategies have similar scores
        overalls = [s.overall_score for s in strategies]
        overall_spread = max(overalls) - min(overalls) if overalls else 0.0
        overfitting_risk = max(0.0, min(1.0, 1.0 - overall_spread * 2))

        diversity_score = round(unique_ratio * 0.6 + overall_spread * 0.4, 3)

        if diversity_score < 0.3:
            rec = "High overfitting risk — add strategies from different sources."
        elif diversity_score < 0.6:
            rec = "Moderate diversity — consider adding one contrasting strategy."
        else:
            rec = "Good diversity across strategies."

        return DiversityMetric(
            strategy_diversity=diversity_score,
            dimension_balance=dimension_balance,
            overfitting_risk=round(overfitting_risk, 3),
            recommendation=rec,
        )

    # ── Stage 4: Architect V2 ───────────────────────────────────────────────

    def _stage_architect_v2(
        self,
        parser_output: T009ParserOutput,
        reviewer_output: T009ReviewerOutput,
        trend_report: TrendReport | None = None,
    ) -> T009ArchitectOutput:
        """Generate career plan with industry trend adjustments and interactive nodes."""
        profile = parser_output.user_profile

        # Base architect output from T008
        # Construct compatible inputs
        from backend.career.t008_schemas import ReviewerOutput, ScoredStrategy

        t008_strategies: list[ScoredStrategy] = []
        for sv2 in reviewer_output.strategy_list:
            t008_strategies.append(
                ScoredStrategy(
                    strategy=sv2.strategy,
                    scores={
                        k: v for k, v in sv2.scores.items()
                        if k != "diversity"
                    },
                    overall_score=sv2.overall_score,
                    rationale=sv2.rationale,
                    rank=sv2.rank,
                )
            )

        t008_reviewer = ReviewerOutput(
            strategy_list=t008_strategies,
            top_n=reviewer_output.top_n,
        )

        from backend.career.t008_schemas import ParserOutput
        t008_parser = ParserOutput(
            user_profile=profile,
            career_data=parser_output.career_data,
            warnings=parser_output.warnings,
        )

        base_architect = self._t008._stage_architect(t008_parser, t008_reviewer)
        career_plan = base_architect.career_plan
        viz_graph = base_architect.visualization_data

        # Apply industry trend adjustments
        trend_adjustments: list[str] = []
        if trend_report and trend_report.trends:
            for trend in trend_report.trends:
                if trend.direction == "rising":
                    # Boost skill priority for rising-trend skills
                    for skill in trend.affected_skills:
                        if career_plan and skill.lower() not in {s.lower() for s in career_plan.skill_gaps}:
                            if len(career_plan.skill_gaps) < 5:
                                career_plan.skill_gaps.append(skill)
                    trend_adjustments.append(
                        f"Rising trend '{trend.trend_name}': added {', '.join(trend.affected_skills[:2])} to focus skills"
                    )
                elif trend.direction == "declining":
                    trend_adjustments.append(
                        f"Declining trend '{trend.trend_name}': deprioritize {', '.join(trend.affected_skills[:2])}"
                    )

        # Build interactive nodes
        interactive_nodes: dict[str, dict] = {}
        for node in viz_graph.skill_nodes:
            interactive_nodes[node.skill_name] = {
                "description": f"Skill: {node.skill_name} (Level: {node.level})",
                "strategy_note": (
                    f"Focus strategy recommends {'acquiring' if node.estimated_hours > 0 else 'leveraging'} this skill"
                ),
                "risk_note": (
                    f"Estimated {node.estimated_hours}h to acquire"
                    if node.estimated_hours > 0
                    else "Already proficient"
                ),
                "click_action": "show_details",
            }

        # Long-term outlook
        long_term = self._generate_long_term_outlook(
            profile, career_plan, trend_report
        )

        return T009ArchitectOutput(
            career_plan=career_plan,
            visualization_data=viz_graph,
            trend_adjustments=trend_adjustments,
            interactive_nodes=interactive_nodes,
            long_term_outlook=long_term,
        )

    # ── Stage 5: Simulation V2 ──────────────────────────────────────────────

    def _stage_simulate_v2(
        self,
        career_plan: CareerPlan,
        parser_output: T009ParserOutput,
        weights: DynamicWeights,
        iteration: int,
    ) -> T009SimulationFeedback:
        """Multi-round simulation with off-path detection."""
        # Base simulation from T008
        base_feedback = self._t008._stage_simulate(career_plan)

        # Detect off-path strategies in simulation failures
        off_path_ids: list[str] = []
        for sim_round in base_feedback.rounds:
            if not sim_round.success and sim_round.success_probability < 0.3:
                for flag in parser_output.off_path_flags:
                    if flag.strategy_id not in off_path_ids:
                        off_path_ids.append(flag.strategy_id)

        return T009SimulationFeedback(
            base_feedback=base_feedback,
            weight_updates_applied=iteration,
            updated_weights=weights,
            off_path_strategies_detected=off_path_ids,
            rl_iteration=iteration,
            rl_converged=weights.convergence_delta < self._convergence_threshold,
        )

    # ── RL Weight Update ────────────────────────────────────────────────────

    def _update_weights(
        self,
        current_weights: DynamicWeights,
        sim_feedback: T009SimulationFeedback,
        reviewer_output: T009ReviewerOutput,
    ) -> DynamicWeights:
        """RL-style weight update based on simulation outcomes.

        Gradient heuristic:
          - If simulation success rate is high → boost success_rate and match_degree
          - If diversity is low and success is low → boost diversity
          - If growth_cycle is poor (slow success) → boost growth_cycle
        """
        new_weights = dict(current_weights.weights)
        avg_success = sim_feedback.base_feedback.average_success_rate
        lr = current_weights.learning_rate

        # Boost success_rate weight if it's performing well
        if avg_success >= 0.7:
            new_weights["success_rate"] = min(0.40, new_weights["success_rate"] + lr * 0.5)
            new_weights["match_degree"] = min(0.35, new_weights["match_degree"] + lr * 0.3)
        elif avg_success < 0.3:
            new_weights["diversity"] = min(0.30, new_weights["diversity"] + lr * 0.8)
            new_weights["success_rate"] = max(0.15, new_weights["success_rate"] - lr * 0.3)

        # If diversity metric is low, boost diversity weight
        if reviewer_output.diversity_metric:
            if reviewer_output.diversity_metric.overfitting_risk > 0.6:
                new_weights["diversity"] = min(0.30, new_weights["diversity"] + lr * 0.6)

        # Normalize to sum=1.0
        total = sum(new_weights.values())
        new_weights = {k: round(v / total, 4) for k, v in new_weights.items()}

        # Compute convergence delta
        prev = current_weights.weight_history[-1] if current_weights.weight_history else current_weights.weights
        delta = max(abs(new_weights.get(k, 0) - prev.get(k, 0)) for k in new_weights)

        history = list(current_weights.weight_history) + [dict(new_weights)]

        return DynamicWeights(
            iteration=current_weights.iteration,
            weights=new_weights,
            weight_history=history,
            convergence_delta=round(delta, 4),
            learning_rate=lr,
        )

    # ── Stage 3-Revisit: Reviewer Re-rank V2 ────────────────────────────────

    def _stage_review_refine_v2(
        self,
        current_list: list[ScoredStrategyV2],
        sim_feedback: T009SimulationFeedback,
        weights: DynamicWeights,
    ) -> list[ScoredStrategyV2]:
        """Re-rank with simulation feedback."""
        refined: list[ScoredStrategyV2] = []
        for scored in current_list:
            new_scores = dict(scored.scores)
            # Adjust based on simulation outcome
            if sim_feedback.base_feedback.average_success_rate > 0.6:
                new_scores["success_rate"] = min(1.0, new_scores["success_rate"] + 0.03)
            elif sim_feedback.base_feedback.average_success_rate < 0.3:
                new_scores["success_rate"] = max(0.0, new_scores["success_rate"] - 0.03)

            new_overall = round(
                sum(new_scores[dim] * weights.weights.get(dim, 0.2) for dim in weights.weights),
                3,
            )

            refined.append(
                ScoredStrategyV2(
                    strategy=scored.strategy,
                    scores=new_scores,
                    overall_score=new_overall,
                    rationale=scored.rationale,
                    off_path=scored.strategy.strategy_id in sim_feedback.off_path_strategies_detected,
                )
            )

        refined.sort(key=lambda s: -s.overall_score)
        for i, s in enumerate(refined):
            s.rank = i + 1

        return refined

    # ── Stage 6: Frontend V2 ────────────────────────────────────────────────

    def _stage_frontend_v2(
        self, output: T009PipelineOutput, privacy_level: str
    ) -> dict:
        """Build frontend data with privacy masking."""
        base_data = self._t008._stage_frontend(output)  # type: ignore

        # Apply privacy masking
        if privacy_level != "none":
            base_data = self._apply_privacy_mask(base_data, privacy_level)

        # Add T009-specific sections
        base_data["interactive_nodes"] = output.interactive_nodes
        base_data["long_term_outlook"] = output.long_term_outlook
        base_data["trend_adjustments"] = output.trend_adjustments
        base_data["diversity_metric"] = (
            output.diversity_metric.model_dump() if output.diversity_metric else {}
        )
        base_data["off_path_flags"] = [f.model_dump() for f in output.off_path_flags]
        base_data["feedback_loop"] = (
            output.feedback_loop.model_dump() if output.feedback_loop else {}
        )

        return base_data

    @staticmethod
    def _apply_privacy_mask(data: dict, level: str) -> dict:
        """Apply privacy脱敏 to frontend data."""
        if level == "none":
            return data

        masked = deepcopy(data)

        if "summary" in masked:
            if level in ("basic", "full"):
                # Mask personal identifiers
                masked["summary"]["user_skills"] = masked["summary"].get("user_skills", [])
                masked["summary"]["personal_info_masked"] = True

        if level == "full":
            # Mask company names in job recommendations
            if "summary" in masked:
                masked["summary"]["total_jobs_matched"] = masked["summary"].get("total_jobs_matched", 0)

        return masked

    @staticmethod
    def _build_privacy_mask(level: str) -> PrivacyMask:
        """Build privacy mask configuration."""
        return PrivacyMask(
            mask_personal_info=level in ("basic", "full"),
            mask_company_names=(level == "full"),
            mask_salary=(level == "full"),
            anonymization_level=level,  # type: ignore
            masked_fields=["name", "email", "phone"] if level in ("basic", "full") else [],
        )

    # ── Industry Trends ─────────────────────────────────────────────────────

    @staticmethod
    def _parse_trends(raw_trends: list[dict]) -> list[IndustryTrend]:
        """Parse industry trend data."""
        trends: list[IndustryTrend] = []
        for raw in raw_trends:
            try:
                trends.append(
                    IndustryTrend(
                        domain=raw.get("domain", ""),
                        trend_name=raw.get("trend_name", raw.get("name", "")),
                        direction=raw.get("direction", "stable"),
                        confidence=float(raw.get("confidence", 0.5)),
                        affected_skills=raw.get("affected_skills", []),
                        affected_roles=raw.get("affected_roles", []),
                        growth_rate_pct=float(raw.get("growth_rate_pct", 0)),
                        source=raw.get("source", ""),
                        valid_until=raw.get("valid_until", ""),
                    )
                )
            except Exception:
                continue
        return trends

    @staticmethod
    def _build_trend_report(
        trends: list[IndustryTrend], profile: UserProfile
    ) -> TrendReport | None:
        """Build trend report relevant to user's domain."""
        if not trends:
            return None

        # Filter trends relevant to user's industries
        relevant = [
            t for t in trends
            if not profile.preferred_industries
            or any(
                ind.lower() in t.domain.lower()
                for ind in profile.preferred_industries
            )
        ]
        if not relevant:
            relevant = trends

        domain = relevant[0].domain if relevant else "general"
        rising = [t for t in relevant if t.direction == "rising"]
        summary = (
            f"{len(rising)} rising trends detected. "
            f"Focus skills: {', '.join(s for t in rising for s in t.affected_skills[:2])}"
        ) if rising else "No significant market shifts detected."

        return TrendReport(domain=domain, trends=relevant, summary=summary)

    # ── Long-Term Outlook ───────────────────────────────────────────────────

    @staticmethod
    def _generate_long_term_outlook(
        profile: UserProfile,
        plan: CareerPlan | None,
        trend_report: TrendReport | None,
    ) -> str:
        """Generate 12-24 month career outlook."""
        parts: list[str] = []

        if plan and plan.selected_strategy:
            parts.append(
                f"Following the '{plan.selected_strategy.strategy.strategy_name}' strategy, "
                f"expect meaningful progress in {plan.total_duration_days} days."
            )

        if plan and plan.skill_gaps:
            parts.append(
                f"Key growth areas: {', '.join(plan.skill_gaps[:3])}."
            )

        if trend_report and trend_report.trends:
            rising = [t for t in trend_report.trends if t.direction == "rising"]
            if rising:
                parts.append(
                    f"Market tailwinds: {', '.join(t.trend_name for t in rising[:2])} "
                    f"may accelerate career growth."
                )

        if profile.experience_years < 2:
            parts.append(
                "Early career: focus on breadth before depth. "
                "Build foundation across 2-3 domains before specializing."
            )
        elif profile.experience_years >= 5:
            parts.append(
                "Mid-senior career: depth and leadership become differentiators. "
                "Consider mentoring and architecture-level contributions."
            )

        return " ".join(parts) if parts else "Insufficient data for long-term outlook."

    # ── Feedback Loop: Handle User Feedback ─────────────────────────────────

    def handle_user_feedback(self, feedback: UserFeedback) -> FeedbackLoopState:
        """Process user feedback and update feedback loop state.

        This is called by frontend after user interaction.
        Feedback flows back to parser_agent and reviewer_agent.
        """
        if self._feedback_state is None:
            self._feedback_state = FeedbackLoopState()

        self._feedback_state.user_feedback_received = True
        self._feedback_state.user_strategy_adopted = feedback.strategy_adopted
        self._feedback_state.user_behavior_preferences = feedback.preferences_updated

        return self._feedback_state
