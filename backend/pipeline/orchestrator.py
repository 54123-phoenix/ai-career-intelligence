"""PipelineOrchestrator — the central multi-agent pipeline.

Wires all 6 agents into the closed-loop pipeline:
  Retrieval → Simulation → Review → Feedback → Learning

This is the single entry point for the T005 multi-agent system.
All agents communicate through PipelineContext — no hidden state.
"""

from __future__ import annotations

import time

from backend.data_ingestion.agent import DataIngestionAgent
from backend.data_ingestion.sources.mock_source import MockJobSource
from backend.feedback.feedback_agent import FeedbackAgent
from backend.feedback.reviewer import ReviewerAgent
from backend.pipeline.architect import ArchitectAgent
from backend.pipeline.cache import RetrievalCache
from backend.pipeline.config import PipelineConfig, config as default_config
from backend.pipeline.modes import ExecutionMode, ExecutionPlan, PipelineContext
from backend.ranking.feature_builder import FeatureBuilderAgent
from backend.ranking.model_store import ModelStore
from backend.ranking.pair_builder import PairBuilderAgent
from backend.ranking.reranker import RerankEngineAgent
from backend.ranking.schemas import UserBehaviorLog
from backend.retrieval.embedder import embedder
from backend.session.behavior_aggregator import BehaviorAggregator
from backend.session.feedback_queue import FeedbackQueueAgent
from backend.session.preference_updater import PreferenceUpdater
from backend.session.schemas import (
    DynamicPreferences,
    SessionAction,
    SessionReview,
    SessionSummary,
)
from backend.session.session_tracker import SessionTracker
from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer
from backend.career.career_architect import CareerArchitect
from backend.career.career_simulator import CareerSimulator
from backend.career.career_frontend import CareerFrontend
from backend.career.schemas import (
    BottleneckAnalysis,
    CareerEvent,
    CareerStrategy,
    CareerTimeline,
    CareerVisualization,
    StrategySimulation,
)
from backend.shared.types import MatchResult, StructuredJob, StructuredResume
from backend.simulation.engine import SimulationEngine
from backend.simulation.state import SimulationResult


