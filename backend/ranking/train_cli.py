"""Offline CLI for ranking model retraining.

Never called during request handling. Designed for cron / scheduled task execution.

Usage:
    python -m backend.ranking.train_cli --pairs-file data/ranking_pairs.jsonl
    python -m backend.ranking.train_cli --from-traces --days 7
    python -m backend.ranking.train_cli --evaluate --model-version 3
    python -m backend.ranking.train_cli --list-models
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on the path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def main():
    parser = argparse.ArgumentParser(
        description="Offline CLI for LTR ranking model training",
    )
    parser.add_argument(
        "--pairs-file",
        help="JSONL file with RankingPair data (one JSON object per line)",
    )
    parser.add_argument(
        "--from-traces",
        action="store_true",
        help="Build pairs from recent InteractionTrace records",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days of traces to use when building pairs (default: 7)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate an existing model instead of training",
    )
    parser.add_argument(
        "--model-version",
        type=int,
        help="Model version to evaluate or activate",
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Activate a specific model version (use with --model-version)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all stored model versions",
    )
    parser.add_argument(
        "--validation-split",
        type=float,
        default=0.2,
        help="Fraction of pairs for validation (default: 0.2)",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Directory for model storage (default: backend/ranking/models)",
    )
    parser.add_argument(
        "--delete-version",
        type=int,
        help="Delete a model version",
    )

    args = parser.parse_args()

    # Resolve model store
    model_store = _make_model_store(args.output_dir)

    # ── List models ──────────────────────────────────────────────────────
    if args.list_models:
        return _cmd_list_models(model_store)

    # ── Activate model ───────────────────────────────────────────────────
    if args.activate:
        return _cmd_activate(model_store, args.model_version)

    # ── Delete model ─────────────────────────────────────────────────────
    if args.delete_version:
        return _cmd_delete(model_store, args.delete_version)

    # ── Evaluate ─────────────────────────────────────────────────────────
    if args.evaluate:
        return _cmd_evaluate(model_store, args.model_version, args.pairs_file)

    # ── Train ────────────────────────────────────────────────────────────
    return _cmd_train(
        model_store=model_store,
        pairs_file=args.pairs_file,
        from_traces=args.from_traces,
        days=args.days,
        validation_split=args.validation_split,
    )


# ── Command implementations ───────────────────────────────────────────────


def _cmd_list_models(model_store) -> int:
    versions = model_store.list_versions()
    if not versions:
        print("No models stored.")
        return 0
    print(f"{'Version':>8}  {'Active':>6}  {'Samples':>8}  {'NDCG@5':>8}  {'Pair Acc':>8}  Created")
    print("-" * 80)
    for m in versions:
        active = "  *" if m.is_active else ""
        ndcg5 = m.metrics.get("validation_ndcg_5" if "validation_ndcg_5" in m.metrics else "train_ndcg_5", "-")
        pair_acc = m.metrics.get("pairwise_accuracy", "-")
        ndcg5_str = f"{ndcg5:.4f}" if isinstance(ndcg5, float) else str(ndcg5)
        pair_str = f"{pair_acc:.4f}" if isinstance(pair_acc, float) else str(pair_acc)
        print(
            f"{m.model_version:>8}  {active:>6}  {m.training_samples_count:>8}  "
            f"{ndcg5_str:>8}  {pair_str:>8}  {m.created_at[:19]}"
        )
    return 0


def _cmd_activate(model_store, version: int) -> int:
    if version is None:
        print("Error: --model-version is required for --activate", file=sys.stderr)
        return 1
    meta = model_store.activate(version)
    if meta is None:
        print(f"Error: model version {version} not found", file=sys.stderr)
        return 1
    print(f"Activated model version {version}")
    print(f"  NDCG@5: {meta.metrics.get('validation_ndcg_5', 'N/A')}")
    print(f"  Pairwise accuracy: {meta.metrics.get('pairwise_accuracy', 'N/A')}")
    return 0


def _cmd_delete(model_store, version: int) -> int:
    ok = model_store.delete(version)
    if ok:
        print(f"Deleted model version {version}")
        return 0
    print(f"Error: model version {version} not found", file=sys.stderr)
    return 1


def _cmd_evaluate(model_store, version: int, pairs_file: str | None) -> int:
    from backend.ranking.trainer import RankingTrainerAgent

    loaded = model_store.load(version)
    if loaded is None:
        print("Error: no model found to evaluate", file=sys.stderr)
        return 1

    booster, meta = loaded
    print(f"Loaded model v{meta.model_version} ({meta.training_samples_count} training samples)")

    if pairs_file:
        pairs = _load_pairs(pairs_file)
        if not pairs:
            print("Error: no pairs loaded from file", file=sys.stderr)
            return 1
        trainer = RankingTrainerAgent(model_store=model_store)
        metrics = trainer.evaluate(booster, pairs)
        print("\nEvaluation metrics:")
        for k, v in sorted(metrics.items()):
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
    else:
        print("\nStored metrics:")
        for k, v in sorted(meta.metrics.items()):
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

    return 0


def _cmd_train(
    model_store,
    pairs_file: str | None,
    from_traces: bool,
    days: int,
    validation_split: float,
) -> int:
    from backend.ranking.trainer import RankingTrainerAgent

    pairs = _load_pairs_from_args(pairs_file, from_traces, days)
    if not pairs:
        print("Error: no training pairs available. Provide --pairs-file or --from-traces.", file=sys.stderr)
        return 1

    print(f"Loaded {len(pairs)} ranking pairs")

    # Check if features are populated
    pairs_with_features = sum(1 for p in pairs if p.positive_features)
    print(f"Pairs with features: {pairs_with_features}/{len(pairs)}")

    if pairs_with_features < 10:
        print("Error: need at least 10 pairs with features to train", file=sys.stderr)
        return 1

    trainer = RankingTrainerAgent(model_store=model_store)
    print("\nTraining LightGBM LambdaRank model...")
    print(f"  Objective: lambdarank")
    print(f"  Validation split: {validation_split}")
    print(f"  Min training pairs: {int(len(pairs) * (1 - validation_split))}")

    try:
        booster, meta = trainer.train(
            pairs=pairs,
            validation_split=validation_split,
        )
    except Exception as e:
        print(f"\nTraining failed: {e}", file=sys.stderr)
        return 1

    print(f"\nTraining complete — model v{meta.model_version} saved")
    print(f"  Model path: {meta.model_path}")
    print(f"  Feature names: {meta.feature_names}")
    print("\nMetrics:")
    for k, v in sorted(meta.metrics.items()):
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    # Feature importance
    try:
        importance = booster.feature_importance(importance_type="gain")
        names = meta.feature_names
        print("\nFeature importance (gain):")
        for name, gain in sorted(zip(names, importance), key=lambda x: -x[1]):
            print(f"  {name}: {gain:.2f}")
    except Exception:
        pass

    return 0


# ── Helpers ───────────────────────────────────────────────────────────────


def _make_model_store(output_dir: str):
    from backend.ranking.model_store import ModelStore
    return ModelStore(storage_dir=output_dir) if output_dir else ModelStore()


def _load_pairs_from_args(
    pairs_file: str | None,
    from_traces: bool,
    days: int,
) -> list:
    from backend.ranking.schemas import RankingPair

    if pairs_file:
        return _load_pairs(pairs_file)

    if from_traces:
        return _pairs_from_traces(days)

    return []


def _load_pairs(path: str) -> list:
    from backend.ranking.schemas import RankingPair

    pairs: list = []
    filepath = Path(path)
    if not filepath.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return []

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                pairs.append(RankingPair(**data))
            except Exception as e:
                print(f"Warning: skipping invalid line: {e}", file=sys.stderr)
    return pairs


def _pairs_from_traces(days: int) -> list:
    from backend.ranking.schemas import RankingPair, UserBehaviorLog
    from backend.ranking.pair_builder import PairBuilderAgent
    from backend.signal_layer.trace_store import TraceStore

    store = TraceStore()
    traces = store.list(limit=1000)

    # Filter by recency
    import time
    cutoff = time.time() - (days * 86400)
    recent = [t for t in traces if t.started_at >= cutoff]

    if not recent:
        print(f"No traces found in the last {days} days.")
        return []

    builder = PairBuilderAgent()
    all_pairs: list[RankingPair] = []

    for trace in recent:
        # Extract behavior logs from trace (stored in ranking_pairs or interaction_history)
        trace_pairs = getattr(trace, "ranking_pairs", [])
        if trace_pairs:
            all_pairs.extend(trace_pairs)
            continue

        # Fallback: build pairs from interaction history
        logs = getattr(trace, "interaction_history", None)
        if logs:
            behavior_logs = [UserBehaviorLog(**l) if isinstance(l, dict) else l for l in logs]
            pairs = builder.build_pairs(trace.trace_id, behavior_logs)
            all_pairs.extend(pairs)

    print(f"Built {len(all_pairs)} pairs from {len(recent)} recent traces")
    return all_pairs


if __name__ == "__main__":
    sys.exit(main())
