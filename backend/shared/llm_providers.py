"""LLM provider implementations. Injected via register_llm().

Auto-registration at startup: DashScope → Ollama → mock fallback chain.
"""

from __future__ import annotations

import json
import os


def create_mock_provider():
    """Returns a callable that always returns a minimal valid StructuredResume JSON.

    Used as a last-resort fallback when no real LLM is available. The resume_parser's
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


def create_dashscope_provider(model: str | None = None):
    """Returns a callable for register_llm() that calls DashScope (通义千问) Chat API.

    Uses the OpenAI-compatible endpoint: /compatible-mode/v1/chat/completions.
    Requires DASHSCOPE_API_KEY env var.
    """
    import httpx

    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    api_base = os.getenv("LLM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    chat_model = model or os.getenv("LLM_MODEL", "qwen-plus")

    def call_dashscope(prompt: str) -> str:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": chat_model,
                    "messages": [
                        {"role": "system", "content": "You are a resume parser. Output ONLY valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2048,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    return call_dashscope


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
    """Fallback chain: DashScope → Ollama → mock."""
    from backend.shared.llm_client import register_llm

    # 1. Try DashScope (阿里云通义千问) — primary provider per Constraint 3
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if api_key and len(api_key) > 10:
        try:
            register_llm(create_dashscope_provider())
            return
        except Exception:
            pass  # fall through to next provider

    # 2. Try local Ollama
    try:
        import httpx

        with httpx.Client(timeout=3) as client:
            client.get("http://localhost:11434/api/tags")
        register_llm(create_ollama_provider())
    except Exception:
        # 3. Last resort: mock
        register_llm(create_mock_provider())
