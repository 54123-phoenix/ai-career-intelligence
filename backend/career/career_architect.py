"""CareerArchitect — design next-phase career strategy (T007 Step 4).

Output: CareerStrategy with focus_skill, 7-14 day action plan (max 5),
risk analysis, success expectation.

All strategy MUST be specific, executable, and based on pattern data.
No generic advice.
"""

from __future__ import annotations

from backend.career.schemas import (
    ActionItem,
    BottleneckAnalysis,
    CareerStrategy,
    CareerTimeline,
)


class CareerArchitect:
    """Design career development strategies based on profile + pattern analysis.

    Usage:
        architect = CareerArchitect()
        strategy = architect.design(timeline, bottleneck_analysis)
    """

    # Action templates per bottleneck type
    _ACTION_TEMPLATES: dict[str, list[dict]] = {
        "skill_gap": [
            {"action": "Identify top 3 required skills from target job descriptions", "category": "research", "hours": 2.0},
            {"action": "Complete online course/ tutorial for {skill} fundamentals", "category": "skill", "hours": 4.0},
            {"action": "Build a mini-project demonstrating {skill} proficiency", "category": "skill", "hours": 6.0},
            {"action": "Update resume and portfolio with new {skill} projects", "category": "application", "hours": 2.0},
            {"action": "Apply to 5 positions requiring {skill} at junior-mid level", "category": "application", "hours": 3.0},
        ],
        "interview_skill": [
            {"action": "Schedule 2 mock interviews (friend/mentor/platform)", "category": "interview_prep", "hours": 3.0},
            {"action": "Practice top 20 behavioral questions with STAR format", "category": "interview_prep", "hours": 3.0},
            {"action": "Review and document past interview failures — what went wrong", "category": "research", "hours": 2.0},
            {"action": "Do 5 LeetCode/system design problems in target domain", "category": "skill", "hours": 5.0},
            {"action": "Apply to 3 'practice' companies before target companies", "category": "application", "hours": 2.0},
        ],
        "application_volume_low": [
            {"action": "Set up job alerts on 3 platforms (LinkedIn, BOSS, Lagou)", "category": "research", "hours": 1.0},
            {"action": "Apply to 10 positions matching current skills", "category": "application", "hours": 4.0},
            {"action": "Expand search to 2 adjacent cities or remote positions", "category": "research", "hours": 1.0},
            {"action": "Reach out to 5 recruiters or hiring managers directly", "category": "networking", "hours": 2.0},
            {"action": "Track all applications in a spreadsheet with follow-up dates", "category": "application", "hours": 1.0},
        ],
        "experience_deficit": [
            {"action": "Identify 2 open-source projects in target domain to contribute to", "category": "research", "hours": 2.0},
            {"action": "Submit first PR to an open-source project", "category": "skill", "hours": 4.0},
            {"action": "Build a comprehensive side project mimicking production systems", "category": "skill", "hours": 8.0},
            {"action": "Write a technical blog post demonstrating domain knowledge", "category": "networking", "hours": 3.0},
            {"action": "Apply to positions one level below target with growth potential", "category": "application", "hours": 2.0},
        ],
        "resume_quality": [
            {"action": "Rewrite resume with quantifiable achievements (numbers, percentages)", "category": "application", "hours": 3.0},
            {"action": "Get resume reviewed by 3 peers or professional service", "category": "networking", "hours": 2.0},
            {"action": "Tailor resume for 3 different role types", "category": "application", "hours": 2.0},
            {"action": "Add portfolio links and GitHub profile to resume", "category": "application", "hours": 1.0},
            {"action": "A/B test new resume with 10 applications and track response rate", "category": "application", "hours": 2.0},
        ],
        "compensation_mismatch": [
            {"action": "Research market rates for target role on 3 salary platforms", "category": "research", "hours": 2.0},
            {"action": "Practice compensation negotiation scripts", "category": "interview_prep", "hours": 2.0},
            {"action": "Identify 5 companies known for competitive compensation", "category": "research", "hours": 2.0},
            {"action": "Adjust target salary range to market median + 10%", "category": "application", "hours": 1.0},
            {"action": "Apply to 5 positions at target compensation level", "category": "application", "hours": 3.0},
        ],
    }

    _DEFAULT_ACTIONS = [
        {"action": "Review career goals and set 3-month target", "category": "research", "hours": 1.0},
        {"action": "Identify skill gaps from recent job descriptions", "category": "research", "hours": 2.0},
        {"action": "Update resume with latest achievements", "category": "application", "hours": 2.0},
        {"action": "Apply to 5 matching positions", "category": "application", "hours": 3.0},
        {"action": "Network with 3 industry contacts", "category": "networking", "hours": 2.0},
    ]

    def design(
        self,
        timeline: CareerTimeline,
        bottleneck: BottleneckAnalysis,
    ) -> CareerStrategy:
        """Design a career strategy from timeline + bottleneck analysis.

        Args:
            timeline: CareerTimeline with user history
            bottleneck: BottleneckAnalysis with identified patterns

        Returns:
            CareerStrategy with concrete action plan
        """
        # Focus skill: derive from bottleneck + skill gaps
        focus_skill = self._determine_focus_skill(bottleneck, timeline)

        # Action plan: select from templates based on bottleneck
        actions = self._build_action_plan(bottleneck, focus_skill)

        # Risk analysis
        risk, severity = self._assess_risk(bottleneck, timeline)

        # Success probability
        success_prob = self._estimate_success(bottleneck, timeline)

        return CareerStrategy(
            user_id=timeline.user_id,
            focus_skill=focus_skill,
            focus_reason=self._focus_reason(bottleneck, focus_skill),
            action_plan=actions,
            risk_if_no_adjustment=risk,
            risk_severity=severity,
            success_probability=round(success_prob, 2),
            expected_timeline_weeks=self._estimate_timeline(bottleneck),
            based_on_bottleneck=bottleneck.dominant_bottleneck,
            based_on_trend=bottleneck.trend,
        )

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _determine_focus_skill(
        bottleneck: BottleneckAnalysis,
        timeline: CareerTimeline,
    ) -> str:
        """Determine the primary skill to focus on."""
        gaps = bottleneck.skill_gap_areas
        if gaps:
            return gaps[0]

        # Fallback: top skill from trajectory
        if timeline.skill_trajectory:
            latest = timeline.skill_trajectory[-1]
            if latest.skills:
                top = max(latest.skills.items(), key=lambda x: x[1])
                return top[0]

        return "targeted skill development"

    def _build_action_plan(
        self,
        bottleneck: BottleneckAnalysis,
        focus_skill: str,
    ) -> list[ActionItem]:
        """Build a 7-14 day concrete action plan (max 5 items)."""
        templates = self._ACTION_TEMPLATES.get(
            bottleneck.dominant_bottleneck, self._DEFAULT_ACTIONS
        )

        actions: list[ActionItem] = []
        day_step = max(1, 14 // len(templates))  # spread across 14 days
        for i, tmpl in enumerate(templates[:5]):
            action_text = tmpl["action"].replace("{skill}", focus_skill)
            actions.append(
                ActionItem(
                    day=min(i * day_step + 1, 14),
                    action=action_text,
                    category=tmpl.get("category", "skill"),
                    expected_outcome=f"Progress toward resolving '{bottleneck.dominant_bottleneck}'",
                    hours_estimate=tmpl.get("hours", 2.0),
                )
            )
        return actions

    @staticmethod
    def _assess_risk(
        bottleneck: BottleneckAnalysis,
        timeline: CareerTimeline,
    ) -> tuple[str, str]:
        """Assess what happens if no strategy adjustment is made."""
        trend = bottleneck.trend

        risk_map = {
            "declining": (
                "Without intervention, declining trend continues: fewer interviews, "
                "longer search time, potential skill obsolescence. "
                f"Current app→interview rate: {bottleneck.application_to_interview_rate:.0%}, "
                f"interview→offer rate: {bottleneck.interview_to_offer_rate:.0%}.",
                "high",
            ),
            "stable": (
                "Without adjustment, plateau continues: maintaining current trajectory "
                "with no improvement. Missed opportunities for growth. "
                "Current metrics stable but below optimal.",
                "medium",
            ),
            "improving": (
                "Trajectory is positive but fragile. Without reinforcement, "
                "gains may not compound. Opportunity to accelerate improvement.",
                "low",
            ),
        }
        return risk_map.get(trend, risk_map["stable"])

    @staticmethod
    def _estimate_success(
        bottleneck: BottleneckAnalysis,
        timeline: CareerTimeline,
    ) -> float:
        """Estimate strategy success probability based on current metrics."""
        # Base probability from trend
        trend_base = {"improving": 0.65, "stable": 0.45, "declining": 0.25}
        base = trend_base.get(bottleneck.trend, 0.4)

        # Boost if systemic issue identified (actionable)
        if bottleneck.systemic_issue:
            base += 0.1

        # Boost if specific skill gaps found (targetable)
        if bottleneck.skill_gap_areas:
            base += 0.05

        # Penalize if very low interview→offer rate
        if bottleneck.interview_to_offer_rate < 0.1 and bottleneck.interview_to_offer_rate > 0:
            base -= 0.1

        return max(0.10, min(0.90, base))

    @staticmethod
    def _estimate_timeline(bottleneck: BottleneckAnalysis) -> int:
        """Estimate weeks to see meaningful improvement."""
        estimates = {
            "skill_gap": 8,
            "interview_skill": 4,
            "application_volume_low": 2,
            "experience_deficit": 12,
            "resume_quality": 2,
            "compensation_mismatch": 3,
        }
        return estimates.get(bottleneck.dominant_bottleneck, 6)

    @staticmethod
    def _focus_reason(bottleneck: BottleneckAnalysis, focus_skill: str) -> str:
        """Generate the reasoning for why this skill is the focus."""
        return (
            f"Analysis identifies '{bottleneck.dominant_bottleneck}' as the primary bottleneck "
            f"(confidence: {bottleneck.bottleneck_confidence:.0%}). "
            f"Trend is {bottleneck.trend}. "
            f"Focusing on {focus_skill} directly addresses the identified gap."
        )
