"""CareerReviewer — analyze career development patterns (T007 Step 3).

Output: BottleneckAnalysis with dominant_bottleneck, secondary_bottlenecks,
trend, systemic_issue, quantified metrics.

All analysis MUST be based on historical data. No generic advice.
"""

from __future__ import annotations

from collections import Counter

from backend.career.schemas import BottleneckAnalysis, CareerTimeline


class CareerReviewer:
    """Analyze career patterns from historical timeline data.

    Identifies bottlenecks, trends, and systemic issues from event history.
    All conclusions are data-driven — no generic recommendations.

    Usage:
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
    """

    def analyze(self, timeline: CareerTimeline) -> BottleneckAnalysis:
        """Analyze career patterns from a user's timeline.

        Args:
            timeline: CareerTimeline from CareerRetriever.retrieve()

        Returns:
            BottleneckAnalysis with quantified findings
        """
        events = timeline.recent_events
        all_events = (
            timeline.recent_events
            + list(timeline.interview_successes)
            + list(timeline.interview_failures)
        )

        # 1. Identify dominant bottleneck
        dominant, dom_conf, secondary = self._identify_bottlenecks(timeline)

        # 2. Assess trend
        trend, trend_detail = self._assess_trend(timeline)

        # 3. Check if systemic
        systemic, systemic_reason = self._check_systemic(timeline)

        # 4. Quantified metrics
        app_count = timeline.application_distribution.get("application_sent", 0)
        interview_count = len(timeline.interview_successes) + len(timeline.interview_failures)
        offer_count = timeline.application_distribution.get("offer_received", 0)

        app_to_interview = (interview_count / app_count) if app_count > 0 else 0.0
        interview_to_offer = (offer_count / interview_count) if interview_count > 0 else 0.0

        # Skill gap areas
        skill_gaps = self._detect_skill_gaps(timeline)

        return BottleneckAnalysis(
            user_id=timeline.user_id,
            dominant_bottleneck=dominant,
            bottleneck_confidence=round(dom_conf, 2),
            secondary_bottlenecks=secondary[:3],
            trend=trend,
            trend_detail=trend_detail,
            systemic_issue=systemic,
            systemic_reason=systemic_reason,
            application_to_interview_rate=round(app_to_interview, 2),
            interview_to_offer_rate=round(interview_to_offer, 2),
            skill_gap_areas=skill_gaps,
            recommended_focus=self._derive_recommended_focus(dominant, secondary, skill_gaps),
        )

    # ── Internal: bottleneck identification ──────────────────────────────

    @staticmethod
    def _identify_bottlenecks(timeline: CareerTimeline) -> tuple[str, float, list[str]]:
        """Identify the dominant bottleneck from timeline data."""
        scores: dict[str, float] = {}

        failures = timeline.interview_failures
        successes = timeline.interview_successes
        total_interviews = len(failures) + len(successes)

        # Skill gap: low app→interview rate + few skills in trajectory
        app_count = timeline.application_distribution.get("application_sent", 0)
        interview_count = total_interviews
        if app_count >= 5 and (interview_count / app_count) < 0.15:
            scores["skill_gap"] = min(0.9, (1.0 - (interview_count / app_count)) * 2)

        # Interview skill: high interview count but low offer rate
        offer_count = timeline.application_distribution.get("offer_received", 0)
        if total_interviews >= 3 and (offer_count / total_interviews) < 0.3:
            scores["interview_skill"] = min(0.85, (1.0 - (offer_count / max(total_interviews, 1))) * 1.5)

        # Application volume: very few applications
        if app_count < 5 and timeline.total_events > 0:
            scores["application_volume_low"] = 0.7

        # Experience deficit: many rejections at interview stage
        if len(failures) >= 3 and len(successes) == 0:
            if not scores.get("interview_skill"):
                scores["experience_deficit"] = 0.65

        # Resume quality: many applications, zero interviews
        if app_count >= 10 and interview_count == 0:
            scores["resume_quality"] = 0.8

        # Compensation mismatch: offers received but declined
        declined = timeline.application_distribution.get("offer_declined", 0)
        if declined >= 2:
            scores["compensation_mismatch"] = 0.7

        if not scores:
            return "insufficient_data", 0.3, []

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        dominant, dom_conf = ranked[0]
        secondary = [name for name, _ in ranked[1:4]]
        return dominant, dom_conf, secondary

    # ── Internal: trend assessment ────────────────────────────────────────

    @staticmethod
    def _assess_trend(timeline: CareerTimeline) -> tuple[str, str]:
        """Assess whether career trajectory is improving, stable, or declining."""
        events = timeline.recent_events
        if len(events) < 3:
            return "stable", "Insufficient data for trend assessment"

        # recent_events is newest-first; reverse to chronological order
        events = list(reversed(events))

        # Compare first half (older) vs second half (newer) outcomes
        mid = len(events) // 2
        first_half = events[:mid]
        second_half = events[mid:]

        def success_rate(evts):
            total = len(evts)
            if total == 0:
                return 0.0
            successes = sum(1 for e in evts if e.outcome == "success")
            return successes / total

        def failure_rate(evts):
            total = len(evts)
            if total == 0:
                return 0.0
            failures = sum(1 for e in evts if e.outcome == "failure")
            return failures / total

        first_sr = success_rate(first_half)
        second_sr = success_rate(second_half)
        first_fr = failure_rate(first_half)
        second_fr = failure_rate(second_half)

        if second_sr > first_sr + 0.1 and second_fr < first_fr:
            return "improving", f"Success rate improved from {first_sr:.0%} to {second_sr:.0%}"
        elif second_fr > first_fr + 0.15 or second_sr < first_sr - 0.1:
            return "declining", f"Failure rate increased from {first_fr:.0%} to {second_fr:.0%}"
        return "stable", f"Success rate consistent at ~{second_sr:.0%}"

    # ── Internal: systemic check ──────────────────────────────────────────

    @staticmethod
    def _check_systemic(timeline: CareerTimeline) -> tuple[bool, str]:
        """Check if issues are systemic (persistent pattern) vs isolated incidents."""
        failures = timeline.interview_failures
        if len(failures) >= 3:
            # Check if failures cluster at the same stage
            failure_types = Counter(
                f.event_type for f in failures
            )
            # If 60%+ of failures are same type, it's systemic
            total = len(failures)
            if total > 0:
                most_common_type, count = failure_types.most_common(1)[0]
                if count / total >= 0.6:
                    return True, f"Systemic issue: {count}/{total} failures at '{most_common_type}' stage"
                return False, "Failures distributed across multiple stages — likely isolated incidents"

        if len(failures) == 0 and len(timeline.interview_successes) > 0:
            return False, "No persistent failure pattern detected"

        return False, "Insufficient failure data for systemic assessment"

    # ── Internal: skill gaps ──────────────────────────────────────────────

    @staticmethod
    def _detect_skill_gaps(timeline: CareerTimeline) -> list[str]:
        """Detect skill gaps by analyzing rejection patterns."""
        gaps: list[str] = []

        # Skills from failed interviews minus skills from successes
        fail_skills: Counter = Counter()
        for e in timeline.interview_failures:
            for s in e.skills_involved:
                fail_skills[s.lower().strip()] += 1

        success_skills: set[str] = set()
        for e in timeline.interview_successes:
            for s in e.skills_involved:
                success_skills.add(s.lower().strip())

        # Skills that appear in failures but not successes are gaps
        for skill, count in fail_skills.most_common(5):
            if skill not in success_skills:
                gaps.append(skill)

        return gaps[:3]

    # ── Internal: recommended focus ───────────────────────────────────────

    @staticmethod
    def _derive_recommended_focus(
        dominant: str,
        secondary: list[str],
        skill_gaps: list[str],
    ) -> list[str]:
        """Derive recommended focus areas from bottleneck analysis."""
        focus: list[str] = []

        bottleneck_to_focus = {
            "skill_gap": "Targeted skill acquisition in identified gap areas",
            "interview_skill": "Interview practice and mock interviews",
            "application_volume_low": "Increase application volume and broaden search",
            "experience_deficit": "Bridge projects or internships to build relevant experience",
            "resume_quality": "Resume overhaul with quantifiable achievements",
            "compensation_mismatch": "Market research and compensation negotiation preparation",
        }

        if dominant in bottleneck_to_focus:
            focus.append(bottleneck_to_focus[dominant])

        if skill_gaps:
            focus.append(f"Close skill gap: {', '.join(skill_gaps[:2])}")

        return focus[:3]
