"""PreferenceUpdater — update dynamic user preferences from session behavior.

Formula: new_pref = 0.7 * recent_session_behavior + 0.3 * historical_profile

Skills are blended via frequency-weighted EMA. Locations/companies/levels use EMA.
Shift score is computed as cosine distance between old and new skill weight vectors.
Cold start: 100% session → gracefully shifts toward 70/30 as history accumulates.
"""

from __future__ import annotations

import math
from collections import Counter

from backend.session.schemas import DynamicPreferences, SessionSummary


class PreferenceUpdater:
    """Update dynamic user preferences based on recent session behavior.

    Usage:
        updater = PreferenceUpdater(recent_weight=0.7)
        new_prefs = updater.update(current_prefs, session_summary)
    """

    def __init__(self, recent_weight: float = 0.7):
        self._w_recent = max(0.0, min(1.0, recent_weight))
        self._w_historical = 1.0 - self._w_recent

    # ── Public API ────────────────────────────────────────────────────────

    def update(
        self,
        historical: DynamicPreferences | None,
        summary: SessionSummary,
    ) -> DynamicPreferences:
        """Compute updated preferences from historical profile + session summary.

        Args:
            historical: Existing preferences, or None for cold start
            summary: Current session behavioral summary

        Returns:
            DynamicPreferences with blended values and shift score
        """
        if historical is None:
            historical = self.create_default(summary.user_id)

        # Use effective weight based on session count (cold start → more weight to recent)
        effective_w = self._effective_weight(historical.session_count)

        # Blend skill weights
        session_skills = self._skills_from_summary(summary)
        new_skill_weights = self._blend_skills(
            historical.skill_weights, session_skills, effective_w
        )

        # Blend locations (EMA on frequency counts)
        session_locations = self._locations_from_summary(summary)
        new_locations = self._blend_list(
            historical.preferred_locations, session_locations, effective_w, max_items=10
        )

        # Blend companies
        session_companies = self._companies_from_summary(summary)
        new_companies = self._blend_list(
            historical.preferred_companies, session_companies, effective_w, max_items=10
        )

        # Blend levels
        session_levels = self._levels_from_summary(summary)
        new_levels = self._blend_list(
            historical.preferred_levels, session_levels, effective_w, max_items=5
        )

        # Blend categories
        session_cats = summary.clicked_categories
        new_categories = self._blend_list(
            historical.preferred_categories, session_cats, effective_w, max_items=20
        )

        # Compute shift score
        shift_score = self._compute_shift_score(historical.skill_weights, new_skill_weights)

        return DynamicPreferences(
            user_id=summary.user_id,
            skill_weights=new_skill_weights,
            preferred_locations=new_locations,
            preferred_companies=new_companies,
            preferred_levels=new_levels,
            salary_preference=historical.salary_preference,  # preserved from history
            preferred_categories=new_categories,
            preference_shift_score=round(shift_score, 4),
            session_count=historical.session_count + 1,
        )

    def create_default(self, user_id: str) -> DynamicPreferences:
        """Create a default (cold-start) preference profile."""
        return DynamicPreferences(
            user_id=user_id,
            skill_weights={},
            preferred_locations=[],
            preferred_companies=[],
            preferred_levels=[],
            preferred_categories=[],
            salary_preference=None,
            preference_shift_score=0.0,
            session_count=0,
        )

    # ── Internal: blending ────────────────────────────────────────────────

    def _effective_weight(self, session_count: int) -> float:
        """Compute effective recent weight accounting for cold start.

        With 0 prior sessions: 100% recent.
        After 3+ sessions: full EMA (70% recent).
        """
        if session_count == 0:
            return 1.0
        if session_count == 1:
            return 0.85
        if session_count == 2:
            return 0.78
        return self._w_recent

    def _blend_skills(
        self,
        historical: dict[str, float],
        session_skills: dict[str, float],
        effective_w: float,
    ) -> dict[str, float]:
        """Blend skill weight vectors using EMA.

        new_skill = effective_w * session_freq + (1-effective_w) * historical_weight
        """
        # Normalize session skills to [0,1]
        max_freq = max(session_skills.values()) if session_skills else 1
        session_norm = {k: v / max_freq for k, v in session_skills.items()} if max_freq > 0 else {}

        result: dict[str, float] = {}
        all_keys = set(historical.keys()) | set(session_norm.keys())
        for key in all_keys:
            hist_val = historical.get(key, 0.0)
            sess_val = session_norm.get(key, 0.0)
            blended = effective_w * sess_val + (1.0 - effective_w) * hist_val
            # Clamp and only retain if above threshold
            if blended > 0.01:
                result[key] = round(blended, 4)

        return result

    def _blend_list(
        self,
        historical: list[str],
        session_items: list[str],
        effective_w: float,
        max_items: int = 10,
    ) -> list[str]:
        """Blend ordered lists using position-weighted EMA.

        Session items get effective_w boost by appearing at the front.
        Historical items are preserved with (1-effective_w) decay.
        """
        # Score: session items at front get high weight, historical items get lower
        scored: dict[str, float] = {}

        # Session items: weight = effective_w * (1 - pos/len)
        n_sess = max(len(session_items), 1)
        for i, item in enumerate(session_items):
            pos_weight = 1.0 - (i / n_sess)
            scored[item] = scored.get(item, 0.0) + effective_w * pos_weight

        # Historical items: weight = (1-effective_w) * (1 - pos/len)
        n_hist = max(len(historical), 1)
        for i, item in enumerate(historical):
            pos_weight = 1.0 - (i / n_hist)
            scored[item] = scored.get(item, 0.0) + (1.0 - effective_w) * pos_weight

        # Sort by score descending, return top items
        sorted_items = sorted(scored.items(), key=lambda x: -x[1])
        return [item for item, _ in sorted_items[:max_items]]

    # ── Internal: feature extraction ──────────────────────────────────────

    @staticmethod
    def _skills_from_summary(summary: SessionSummary) -> dict[str, float]:
        """Extract skill frequencies from summary categories."""
        counter: Counter = Counter()
        for cat in summary.clicked_categories:
            counter[cat] += 1
        # Add top skills from clicked_jobs as direct signals
        for skill in summary.top_clicked_skills:
            counter[skill] += 2  # higher weight for explicit skills
        total = max(counter.total(), 1)
        return {k: v / total for k, v in counter.items()}

    @staticmethod
    def _locations_from_summary(summary: SessionSummary) -> list[str]:
        """Extract location preferences from summary categories."""
        # Location-like categories (Chinese city names, province names)
        location_keywords = {
            "北京", "上海", "深圳", "广州", "杭州", "成都", "南京", "武汉",
            "beijing", "shanghai", "shenzhen", "guangzhou", "hangzhou",
        }
        locs = [c for c in summary.clicked_categories if c.lower() in location_keywords]
        return list(dict.fromkeys(locs))  # dedup preserving order

    @staticmethod
    def _companies_from_summary(summary: SessionSummary) -> list[str]:
        """Extract company preferences from top_clicked_companies."""
        return list(summary.top_clicked_companies)

    @staticmethod
    def _levels_from_summary(summary: SessionSummary) -> list[str]:
        """Extract level preferences from summary categories."""
        level_keywords = {
            "junior", "mid-level", "senior", "lead", "manager", "director",
            "vp", "cto", "初级", "中级", "高级", "资深", "专家",
        }
        levels = [c for c in summary.clicked_categories if c.lower() in level_keywords]
        return list(dict.fromkeys(levels))

    # ── Internal: metrics ─────────────────────────────────────────────────

    @staticmethod
    def _compute_shift_score(
        old_weights: dict[str, float],
        new_weights: dict[str, float],
    ) -> float:
        """Compute cosine distance between old and new skill weight vectors.

        Returns value in [0, 1] where 0 = no shift, 1 = complete shift.
        """
        if not old_weights and not new_weights:
            return 0.0
        if not old_weights or not new_weights:
            return 1.0

        all_keys = set(old_weights.keys()) | set(new_weights.keys())
        old_vec = [old_weights.get(k, 0.0) for k in all_keys]
        new_vec = [new_weights.get(k, 0.0) for k in all_keys]

        dot = sum(a * b for a, b in zip(old_vec, new_vec))
        norm_old = math.sqrt(sum(a * a for a in old_vec))
        norm_new = math.sqrt(sum(b * b for b in new_vec))

        if norm_old == 0 or norm_new == 0:
            return 1.0 if (norm_old > 0) != (norm_new > 0) else 0.0

        cosine_sim = dot / (norm_old * norm_new)
        # Clamp and convert to distance
        cosine_sim = max(-1.0, min(1.0, cosine_sim))
        return round((1.0 - cosine_sim) / 2.0, 4)
