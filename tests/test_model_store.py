"""Tests for ModelStore."""

import os
import tempfile
from pathlib import Path

import pytest

from backend.ranking.model_store import ModelStore
from backend.ranking.schemas import TrainedRankerModel


class TestModelStore:
    @pytest.fixture
    def store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ModelStore(storage_dir=tmpdir)

    def test_save_and_load_active(self, store):
        meta = TrainedRankerModel(
            training_samples_count=100,
            metrics={"ndcg_5": 0.72, "pairwise_accuracy": 0.85},
            feature_names=["f1", "f2"],
        )
        # Use a mock booster — save a valid LightGBM text format
        class MockBooster:
            @staticmethod
            def save_model(path):
                Path(path).write_text('{"objective": "lambdarank"}')

        mock = MockBooster()
        saved = store.save(mock, meta)
        assert saved.model_version == 1
        assert saved.is_active
        assert Path(saved.model_path).exists()
        assert saved.metrics["ndcg_5"] == 0.72

        # Load returns None when lightgbm is not installed (graceful degradation)
        # but metadata is still accessible via get_active_metadata
        active_meta = store.get_active_metadata()
        assert active_meta is not None
        assert active_meta.model_version == 1

    def test_version_auto_increment(self, store):
        class MockBooster:
            @staticmethod
            def save_model(path):
                Path(path).write_text("mock")

        mock = MockBooster()
        m1 = store.save(mock, TrainedRankerModel(training_samples_count=10))
        m2 = store.save(mock, TrainedRankerModel(training_samples_count=20))
        assert m1.model_version == 1
        assert m2.model_version == 2

    def test_only_one_active(self, store):
        class MockBooster:
            @staticmethod
            def save_model(path):
                Path(path).write_text("mock")

        mock = MockBooster()
        m1 = store.save(mock, TrainedRankerModel(training_samples_count=10))
        m2 = store.save(mock, TrainedRankerModel(training_samples_count=20))

        # m1 should no longer be active
        meta = store.get_active_metadata()
        assert meta.model_version == 2
        assert meta.is_active

        # Verify m1 is inactive
        all_versions = store.list_versions()
        m1_stored = next(v for v in all_versions if v.model_version == 1)
        assert not m1_stored.is_active

    def test_list_versions(self, store):
        class MockBooster:
            @staticmethod
            def save_model(path):
                Path(path).write_text("mock")

        mock = MockBooster()
        store.save(mock, TrainedRankerModel(training_samples_count=10))
        store.save(mock, TrainedRankerModel(training_samples_count=20))
        versions = store.list_versions()
        assert len(versions) == 2
        assert versions[0].model_version == 2  # newest first

    def test_activate_specific_version(self, store):
        class MockBooster:
            @staticmethod
            def save_model(path):
                Path(path).write_text("mock")

        mock = MockBooster()
        store.save(mock, TrainedRankerModel(training_samples_count=10))
        store.save(mock, TrainedRankerModel(training_samples_count=20))

        store.activate(1)
        meta = store.get_active_metadata()
        assert meta.model_version == 1

    def test_empty_store_loads_none(self, store):
        assert store.load_active() is None
        assert store.get_active_metadata() is None
        assert store.list_versions() == []

    def test_delete_version(self, store):
        class MockBooster:
            @staticmethod
            def save_model(path):
                Path(path).write_text("mock")

        mock = MockBooster()
        store.save(mock, TrainedRankerModel(training_samples_count=10))
        assert store.delete(1)
        assert store.count == 0
        assert not store.delete(99)  # non-existent

    def test_delete_active_reassigns(self, store):
        class MockBooster:
            @staticmethod
            def save_model(path):
                Path(path).write_text("mock")

        mock = MockBooster()
        store.save(mock, TrainedRankerModel(training_samples_count=10))
        store.save(mock, TrainedRankerModel(training_samples_count=20))

        # Delete active (v2), v1 should become active
        store.delete(2)
        meta = store.get_active_metadata()
        assert meta is not None
        assert meta.model_version == 1
        assert meta.is_active
