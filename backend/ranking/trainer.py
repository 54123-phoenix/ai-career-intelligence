"""RankingTrainerAgent — train LightGBM LambdaRank model from pairwise ranking data.

Constraints:
  - Uses LightGBM Ranker with lambdarank objective
  - No transformer ranking
  - No reinforcement learning
  - Prioritizes interpretability and stability
  - Offline batch training only (never called during request handling)
  - Outputs versioned model via ModelStore
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

from backend.ranking.model_store import ModelStore
from backend.ranking.schemas import RankingPair, TrainedRankerModel


class RankingTrainerAgent:
    """Train a LightGBM LambdaRank model from pairwise ranking data.

    Usage:
        trainer = RankingTrainerAgent(model_store=store)
        booster, meta = trainer.train(pairs, validation_split=0.2)
        metrics = trainer.evaluate(booster, holdout_pairs)
    """

    DEFAULT_PARAMS: dict = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "ndcg_eval_at": [1, 3, 5, 10],
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "num_threads": 4,
        "seed": 42,
    }

    def __init__(self, model_store: ModelStore | None = None):
        self._model_store = model_store or ModelStore()

    # ── Public API ────────────────────────────────────────────────────────

    def train(
        self,
        pairs: list[RankingPair],
        validation_split: float = 0.2,
        params: dict | None = None,
    ) -> tuple[Any, TrainedRankerModel]:
        """Train a LightGBM LambdaRank model.

        Args:
            pairs: Pairwise ranking samples (must have features populated)
            validation_split: Fraction of pairs reserved for validation
            params: Optional LightGBM parameter overrides

        Returns:
            (LightGBM Booster, TrainedRankerModel metadata)
        """
        if not pairs:
            raise ValueError("Cannot train with empty pairs list")

        import lightgbm as lgb

        # Extract feature names from the first pair that has features
        feature_names = self._infer_feature_names(pairs)
        if not feature_names:
            raise ValueError("No features found in pairs — run FeatureBuilderAgent first")

        # Convert pairs to LightGBM Dataset format
        train_data, val_data = self._pairs_to_dataset(pairs, feature_names, validation_split)

        # Merge params
        train_params = {**self.DEFAULT_PARAMS, **(params or {})}

        # Train
        t0 = time.perf_counter()
        booster = lgb.train(
            train_params,
            train_data,
            valid_sets=[val_data] if val_data is not None else None,
            valid_names=["validation"] if val_data is not None else None,
        )
        train_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Compute metrics
        metrics = self._compute_metrics(booster, train_data, val_data, pairs, feature_names)
        metrics["train_time_ms"] = train_time_ms

        # Build metadata
        meta = TrainedRankerModel(
            model_version=0,  # filled by ModelStore.save()
            created_at=datetime.now(timezone.utc).isoformat(),
            training_samples_count=len(pairs),
            metrics=metrics,
            model_path="",
            feature_names=feature_names,
            is_active=True,
        )

        # Persist
        saved_meta = self._model_store.save(booster, meta)
        return booster, saved_meta

    def train_incremental(
        self,
        existing_model_version: int,
        new_pairs: list[RankingPair],
        params: dict | None = None,
    ) -> tuple[Any, TrainedRankerModel] | None:
        """Continue training an existing model with new pairs (incremental update).

        Loads the existing booster, continues training with new data using a
        lower learning rate to prevent catastrophic forgetting. Compares NDCG
        before and after to ensure no degradation.

        Args:
            existing_model_version: Version of model to fine-tune
            new_pairs: New pairwise ranking samples
            params: Optional LightGBM param overrides

        Returns:
            (Booster, TrainedRankerModel) or None if existing model not found
        """
        if not new_pairs:
            return None

        import lightgbm as lgb

        # Load existing model
        loaded = self._model_store.load(existing_model_version)
        if loaded is None:
            return None

        existing_booster, existing_meta = loaded

        # Extract feature names
        feature_names = self._infer_feature_names(new_pairs)
        if not feature_names:
            feature_names = existing_meta.feature_names
        if not feature_names:
            return None

        # Build datasets
        train_data, val_data = self._pairs_to_dataset(new_pairs, feature_names, validation_split=0.2)

        # Incremental params: lower learning rate, continue from existing model
        inc_params = {
            **self.DEFAULT_PARAMS,
            "learning_rate": 0.02,  # Lower for incremental updates
            "num_boost_round": 50,  # Fewer rounds
        }
        inc_params.update(params or {})

        # Save existing model to temp file for init_model
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            init_path = Path(tmpdir) / "init_model.txt"
            existing_booster.save_model(str(init_path))

            # Retrain with init_model
            booster = lgb.train(
                inc_params,
                train_data,
                valid_sets=[val_data] if val_data is not None else None,
                valid_names=["validation"] if val_data is not None else None,
                init_model=str(init_path),
            )

        # Compute metrics
        metrics = self._compute_metrics(booster, train_data, val_data, new_pairs, feature_names)

        # Verify no catastrophic degradation
        old_ndcg = existing_meta.metrics.get("train_ndcg_5", 0.0)
        new_ndcg = metrics.get("train_ndcg_5", 0.0)
        if old_ndcg > 0 and new_ndcg > 0 and new_ndcg < old_ndcg * 0.8:
            # Significant degradation — warn but still save (caller decides)
            metrics["degradation_warning"] = 1.0
            metrics["old_ndcg_5"] = old_ndcg

        # Save with parent lineage
        meta = TrainedRankerModel(
            model_version=0,
            created_at=datetime.now(timezone.utc).isoformat(),
            training_samples_count=len(new_pairs),
            metrics=metrics,
            model_path="",
            feature_names=feature_names,
            is_active=True,
            parent_model_version=existing_model_version,
        )
        saved_meta = self._model_store.save(booster, meta)
        return booster, saved_meta

    @staticmethod
    def should_retrain(
        event_count: int,
        min_events: int = 100,
        hours_since_last: float = 0.0,
        interval_hours: float = 24.0,
    ) -> bool:
        """Check whether conditions are met for retraining.

        Args:
            event_count: Number of pending feedback queue events
            min_events: Minimum events required to trigger training
            hours_since_last: Hours since last training
            interval_hours: Minimum interval between trainings

        Returns:
            True if retraining should proceed
        """
        if event_count < min_events:
            return False
        if hours_since_last > 0 and hours_since_last < interval_hours:
            return False
        return True

    def evaluate(
        self,
        booster: Any,
        pairs: list[RankingPair],
    ) -> dict[str, float]:
        """Evaluate a trained model on held-out pairs.

        Returns dict with: ndcg_1, ndcg_3, ndcg_5, ndcg_10, pairwise_accuracy.
        """
        if not pairs:
            return {}

        feature_names = self._infer_feature_names(pairs)
        if not feature_names:
            return {}

        # Build dataset with group info
        groups = self._build_groups(pairs)
        X = self._pairs_to_matrix(pairs, feature_names)

        import lightgbm as lgb
        dataset = lgb.Dataset(X, group=groups, free_raw_data=False)

        return self._compute_metrics(booster, dataset, None, pairs, feature_names)

    # ── Internal: data preparation ───────────────────────────────────────

    def _pairs_to_dataset(
        self,
        pairs: list[RankingPair],
        feature_names: list[str],
        validation_split: float,
    ) -> tuple[Any, Any | None]:
        """Convert RankingPair list to LightGBM Dataset(s) with group info.

        Each pair → two rows (positive=relevance 1, negative=relevance 0).
        Groups are per original query (trace_id).
        """
        import lightgbm as lgb

        # Group pairs by trace_id for proper NDCG computation
        by_trace: dict[str, list[RankingPair]] = {}
        for p in pairs:
            by_trace.setdefault(p.trace_id, []).append(p)

        all_X: list[list[float]] = []
        all_y: list[float] = []
        all_groups: list[int] = []

        for trace_id, trace_pairs in by_trace.items():
            rows, labels = self._pairs_to_rows(trace_pairs, feature_names)
            # Deduplicate rows (same positive/negative job may appear in multiple pairs)
            # We assign relevance 1 to all jobs that appear as positive in any pair,
            # relevance 0 to all jobs that appear only as negative.
            seen: dict[str, float] = {}
            for row, label in zip(rows, labels):
                # Use the first 8 features as a key fingerprint (heuristic dedup)
                key = tuple(round(x, 4) for x in row[:8])
                seen[key] = max(seen.get(key, 0.0), label)

            dedup_rows = list(seen.keys())
            dedup_labels = [seen[k] for k in dedup_rows]

            all_X.extend([list(r) for r in dedup_rows])
            all_y.extend(dedup_labels)
            all_groups.append(len(dedup_rows))

        if not all_X:
            raise ValueError("No valid rows extracted from pairs")

        X = np.array(all_X, dtype=np.float32)
        y = np.array(all_y, dtype=np.float32)

        if validation_split > 0 and len(all_groups) > 1:
            n_train_groups = max(1, int(len(all_groups) * (1 - validation_split)))
            train_groups = all_groups[:n_train_groups]
            val_groups = all_groups[n_train_groups:]

            train_end = sum(train_groups)
            train_data = lgb.Dataset(
                X[:train_end], label=y[:train_end],
                group=train_groups, free_raw_data=False,
            )
            val_data = lgb.Dataset(
                X[train_end:], label=y[train_end:],
                group=val_groups, free_raw_data=False,
            )
            return train_data, val_data
        else:
            train_data = lgb.Dataset(
                X, label=y, group=all_groups, free_raw_data=False,
            )
            return train_data, None

    @staticmethod
    def _pairs_to_matrix(
        pairs: list[RankingPair],
        feature_names: list[str],
    ) -> np.ndarray:
        """Convert pairs to a feature matrix. Each pair → 2 rows."""
        rows: list[list[float]] = []
        for p in pairs:
            rows.append([p.positive_features.get(k, 0.0) for k in feature_names])
            rows.append([p.negative_features.get(k, 0.0) for k in feature_names])
        return np.array(rows, dtype=np.float32)

    @staticmethod
    def _build_groups(pairs: list[RankingPair]) -> list[int]:
        """Build group sizes from pairs grouped by trace_id."""
        by_trace: dict[str, set[str]] = {}
        for p in pairs:
            by_trace.setdefault(p.trace_id, set()).add(p.positive_job_id)
            by_trace.setdefault(p.trace_id, set()).add(p.negative_job_id)
        return [len(jobs) for jobs in by_trace.values()]

    @staticmethod
    def _pairs_to_rows(
        pairs: list[RankingPair],
        feature_names: list[str],
    ) -> tuple[list[list[float]], list[float]]:
        """Convert one trace's pairs to (rows, labels) with per-job aggregation.

        Jobs appearing as positive in any pair → label 1.
        Jobs appearing only as negative → label 0.
        """
        pos_ids = {p.positive_job_id for p in pairs}
        neg_only_ids = {p.negative_job_id for p in pairs} - pos_ids

        rows: list[list[float]] = []
        labels: list[float] = []

        for p in pairs:
            if p.positive_job_id in pos_ids:
                pos_ids.discard(p.positive_job_id)  # deduplicate
                rows.append([p.positive_features.get(k, 0.0) for k in feature_names])
                labels.append(1.0)

        for p in pairs:
            if p.negative_job_id in neg_only_ids:
                neg_only_ids.discard(p.negative_job_id)  # deduplicate
                rows.append([p.negative_features.get(k, 0.0) for k in feature_names])
                labels.append(0.0)

        return rows, labels

    # ── Internal: metrics ─────────────────────────────────────────────────

    def _compute_metrics(
        self,
        booster: Any,
        train_data: Any,
        val_data: Any | None,
        pairs: list[RankingPair],
        feature_names: list[str],
    ) -> dict[str, float]:
        """Compute NDCG, pairwise accuracy, and validation loss."""
        metrics: dict[str, float] = {}

        # NDCG from LightGBM eval
        try:
            eval_result = {}
            booster.eval_train(train_data, "train", eval_result)
            if val_data is not None:
                booster.eval_valid(val_data, eval_result)
            for k, v in eval_result.items():
                # e.g., "train's ndcg@1" -> "train_ndcg_1"
                clean = k.replace("'s ", "_").replace("@", "_").replace(" ", "_")
                metrics[clean] = round(float(v), 4)
        except Exception:
            pass

        # Pairwise accuracy on training data
        metrics["pairwise_accuracy"] = self._compute_pairwise_accuracy(
            booster, pairs, feature_names
        )

        # Validation loss approximation
        if val_data is not None:
            try:
                X_val = val_data.get_data()
                y_val = val_data.get_label()
                y_pred = booster.predict(X_val)
                metrics["validation_loss"] = round(
                    float(np.mean((y_val - y_pred) ** 2)), 4
                )
            except Exception:
                metrics["validation_loss"] = 0.0
        else:
            metrics["validation_loss"] = 0.0

        return metrics

    def _compute_pairwise_accuracy(
        self,
        booster: Any,
        pairs: list[RankingPair],
        feature_names: list[str],
    ) -> float:
        """Fraction of pairs where model correctly ranks positive above negative."""
        if not pairs:
            return 0.0

        correct = 0
        for p in pairs:
            pos_vec = np.array(
                [[p.positive_features.get(k, 0.0) for k in feature_names]],
                dtype=np.float32,
            )
            neg_vec = np.array(
                [[p.negative_features.get(k, 0.0) for k in feature_names]],
                dtype=np.float32,
            )
            pos_score = float(booster.predict(pos_vec)[0])
            neg_score = float(booster.predict(neg_vec)[0])
            if pos_score > neg_score:
                correct += 1

        return round(correct / len(pairs), 4)

    @staticmethod
    def _infer_feature_names(pairs: list[RankingPair]) -> list[str]:
        """Extract feature names from the first pair that has positive_features."""
        for p in pairs:
            if p.positive_features:
                return list(p.positive_features.keys())
        return []
