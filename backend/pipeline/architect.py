"""ArchitectAgent — runtime decision engine for pipeline execution mode selection.

Decision tree:
  1. Check system health → any core service degraded? → FALLBACK
  2. Check cache → warm cache with high-confidence results? → FAST
  3. Otherwise → FULL

The ArchitectAgent is a runtime component, distinct from the design-time
architect_agent.md prompt which defines system architecture and interfaces.
"""

from __future__ import annotations

from backend.pipeline.cache import RetrievalCache
from backend.pipeline.modes import ExecutionMode, ExecutionPlan


class ArchitectAgent:
    """Controls execution flow and selects execution mode.

    Analyzes system state, query characteristics, and cache status to produce
    an ExecutionPlan dictating which pipeline stages to run.

    Usage:
        architect = ArchitectAgent(cache=cache)
        plan = architect.determine_plan("Python 后端 北京", filters={"location": "北京"})
        # → ExecutionPlan(mode=FAST, steps=[...], reason="Cache hit", ...)
    """

    def __init__(self, cache: RetrievalCache | None = None):
        self._cache = cache

    def determine_plan(
        self,
        user_query: str,
        user_embedding: list[float] | None = None,
        filters: dict | None = None,
        force_mode: ExecutionMode | None = None,
    ) -> ExecutionPlan:
        """Build an execution plan based on current conditions.

        Args:
            user_query: Raw natural language query
            user_embedding: Optional pre-computed embedding vector
            filters: Optional dict of filters (location, salary, skills)
            force_mode: If provided, bypass decision logic and use this mode

        Returns:
            ExecutionPlan with mode, steps, and rationale
        """
        if force_mode is not None:
            return self._plan_for_mode(force_mode, reason=f"User-forced {force_mode.value} mode")

        # 1. Check system health
        health = self._check_system_health()
        degraded = not all(health.values())
        if degraded:
            failed = [k for k, v in health.items() if not v]
            return self._plan_for_mode(
                ExecutionMode.FALLBACK,
                reason=f"Degraded services: {', '.join(failed)}",
            )

        # 2. Check cache
        if self._cache is not None:
            cache_key = RetrievalCache.make_key(user_query, filters)
            if self._cache.is_valid(cache_key):
                cached = self._cache.get(cache_key)
                if cached and len(cached) >= 3:
                    # Warm cache with sufficient results → fast mode
                    return ExecutionPlan(
                        mode=ExecutionMode.FAST,
                        steps=["cache_lookup", "simulation_top3", "review", "feedback"],
                        reason="Warm retrieval cache with sufficient results",
                        cache_used=True,
                        simulation_needed=True,
                        retrieval_top_k=3,
                    )

        # 3. Default: full mode
        query_complexity = self._assess_query_complexity(user_query)
        return ExecutionPlan(
            mode=ExecutionMode.FULL,
            steps=["retrieval", "simulation", "review", "feedback"],
            reason=(
                f"Query complexity={query_complexity:.2f}, "
                f"cache={'miss' if self._cache else 'disabled'}"
            ),
            cache_used=False,
            simulation_needed=True,
            retrieval_top_k=20,
        )

    # ------------------------------------------------------------------
    # Internal checks
    # ------------------------------------------------------------------

    def _check_system_health(self) -> dict[str, bool]:
        """Check if core services are available.

        In MVP, checks are best-effort — only qdrant and embedder are checked.
        Returns: {"qdrant": bool, "embedder": bool, "simulation_engine": bool}
        """
        status: dict[str, bool] = {
            "qdrant": True,
            "embedder": True,
            "simulation_engine": True,
        }

        # Qdrant health check
        try:
            from backend.retrieval.qdrant_client import store
            # Lightweight: check the store is initialized
            _ = store
        except Exception:
            status["qdrant"] = False

        # Embedder health check (lazy-load would trigger on first use)
        try:
            from backend.retrieval.embedder import embedder
            _ = embedder.dim  # doesn't load model, just reads constant
        except Exception:
            status["embedder"] = False

        # Simulation engine — always available (pure computation, no external deps)
        status["simulation_engine"] = True

        return status

    @staticmethod
    def _assess_query_complexity(user_query: str) -> float:
        """Estimate query complexity on a [0, 1] scale.

        Simple (0.0-0.3): short query, common keywords
        Complex (0.7-1.0): long query, niche skills, multiple constraints

        Factors:
          - Length: < 8 chars → simple, > 50 chars → complex
          - Word count: < 3 words → simple, > 10 words → complex
          - Special tokens: contains numbers, parentheses, slashes → complex
        """
        if not user_query.strip():
            return 0.0

        text = user_query.strip()
        words = text.split()

        score = 0.0

        # Length factor
        if len(text) < 8:
            score += 0.1
        elif len(text) > 50:
            score += 0.4
        else:
            score += 0.25

        # Word count factor
        if len(words) < 3:
            score += 0.0
        elif len(words) > 10:
            score += 0.35
        else:
            score += 0.2

        # Special token factor (numbers, parens, slashes suggest constraints)
        special_count = sum(
            1 for c in text if c in "0123456789()/\\-"
        )
        if special_count >= 5:
            score += 0.25
        elif special_count >= 2:
            score += 0.15
        else:
            score += 0.05

        return round(min(score, 1.0), 2)

    @staticmethod
    def _should_simulate(match_count: int, query_complexity: float) -> bool:
        """Determine if simulation adds value given match count and query complexity.

        Skip simulation when:
          - 0 matches (nothing to simulate)
          - query_complexity < 0.2 (too simple to benefit from simulation)
        """
        if match_count == 0:
            return False
        if query_complexity < 0.2:
            return False
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _plan_for_mode(self, mode: ExecutionMode, reason: str) -> ExecutionPlan:
        """Build a standard ExecutionPlan for a given mode."""
        steps_map = {
            ExecutionMode.FAST: ["cache_lookup", "retrieval", "simulation_top3", "review", "feedback"],
            ExecutionMode.FULL: ["retrieval", "simulation", "review", "feedback"],
            ExecutionMode.FALLBACK: ["cache_lookup", "fallback_retrieval"],
            ExecutionMode.RANKING: ["retrieval", "feature_build", "rerank", "review", "pair_build"],
            ExecutionMode.SESSION: ["session_track", "behavior_aggregate", "preference_update", "retrieval", "feature_build", "rerank", "review", "feedback_queue", "feedback"],
            ExecutionMode.CAREER: ["career_parse", "career_retrieve", "career_review", "career_architect", "career_simulate", "career_frontend"],
        }
        return ExecutionPlan(
            mode=mode,
            steps=steps_map.get(mode, steps_map[ExecutionMode.FULL]),
            reason=reason,
            cache_used=(mode == ExecutionMode.FAST),
            simulation_needed=(mode not in (ExecutionMode.FALLBACK, ExecutionMode.RANKING, ExecutionMode.SESSION, ExecutionMode.CAREER)),
            retrieval_top_k=3 if mode == ExecutionMode.FAST else 20,
            rerank_needed=(mode in (ExecutionMode.RANKING, ExecutionMode.SESSION)),
            dynamic_preferences_needed=(mode == ExecutionMode.SESSION),
        )
