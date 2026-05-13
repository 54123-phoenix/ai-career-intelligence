"""LLM provider implementations. Injected via register_llm().

Auto-registration at startup: tries Ollama at localhost, falls back to mock.
"""

from __future__ import annotations

import json


def create_mock_provider():
    """Returns a callable that always returns a minimal valid StructuredResume JSON.

    Used as a fallback when no real LLM is available. The resume_parser's
    _rule_parse() still kicks in for actual field extraction.
    """

    def mock_call(prompt: str) -> str:
        return json.dumps(
            {
                "name": "",
                "email": None,
                "phone": None,
                "summary": "",
                "skills": [],
                "projects": [],
                "education": [],
                "experience": [],
                "certifications": [],
            }
        )

    return mock_call


def create_ollama_provider(
    model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"
):
    """Returns a callable for register_llm() that calls Ollama HTTP API."""

    import httpx

    def call_ollama(prompt: str) -> str:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]

    return call_ollama


def register_default_provider():
    """Attempt to register Ollama; fall back to mock if unavailable."""
    from backend.shared.llm_client import register_llm

    try:
        import httpx

        with httpx.Client(timeout=3) as client:
            client.get("http://localhost:11434/api/tags")
        register_llm(create_ollama_provider())
    except Exception:
        register_llm(create_mock_provider())
