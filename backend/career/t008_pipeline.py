"""T008 Pipeline — Career Growth System Convergence & Strategy Optimization.

Orchestrates the 6-agent T008 flow:
  parser → retrieval → reviewer → architect → simulation → (reviewer re-rank) → frontend

All agents communicate through typed Pydantic models. No hidden state.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from backend.career.career_architect import CareerArchitect
from backend.career.career_frontend import CareerFrontend
from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer
from backend.career.career_simulator import CareerSimulator
from backend.career.schemas import (
    ActionItem,
    BottleneckAnalysis,
    CareerEvent,
    CareerStrategy,
    CareerTimeline,
    CareerVisualization,
    SkillSnapshot,
    StrategySimulation,
)
from backend.career.t008_schemas import (
    ArchitectOutput,
    CareerData,
    CareerDataEntry,
    CareerPlan,
    JobRecommendation,
    ParserOutput,
    PlanStep,
    RetrievalOutput,
    ReviewerOutput,
    ScoredStrategy,
    SimulationFeedback,
    SimulationRound,
    SkillNode,
    StrategyCandidate,
    T008PipelineOutput,
    TimelineNode,
    UserProfile,
    VisualizationGraph,
)


class T008Pipeline:
    """Orchestrates the 6-agent career growth convergence pipeline.

    Data flow:
      raw_input → parser → retrieval → reviewer → architect → simulation → reviewer(re-rank) → frontend

    Usage:
        pipeline = T008Pipeline()
        output = pipeline.run(user_input_text, career_dataset_entries)
    """

    def __init__(
        self,
        parser: CareerParser | None = None,
        retriever: CareerRetriever | None = None,
        reviewer: CareerReviewer | None = None,
        architect: CareerArchitect | None = None,
        simulator: CareerSimulator | None = None,
        frontend: CareerFrontend | None = None,
        simulation_rounds: int = 10,
    ):
        self._parser = parser or CareerParser()
        self._retriever = retriever or CareerRetriever()
        self._reviewer = reviewer or CareerReviewer()
        self._architect = architect or CareerArchitect()
        self._simulator = simulator or CareerSimulator()
        self._frontend = frontend or CareerFrontend()
        self._simulation_rounds = max(3, min(simulation_rounds, 50))

    # ── Public API ──────────────────────────────────────────────────────────

    def run(
        self,
        user_input: dict | str,
        career_dataset: list[dict] | None = None,
        user_id: str | None = None,
    ) -> T008PipelineOutput:
        """Execute the full T008 6-agent pipeline.

        Args:
            user_input: Dict with career goals/skills/experience, or free-text
            career_dataset: List of dicts with recruitment/career path data
            user_id: User identifier (auto-generated if None)

        Returns:
            T008PipelineOutput with all stage outputs populated
        """
        uid = user_id or f"user-{uuid.uuid4().hex[:8]}"
        output = T008PipelineOutput()
        t0 = time.perf_counter()

        try:
            # Stage 1: Parse user profile + career dataset
            parser_output = self._stage_parse(user_input, career_dataset, uid)
            output.user_profile = parser_output.user_profile
            output.career_data = parser_output.career_data
            output.errors.extend(parser_output.warnings)

            # Stage 2: Retrieve matching jobs + strategies
            retrieval_output = self._stage_retrieve(parser_output)
            output.job_recommendations = retrieval_output.job_recommendations
            output.strategy_candidates = retrieval_output.strategy_candidates

            # Stage 3: Reviewer scores & ranks strategies
            reviewer_output = self._stage_review(retrieval_output)
            output.strategy_list = reviewer_output.strategy_list

            # Stage 4: Architect generates career plan + visualization
            architect_output = self._stage_architect(parser_output, reviewer_output)
            output.career_plan = architect_output.career_plan
            output.visualization_data = architect_output.visualization_data

            # Stage 5: Multi-round simulation + feedback
            if output.career_plan is not None:
                sim_feedback = self._stage_simulate(output.career_plan)
                output.simulation_feedback = sim_feedback

                # Stage 3-revisit: Re-rank with simulation feedback
                if sim_feedback is not None and output.strategy_list:
                    output.refined_strategy_list = self._stage_review_refine(
                        output.strategy_list, sim_feedback
                    )

            # Stage 6: Build frontend data
            output.frontend_data = self._stage_frontend(output)

            output.status = "success"
        except Exception as e:
            output.errors.append(f"Pipeline error: {e}")
            output.status = "partial" if output.user_profile is not None else "failed"

        output.elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return output

    # ── Stage 1: Parser ─────────────────────────────────────────────────────

    def _stage_parse(
        self,
        user_input: dict | str,
        career_dataset: list[dict] | None,
        user_id: str,
    ) -> ParserOutput:
        """Parse user profile and career dataset into standardized format."""
        warnings: list[str] = []

        # Parse user profile
        if isinstance(user_input, str):
            profile = self._parse_user_text(user_input, user_id)
        elif isinstance(user_input, dict):
            profile = self._parse_user_dict(user_input, user_id)
        else:
            raise TypeError(f"user_input must be dict or str, got {type(user_input)}")

        # Parse career dataset
        career_data = None
        if career_dataset:
            entries = self._parse_career_dataset(career_dataset)
            career_data = CareerData(entries=entries, total_entries=len(entries))
            if len(entries) < len(career_dataset):
                warnings.append(
                    f"Parsed {len(entries)}/{len(career_dataset)} dataset entries "
                    f"— {len(career_dataset) - len(entries)} entries were invalid"
                )

        return ParserOutput(user_profile=profile, career_data=career_data, warnings=warnings)

    def _parse_user_text(self, text: str, user_id: str) -> UserProfile:
        """Parse free-text user input into UserProfile.

        Extracts skills from keyword matching, goals from intent patterns.
        """
        text_lower = text.lower().strip()

        # Extract career goals from intent patterns
        goals = self._extract_goals(text_lower)

        # Extract skills from known skill keywords
        skills = self._extract_skills(text_lower)

        # Detect experience level
        exp_years = self._detect_experience(text_lower)

        # Detect education
        education = self._detect_education(text_lower)

        # Detect locations
        locations = self._extract_locations(text_lower)

        return UserProfile(
            user_id=user_id,
            career_goals=goals,
            skills=skills,
            experience_years=exp_years,
            education_level=education,
            preferred_locations=locations,
            raw_text=text,
        )

    def _parse_user_dict(self, data: dict, user_id: str) -> UserProfile:
        """Parse structured dict into UserProfile with validation."""
        salary = None
        raw_salary = data.get("salary_expectation") or data.get("salary")
        if raw_salary and isinstance(raw_salary, (list, tuple)) and len(raw_salary) == 2:
            salary = (int(raw_salary[0]), int(raw_salary[1]))

        return UserProfile(
            user_id=user_id,
            career_goals=self._normalize_list(data.get("career_goals") or data.get("goals", [])),
            skills=self._normalize_list(data.get("skills", [])),
            experience_years=float(data.get("experience_years") or data.get("experience", 0)),
            education_level=str(data.get("education_level") or data.get("education", "")),
            preferred_locations=self._normalize_list(
                data.get("preferred_locations") or data.get("locations", [])
            ),
            preferred_industries=self._normalize_list(
                data.get("preferred_industries") or data.get("industries", [])
            ),
            salary_expectation=salary,
            raw_text=str(data.get("raw_text") or data.get("description", "")),
        )

    def _parse_career_dataset(self, entries: list[dict]) -> list[CareerDataEntry]:
        """Parse raw career dataset entries (recruitment info, career paths)."""
        parsed: list[CareerDataEntry] = []
        for entry in entries:
            try:
                salary = None
                raw_salary = entry.get("salary_range") or entry.get("salary")
                if raw_salary and isinstance(raw_salary, (list, tuple)) and len(raw_salary) == 2:
                    salary = (int(raw_salary[0]), int(raw_salary[1]))

                parsed.append(
                    CareerDataEntry(
                        job_title=str(entry.get("job_title") or entry.get("title", "")),
                        required_skills=self._normalize_list(
                            entry.get("required_skills") or entry.get("skills", [])
                        ),
                        optional_skills=self._normalize_list(
                            entry.get("optional_skills") or entry.get("nice_to_have", [])
                        ),
                        growth_path=self._normalize_list(
                            entry.get("growth_path") or entry.get("career_path", [])
                        ),
                        level=str(entry.get("level", "")),
                        salary_range=salary,
                        location=str(entry.get("location", "")),
                        industry=str(entry.get("industry", "")),
                        source=str(entry.get("source", "dataset")),
                    )
                )
            except Exception:
                continue
        return parsed

    # ── Stage 2: Retrieval ──────────────────────────────────────────────────

    def _stage_retrieve(self, parser_output: ParserOutput) -> RetrievalOutput:
        """Retrieve matching jobs and strategies from available data."""
        profile = parser_output.user_profile

        # Match jobs from career dataset
        job_recs: list[JobRecommendation] = []
        if parser_output.career_data:
            for entry in parser_output.career_data.entries:
                match_score = self._compute_job_match(profile, entry)
                job_recs.append(
                    JobRecommendation(
                        job_id=f"job-{uuid.uuid4().hex[:8]}",
                        title=entry.job_title,
                        level=entry.level,
                        location=entry.location,
                        required_skills=entry.required_skills,
                        optional_skills=entry.optional_skills,
                        salary_range=entry.salary_range,
                        match_score=round(match_score, 3),
                        match_details=self._match_details(profile, entry),
                    )
                )
            job_recs.sort(key=lambda j: -j.match_score)

        # Retrieve strategy candidates from historical patterns
        strategy_candidates = self._retrieve_strategies(profile)

        return RetrievalOutput(
            job_recommendations=job_recs[:10],
            strategy_candidates=strategy_candidates,
            total_matches=len(job_recs),
        )

    def _retrieve_strategies(self, profile: UserProfile) -> list[StrategyCandidate]:
        """Retrieve strategy candidates based on user profile.

        Maps profile characteristics to known effective strategies.
        Strategy types: aggressive (fast application), conservative (skill-first),
        balanced (mixed approach), pivot (career change).
        """
        strategies: list[StrategyCandidate] = []

        # Determine applicable strategies based on profile
        if profile.experience_years >= 3:
            strategies.append(
                StrategyCandidate(
                    strategy_id="strat-aggressive",
                    strategy_name="aggressive",
                    description="Rapid application to senior roles leveraging existing experience",
                    match_score=0.85 if profile.experience_years >= 5 else 0.70,
                    historical_success_rate=0.72,
                    source="history",
                )
            )

        if profile.skills and len(profile.skills) >= 5:
            strategies.append(
                StrategyCandidate(
                    strategy_id="strat-balanced",
                    strategy_name="balanced",
                    description="Balanced preparation with targeted applications matching skill profile",
                    match_score=0.90,
                    historical_success_rate=0.78,
                    source="history",
                )
            )

        strategies.append(
            StrategyCandidate(
                strategy_id="strat-conservative",
                strategy_name="conservative",
                description="Skill development first, then targeted high-quality applications",
                match_score=0.75,
                historical_success_rate=0.82,
                source="history",
            )
        )

        # Pivot strategy — applicable if goals diverge from current skills
        if profile.career_goals and profile.skills:
            goal_skills = set()
            for goal in profile.career_goals:
                for token in goal.lower().split():
                    goal_skills.add(token)
            current_skills = {s.lower() for s in profile.skills}
            overlap = goal_skills & current_skills
            if len(overlap) < max(2, len(profile.skills) * 0.3):
                strategies.append(
                    StrategyCandidate(
                        strategy_id="strat-pivot",
                        strategy_name="pivot",
                        description="Career pivot: acquire new skills for target role transition",
                        match_score=0.60,
                        historical_success_rate=0.65,
                        source="history",
                    )
                )

        return strategies

    # ── Stage 3: Reviewer ───────────────────────────────────────────────────

    def _stage_review(self, retrieval_output: RetrievalOutput) -> ReviewerOutput:
        """Score and rank strategies across 4 dimensions."""
        scored: list[ScoredStrategy] = []

        weights = {
            "success_rate": 0.35,
            "match_degree": 0.30,
            "growth_cycle": 0.20,
            "skill_adaptability": 0.15,
        }

        for candidate in retrieval_output.strategy_candidates:
            scores = self._score_strategy(candidate)
            overall = sum(scores[dim] * weights[dim] for dim in weights)
            scored.append(
                ScoredStrategy(
                    strategy=candidate,
                    scores=scores,
                    overall_score=round(overall, 3),
                    rationale=self._generate_rationale(candidate, scores),
                )
            )

        # Sort by overall score, descending
        scored.sort(key=lambda s: -s.overall_score)

        # Assign ranks
        for i, s in enumerate(scored):
            s.rank = i + 1

        return ReviewerOutput(strategy_list=scored, top_n=min(3, len(scored)))

    def _score_strategy(self, candidate: StrategyCandidate) -> dict[str, float]:
        """Compute 4-dimension scores for a strategy candidate.

        Dimensions:
          - success_rate: Based on historical T007 simulation results
          - match_degree: How well the strategy matches user profile
          - growth_cycle: How long the strategy takes to yield results (shorter = higher)
          - skill_adaptability: How well the strategy accommodates skill gaps
        """
        # Success rate — directly from historical data
        success_rate = candidate.historical_success_rate

        # Match degree — how well this strategy type fits the profile
        match_degree = candidate.match_score

        # Growth cycle — aggressive is fast (high score), conservative is slow (low score)
        growth_cycle_map = {
            "aggressive": 0.80,
            "balanced": 0.70,
            "pivot": 0.45,
            "conservative": 0.40,
        }
        growth_cycle = growth_cycle_map.get(candidate.strategy_name, 0.60)

        # Skill adaptability — how well the strategy handles skill gaps
        adaptability_map = {
            "conservative": 0.90,  # Skill-first approach
            "balanced": 0.75,
            "pivot": 0.70,
            "aggressive": 0.50,  # Fast application can expose gaps
        }
        skill_adaptability = adaptability_map.get(candidate.strategy_name, 0.65)

        return {
            "success_rate": round(success_rate, 3),
            "match_degree": round(match_degree, 3),
            "growth_cycle": round(growth_cycle, 3),
            "skill_adaptability": round(skill_adaptability, 3),
        }

    @staticmethod
    def _generate_rationale(candidate: StrategyCandidate, scores: dict[str, float]) -> str:
        """Generate human-readable rationale for strategy scoring."""
        strengths = [dim for dim, score in scores.items() if score >= 0.75]
        weaknesses = [dim for dim, score in scores.items() if score < 0.5]

        dim_labels = {
            "success_rate": "historical success rate",
            "match_degree": "profile match",
            "growth_cycle": "growth speed",
            "skill_adaptability": "skill gap tolerance",
        }

        parts: list[str] = []
        if strengths:
            strong_labels = [dim_labels.get(d, d) for d in strengths]
            parts.append(f"Strengths: {', '.join(strong_labels)}")
        if weaknesses:
            weak_labels = [dim_labels.get(d, d) for d in weaknesses]
            parts.append(f"Weaknesses: {', '.join(weak_labels)}")
        if not parts:
            parts.append("All dimensions at moderate levels")

        return ". ".join(parts)

    # ── Stage 3-revisit: Reviewer re-rank ───────────────────────────────────

    def _stage_review_refine(
        self,
        current_list: list[ScoredStrategy],
        simulation_feedback: SimulationFeedback,
    ) -> list[ScoredStrategy]:
        """Re-rank strategies after incorporating simulation feedback.

        Adjusts scores based on simulated outcomes — strategies that performed
        well in simulation get a boost.
        """
        refined: list[ScoredStrategy] = []
        for scored in current_list:
            # Boost success_rate score if simulation confirmed high success
            sim_adjustment = 0.0
            strategy_name = scored.strategy.strategy_name
            if simulation_feedback.average_success_rate > 0.6:
                sim_adjustment = 0.05
            elif simulation_feedback.average_success_rate < 0.3:
                sim_adjustment = -0.05

            new_scores = dict(scored.scores)
            new_scores["success_rate"] = round(
                max(0.0, min(1.0, scored.scores["success_rate"] + sim_adjustment)), 3
            )

            weights = {"success_rate": 0.35, "match_degree": 0.30, "growth_cycle": 0.20, "skill_adaptability": 0.15}
            new_overall = round(
                sum(new_scores[dim] * weights[dim] for dim in weights), 3
            )

            refined.append(
                ScoredStrategy(
                    strategy=scored.strategy,
                    scores=new_scores,
                    overall_score=new_overall,
                    rationale=(
                        f"{scored.rationale} "
                        f"[Refined: simulation avg success={simulation_feedback.average_success_rate:.0%}]"
                    ),
                    rank=0,
                )
            )

        refined.sort(key=lambda s: -s.overall_score)
        for i, s in enumerate(refined):
            s.rank = i + 1

        return refined

    # ── Stage 4: Architect ──────────────────────────────────────────────────

    def _stage_architect(
        self,
        parser_output: ParserOutput,
        reviewer_output: ReviewerOutput,
    ) -> ArchitectOutput:
        """Generate career growth plan and visualization data."""
        profile = parser_output.user_profile
        top_strategies = reviewer_output.strategy_list[: reviewer_output.top_n]

        # Select top strategy
        selected = top_strategies[0] if top_strategies else None

        # Build plan steps
        steps = self._build_plan_steps(profile, selected, parser_output.career_data)
        total_days = sum(s.duration_days for s in steps)

        # Identify skill gaps
        skill_gaps = self._identify_skill_gaps(profile, parser_output.career_data)

        # Estimate success rate
        success_rate = selected.overall_score if selected else 0.5

        # Risk assessment
        risks = self._assess_risks(profile, skill_gaps, steps)

        career_plan = CareerPlan(
            user_id=profile.user_id,
            selected_strategy=selected,
            alternative_strategies=top_strategies[1:] if len(top_strategies) > 1 else [],
            steps=steps,
            total_duration_days=total_days,
            estimated_success_rate=round(success_rate, 2),
            risk_points=risks,
            skill_gaps=skill_gaps,
            recommendation=self._generate_recommendation(selected, steps, risks),
        )

        # Build visualization graph
        viz_graph = self._build_visualization_graph(profile, career_plan, top_strategies)

        return ArchitectOutput(career_plan=career_plan, visualization_data=viz_graph)

    def _build_plan_steps(
        self,
        profile: UserProfile,
        strategy: ScoredStrategy | None,
        career_data: CareerData | None,
    ) -> list[PlanStep]:
        """Build executable step-by-step career plan."""
        strategy_name = strategy.strategy.strategy_name if strategy else "balanced"

        steps: list[PlanStep] = []
        step_num = 0

        if strategy_name == "aggressive":
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="preparation",
                title="Resume optimization",
                description="Quick resume polish focusing on quantifiable achievements. Target 1-day turnaround.",
                duration_days=2,
                skills_required=profile.skills[:5],
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="application",
                title="High-volume targeted applications",
                description="Apply to 10-15 positions matching top skills. Prioritize speed over customization.",
                duration_days=5,
                skills_required=profile.skills[:3],
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="interview",
                title="Intensive interview sprint",
                description="Schedule interviews within a compressed window. Prepare core talking points.",
                duration_days=7,
                skills_required=profile.skills,
                milestones=["First interview scheduled", "Offer received"],
            ))

        elif strategy_name == "conservative":
            focus_skills = self._identify_skill_gaps(profile, career_data)
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="preparation",
                title="Skill gap analysis & learning plan",
                description=f"Deep assessment of {', '.join(focus_skills[:3]) or 'target'} skills. Create structured learning roadmap.",
                duration_days=5,
                skills_acquired=focus_skills[:2],
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="preparation",
                title="Hands-on skill building",
                description="Complete courses, build projects, earn certifications in target areas.",
                duration_days=21,
                skills_acquired=focus_skills[:3],
                milestones=["Course completed", "Project deployed"],
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="application",
                title="Selective high-quality applications",
                description="Apply to 5 carefully selected positions with tailored materials.",
                duration_days=10,
            ))

        elif strategy_name == "pivot":
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="preparation",
                title="Target role skill mapping",
                description="Map all required skills for target career path. Identify transferable vs. new skills.",
                duration_days=3,
                milestones=["Skill map completed"],
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="preparation",
                title="Foundational skill acquisition",
                description="Learn core new skills. Build portfolio projects demonstrating capability.",
                duration_days=30,
                skills_acquired=["foundational skills for target role"],
                milestones=["First portfolio project completed"],
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="application",
                title="Bridge role applications",
                description="Target transitional roles that value transferable skills while building new ones.",
                duration_days=14,
            ))

        else:  # balanced
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="preparation",
                title="Skills refresh & gap assessment",
                description="Review current skills against market demand. Identify 1-2 high-impact skills to acquire.",
                duration_days=5,
                skills_required=profile.skills[:5],
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="application",
                title="Balanced application strategy",
                description="Apply to 8-10 positions weekly. Mix of stretch roles and safe matches.",
                duration_days=7,
            ))
            steps.append(PlanStep(
                step_number=(step_num := step_num + 1),
                phase="interview",
                title="Parallel interview + skill building",
                description="Interview while continuing targeted skill development. Iterate based on feedback.",
                duration_days=14,
                milestones=["3+ interviews completed", "Skill milestone reached"],
            ))

        return steps

    # ── Stage 5: Simulation ─────────────────────────────────────────────────

    def _stage_simulate(self, career_plan: CareerPlan) -> SimulationFeedback:
        """Run multi-round simulation of the career plan."""
        rounds: list[SimulationRound] = []
        risk_counts: dict[str, int] = {}
        gap_counts: dict[str, int] = {}

        for i in range(self._simulation_rounds):
            sim_round = self._run_single_simulation(career_plan, i + 1)
            rounds.append(sim_round)

            for risk in sim_round.risk_triggered:
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
            for gap in sim_round.skill_gaps_exposed:
                gap_counts[gap] = gap_counts.get(gap, 0) + 1

        successful = sum(1 for r in rounds if r.success)
        avg_success = successful / len(rounds) if rounds else 0.0

        recommendation = self._simulation_recommendation(avg_success, risk_counts, gap_counts)

        return SimulationFeedback(
            career_plan_id=career_plan.plan_id,
            total_rounds=len(rounds),
            successful_rounds=successful,
            average_success_rate=round(avg_success, 3),
            rounds=rounds,
            aggregated_risks=risk_counts,
            aggregated_skill_gaps=gap_counts,
            recommendation=recommendation,
        )

    def _run_single_simulation(
        self, career_plan: CareerPlan, round_id: int
    ) -> SimulationRound:
        """Run one simulation round with stochastic outcome.

        Success probability is modulated by:
          - Base success rate from the plan
          - Random noise (market conditions, luck)
          - Risk factors that may trigger
        """
        import random

        base_prob = career_plan.estimated_success_rate

        # Market noise: ±15%
        noise = random.uniform(-0.15, 0.15)
        adjusted_prob = max(0.05, min(0.95, base_prob + noise))

        # Roll for success
        success = random.random() < adjusted_prob

        # Determine which risks triggered
        triggered_risks: list[str] = []
        for risk in career_plan.risk_points:
            # Risks have a chance of triggering inversely related to success prob
            trigger_chance = 0.3 * (1.0 - adjusted_prob)
            if random.random() < trigger_chance:
                triggered_risks.append(risk)

        # Determine which skill gaps were exposed
        exposed_gaps: list[str] = []
        for gap in career_plan.skill_gaps:
            if random.random() < 0.25:
                exposed_gaps.append(gap)

        steps = max(1, career_plan.total_duration_days // 7) if career_plan.total_duration_days > 0 else len(career_plan.steps)

        return SimulationRound(
            round_id=round_id,
            success=success,
            success_probability=round(adjusted_prob, 3),
            risk_triggered=triggered_risks,
            skill_gaps_exposed=exposed_gaps,
            steps_to_outcome=steps,
            notes=f"Round {round_id}: {'succeeded' if success else 'failed'} (P={adjusted_prob:.0%})",
        )

    @staticmethod
    def _simulation_recommendation(
        avg_success: float,
        risk_counts: dict[str, int],
        gap_counts: dict[str, int],
    ) -> str:
        """Generate feedback recommendation based on simulation results."""
        if avg_success >= 0.7:
            base = f"High confidence ({avg_success:.0%}): Strategy is robust. "
        elif avg_success >= 0.4:
            base = f"Moderate confidence ({avg_success:.0%}): Strategy works but has variability. "
        else:
            base = f"Low confidence ({avg_success:.0%}): Strategy needs revision. "

        if risk_counts:
            top_risks = sorted(risk_counts.items(), key=lambda x: -x[1])[:2]
            base += f"Top risks: {', '.join(f'{r} ({c}x)' for r, c in top_risks)}. "

        if gap_counts:
            top_gaps = sorted(gap_counts.items(), key=lambda x: -x[1])[:2]
            base += f"Recurring skill gaps: {', '.join(f'{g} ({c}x)' for g, c in top_gaps)}. "

        return base

    # ── Stage 6: Frontend ───────────────────────────────────────────────────

    def _stage_frontend(self, output: T008PipelineOutput) -> dict:
        """Build frontend-ready data structures."""
        return {
            "summary": self._build_frontend_summary(output),
            "career_path_graph": output.visualization_data.model_dump()
            if output.visualization_data
            else {},
            "strategy_comparison": self._build_strategy_comparison(output),
            "action_timeline": self._build_action_timeline(output),
            "simulation_chart": self._build_simulation_chart(output),
            "recommendations": self._build_recommendation_list(output),
        }

    def _build_frontend_summary(self, output: T008PipelineOutput) -> dict:
        """Build summary card data for frontend."""
        profile = output.user_profile
        plan = output.career_plan
        sim = output.simulation_feedback

        return {
            "headline": (
                f"Career plan ready — {plan.selected_strategy.strategy.strategy_name if plan and plan.selected_strategy else 'balanced'} strategy"
                if plan else "Building career plan..."
            ),
            "user_skills": profile.skills[:8] if profile else [],
            "career_goals": profile.career_goals[:3] if profile else [],
            "total_jobs_matched": len(output.job_recommendations),
            "top_strategy_score": (
                output.strategy_list[0].overall_score
                if output.strategy_list
                else 0.0
            ),
            "simulation_success_rate": sim.average_success_rate if sim else 0.0,
            "simulation_rounds": sim.total_rounds if sim else 0,
        }

    def _build_strategy_comparison(self, output: T008PipelineOutput) -> dict:
        """Build strategy comparison data for radar/bar chart."""
        strategies = output.refined_strategy_list or output.strategy_list
        return {
            "strategies": [
                {
                    "name": s.strategy.strategy_name,
                    "overall": s.overall_score,
                    "success_rate": s.scores["success_rate"],
                    "match_degree": s.scores["match_degree"],
                    "growth_cycle": s.scores["growth_cycle"],
                    "skill_adaptability": s.scores["skill_adaptability"],
                    "rank": s.rank,
                }
                for s in strategies[:5]
            ],
            "dimensions": ["success_rate", "match_degree", "growth_cycle", "skill_adaptability"],
        }

    def _build_action_timeline(self, output: T008PipelineOutput) -> list[dict]:
        """Build action timeline for Gantt-like visualization."""
        plan = output.career_plan
        if not plan:
            return []

        timeline: list[dict] = []
        cumulative_days = 0
        for step in plan.steps:
            timeline.append({
                "step_number": step.step_number,
                "phase": step.phase,
                "title": step.title,
                "description": step.description,
                "start_day": cumulative_days,
                "end_day": cumulative_days + step.duration_days,
                "duration_days": step.duration_days,
                "milestones": step.milestones,
            })
            cumulative_days += step.duration_days

        return timeline

    def _build_simulation_chart(self, output: T008PipelineOutput) -> dict:
        """Build simulation results chart data."""
        sim = output.simulation_feedback
        if not sim:
            return {"rounds": [], "average": 0.0}

        return {
            "rounds": [
                {"round": r.round_id, "probability": r.success_probability, "success": r.success}
                for r in sim.rounds
            ],
            "average": sim.average_success_rate,
            "successful": sim.successful_rounds,
            "total": sim.total_rounds,
            "top_risks": dict(sorted(sim.aggregated_risks.items(), key=lambda x: -x[1])[:5]),
            "top_gaps": dict(sorted(sim.aggregated_skill_gaps.items(), key=lambda x: -x[1])[:5]),
        }

    def _build_recommendation_list(self, output: T008PipelineOutput) -> list[dict]:
        """Build prioritized recommendation cards."""
        recs: list[dict] = []

        if output.career_plan and output.career_plan.selected_strategy:
            recs.append({
                "priority": 1,
                "type": "strategy",
                "title": f"Adopt '{output.career_plan.selected_strategy.strategy.strategy_name}' strategy",
                "description": output.career_plan.selected_strategy.rationale,
            })

        if output.simulation_feedback:
            recs.append({
                "priority": 2,
                "type": "simulation",
                "title": f"Simulation confidence: {output.simulation_feedback.average_success_rate:.0%}",
                "description": output.simulation_feedback.recommendation,
            })

        if output.career_plan and output.career_plan.skill_gaps:
            recs.append({
                "priority": 3,
                "type": "skill_gap",
                "title": "Address skill gaps",
                "description": f"Focus on: {', '.join(output.career_plan.skill_gaps[:3])}",
            })

        return recs

    # ── Visualization Graph Builder ─────────────────────────────────────────

    def _build_visualization_graph(
        self,
        profile: UserProfile,
        plan: CareerPlan,
        strategies: list[ScoredStrategy],
    ) -> VisualizationGraph:
        """Build frontend-renderable career path graph."""
        # Skill nodes from profile skills + required skills from plan
        skill_nodes: list[SkillNode] = []
        seen_skills: set[str] = set()

        # Current skills
        for skill in profile.skills[:10]:
            skill_lower = skill.lower().strip()
            if skill_lower not in seen_skills:
                seen_skills.add(skill_lower)
                skill_nodes.append(
                    SkillNode(skill_name=skill_lower, level="intermediate", estimated_hours=0)
                )

        # Target skills (from job matches / plan gaps)
        for gap in plan.skill_gaps[:5]:
            gap_lower = gap.lower().strip()
            if gap_lower not in seen_skills:
                seen_skills.add(gap_lower)
                skill_nodes.append(
                    SkillNode(
                        skill_name=gap_lower,
                        level="beginner",
                        dependencies=profile.skills[:3] if profile.skills else [],
                        estimated_hours=40.0,
                    )
                )

        # Skill edges: current skills → target skills (dependency)
        skill_edges: list[tuple[str, str]] = []
        for node in skill_nodes:
            for dep in node.dependencies:
                if dep.lower().strip() in seen_skills:
                    skill_edges.append((dep.lower().strip(), node.skill_name))

        # Timeline nodes from plan steps
        timeline_nodes: list[TimelineNode] = []
        cumulative_weeks = 0
        for step in plan.steps:
            weekly_start = cumulative_weeks // 7
            timeline_nodes.append(
                TimelineNode(
                    week=weekly_start,
                    label=step.title,
                    event_type="milestone" if step.milestones else "skill_acquisition" if step.skills_acquired else "application",
                    details=step.description,
                )
            )
            cumulative_weeks += step.duration_days // 7 + 1

        # Primary path: ordered skill acquisition
        primary_path = [n.skill_name for n in skill_nodes if n.estimated_hours > 0]

        # Strategy comparison
        strategy_comparison = {}
        for s in strategies:
            strategy_comparison[s.strategy.strategy_name] = {
                "success_rate": s.scores["success_rate"],
                "growth_cycle": s.scores["growth_cycle"],
                "skill_adaptability": s.scores["skill_adaptability"],
            }

        return VisualizationGraph(
            skill_nodes=skill_nodes,
            skill_edges=skill_edges,
            timeline_nodes=timeline_nodes,
            primary_path=primary_path,
            alternative_paths=[],
            strategy_comparison=strategy_comparison,
            render_hints={
                "layout": "tree",
                "color_scheme": "professional",
                "zoom_range": [0.5, 3.0],
                "skill_colors": {"beginner": "#3498db", "intermediate": "#2ecc71", "advanced": "#f39c12", "expert": "#e74c3c"},
            },
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_job_match(profile: UserProfile, entry: CareerDataEntry) -> float:
        """Compute match score between user profile and a career data entry."""
        if not profile.skills:
            return 0.3

        profile_skills = {s.lower().strip() for s in profile.skills}
        required = {s.lower().strip() for s in entry.required_skills}
        optional = {s.lower().strip() for s in entry.optional_skills}

        if not required:
            return 0.4

        # Required skill overlap (70% weight)
        required_overlap = len(profile_skills & required) / len(required)
        # Optional skill overlap (30% weight)
        optional_overlap = len(profile_skills & optional) / len(optional) if optional else 0.5

        score = required_overlap * 0.7 + optional_overlap * 0.3

        # Level bonus
        if entry.level:
            level_map = {"初级": 0.0, "中级": 0.05, "高级": 0.10, "专家": 0.15}
            for key, bonus in level_map.items():
                if key in entry.level:
                    score = min(1.0, score + bonus)
                    break

        # Location bonus
        if profile.preferred_locations and entry.location:
            if any(loc.lower() in entry.location.lower() for loc in profile.preferred_locations):
                score = min(1.0, score + 0.05)

        return max(0.0, min(1.0, score))

    @staticmethod
    def _match_details(profile: UserProfile, entry: CareerDataEntry) -> dict:
        """Build detailed match breakdown."""
        profile_skills = {s.lower().strip() for s in profile.skills}
        required = {s.lower().strip() for s in entry.required_skills}
        optional = {s.lower().strip() for s in entry.optional_skills}

        return {
            "skill_overlap": sorted(profile_skills & required),
            "missing_required": sorted(required - profile_skills),
            "optional_match": sorted(profile_skills & optional),
            "level": entry.level,
            "location": entry.location,
        }

    @staticmethod
    def _extract_goals(text: str) -> list[str]:
        """Extract career goals from free text."""
        goal_patterns = [
            "想要成为", "目标", "期望", "希望从事", "想做", "转行", "晋升",
            "want to become", "goal", "target role", "seeking", "aspiring",
        ]
        goals: list[str] = []
        for pattern in goal_patterns:
            idx = text.find(pattern)
            if idx >= 0:
                snippet = text[idx + len(pattern):idx + len(pattern) + 60].strip()
                # Take first sentence-like segment
                for delimiter in ["。", ".", "，", ",", "\n", "；", ";"]:
                    if delimiter in snippet:
                        snippet = snippet.split(delimiter)[0]
                if len(snippet) >= 2:
                    goals.append(snippet.strip())
        return goals[:3]

    @staticmethod
    def _extract_skills(text: str) -> list[str]:
        """Extract skill keywords from text."""
        known_skills = {
            "python", "java", "javascript", "typescript", "react", "vue", "angular",
            "node", "golang", "rust", "c++", "sql", "mongodb", "postgresql",
            "redis", "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
            "machine learning", "深度学习", "nlp", "计算机视觉",
            "数据分析", "数据挖掘", "大数据", "spark", "hadoop", "flink",
            "项目管理", "产品设计", "ui设计", "用户体验",
            "营销", "销售", "运营", "财务", "人力资源",
        }
        found: set[str] = set()
        text_lower = text.lower()
        for skill in known_skills:
            if skill in text_lower:
                found.add(skill)
        return sorted(found)

    @staticmethod
    def _detect_experience(text: str) -> float:
        """Detect years of experience from text."""
        import re
        # Match patterns like "5年", "3 years", "十年"
        patterns = [
            (r"(\d+)\s*年", 1),
            (r"(\d+)\s*years?", 1),
            (r"十(\d+)\s*年", 10),
            (r"(\d+)年经验", 1),
        ]
        for pattern, multiplier in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1)) * multiplier
        return 1.0

    @staticmethod
    def _detect_education(text: str) -> str:
        """Detect education level from text."""
        edu_map = {
            "博士": "博士", "phd": "博士",
            "硕士": "硕士", "master": "硕士",
            "本科": "本科", "bachelor": "本科",
            "大专": "大专", "associate": "大专",
        }
        text_lower = text.lower()
        for key, value in edu_map.items():
            if key in text_lower:
                return value
        return "本科"

    @staticmethod
    def _extract_locations(text: str) -> list[str]:
        """Extract preferred locations from text."""
        known_locations = [
            "北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京",
            "西安", "苏州", "重庆", "天津", "长沙", "郑州", "东莞", "青岛",
            "remote", "远程",
        ]
        found: list[str] = []
        for loc in known_locations:
            if loc in text:
                found.append(loc)
        return found[:3]

    @staticmethod
    def _normalize_list(value) -> list[str]:
        """Normalize input to list of strings."""
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        if isinstance(value, str):
            return [s.strip() for s in value.replace("，", ",").split(",") if s.strip()]
        return []

    @staticmethod
    def _identify_skill_gaps(
        profile: UserProfile,
        career_data: CareerData | None,
    ) -> list[str]:
        """Identify skills missing from profile that appear in target career paths."""
        if not career_data:
            return []

        profile_skills = {s.lower().strip() for s in profile.skills}
        all_required: set[str] = set()
        for entry in career_data.entries:
            all_required.update(s.lower().strip() for s in entry.required_skills)

        gaps = all_required - profile_skills
        return sorted(gaps)[:5]

    @staticmethod
    def _assess_risks(
        profile: UserProfile,
        skill_gaps: list[str],
        steps: list[PlanStep],
    ) -> list[str]:
        """Identify risks in the career plan."""
        risks: list[str] = []

        if len(skill_gaps) >= 3:
            risks.append(f"Multiple skill gaps ({len(skill_gaps)}) may require extended preparation time")

        if profile.experience_years < 1:
            risks.append("Limited experience may disadvantage in senior role applications")

        total_days = sum(s.duration_days for s in steps)
        if total_days > 30:
            risks.append(f"Extended plan duration ({total_days} days) — risk of market conditions changing")

        if not profile.preferred_locations:
            risks.append("No location preference specified — may face location mismatch in offers")

        return risks

    @staticmethod
    def _generate_recommendation(
        strategy: ScoredStrategy | None,
        steps: list[PlanStep],
        risks: list[str],
    ) -> str:
        """Generate human-readable career recommendation."""
        if not strategy:
            return "Insufficient data to generate recommendation. Provide more career context."

        parts: list[str] = [
            f"Recommended strategy: '{strategy.strategy.strategy_name}' "
            f"(overall score: {strategy.overall_score:.0%})."
        ]

        if steps:
            parts.append(
                f"Plan spans {len(steps)} phases over approximately "
                f"{sum(s.duration_days for s in steps)} days."
            )

        if risks:
            parts.append(f"Watch for: {'; '.join(risks[:2])}.")

        return " ".join(parts)
