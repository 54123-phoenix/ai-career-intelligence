"""Unit tests for CareerService facade — L3 simulation integration."""

from __future__ import annotations

import pytest

from backend.career.career_service import CareerService


class TestCareerService:
    def test_analyze_returns_valid_response(self):
        """Call analyze() with minimal input, verify response structure."""
        service = CareerService()
        result = service.analyze(user_input="Python backend engineer, 5 years")

        assert "id" in result
        assert "status" in result
        assert "user_profile" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert "strategies" in result
        assert "plan" in result
        assert "simulation" in result
        assert "frontend_data" in result
        assert "errors" in result

    def test_simulations_key_present(self):
        """Verify 'simulations' key is present in response."""
        service = CareerService()
        result = service.analyze(user_input="Python backend engineer")

        assert "simulations" in result
        assert isinstance(result["simulations"], list)

    def test_simulation_envelope_structure(self):
        """When simulations are present, each envelope has required fields."""
        service = CareerService()
        result = service.analyze(
            user_input="Python backend engineer, skilled in FastAPI and Docker"
        )

        sims = result["simulations"]
        for env in sims:
            # Every envelope has these keys from build_envelope()
            assert "simulation_id" in env
            assert "strategy_name" in env
            assert "outcome" in env

    def test_no_internal_details_leaked(self):
        """Response must not contain T008/T009/T010 internal keys."""
        service = CareerService()
        result = service.analyze(user_input="test user")

        # Flatten all string keys recursively
        def collect_keys(obj, keys_set):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    keys_set.add(k)
                    collect_keys(v, keys_set)
            elif isinstance(obj, list):
                for item in obj:
                    collect_keys(item, keys_set)

        all_keys: set[str] = set()
        collect_keys(result, all_keys)

        forbidden = {"t008_", "t009_", "t010_", "rl_iterations", "convergence_delta"}
        for key in all_keys:
            key_lower = key.lower()
            for fb in forbidden:
                assert fb not in key_lower, f"Forbidden key leaked: {key!r}"

    def test_response_keys_match_facade_contract(self):
        """Verify the facade /analyze response contract is preserved."""
        service = CareerService()
        result = service.analyze(user_input="test")

        expected_keys = {
            "id",
            "status",
            "user_profile",
            "recommendations",
            "strategies",
            "plan",
            "simulation",
            "frontend_data",
            "generated_at",
            "career_data",
            "errors",
            "simulations",
        }
        for key in expected_keys:
            assert key in result, f"Missing contract key: {key!r}"
