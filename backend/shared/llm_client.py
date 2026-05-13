"""LLM 调用封装层 —— 所有 Agent 通过此模块调用 LLM，不直接调用外部 API。"""
from __future__ import annotations

from collections.abc import Callable

# 占位符：实际 LLM 调用函数由 Orchestrator 在运行时注入
# Agent 不应关心底层是 OpenAI / Anthropic / DeepSeek
_llm_callable: Callable[[str], str] | None = None


def register_llm(fn: Callable[[str], str]):
    global _llm_callable
    _llm_callable = fn


async def call_llm(prompt: str, *, temperature: float = 0.3, max_retries: int = 2) -> str:
    if _llm_callable is None:
        raise RuntimeError("LLM not registered. Call register_llm() first.")
    for attempt in range(max_retries + 1):
        try:
            return _llm_callable(prompt)
        except Exception:
            if attempt == max_retries:
                raise
    return ""
