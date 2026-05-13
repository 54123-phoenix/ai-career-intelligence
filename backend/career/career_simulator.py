"""CareerSimulator — simulate career strategy execution outcomes (T007 Step 5).

Output: StrategySimulation with success_probability, main_failure_risk,
expected_outcome, adjustment_suggestion.

Must base predictions on strategy input. Must output probabilities.
"""

from __future__ import annotations

from backend.career.schemas import BottleneckAnalysis, CareerStrategy, StrategySimulation


class CareerSimulator:
    """Simulate the expected outcome of executing a career strategy.

    Usage:
        simulator = CareerSimulator()
        result = simulator.simulate(strategy, bottleneck)
    """

    def simulate(
        self,
        strategy: CareerStrategy,
        bottleneck: BottleneckAnalysis,
    ) -> StrategySimulation:
        """Simulate strategy execution and predict outcomes.

        Args:
            strategy: CareerStrategy from CareerArchitect
            bottleneck: BottleneckAnalysis from CareerReviewer

        Returns:
            StrategySimulation with probability, risk, outcome, and adjustments
        """
        # Base success probability from strategy
        base_prob = strategy.success_probability

        # Adjust based on action plan quality
        action_bonus = min(0.15, len(strategy.action_plan) * 0.03)
        adjusted_prob = min(0.90, base_prob + action_bonus)

        # Identify main failure risk
        failure_risk = self._identify_failure_risk(strategy, bottleneck)

        # Expected outcome
        expected_outcome = self._describe_outcome(strategy, adjusted_prob)

        # Adjustment suggestion
        needs_adjustment, adjustment = self._suggest_adjustment(
            strategy, bottleneck, adjusted_prob
        )

        return StrategySimulation(
            strategy_id=strategy.strategy_id,
            success_probability=round(adjusted_prob, 2),
            main_failure_risk=failure_risk,
            expected_outcome=expected_outcome,
            adjustment_needed=needs_adjustment,
            adjustment_suggestion=adjustment,
            simulation_confidence=self._compute_confidence(bottleneck),
        )

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _identify_failure_risk(
        strategy: CareerStrategy,
        bottleneck: BottleneckAnalysis,
    ) -> str:
        """Identify the most likely reason this strategy could fail."""
        # Insufficient action plan
        if len(strategy.action_plan) < 3:
            return "Action plan too sparse — insufficient concrete steps to drive change"

        # Skill gap too wide
        if bottleneck.dominant_bottleneck == "skill_gap" and bottleneck.bottleneck_confidence > 0.7:
            return (
                f"Skill gap in {strategy.focus_skill} is deeply entrenched. "
                "14-day plan may be insufficient without longer commitment."
            )

        # Declining trend resistance
        if bottleneck.trend == "declining":
            return (
                "Declining trend creates headwinds — initial applications may face "
                "higher rejection rate before improvement becomes visible."
            )

        # Interview skill — takes practice
        if bottleneck.dominant_bottleneck == "interview_skill":
            return "Interview skills require repeated practice — first mock interviews may show minimal improvement"

        # Low application volume
        if bottleneck.dominant_bottleneck == "application_volume_low":
            return "Response rate depends on market conditions — may need to increase volume further"

        # Systemic issues resist quick fixes
        if bottleneck.systemic_issue:
            return "Systemic issues require sustained effort — short-term plan may only partially address root cause"

        return "External market factors beyond individual control may delay results"

    @staticmethod
    def _describe_outcome(
        strategy: CareerStrategy,
        probability: float,
    ) -> str:
        """Describe the expected outcome of following the strategy."""
        if probability >= 0.7:
            return (
                f"High confidence ({probability:.0%}): Following this plan is likely to "
                f"improve {strategy.based_on_bottleneck} within {strategy.expected_timeline_weeks} weeks. "
                f"Focus on {strategy.focus_skill} with consistent execution."
            )
        elif probability >= 0.4:
            return (
                f"Moderate confidence ({probability:.0%}): Strategy addresses core issues but "
                f"results depend on execution quality and market conditions. "
                f"Expect gradual improvement over {strategy.expected_timeline_weeks} weeks."
            )
        else:
            return (
                f"Low confidence ({probability:.0%}): Current strategy may need reinforcement. "
                f"Consider extending timeline beyond {strategy.expected_timeline_weeks} weeks "
                f"and adding supplementary tactics."
            )

    @staticmethod
    def _suggest_adjustment(
        strategy: CareerStrategy,
        bottleneck: BottleneckAnalysis,
        probability: float,
    ) -> tuple[bool, str]:
        """Suggest strategy adjustments if needed."""
        if probability >= 0.65:
            return False, ""

        if len(strategy.action_plan) < 5:
            return True, (
                f"Add 1-2 more actions to strengthen the plan. "
                f"Current plan has {len(strategy.action_plan)} actions; 5 is recommended for "
                f"addressing '{bottleneck.dominant_bottleneck}'."
            )

        if bottleneck.trend == "declining" and probability < 0.5:
            return True, (
                f"Declining trend + low probability suggests the strategy needs a stronger "
                f"intervention. Consider: (1) extending timeline to {strategy.expected_timeline_weeks * 2} weeks, "
                f"(2) adding a mentorship component, or (3) targeting more junior positions temporarily."
            )

        if bottleneck.bottleneck_confidence < 0.5:
            return True, (
                "Bottleneck analysis has low confidence. Recommend collecting more "
                "career events before committing to this strategy."
            )

        return False, ""

    @staticmethod
    def _compute_confidence(bottleneck: BottleneckAnalysis) -> float:
        """Compute how confident the simulation is in its prediction."""
        # More data = higher confidence
        base = bottleneck.bottleneck_confidence

        # Systemic issues are more predictable
        if bottleneck.systemic_issue:
            base = min(0.95, base + 0.1)

        # Clear trend improves confidence
        if bottleneck.trend in ("improving", "declining"):
            base = min(0.95, base + 0.05)

        return round(base, 2)
