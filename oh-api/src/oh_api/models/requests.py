"""Request models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request model."""

    session_id: str | None = None
    message: str = Field(..., min_length=1)
    stream: bool = True
    model: str | None = None
    system_prompt: str | None = None


class SessionCreateRequest(BaseModel):
    """Session creation request."""

    model: str | None = None
    system_prompt: str | None = None


class ToolExecuteRequest(BaseModel):
    """Tool execution request."""

    tool: str = Field(..., min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
