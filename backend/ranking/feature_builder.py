"""FeatureBuilderAgent — convert retrieval candidates + interaction history into numeric ranking features.

Produces 8-dim feature vectors for every candidate:
  0. skill_overlap_score    — Jaccard similarity between user skills and job required_skills
  1. embedding_similarity   — Retrieval cosine score from MatchResult
  2. salary_match_score     — Normalized salary alignment (user pref vs job range)
  3. company_quality_score  — Heuristic company tier score
  4. retrieval_rank         — 1 - (position / top_k), normalized position
  5. historical_ctr         — Click-through rate from interaction history
  6. dwell_time             — Normalized average dwell time from interaction history
  7. save_frequency         — Normalized save rate from interaction history

All features are in [0.0, 1.0], null-safe (default 0.0), with consistent key ordering.
"""

from __future__ import annotations

from collections import defaultdict

from backend.ranking.schemas import FeatureVector, UserBehaviorLog
from backend.shared.types import MatchResult


class FeatureBuilderAgent:
    """Convert retrieval candidates and interaction history into ranked feature vectors.

    Usage:
        builder = FeatureBuilderAgent()
        vectors = builder.build_features(
            trace_id="exec-abc123",
            user_profile={"skills": ["Python", "SQL"], "query": "后端 北京"},
            candidates=retrieved_candidates,
            interaction_history=behavior_logs,
        )
    """

    # Ordered feature keys — insertion order is the contract
    FEATURE_KEYS: tuple[str, ...] = (
        "skill_overlap_score",
        "embedding_similarity",
        "salary_match_score",
        "company_quality_score",
        "retrieval_rank",
        "historical_ctr",
        "dwell_time",
        "save_frequency",
    )

    # Heuristic company quality tiers (score mapped from 0.0–1.0)
    _COMPANY_TIERS: dict[str, float] = {
        "FAANG": 1.0,
        "BAT": 0.95,       # Baidu, Alibaba, Tencent
        "TMD": 0.85,       # Toutiao, Meituan, DiDi
        "unicorn": 0.80,
        "listed": 0.70,
        "series_d": 0.65,
        "series_c": 0.60,
        "series_b": 0.50,
        "series_a": 0.40,
        "startup": 0.30,
        "unknown": 0.50,
    }

    def __init__(self):
        self._ctr_cache: dict[str, float] = {}
        self._dwell_cache: dict[str, float] = {}
        self._save_cache: dict[str, float] = {}

    # ── Public API ────────────────────────────────────────────────────────

    def build_features(
        self,
        trace_id: str,
        user_profile: dict,
        candidates: list[MatchResult],
        interaction_history: list[UserBehaviorLog] | None = None,
    ) -> list[FeatureVector]:
        """Build a FeatureVector for every candidate.

        Args:
            trace_id: Pipeline execution ID (stamped on every vector)
            user_profile: {"skills": [...], "salary_pref": (min,max), "query": "..."}
            candidates: Retrieval output (list of MatchResult)
            interaction_history: User behavior logs (empty for cold start)

        Returns:
            list[FeatureVector] — one per candidate, same order as input
        """
        logs = interaction_history or []
        user_skills = {s.lower().strip() for s in user_profile.get("skills", [])}
        user_salary_pref = user_profile.get("salary_pref")
        total = len(candidates)

        # Precompute historical aggregates from behavior logs
        self._precompute_history(logs)

        vectors: list[FeatureVector] = []
        for i, candidate in enumerate(candidates):
            payload = candidate.payload
            job_skills = payload.get("required_skills", [])
            if isinstance(job_skills, str):
                job_skills = [job_skills]
            job_skills_set = {s.lower().strip() for s in job_skills}

            features = {
                "skill_overlap_score": self._compute_skill_overlap(user_skills, job_skills_set),
                "embedding_similarity": self._clamp(candidate.score),
                "salary_match_score": self._compute_salary_match(
                    user_salary_pref,
                    payload.get("salary_range"),
                ),
                "company_quality_score": self._compute_company_quality(
                    payload.get("company", "")
                ),
                "retrieval_rank": self._compute_retrieval_rank(i, total),
                "historical_ctr": self._compute_historical_ctr(candidate.item_id),
                "dwell_time": self._compute_dwell_time(candidate.item_id),
                "save_frequency": self._compute_save_frequency(candidate.item_id),
            }
            vectors.append(
                FeatureVector(
                    candidate_id=candidate.item_id,
                    trace_id=trace_id,
                    features=features,
                )
            )

        return vectors

    # ── Feature computations ──────────────────────────────────────────────

    @staticmethod
    def _compute_skill_overlap(user_skills: set[str], job_skills: set[str]) -> float:
        """Jaccard similarity: |A ∩ B| / |A ∪ B|. Null-safe."""
        if not job_skills:
            return 1.0  # no requirements → full match
        if not user_skills:
            return 0.0
        intersection = user_skills & job_skills
        union = user_skills | job_skills
        return round(len(intersection) / len(union), 4) if union else 0.0

    @staticmethod
    def _compute_salary_match(
        user_pref: tuple | None,
        job_range: list | None,
    ) -> float:
        """How well job salary aligns with user preference.

        If job_range midpoint falls in user_pref range → 1.0.
        Linear degradation outside the range.
        """
        if user_pref is None or job_range is None:
            return 0.5  # neutral when data missing
        if not isinstance(job_range, (list, tuple)) or len(job_range) != 2:
            return 0.5

        user_min, user_max = user_pref
        job_min, job_max = float(job_range[0]), float(job_range[1])
        job_mid = (job_min + job_max) / 2

        if user_min <= job_mid <= user_max:
            return 1.0
        # Linear decay: distance from nearest bound
        distance = min(abs(job_mid - user_min), abs(job_mid - user_max))
        # Normalize by user range width
        user_range = max(user_max - user_min, 1)
        penalty = min(distance / user_range, 1.0)
        return round(max(1.0 - penalty, 0.0), 4)

    @staticmethod
    def _compute_company_quality(company_name: str) -> float:
        """Heuristic company tier score. Unknown companies default to 0.5."""
        # Simple keyword match against known tiers
        name_lower = company_name.lower()
        for keyword, score in [
            ("alibaba", 0.95), ("tencent", 0.95), ("baidu", 0.95),
            ("bytedance", 0.95), ("meituan", 0.85), ("didi", 0.85),
            ("jd.com", 0.85), ("xiaomi", 0.80), ("huawei", 0.85),
            ("netease", 0.80), ("kuaishou", 0.80), ("pinduoduo", 0.80),
            ("ant group", 0.90), ("sensetime", 0.70), ("megvii", 0.70),
            ("horizon robotics", 0.70), ("ubtech", 0.60),
            ("google", 1.0), ("microsoft", 1.0), ("amazon", 0.95),
            ("apple", 1.0), ("meta", 1.0), ("netflix", 0.95),
        ]:
            if keyword in name_lower:
                return score
        return 0.50

    @staticmethod
    def _compute_retrieval_rank(position: int, total: int) -> float:
        """Normalized retrieval rank: 1 - (position / total). First = 1.0."""
        if total <= 1:
            return 1.0
        return round(1.0 - (position / total), 4)

    def _compute_historical_ctr(self, job_id: str) -> float:
        """Click-through rate from precomputed history. Cold-start → 0.0."""
        return self._ctr_cache.get(job_id, 0.0)

    def _compute_dwell_time(self, job_id: str) -> float:
        """Normalized average dwell time. Cold-start → 0.0."""
        return self._dwell_cache.get(job_id, 0.0)

    def _compute_save_frequency(self, job_id: str) -> float:
        """Normalized save rate. Cold-start → 0.0."""
        return self._save_cache.get(job_id, 0.0)

    # ── History precomputation ────────────────────────────────────────────

    def _precompute_history(self, logs: list[UserBehaviorLog]) -> None:
        """Aggregate user behavior logs into per-job caches.

        CTR = clicks / impressions per job.
        Dwell time = avg dwell_time_ms, normalized by max across all jobs.
        Save frequency = saves / impressions per job.
        """
        self._ctr_cache.clear()
        self._dwell_cache.clear()
        self._save_cache.clear()

        if not logs:
            return

        # Group by job_id
        by_job: dict[str, list[UserBehaviorLog]] = defaultdict(list)
        for log in logs:
            by_job[log.job_id].append(log)

        # Per-job aggregates
        raw_dwell: dict[str, float] = {}
        for job_id, job_logs in by_job.items():
            total_views = len(job_logs)
            clicks = sum(1 for l in job_logs if l.action == "clicked")
            saves = sum(1 for l in job_logs if l.action == "saved")
            dwells = [l.dwell_time_ms for l in job_logs if l.dwell_time_ms > 0]

            self._ctr_cache[job_id] = round(clicks / total_views, 4) if total_views else 0.0
            self._save_cache[job_id] = round(saves / total_views, 4) if total_views else 0.0
            raw_dwell[job_id] = sum(dwells) / len(dwells) if dwells else 0.0

        # Normalize dwell_time across all jobs
        max_dwell = max(raw_dwell.values()) if raw_dwell else 1
        if max_dwell > 0:
            for job_id, dwell in raw_dwell.items():
                self._dwell_cache[job_id] = round(min(dwell / max_dwell, 1.0), 4)

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
        """Clamp a float value to [lo, hi]."""
        return round(max(lo, min(hi, value)), 4)
