"""RerankEngineAgent — apply trained LightGBM ranking model to rerank candidates.

Ranking score comes ONLY from the ranking model (Constraint).
Semantic retrieval score is preserved as original_score (auxiliary only).
Does NOT modify the candidate pool — returns new RerankedCandidate objects.
"""

from __future__ import annotations

from typing import Any

from backend.ranking.model_store import ModelStore
from backend.ranking.schemas import FeatureVector, RerankedCandidate, TrainedRankerModel


class RerankEngineAgent:
    """Apply a trained LightGBM ranking model to rerank feature vectors.

    Falls back to identity rerank (ranking_score = embedding_similarity) when
    no trained model is available — graceful degradation with full traceability.

    Usage:
        store = ModelStore()
        engine = RerankEngineAgent(model_store=store)
        if engine.has_active_model():
            reranked = engine.rerank("exec-001", feature_vectors)
        else:
            reranked = engine.rerank_identity("exec-001", feature_vectors)
    """

    def __init__(self, model_store: ModelStore | None = None):
        self._model_store = model_store or ModelStore()
        self._active_model: Any = None
        self._active_meta: TrainedRankerModel | None = None
        self._refresh_model()

    # ── Public API ────────────────────────────────────────────────────────

    def rerank(
        self,
        trace_id: str,
        feature_vectors: list[FeatureVector],
        trained_model: Any | None = None,
    ) -> list[RerankedCandidate]:
        """Apply ranking model to produce reranked candidates.

        Args:
            trace_id: Pipeline execution ID
            feature_vectors: Features for each candidate (from FeatureBuilderAgent)
            trained_model: Optional pre-loaded (booster, metadata) tuple. If None,
                           uses the active model from ModelStore.

        Returns:
            list[RerankedCandidate] sorted by ranking_score descending, final_rank 1-indexed.
        """
        if not feature_vectors:
            return []

        # Resolve model
        if trained_model is not None:
            booster, meta = trained_model[0], trained_model[1]
        else:
            self._refresh_model()
            booster = self._active_model
            meta = self._active_meta

        # Compute scores
        if booster is not None and meta is not None:
            ranking_scores = self._predict(booster, meta, feature_vectors)
        else:
            # Identity fallback: use embedding_similarity as ranking_score
            ranking_scores = self._identity_scores(feature_vectors)

        # Sort by ranking_score descending, assign ranks
        indexed = list(enumerate(ranking_scores))
        indexed.sort(key=lambda x: x[1], reverse=True)

        results: list[RerankedCandidate] = []
        for rank, (orig_idx, score) in enumerate(indexed, start=1):
            fv = feature_vectors[orig_idx]
            results.append(
                RerankedCandidate(
                    candidate_id=fv.candidate_id,
                    trace_id=trace_id,
                    original_score=fv.features.get("embedding_similarity", 0.0),
                    ranking_score=score,
                    final_rank=rank,
                    features=fv.features,
                )
            )
        return results

    def rerank_identity(
        self,
        trace_id: str,
        feature_vectors: list[FeatureVector],
    ) -> list[RerankedCandidate]:
        """Explicit identity rerank — ranking_score = embedding_similarity, order preserved.

        Used when no model is available and caller wants to be explicit about fallback.
        Results are identical to calling rerank() with no model, but this method
        does not attempt to load from ModelStore.
        """
        ranking_scores = self._identity_scores(feature_vectors)
        return self._build_results(trace_id, feature_vectors, ranking_scores)

    def has_active_model(self) -> bool:
        """Check whether a trained ranking model is available."""
        self._refresh_model()
        return self._active_model is not None

    def get_active_metadata(self) -> TrainedRankerModel | None:
        """Get metadata for the active model."""
        self._refresh_model()
        return self._active_meta

    # ── Internal ──────────────────────────────────────────────────────────

    def _refresh_model(self) -> None:
        """Reload active model from ModelStore."""
        loaded = self._model_store.load_active()
        if loaded:
            self._active_model, self._active_meta = loaded
        else:
            self._active_model = None
            self._active_meta = None

    def _predict(
        self,
        booster: Any,
        meta: TrainedRankerModel,
        feature_vectors: list[FeatureVector],
    ) -> list[float]:
        """Run LightGBM Booster.predict() on ordered feature arrays.

        Returns raw scores — they may not be in [0,1] range.
        We normalize via sigmoid for consistent output range.
        """
        feature_names = meta.feature_names
        if not feature_names:
            # No feature names stored — use current feature keys as fallback
            feature_names = list(next(iter(feature_vectors)).features.keys())

        import numpy as np
        X = np.array(
            [[fv.features.get(k, 0.0) for k in feature_names] for fv in feature_vectors],
            dtype=np.float32,
        )
        raw_scores = booster.predict(X)
        # Normalize to [0, 1] via sigmoid
        scores = 1.0 / (1.0 + np.exp(-raw_scores))
        return [round(float(s), 4) for s in scores]

    @staticmethod
    def _identity_scores(feature_vectors: list[FeatureVector]) -> list[float]:
        """Fallback: use embedding_similarity as ranking score."""
        return [fv.features.get("embedding_similarity", 0.0) for fv in feature_vectors]

    def _build_results(
        self,
        trace_id: str,
        feature_vectors: list[FeatureVector],
        scores: list[float],
    ) -> list[RerankedCandidate]:
        """Sort by score descending, assign ranks, build RerankedCandidate list."""
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)

        results: list[RerankedCandidate] = []
        for rank, (orig_idx, score) in enumerate(indexed, start=1):
            fv = feature_vectors[orig_idx]
            results.append(
                RerankedCandidate(
                    candidate_id=fv.candidate_id,
                    trace_id=trace_id,
                    original_score=fv.features.get("embedding_similarity", 0.0),
                    ranking_score=score,
                    final_rank=rank,
                    features=fv.features,
                )
            )
        return results
