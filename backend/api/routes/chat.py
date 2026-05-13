"""Chat API routes — AI Career Assistant (SSE streaming).

Registered at /api/v1/chat
"""

from __future__ import annotations

import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: str | None = Field(default=None)
    context: dict | None = Field(default=None)


async def _mock_stream(message: str):
    """MVP: yield mock streaming tokens. Replace with LLM call in production."""
    prefix = f"收到您的问题：\"{message}\"。"
    answer = (
        "作为您的职业智能助手，我建议您从以下几个方面考虑："
        "首先，梳理当前技能栈与目标岗位的差距；"
        "其次，制定分阶段的学习计划；"
        "最后，通过模拟验证不同策略的可行性。"
    )
    full_text = prefix + answer

    # Simulate token-by-token streaming
    chunk_size = 2
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i : i + chunk_size]
        yield chunk.encode("utf-8")
        await asyncio.sleep(0.03)


@router.post("/message", tags=["Chat"])
async def chat_message(body: ChatMessageRequest):
    """AI Career Assistant — SSE streaming endpoint.

    Returns a stream of UTF-8 text chunks. Client should decode and append.
    """
    return StreamingResponse(
        _mock_stream(body.message),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
