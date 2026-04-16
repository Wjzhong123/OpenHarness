"""Response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail model."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str


class SessionInfo(BaseModel):
    """Session info model."""

    id: str
    created_at: datetime
    updated_at: datetime | None = None
    message_count: int = 0
    model: str | None = None


class SessionResponse(BaseModel):
    """Single session response."""

    session: SessionInfo
    messages: list[dict] = Field(default_factory=list)


class SessionListResponse(BaseModel):
    """Session list response."""

    sessions: list[SessionInfo]


class SkillInfo(BaseModel):
    """Skill info model."""

    name: str
    description: str | None = None


class SkillListResponse(BaseModel):
    """Skill list response."""

    skills: list[SkillInfo]


class ToolExecuteResponse(BaseModel):
    """Tool execution response."""

    success: bool
    result: str | None = None
    error: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""

    session_id: str
    message: str
    model: str | None = None
    usage: dict[str, int] | None = None
