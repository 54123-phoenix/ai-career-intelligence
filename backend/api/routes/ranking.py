"""Ranking API routes — LTR endpoints for reranking, pair building, and model management.

Registered at /api/v1/ranking
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.ranking.feature_builder import FeatureBuilderAgent
from backend.ranking.model_store import ModelStore
from backend.ranking.pair_builder import PairBuilderAgent
from backend.ranking.reranker import RerankEngineAgent
from backend.ranking.schemas import (
    PairRequest,
    RankingPair,
    RerankRequest,
    RerankedCandidate,
    TrainRequest,
    TrainedRankerModel,
    UserBehaviorLog,
)
from backend.ranking.trainer import RankingTrainerAgent
from backend.shared.types import MatchResult

router = APIRouter()

# Module-level singletons — shared across requests
_model_store = ModelStore()
_feature_builder = FeatureBuilderAgent()
_reranker = RerankEngineAgent(model_store=_model_store)
_pair_builder = PairBuilderAgent()
_trainer = RankingTrainerAgent(model_store=_model_store)


# ── Rerank ────────────────────────────────────────────────────────────────

@router.post("/rerank", response_model=list[RerankedCandidate], tags=["Ranking"])
async def rerank_candidates(body: RerankRequest):
    """Apply ranking model to a set of retrieval candidates.

    If no trained model is active, returns identity-reranked results
    (ranking_score = embedding_similarity, order preserved).
    """
    candidates = [
        MatchResult(
            item_id=c.get("item_id", c.get("job_id", "")),
            score=c.get("score", 0.0),
            payload=c.get("payload", {}),
            match_type=c.get("match_type", "resume_to_job"),
        )
        for c in body.candidates
    ]

    interaction_history = body.interaction_history or []

    feature_vectors = _feature_builder.build_features(
        trace_id=body.trace_id,
        user_profile=body.user_profile,
        candidates=candidates,
        interaction_history=interaction_history,
    )

    reranked = _reranker.rerank(
        trace_id=body.trace_id,
        feature_vectors=feature_vectors,
    )
    return reranked


# ── Pairs ─────────────────────────────────────────────────────────────────

@router.post("/pairs", response_model=list[RankingPair], tags=["Ranking"])
async def build_pairs(body: PairRequest):
    """Generate pairwise ranking samples from real user behavior logs.

    Applies: clicked > skipped, saved > clicked. Never self-pairs.
    """
    return _pair_builder.build_pairs(
        trace_id=body.trace_id,
        behavior_logs=body.behavior_logs,
    )


# ── Model Status ──────────────────────────────────────────────────────────

class ModelStatusResponse(BaseModel):
    active: bool = False
    model: TrainedRankerModel | None = None
    versions_count: int = 0


@router.get("/model/status", response_model=ModelStatusResponse, tags=["Ranking"])
async def model_status():
    """Get active ranking model info."""
    meta = _model_store.get_active_metadata()
    versions = _model_store.list_versions()
    return ModelStatusResponse(
        active=meta is not None,
        model=meta,
        versions_count=len(versions),
    )


@router.get("/model/versions", response_model=list[TrainedRankerModel], tags=["Ranking"])
async def model_versions():
    """List all stored model versions (newest first)."""
    return _model_store.list_versions()


@router.post("/model/activate/{version}", response_model=TrainedRankerModel, tags=["Ranking"])
async def activate_model(version: int):
    """Activate a specific model version for reranking."""
    meta = _model_store.activate(version)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Model version {version} not found")
    return meta


# ── Train ─────────────────────────────────────────────────────────────────

class TrainResponse(BaseModel):
    model: TrainedRankerModel | None = None
    message: str = ""


@router.post("/train", response_model=TrainResponse, tags=["Ranking"])
async def train_model(body: TrainRequest):
    """Trigger offline batch training of the ranking model.

    Requires pairs to be provided directly or built from recent traces.
    This is an admin endpoint — production should use train_cli.py.
    """
    if body.from_recent_traces:
        from backend.signal_layer.trace_store import TraceStore
        import time as _time

        store = TraceStore()
        traces = store.list(limit=1000)
        cutoff = _time.time() - (body.days * 86400)
        recent = [t for t in traces if t.started_at >= cutoff]

        all_pairs: list[RankingPair] = []
        for trace in recent:
            trace_pairs = getattr(trace, "ranking_pairs", [])
            if trace_pairs:
                all_pairs.extend(trace_pairs)

        if not all_pairs:
            return TrainResponse(
                message=f"No pairs found in recent traces (last {body.days} days)"
            )
        pairs = all_pairs
    else:
        pairs = body.pairs or []

    if not pairs:
        return TrainResponse(message="No training pairs provided")

    try:
        booster, meta = _trainer.train(
            pairs=pairs,
            validation_split=body.validation_split,
        )
        return TrainResponse(model=meta, message=f"Model v{meta.model_version} trained successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")
