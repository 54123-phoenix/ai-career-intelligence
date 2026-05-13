"""ModelStore — versioned file-system storage for trained LightGBM ranking models.

Provides save/load/activate/list with auto-incrementing version numbers.
Only one model is active at a time. Thread-safe via file-level registry.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from backend.ranking.schemas import TrainedRankerModel


class ModelStore:
    """Versioned on-disk storage for LightGBM ranking models.

    Directory layout:
        {storage_dir}/
            registry.json      # list of TrainedRankerModel dicts
            ranker_v1.txt      # LightGBM booster.save_model() output
            ranker_v2.txt
            ...

    Usage:
        store = ModelStore()
        store.save(booster, metadata)
        booster, meta = store.load_active()
        versions = store.list_versions()
    """

    def __init__(self, storage_dir: str = ""):
        if storage_dir:
            self._dir = Path(storage_dir)
        else:
            self._dir = Path(__file__).resolve().parent / "models"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._registry_path = self._dir / "registry.json"

    # ── Public API ────────────────────────────────────────────────────────

    def save(self, booster: Any, metadata: TrainedRankerModel) -> TrainedRankerModel:
        """Persist a LightGBM Booster and its metadata.

        Assigns the next version number, deactivates previous active model,
        writes model file + updates registry.

        Args:
            booster: LightGBM Booster object (booster.save_model() is called)
            metadata: TrainedRankerModel with metrics, feature_names, etc.

        Returns:
            TrainedRankerModel with version, model_path, is_active filled.
        """
        registry = self._load_registry()
        next_version = max([m.model_version for m in registry] + [0]) + 1

        # Deactivate all existing models
        for m in registry:
            m.is_active = False

        # Write model file
        model_filename = f"ranker_v{next_version}.txt"
        model_path = self._dir / model_filename
        if hasattr(booster, "save_model"):
            booster.save_model(str(model_path))
        else:
            raise TypeError("booster must be a LightGBM Booster with save_model()")

        # Create metadata entry
        saved = TrainedRankerModel(
            model_id=metadata.model_id or f"ranker-{next_version:04d}",
            model_version=next_version,
            created_at=metadata.created_at,
            training_samples_count=metadata.training_samples_count,
            metrics=metadata.metrics,
            model_path=str(model_path),
            feature_names=metadata.feature_names,
            is_active=True,
        )
        registry.append(saved)
        self._save_registry(registry)
        return saved

    def load(self, version: int | None = None) -> tuple[Any, TrainedRankerModel] | None:
        """Load a specific model version. If version is None, loads active.

        Returns:
            (LightGBM Booster, TrainedRankerModel) or None if not found.
        """
        registry = self._load_registry()
        if not registry:
            return None

        if version is not None:
            target = next((m for m in registry if m.model_version == version), None)
        else:
            target = next((m for m in registry if m.is_active), None)

        if target is None:
            return None

        return self._load_booster(target)

    def load_active(self) -> tuple[Any, TrainedRankerModel] | None:
        """Load the currently active model. Returns None if no models exist."""
        return self.load(version=None)

    def get_active_metadata(self) -> TrainedRankerModel | None:
        """Get metadata for the active model without loading the booster."""
        registry = self._load_registry()
        return next((m for m in registry if m.is_active), None)

    def list_versions(self) -> list[TrainedRankerModel]:
        """Return all model versions sorted by version descending."""
        registry = self._load_registry()
        return sorted(registry, key=lambda m: m.model_version, reverse=True)

    def activate(self, version: int) -> TrainedRankerModel | None:
        """Set a specific version as the active model.

        Deactivates all others. Returns the activated model or None.
        """
        registry = self._load_registry()
        target = next((m for m in registry if m.model_version == version), None)
        if target is None:
            return None

        for m in registry:
            m.is_active = (m.model_version == version)
        self._save_registry(registry)
        return target

    def delete(self, version: int) -> bool:
        """Delete a model version (file + registry entry). Returns True if deleted."""
        registry = self._load_registry()
        target = next((m for m in registry if m.model_version == version), None)
        if target is None:
            return False

        # Remove model file
        model_path = Path(target.model_path) if target.model_path else self._dir / f"ranker_v{version}.txt"
        if model_path.exists():
            model_path.unlink()

        # Remove from registry
        registry = [m for m in registry if m.model_version != version]

        # If deleted the active model, activate the highest remaining version
        if target.is_active and registry:
            max_ver = max(m.model_version for m in registry)
            for m in registry:
                m.is_active = (m.model_version == max_ver)

        self._save_registry(registry)
        return True

    @property
    def count(self) -> int:
        """Number of stored model versions."""
        return len(self._load_registry())

    # ── Internal ──────────────────────────────────────────────────────────

    def _load_registry(self) -> list[TrainedRankerModel]:
        """Load registry from disk. Returns empty list if file missing or corrupt."""
        if not self._registry_path.exists():
            return []
        try:
            data = json.loads(self._registry_path.read_text(encoding="utf-8"))
            return [TrainedRankerModel(**item) for item in data]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def _save_registry(self, registry: list[TrainedRankerModel]) -> None:
        """Write registry to disk as JSON array."""
        data = [m.model_dump() for m in registry]
        self._registry_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _load_booster(metadata: TrainedRankerModel) -> tuple[Any, TrainedRankerModel] | None:
        """Deserialize LightGBM Booster from the path in metadata."""
        model_path = Path(metadata.model_path)
        if not model_path.exists():
            return None
        try:
            import lightgbm as lgb
            booster = lgb.Booster(model_file=str(model_path))
            return booster, metadata
        except ImportError:
            return None
        except Exception:
            return None