class PipelineOrchestrator:
    """Wire all agents into the full closed-loop pipeline.

    Retrieval → Simulation → Review → Feedback → Learning

    Dependencies are injected; sensible defaults provided for all.

    Usage:
        orchestrator = PipelineOrchestrator()
        ctx = await orchestrator.run("Python 后端 北京", filters={"location": "北京"})
        print(f"Found {len(ctx.retrieved_candidates)} candidates")
        print(f"Generated {len(ctx.training_samples)} training samples")
    """

    def __init__(
        self,
        retriever=None,
        simulation_engine: SimulationEngine | None = None,
        data_ingestion: DataIngestionAgent | None = None,
        reviewer: ReviewerAgent | None = None,
        feedback_agent: FeedbackAgent | None = None,
        architect: ArchitectAgent | None = None,
        cache: RetrievalCache | None = None,
        config: PipelineConfig | None = None,
        feature_builder: FeatureBuilderAgent | None = None,
        reranker: RerankEngineAgent | None = None,
        pair_builder: PairBuilderAgent | None = None,
        model_store: ModelStore | None = None,
        session_tracker: SessionTracker | None = None,
        behavior_aggregator: BehaviorAggregator | None = None,
        preference_updater: PreferenceUpdater | None = None,
        feedback_queue: FeedbackQueueAgent | None = None,
        career_parser: CareerParser | None = None,
        career_retriever: CareerRetriever | None = None,
        career_reviewer: CareerReviewer | None = None,
        career_architect: CareerArchitect | None = None,
        career_simulator: CareerSimulator | None = None,
        career_frontend: CareerFrontend | None = None,
    ):
        # Lazy import to avoid circular deps
        from backend.retrieval.retriever import Retriever

        self._config = config or default_config
        self._retriever = retriever or Retriever()
        self._simulation = simulation_engine or SimulationEngine()
        self._data_ingestion = data_ingestion or DataIngestionAgent()
        self._reviewer = reviewer or ReviewerAgent()
        self._feedback = feedback_agent or FeedbackAgent()
        self._cache = cache or RetrievalCache(ttl_seconds=self._config.cache_ttl_seconds)
        self._architect = architect or ArchitectAgent(cache=self._cache)

        # Ranking agents (T006 LTR)
        self._model_store = model_store or ModelStore(storage_dir=self._config.ranking_model_dir)
        self._feature_builder = feature_builder or FeatureBuilderAgent()
        self._reranker = reranker or RerankEngineAgent(model_store=self._model_store)
        self._pair_builder = pair_builder or PairBuilderAgent()

        # Session agents (T006 L3 — Session Feedback Loop)
        self._session_tracker = session_tracker or SessionTracker(
            timeout_minutes=self._config.session_timeout_minutes
        )
        self._behavior_aggregator = behavior_aggregator or BehaviorAggregator()
        self._preference_updater = preference_updater or PreferenceUpdater(
            recent_weight=self._config.session_preference_recent_weight
        )
        self._feedback_queue = feedback_queue or FeedbackQueueAgent(
            max_events=self._config.session_feedback_queue_max
        )
        self._preference_store: dict[str, DynamicPreferences] = {}

        # Career agents (T007 — Career Memory & Evolution Engine)
        self._career_parser = career_parser or CareerParser()
        self._career_retriever = career_retriever or CareerRetriever()
        self._career_reviewer = career_reviewer or CareerReviewer()
        self._career_architect = career_architect or CareerArchitect()
        self._career_simulator = career_simulator or CareerSimulator()
        self._career_frontend = career_frontend or CareerFrontend()

        # Ensure mock source is registered for dev
        if not self._data_ingestion.source_names():
            self._data_ingestion.register_adapter(MockJobSource())

    # ── Public API ────────────────────────────────────────────────────────

    async def run(
        self,
        user_query: str,
        user_embedding: list[float] | None = None,
        filters: dict | None = None,
        force_mode: ExecutionMode | None = None,
    ) -> PipelineContext:
        """Execute the full pipeline. Returns PipelineContext with all results.

        Args:
            user_query: Natural language job search query
            user_embedding: Optional pre-computed embedding vector
            filters: Optional dict of filters (e.g., {"location": "北京"})
            force_mode: Bypass architect decision and use this mode

        Returns:
            PipelineContext with all stage outputs populated
        """
        ctx = PipelineContext(
            user_query=user_query,
            user_embedding=user_embedding,
            filters=filters,
        )

        # Architect decides execution plan
        ctx.plan = self._architect.determine_plan(
            user_query=user_query,
            user_embedding=user_embedding,
            filters=filters,
            force_mode=force_mode,
        )
        ctx.mode = ctx.plan.mode

        # Dispatch to mode-specific handler
        t0 = time.perf_counter()
        try:
            if ctx.mode == ExecutionMode.FAST:
                ctx = await self._run_fast(ctx)
            elif ctx.mode == ExecutionMode.FULL:
                ctx = await self._run_full(ctx)
            elif ctx.mode == ExecutionMode.FALLBACK:
                ctx = await self._run_fallback(ctx)
            elif ctx.mode == ExecutionMode.RANKING:
                ctx = await self._run_ranking(ctx)
            elif ctx.mode == ExecutionMode.SESSION:
                ctx = await self._run_session(ctx)
            elif ctx.mode == ExecutionMode.CAREER:
                ctx = await self._run_career(ctx)
        except Exception as e:
            ctx.errors.append(f"Pipeline error in {ctx.mode.value} mode: {e}")

        ctx.elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return ctx

    # ── Mode dispatchers ─────────────────────────────────────────────────

    async def _run_fast(self, ctx: PipelineContext) -> PipelineContext:
        """Fast mode: use cached retrieval, minimal simulation (top 3 only)."""
        # Step 1: Cache lookup
        cache_key = RetrievalCache.make_key(ctx.user_query, ctx.filters)
        cached = self._cache.get(cache_key)
        if cached:
            ctx.retrieved_candidates = cached[: ctx.plan.retrieval_top_k]
        else:
            # Cache miss — fall back to retrieval
            ctx = await self._retrieve(ctx)
            self._cache.set(cache_key, ctx.retrieved_candidates)

        # Step 2: Simulate only top 3 (fast path)
        if ctx.plan.simulation_needed and ctx.retrieved_candidates:
            top_n = ctx.retrieved_candidates[:3]
            ctx = await self._simulate(ctx, candidates=top_n)
        else:
            ctx.plan.simulation_needed = False

        # Step 3: Review
        if ctx.simulation_results:
            ctx = await self._review(ctx)

        # Step 4: Feedback
        if ctx.reviewer_aggregate is not None:
            ctx = await self._feedback(ctx)

        return ctx

    async def _run_full(self, ctx: PipelineContext) -> PipelineContext:
        """Full mode: complete pipeline with full retrieval and simulation.

        When ranking is enabled and a trained model exists, optionally injects
        a rerank step between retrieval and simulation to improve candidate ordering.
        """
        # Step 1: Retrieval
        ctx = await self._retrieve(ctx)

        # Step 1.5 (optional): Rerank injection when ranking model is available
        if self._config.ranking_enabled and self._reranker.has_active_model() and ctx.retrieved_candidates:
            ctx = await self._build_features(ctx)
            ctx = await self._rerank(ctx)
            # Reorder retrieved_candidates to match reranked order for simulation
            if ctx.reranked_candidates:
                reranked_ids = [rc.candidate_id for rc in ctx.reranked_candidates]
                ctx.retrieved_candidates.sort(
                    key=lambda m: reranked_ids.index(m.item_id)
                    if m.item_id in reranked_ids
                    else 999
                )

        # Step 2: Simulation
        if ctx.retrieved_candidates:
            ctx = await self._simulate(ctx)

        # Step 3: Review
        if ctx.simulation_results:
            ctx = await self._review(ctx)

        # Step 4: Feedback
        if ctx.reviewer_aggregate is not None:
            ctx = await self._feedback(ctx)

        return ctx

    async def _run_fallback(self, ctx: PipelineContext) -> PipelineContext:
        """Fallback mode: cached or degraded results only, no simulation."""
        cache_key = RetrievalCache.make_key(ctx.user_query, ctx.filters)
        cached = self._cache.get(cache_key)

        if cached:
            ctx.retrieved_candidates = cached
            ctx.plan.cache_used = True
            ctx.plan.simulation_needed = False
        else:
            # Best-effort retrieval even in fallback
            try:
                ctx = await self._retrieve(ctx)
            except Exception as e:
                ctx.errors.append(f"Fallback retrieval failed: {e}")

        return ctx

    # ── Ranking mode pipeline (T006 LTR) ──────────────────────────────────

    async def _run_ranking(self, ctx: PipelineContext) -> PipelineContext:
        """Ranking mode: retrieval → feature_build → rerank → review → pair_build.

        Uses real user behavior for training signal, never simulation output.
        """
        # Step 1: Retrieval (same as FULL mode)
        ctx = await self._retrieve(ctx)

        # Step 2: Feature building
        if ctx.retrieved_candidates:
            ctx = await self._build_features(ctx)

        # Step 3: Rerank
        if ctx.feature_vectors and (ctx.plan.rerank_needed or self._reranker.has_active_model()):
            ctx = await self._rerank(ctx)
        elif ctx.feature_vectors:
            ctx = await self._rerank_identity(ctx)

        # Step 4: Review (on reranked results quality)
        if ctx.simulation_results:
            ctx = await self._review(ctx)

        # Step 5: Pair building (from real user behavior, NOT simulation)
        interaction_history: list = getattr(ctx, 'interaction_history', None) or []
        if interaction_history:
            ctx = await self._build_pairs(ctx)

        return ctx

    # ── Session mode pipeline (T006 L3) ───────────────────────────────────

    async def _run_session(self, ctx: PipelineContext) -> PipelineContext:
        """Session mode: track → aggregate → update_prefs → retrieval → rerank → review → feedback_queue → feedback.

        Uses dynamic user preferences updated from recent session behavior.
        Retrieval blends static profile with dynamic session context.
        """
        user_id = getattr(ctx, 'user_id', None) or "default-user"
        session_id = ctx.plan.session_id or ctx.session_id

        # Step 1: Session tracking — ensure active session
        ctx = await self._session_track(ctx, user_id, session_id)

        # Step 2: Behavior aggregation
        ctx = await self._session_aggregate(ctx)

        # Step 3: Preference updating
        ctx = await self._session_update_preferences(ctx, user_id)

        # Step 4: Retrieval with dynamic context
        ctx = await self._retrieve_with_dynamic_context(ctx)

        # Step 5: Feature build + Rerank (reuse ranking pipeline steps)
        if ctx.retrieved_candidates:
            ctx = await self._build_features(ctx)

        if ctx.feature_vectors and (ctx.plan.rerank_needed or self._reranker.has_active_model()):
            ctx = await self._rerank(ctx)
        elif ctx.feature_vectors:
            ctx = await self._rerank_identity(ctx)

        # Step 6: Session review with drift detection
        ctx = await self._session_review(ctx)

        # Step 7: Enqueue feedback events for nightly training
        ctx = await self._session_enqueue_feedback(ctx)

        # Step 8: Long-term feedback aggregate
        ctx = await self._session_feedback(ctx)

        return ctx

    async def _session_track(
        self, ctx: PipelineContext, user_id: str, session_id: str | None
    ) -> PipelineContext:
        """Step 1-S: Ensure active session exists and load its actions."""
        if session_id:
            session = self._session_tracker.get_session(session_id)
            if session is None:
                session = self._session_tracker.start_session(user_id)
        else:
            session = self._session_tracker.get_active_session(user_id)

        ctx.session_id = session.session_id
        ctx.session_actions = [
            action.model_dump() for action in session.ordered_actions
        ]
        ctx.plan.session_id = session.session_id
        return ctx

    async def _session_aggregate(self, ctx: PipelineContext) -> PipelineContext:
        """Step 2-S: Aggregate session actions into behavioral summary."""
        session = self._session_tracker.get_session(ctx.session_id)
        if session is None:
            return ctx

        summary = self._behavior_aggregator.aggregate(session, trace_id=ctx.execution_id)
        ctx.session_summary = summary.model_dump()
        return ctx

    async def _session_update_preferences(
        self, ctx: PipelineContext, user_id: str
    ) -> PipelineContext:
        """Step 3-S: Update dynamic preferences from session summary."""
        if ctx.session_summary is None:
            return ctx

        summary = SessionSummary(**ctx.session_summary)
        historical = self._preference_store.get(user_id)
        updated = self._preference_updater.update(historical, summary)
        self._preference_store[user_id] = updated

        ctx.dynamic_preferences = updated.model_dump()
        ctx.drift_score = updated.preference_shift_score
        return ctx

    async def _retrieve_with_dynamic_context(self, ctx: PipelineContext) -> PipelineContext:
        """Step 4-S: Retrieval using blended static + dynamic preferences.

        Blends query embedding with dynamic preference embedding:
          blended = 0.7 * query_embedding + 0.3 * preference_embedding
        """
        # Build preference text from dynamic preferences for embedding
        pref_text = self._build_preference_text(ctx)
        if pref_text:
            pref_vec = embedder.encode_query(pref_text)
            query_vec = ctx.user_embedding or embedder.encode_query(ctx.user_query)
            # Blend: 0.7 query + 0.3 preferences
            blended = [0.7 * q + 0.3 * p for q, p in zip(query_vec, pref_vec)]
            ctx.user_embedding = blended

        # Standard retrieval with blended embedding
        ctx = await self._retrieve(ctx)
        return ctx

    async def _session_review(self, ctx: PipelineContext) -> PipelineContext:
        """Step 6-S: Review session quality and detect drift anomalies."""
        if ctx.session_summary is None:
            return ctx

        session_summary = SessionSummary(**ctx.session_summary)
        review = self._reviewer.review_session(
            session_summary=session_summary,
            reranked_results=ctx.reranked_candidates if ctx.reranked_candidates else ctx.retrieved_candidates,
            drift_score=ctx.drift_score,
        )
        ctx.session_review = review.model_dump() if review else None

        # Detect drift anomalies
        if review and review.detected_issues:
            for issue in review.detected_issues:
                ctx.errors.append(f"Session review: {issue}")

        return ctx

    async def _session_enqueue_feedback(self, ctx: PipelineContext) -> PipelineContext:
        """Step 7-S: Convert session behavior into queued ranking feedback events."""
        session = self._session_tracker.get_session(ctx.session_id)
        if session is None or ctx.session_summary is None:
            return ctx

        summary = SessionSummary(**ctx.session_summary)
        model_version = 0
        if ctx.model_used and isinstance(ctx.model_used, dict):
            model_version = ctx.model_used.get("model_version", 0)

        events = self._feedback_queue.enqueue_session(
            session=session,
            summary=summary,
            trace_id=ctx.execution_id,
            model_version=model_version,
        )
        ctx.queued_events = [e.model_dump() for e in events]
        return ctx

    async def _session_feedback(self, ctx: PipelineContext) -> PipelineContext:
        """Step 8-S: Aggregate long-term recommendation performance."""
        # Generate training samples from session review
        if ctx.reviewer_aggregate is not None and ctx.simulation_results:
            ctx = await self._feedback(ctx)

        # Long-term aggregation (collect session metrics for trend analysis)
        # In MVP, store metrics in context; future: write to analytics store
        return ctx

    @staticmethod
    def _build_preference_text(ctx: PipelineContext) -> str:
        """Build a text representation of dynamic preferences for embedding."""
        if ctx.dynamic_preferences is None:
            return ""

        prefs = ctx.dynamic_preferences
        parts: list[str] = []

        skills = prefs.get("skill_weights", {})
        if skills:
            top_skills = sorted(skills.items(), key=lambda x: -x[1])[:10]
            parts.append(" ".join(s for s, _ in top_skills))

        locs = prefs.get("preferred_locations", [])
        if locs:
            parts.append(" ".join(locs[:5]))

        levels = prefs.get("preferred_levels", [])
        if levels:
            parts.append(" ".join(levels[:3]))

        companies = prefs.get("preferred_companies", [])
        if companies:
            parts.append(" ".join(companies[:5]))

        return " ".join(parts)

    # ── Career mode pipeline (T007) ───────────────────────────────────────

    async def _run_career(self, ctx: PipelineContext) -> PipelineContext:
        """Career evolution pipeline: parse → retrieve → review → architect → simulate → frontend.

        All 6 agents execute in strict order. Each feeds output to the next.
        No agent can skip or short-circuit the pipeline.
        """
        user_id = ctx.user_id or "default-user"
        raw_events = getattr(ctx, 'raw_behavior_data', None) or []

        # Step 1: Parse raw behavior → CareerEvent JSON
        ctx = await self._career_parse(ctx, raw_events, user_id)

        # Step 2: Retrieve historical career data
        ctx = await self._career_retrieve(ctx, user_id)

        # Step 3: Analyze career patterns
        ctx = await self._career_review(ctx)

        # Step 4: Design career strategy
        ctx = await self._career_architect_step(ctx)

        # Step 5: Simulate strategy execution
        ctx = await self._career_simulate(ctx)

        # Step 6: Build frontend visualization
        ctx = await self._career_frontend_build(ctx, user_id)

        return ctx

    async def _career_parse(
        self, ctx: PipelineContext, raw_events: list, user_id: str
    ) -> PipelineContext:
        """Step 1-C: Parse raw behavior into CareerEvent objects."""
        if raw_events:
            events = self._career_parser.parse_batch(raw_events, user_id)
        else:
            events = []

        ctx.career_events = [e.model_dump() for e in events]

        # Ingest into retriever for future queries
        for e in events:
            self._career_retriever.ingest(e)

        return ctx

    async def _career_retrieve(
        self, ctx: PipelineContext, user_id: str
    ) -> PipelineContext:
        """Step 2-C: Retrieve historical career timeline."""
        timeline = self._career_retriever.retrieve(user_id)
        ctx.career_timeline = timeline.model_dump()
        return ctx

    async def _career_review(self, ctx: PipelineContext) -> PipelineContext:
        """Step 3-C: Analyze career patterns from timeline."""
        if ctx.career_timeline is None:
            return ctx

        timeline = CareerTimeline(**ctx.career_timeline)
        analysis = self._career_reviewer.analyze(timeline)
        ctx.bottleneck_analysis = analysis.model_dump()
        return ctx

    async def _career_architect_step(self, ctx: PipelineContext) -> PipelineContext:
        """Step 4-C: Design career strategy from profile + pattern."""
        if ctx.career_timeline is None or ctx.bottleneck_analysis is None:
            return ctx

        timeline = CareerTimeline(**ctx.career_timeline)
        bottleneck = BottleneckAnalysis(**ctx.bottleneck_analysis)
        strategy = self._career_architect.design(timeline, bottleneck)
        ctx.career_strategy = strategy.model_dump()
        return ctx

    async def _career_simulate(self, ctx: PipelineContext) -> PipelineContext:
        """Step 5-C: Simulate strategy execution outcomes."""
        if ctx.career_strategy is None or ctx.bottleneck_analysis is None:
            return ctx

        strategy = CareerStrategy(**ctx.career_strategy)
        bottleneck = BottleneckAnalysis(**ctx.bottleneck_analysis)
        simulation = self._career_simulator.simulate(strategy, bottleneck)
        ctx.strategy_simulation = simulation.model_dump()
        return ctx

    async def _career_frontend_build(
        self, ctx: PipelineContext, user_id: str
    ) -> PipelineContext:
        """Step 6-C: Build frontend visualization JSON."""
        timeline = CareerTimeline(**ctx.career_timeline) if ctx.career_timeline else None
        bottleneck = BottleneckAnalysis(**ctx.bottleneck_analysis) if ctx.bottleneck_analysis else None
        strategy = CareerStrategy(**ctx.career_strategy) if ctx.career_strategy else None
        simulation = StrategySimulation(**ctx.strategy_simulation) if ctx.strategy_simulation else None

        viz = self._career_frontend.build(
            user_id=user_id,
            timeline=timeline,
            bottleneck=bottleneck,
            strategy=strategy,
            simulation=simulation,
        )
        ctx.career_visualization = viz.model_dump()
        return ctx

    async def _build_features(self, ctx: PipelineContext) -> PipelineContext:
        """Build ranking features from retrieval candidates."""
        user_skills = self._extract_skills_from_query(ctx.user_query)
        user_profile = {"skills": user_skills, "query": ctx.user_query}

        interaction_history = getattr(ctx, 'interaction_history', None) or []

        ctx.feature_vectors = self._feature_builder.build_features(
            trace_id=ctx.execution_id,
            user_profile=user_profile,
            candidates=ctx.retrieved_candidates,
            interaction_history=interaction_history,
        )
        return ctx

    async def _rerank(self, ctx: PipelineContext) -> PipelineContext:
        """Apply ranking model to rerank candidates."""
        ctx.reranked_candidates = self._reranker.rerank(
            trace_id=ctx.execution_id,
            feature_vectors=ctx.feature_vectors,
        )
        meta = self._model_store.get_active_metadata()
        if meta:
            ctx.model_used = meta.model_dump()
        return ctx

    async def _rerank_identity(self, ctx: PipelineContext) -> PipelineContext:
        """Identity rerank when no model is available."""
        ctx.reranked_candidates = self._reranker.rerank_identity(
            trace_id=ctx.execution_id,
            feature_vectors=ctx.feature_vectors,
        )
        return ctx

    async def _build_pairs(self, ctx: PipelineContext) -> PipelineContext:
        """Generate pairwise ranking data from real user behavior logs."""
        interaction_history = getattr(ctx, 'interaction_history', None) or []
        if not interaction_history:
            return ctx

        behavior_logs: list[UserBehaviorLog] = []
        for item in interaction_history:
            if isinstance(item, UserBehaviorLog):
                behavior_logs.append(item)
            elif isinstance(item, dict):
                behavior_logs.append(UserBehaviorLog(**item))
            else:
                continue

        if behavior_logs:
            ctx.ranking_pairs = self._pair_builder.build_pairs(
                trace_id=ctx.execution_id,
                behavior_logs=behavior_logs,
            )
        return ctx

    # ── Pipeline steps ───────────────────────────────────────────────────

    async def _retrieve(
        self,
        ctx: PipelineContext,
    ) -> PipelineContext:
        """Step 1: Retrieve top-K job candidates via semantic search.

        1. Ensure jobs are indexed (ingest from mock source if needed)
        2. Encode user query
        3. Search jobs via cosine similarity
        4. Apply filters (location, salary, skills) as post-filter
        5. Store in ctx.retrieved_candidates
        """
        # Ensure data is available
        if not self._data_ingestion.get_jobs():
            await self._data_ingestion.ingest_all()

        jobs = self._data_ingestion.get_jobs()
        if not jobs:
            ctx.errors.append("No jobs available for indexing")
            return ctx

        # Create StructuredJob list and index if needed
        structured_jobs: list[StructuredJob] = []
        for uj in jobs:
            sj = self._unified_to_structured(uj)
            structured_jobs.append(sj)

        # Index jobs (lightweight re-index; Qdrant handles upserts)
        try:
            await self._retriever.index_jobs_batch(structured_jobs)
        except Exception as e:
            ctx.errors.append(f"Indexing error: {e}")
            # Continue anyway — search may still work if jobs were already indexed

        # Search
        try:
            query_vec = ctx.user_embedding or embedder.encode_query(ctx.user_query)
            candidates = await self._retriever.search_by_query(
                query_text=ctx.user_query,
                top_k=ctx.plan.retrieval_top_k,
                score_threshold=0.0,
            )
        except Exception as e:
            ctx.errors.append(f"Search error: {e}")
            return ctx

        # Post-filter (location, etc.)
        if ctx.filters:
            candidates = self._apply_filters(candidates, ctx.filters)

        ctx.retrieved_candidates = candidates
        return ctx

    async def _simulate(
        self,
        ctx: PipelineContext,
        candidates: list[MatchResult] | None = None,
    ) -> PipelineContext:
        """Step 2: Simulate candidate-job interactions.

        For each candidate match (up to plan's limit):
        1. Build StructuredResume from query + StructuredJob from match payload
        2. Run SimulationEngine.run() with each strategy
        3. Collect SimulationResults
        """
        matches = candidates or ctx.retrieved_candidates
        if not matches:
            return ctx

        # Build synthetic resume from user query
        resume = self._make_synthetic_resume(ctx.user_query, ctx.user_embedding)

        for match in matches[: ctx.plan.retrieval_top_k]:
            try:
                job = self._build_job_from_match(match)
                # Run with balanced strategy (most informative single path)
                result = self._simulation.run(resume, job, strategy="balanced")
                ctx.simulation_results.append(result)
            except Exception as e:
                ctx.errors.append(
                    f"Simulation failed for {match.item_id}: {e}"
                )

        return ctx

    async def _review(self, ctx: PipelineContext) -> PipelineContext:
        """Step 3: Reviewer evaluates simulation quality.

        Produces FeedbackAggregate with per-simulation entries and bias findings.
        """
        if not ctx.simulation_results:
            return ctx

        # Build retrieval context: {sim_id: [matches used]}
        retrieval_ctx: dict[str, list[MatchResult]] = {}
        for i, result in enumerate(ctx.simulation_results):
            if i < len(ctx.retrieved_candidates):
                retrieval_ctx[result.simulation_id] = [
                    ctx.retrieved_candidates[i]
                ]

        try:
            ctx.reviewer_aggregate = self._reviewer.review_batch(
                ctx.simulation_results,
                retrieval_context=retrieval_ctx,
            )
        except Exception as e:
            ctx.errors.append(f"Review failed: {e}")

        return ctx

    async def _feedback(self, ctx: PipelineContext) -> PipelineContext:
        """Step 4: Generate training samples from all collected outputs.

        Merges simulation + reviewer outputs into a learning-to-rank dataset.
        """
        if ctx.reviewer_aggregate is None or not ctx.simulation_results:
            return ctx

        try:
            ctx.training_samples = self._feedback.generate_dataset(
                ctx.reviewer_aggregate,
                ctx.simulation_results,
                ctx.retrieved_candidates,
            )
        except Exception as e:
            ctx.errors.append(f"Feedback generation failed: {e}")

        return ctx

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_skills_from_query(query: str) -> list[str]:
        """Extract skill keywords from query string for feature building."""
        import re
        tokens = re.split(r"[,，\s]+", query.strip())
        return [t for t in tokens if t and not re.match(r"^\d+$", t)]

    @staticmethod
    def _make_synthetic_resume(
        query: str, embedding: list[float] | None
    ) -> StructuredResume:
        """Create a minimal StructuredResume from a user query string.

        Extracts skill keywords from the query for basic matching.
        """
        # Simple keyword extraction — split on spaces and common delimiters
        import re
        tokens = re.split(r"[,，\s]+", query.strip())
        skills = [t for t in tokens if t and not re.match(r"^\d+$", t)]

        return StructuredResume(
            resume_id=f"query-{hash(query) & 0xFFFFFFFF:08x}",
            name="User Query",
            summary=query,
            skills=skills,
            skill_embedding=embedding,
        )

    @staticmethod
    def _build_job_from_match(match: MatchResult) -> StructuredJob:
        """Reconstruct StructuredJob from MatchResult payload."""
        p = match.payload
        salary_tuple = None
        raw_salary = p.get("salary_range")
        if raw_salary and isinstance(raw_salary, list) and len(raw_salary) == 2:
            salary_tuple = (int(raw_salary[0]), int(raw_salary[1]))

        return StructuredJob(
            job_id=match.item_id,
            title=p.get("title", ""),
            company=p.get("company", ""),
            location=p.get("location", ""),
            level=p.get("level", ""),
            required_skills=p.get("required_skills", []),
            optional_skills=p.get("optional_skills", []),
            salary_range=salary_tuple,
        )

    @staticmethod
    def _unified_to_structured(uj) -> StructuredJob:
        """Convert UnifiedJob (from data_ingestion) to StructuredJob."""
        from backend.data_ingestion.schemas import UnifiedJob

        # Parse salary from UnifiedJob string format back to tuple
        salary_tuple = None
        if uj.salary_range and uj.salary_range != "面议":
            import re
            m = re.match(r"(\d+)K?-(\d+)K?", uj.salary_range)
            if m:
                salary_tuple = (int(m.group(1)), int(m.group(2)))

        return StructuredJob(
            job_id=uj.job_id,
            title=uj.title,
            company=uj.company,
            location=uj.location,
            required_skills=uj.skills,
            optional_skills=[],
            salary_range=salary_tuple,
        )

    @staticmethod
    def _apply_filters(
        candidates: list[MatchResult], filters: dict
    ) -> list[MatchResult]:
        """Post-filter candidates by location, salary, skills.

        Simple exact/substring matching — sufficient for MVP.
        """
        filtered = candidates
        if "location" in filters:
            loc = filters["location"].lower()
            filtered = [
                m
                for m in filtered
                if loc in m.payload.get("location", "").lower()
            ]

        if "skill" in filters:
            skill = filters["skill"].lower()
            filtered = [
                m
                for m in filtered
                if skill in " ".join(m.payload.get("required_skills", [])).lower()
                or skill in " ".join(m.payload.get("optional_skills", [])).lower()
            ]

        return filtered
