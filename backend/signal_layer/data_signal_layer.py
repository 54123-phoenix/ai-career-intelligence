"""DataSignalLayer — thin wrapper enforcing trace_id across all pipeline outputs.

Does NOT modify agent business logic. Only:
  1. Runs the pipeline (delegates to PipelineOrchestrator)
  2. Collects all outputs into InteractionTrace
  3. Stamps trace_id on every TrainingSample
  4. Stores the trace for later retrieval

This is the single entry point for T006. Every request through this layer
produces a fully traceable InteractionTrace.
"""

from __future__ import annotations

from backend.pipeline.modes import ExecutionMode
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.signal_layer.schemas import InteractionTrace
from backend.signal_layer.trace_store import TraceStore


class DataSignalLayer:
    """Thin wrapper around PipelineOrchestrator that enforces trace structure.

    Usage:
        layer = DataSignalLayer()
        trace = await layer.execute("Python 后端 北京", filters={"location": "北京"})
        print(f"trace_id={trace.trace_id}, samples={len(trace.training_samples)}")

        # Later retrieval
        same = layer.get_trace(trace.trace_id)
    """

    def __init__(
        self,
        orchestrator: PipelineOrchestrator | None = None,
        trace_store: TraceStore | None = None,
    ):
        self._orchestrator = orchestrator or PipelineOrchestrator()
        self._store = trace_store or TraceStore()

    # ── Public API ────────────────────────────────────────────────────────

    async def execute(
        self,
        user_query: str,
        user_embedding: list[float] | None = None,
        filters: dict | None = None,
        force_mode: ExecutionMode | None = None,
    ) -> InteractionTrace:
        """Run the full pipeline and produce a unified InteractionTrace.

        This is the single entry point for T006. It:
          1. Delegates to PipelineOrchestrator.run()
          2. Collects all stage outputs from PipelineContext
          3. Stamps trace_id on every TrainingSample
          4. Stores the trace in TraceStore
          5. Returns the complete InteractionTrace

        Args:
            user_query: Natural language job search query
            user_embedding: Optional pre-computed embedding vector
            filters: Optional dict of filters (e.g., {"location": "北京"})
            force_mode: Bypass architect decision and use this mode

        Returns:
            InteractionTrace with all stage outputs linked by trace_id
        """
        # Step 1: Run pipeline (delegates entirely to existing orchestrator)
        ctx = await self._orchestrator.run(
            user_query=user_query,
            user_embedding=user_embedding,
            filters=filters,
            force_mode=force_mode,
        )

        # Step 2: Build trace from pipeline context
        trace = self._build_trace(ctx)

        # Step 3: Store for later retrieval
        self._store.put(trace)

        return trace

    def get_trace(self, trace_id: str) -> InteractionTrace | None:
        """Retrieve a previously stored trace by ID."""
        return self._store.get(trace_id)

    def list_traces(self, limit: int = 50) -> list[InteractionTrace]:
        """List recent traces, newest first."""
        return self._store.list(limit=limit)

    @property
    def orchestrator(self) -> PipelineOrchestrator:
        """Access the underlying orchestrator (for health checks, etc.)."""
        return self._orchestrator

    # ── Internal ──────────────────────────────────────────────────────────

    def _build_trace(self, ctx) -> InteractionTrace:
        """Collect all PipelineContext outputs into a single InteractionTrace.

        trace_id = ctx.execution_id — single source of truth.
        """
        trace_id = ctx.execution_id

        # Stamp trace_id on every training sample
        stamped_samples = self._stamp_trace_id(ctx.training_samples, trace_id)

        return InteractionTrace(
            trace_id=trace_id,
            mode=ctx.mode,
            user_query=ctx.user_query,
            filters=ctx.filters,
            retrieved_candidates=ctx.retrieved_candidates,
            simulation_results=ctx.simulation_results,
            reviewer_aggregate=ctx.reviewer_aggregate,
            training_samples=stamped_samples,
            # Ranking outputs (populated in RANKING mode)
            feature_vectors=getattr(ctx, 'feature_vectors', []),
            reranked_candidates=getattr(ctx, 'reranked_candidates', []),
            ranking_pairs=getattr(ctx, 'ranking_pairs', []),
            model_used=getattr(ctx, 'model_used', None),
            interaction_history=getattr(ctx, 'interaction_history', None),
            # Session outputs (populated in SESSION mode)
            session_id=getattr(ctx, 'session_id', None),
            session_actions=getattr(ctx, 'session_actions', []),
            session_summary=getattr(ctx, 'session_summary', None),
            dynamic_preferences=getattr(ctx, 'dynamic_preferences', None),
            queued_events=getattr(ctx, 'queued_events', []),
            drift_score=getattr(ctx, 'drift_score', 0.0),
            session_review=getattr(ctx, 'session_review', None),
            # Career outputs (populated in CAREER mode — T007)
            career_events=getattr(ctx, 'career_events', []),
            career_timeline=getattr(ctx, 'career_timeline', None),
            bottleneck_analysis=getattr(ctx, 'bottleneck_analysis', None),
            career_strategy=getattr(ctx, 'career_strategy', None),
            strategy_simulation=getattr(ctx, 'strategy_simulation', None),
            career_visualization=getattr(ctx, 'career_visualization', None),
            plan_steps=ctx.plan.steps if ctx.plan else [],
            errors=ctx.errors,
            started_at=ctx.started_at,
            elapsed_ms=ctx.elapsed_ms,
        )

    @staticmethod
    def _stamp_trace_id(
        samples: list, trace_id: str
    ) -> list:
        """Set trace_id on every TrainingSample in the list.

        Returns new TrainingSample objects with trace_id filled.
        Original objects are not mutated (copy-on-write).
        """
        stamped: list = []
        for s in samples:
            stamped.append(
                s.model_copy(update={"trace_id": trace_id})
            )
        return stamped
