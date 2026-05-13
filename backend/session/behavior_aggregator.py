"""BehaviorAggregator — aggregate raw session actions into structured behavioral summaries.

Pure computation: reads Session.ordered_actions, outputs SessionSummary.
Does NOT infer unsupported preferences. Only real action data.
"""

from __future__ import annotations

from collections import Counter

from backend.session.schemas import Session, SessionAction, SessionSummary


class BehaviorAggregator:
    """Aggregate session actions into behavioral summaries.

    Usage:
        aggregator = BehaviorAggregator()
        summary = aggregator.aggregate(session)
    """

    # Engagement score weights
    W_CTR = 0.40
    W_SAVE = 0.20
    W_APPLY = 0.30
    W_DWELL = 0.10

    def aggregate(self, session: Session, trace_id: str = "") -> SessionSummary:
        """Compute SessionSummary from a session's ordered actions.

        Args:
            session: Session with ordered_actions populated
            trace_id: Pipeline execution ID for traceability

        Returns:
            SessionSummary with all computed statistics
        """
        actions = session.ordered_actions
        if not actions:
            return SessionSummary(
                session_id=session.session_id,
                user_id=session.user_id,
                trace_id=trace_id,
            )

        # Categorize actions
        clicked = [a for a in actions if a.action_type == "click"]
        skipped = [a for a in actions if a.action_type == "skip"]
        saved = [a for a in actions if a.action_type == "save"]
        applied = [a for a in actions if a.action_type == "apply"]
        dwell_actions = [a for a in actions if a.action_type == "dwell"]

        total = len(actions)
        click_count = len(clicked)
        save_count = len(saved)
        apply_count = len(applied)

        # Categories from job payloads
        clicked_categories = self._extract_categories(clicked)
        skipped_categories = self._extract_categories(skipped)

        # Rates
        ctr = click_count / total if total > 0 else 0.0
        save_rate = save_count / total if total > 0 else 0.0
        apply_rate = apply_count / total if total > 0 else 0.0

        # Dwell time
        all_dwells = [a.dwell_time_ms for a in actions if a.dwell_time_ms > 0]
        avg_dwell = sum(all_dwells) / len(all_dwells) if all_dwells else 0.0

        # Top skills / companies from clicked jobs
        top_skills = self._top_values(clicked, "skills")
        top_companies = self._top_values(clicked, "company")

        # Engagement score
        dwell_norm = min(avg_dwell / 30_000.0, 1.0)  # normalize to [0,1] with 30s max
        engagement = round(
            self.W_CTR * ctr
            + self.W_SAVE * save_rate
            + self.W_APPLY * apply_rate
            + self.W_DWELL * dwell_norm,
            4,
        )

        return SessionSummary(
            session_id=session.session_id,
            user_id=session.user_id,
            trace_id=trace_id,
            clicked_categories=clicked_categories,
            skipped_categories=skipped_categories,
            clicked_job_ids=[a.job_id for a in clicked if a.job_id],
            saved_job_ids=[a.job_id for a in saved if a.job_id],
            applied_job_ids=[a.job_id for a in applied if a.job_id],
            skipped_job_ids=[a.job_id for a in skipped if a.job_id],
            average_dwell_time_ms=round(avg_dwell, 2),
            save_rate=round(save_rate, 4),
            apply_rate=round(apply_rate, 4),
            click_through_rate=round(ctr, 4),
            engagement_score=engagement,
            total_actions=total,
            top_clicked_skills=top_skills[:5],
            top_clicked_companies=top_companies[:5],
        )

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_categories(actions: list[SessionAction]) -> list[str]:
        """Extract category keywords from job payloads (skills + levels)."""
        cats: set[str] = set()
        for a in actions:
            payload = a.job_payload or {}
            skills = payload.get("required_skills", [])
            if isinstance(skills, str):
                skills = [skills]
            level = payload.get("level", "")
            location = payload.get("location", "")
            for s in skills:
                cats.add(str(s).lower().strip())
            if level:
                cats.add(str(level).lower().strip())
            if location:
                cats.add(str(location).lower().strip())
        return sorted(cats)

    @staticmethod
    def _top_values(actions: list[SessionAction], key: str) -> list[str]:
        """Extract top values from job payloads (e.g., 'skills', 'company')."""
        counter: Counter = Counter()
        for a in actions:
            payload = a.job_payload or {}
            if key == "skills":
                vals = payload.get("required_skills", [])
                if isinstance(vals, str):
                    vals = [vals]
            elif key == "company":
                vals = [payload.get("company", "")]
            else:
                vals = [payload.get(key, "")]
            for v in vals:
                if v:
                    counter[str(v).strip()] += 1
        return [item for item, _ in counter.most_common(10)]
