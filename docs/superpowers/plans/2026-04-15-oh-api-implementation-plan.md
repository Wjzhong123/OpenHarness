# oh-api 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 OpenHarness 实现 REST API Server，使 Accio Frontend 能够通过 HTTP/SSE 调用 OpenHarness 的完整 Agent 能力

**Architecture:** 独立 pip 包 `oh-api`，通过 Python 导入使用 OpenHarness 核心模块，不修改官方代码。FastAPI + SSE 流式响应 + WebSocket 权限审批。

**Tech Stack:** Python 3.10+, FastAPI, sse-starlette, openharness (官方包)

---

## 文件结构

```
oh-api/
├── pyproject.toml
├── README.md
├── src/
│   └── oh_api/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   ├── sessions.py
│       │   ├── tools.py
│       │   └── skills.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── requests.py
│       │   ├── responses.py
│       │   └── events.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── agent_service.py
│       │   ├── session_store.py
│       │   └── openharness_bridge.py
│       └── auth/
│           ├── __init__.py
│           └── api_key.py
└── tests/
    └── ...
```

---

## Task 1: 项目基础结构

**Files:**
- Create: `oh-api/pyproject.toml`
- Create: `oh-api/src/oh_api/__init__.py`
- Create: `oh-api/src/oh_api/config.py`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p oh-api/src/oh_api/{routes,models,services,auth}
mkdir -p oh-api/tests
```

- [ ] **Step 2: 创建 pyproject.toml**

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "oh-api"
version = "0.1.0"
description = "REST API Server for OpenHarness"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [
    { name = "Your Name", email = "your@email.com" }
]
dependencies = [
    "openharness>=0.1.6",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sse-starlette>=2.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]

[project.scripts]
oh-api = "oh_api.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/oh_api"]
```

- [ ] **Step 3: 创建 src/oh_api/__init__.py**

```python
"""oh-api: REST API Server for OpenHarness."""

__version__ = "0.1.0"
```

- [ ] **Step 4: 创建 config.py**

```python
"""Configuration management for oh-api."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="OPENHARNESS_API_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    host: str = "0.0.0.0"
    port: int = 8080
    api_key: str | None = None
    permission_mode: Literal["default", "plan", "full_auto"] = "default"
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: create oh-api project structure"
```

---

## Task 2: 数据模型

**Files:**
- Create: `oh-api/src/oh_api/models/__init__.py`
- Create: `oh-api/src/oh_api/models/requests.py`
- Create: `oh-api/src/oh_api/models/responses.py`
- Create: `oh-api/src/oh_api/models/events.py`

- [ ] **Step 1: 创建 models/__init__.py**

```python
"""Data models for oh-api."""

from oh_api.models.requests import ChatRequest, SessionCreateRequest, ToolExecuteRequest
from oh_api.models.responses import (
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    SessionListResponse,
    SessionResponse,
    SkillListResponse,
    ToolExecuteResponse,
)
from oh_api.models.events import SSEEvent

__all__ = [
    "ChatRequest",
    "SessionCreateRequest",
    "ToolExecuteRequest",
    "ChatResponse",
    "ErrorResponse",
    "HealthResponse",
    "SessionListResponse",
    "SessionResponse",
    "SkillListResponse",
    "ToolExecuteResponse",
    "SSEEvent",
]
```

- [ ] **Step 2: 创建 models/requests.py**

```python
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
```

- [ ] **Step 3: 创建 models/responses.py**

```python
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
```

- [ ] **Step 4: 创建 models/events.py**

```python
"""SSE event models."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any


class SSEEventType(str, Enum):
    """SSE event types."""

    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"
    PERMISSION_REQUEST = "permission_request"


class SSEEvent:
    """Server-Sent Event."""

    def __init__(
        self,
        event_type: SSEEventType,
        data: dict[str, Any],
    ):
        self.event_type = event_type
        self.data = data

    def to_sse(self) -> str:
        """Convert to SSE format."""
        json_data = json.dumps(self.data, ensure_ascii=False)
        return f"event: {self.event_type.value}\ndata: {json_data}\n\n"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.event_type.value,
            **self.data,
        }


def text_event(content: str) -> SSEEvent:
    """Create a text message event."""
    return SSEEvent(SSEEventType.MESSAGE, {"type": "text", "content": content})


def tool_call_event(tool: str, args: dict[str, Any]) -> SSEEvent:
    """Create a tool call event."""
    return SSEEvent(SSEEventType.TOOL_CALL, {"type": "tool_call", "tool": tool, "args": args})


def tool_result_event(tool: str, result: str, success: bool = True) -> SSEEvent:
    """Create a tool result event."""
    return SSEEvent(
        SSEEventType.TOOL_RESULT,
        {"type": "tool_result", "tool": tool, "result": result, "success": success},
    )


def done_event(session_id: str, usage: dict[str, int]) -> SSEEvent:
    """Create a done event."""
    return SSEEvent(
        SSEEventType.DONE,
        {"type": "done", "session_id": session_id, "usage": usage},
    )


def error_event(message: str) -> SSEEvent:
    """Create an error event."""
    return SSEEvent(SSEEventType.ERROR, {"type": "error", "message": message})
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add data models"
```

---

## Task 3: OpenHarness 桥接层

**Files:**
- Create: `oh-api/src/oh_api/services/__init__.py`
- Create: `oh-api/src/oh_api/services/openharness_bridge.py`

- [ ] **Step 1: 创建 services/__init__.py**

```python
"""Services for oh-api."""

from oh_api.services.agent_service import AgentService
from oh_api.services.session_store import SessionStore
from oh_api.services.openharness_bridge import OpenHarnessBridge

__all__ = ["AgentService", "SessionStore", "OpenHarnessBridge"]
```

- [ ] **Step 2: 创建 openharness_bridge.py**

```python
"""Bridge layer to OpenHarness core modules."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator

from openharness.api.client import ApiMessageRequest, ApiStreamEvent
from openharness.api.provider import create_api_client
from openharness.auth.manager import AuthManager
from openharness.config.settings import load_settings
from openharness.engine.query_engine import QueryEngine
from openharness.engine.stream_events import StreamEvent
from openharness.permissions.checker import PermissionChecker, PermissionMode
from openharness.skills import load_skill_registry
from openharness.tools import create_default_tool_registry

log = logging.getLogger(__name__)


class OpenHarnessBridge:
    """Bridge to OpenHarness core capabilities."""

    def __init__(
        self,
        cwd: str | Path = ".",
        permission_mode: str = "default",
    ):
        self._cwd = Path(cwd).resolve()
        self._settings = load_settings()
        self._auth_manager = AuthManager()
        self._tool_registry = create_default_tool_registry()
        self._permission_checker = PermissionChecker(
            mode=PermissionMode(permission_mode),
            cwd=self._cwd,
        )

    def create_query_engine(
        self,
        model: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
    ) -> QueryEngine:
        """Create a QueryEngine instance."""
        profile = self._auth_manager.get_active_profile()
        api_client = create_api_client(
            profile=profile,
            auth_manager=self._auth_manager,
        )

        return QueryEngine(
            api_client=api_client,
            tool_registry=self._tool_registry,
            permission_checker=self._permission_checker,
            cwd=self._cwd,
            model=model or profile.resolved_model,
            system_prompt=system_prompt or "",
            max_tokens=max_tokens,
        )

    def list_tools(self) -> list[dict[str, str]]:
        """List all available tools."""
        tools = []
        for name, tool in self._tool_registry._tools.items():
            tools.append({
                "name": name,
                "description": tool.description or "",
            })
        return tools

    def list_skills(self) -> list[dict[str, str]]:
        """List all available skills."""
        try:
            registry = load_skill_registry()
            skills = []
            for skill in registry.list_skills():
                skills.append({
                    "name": skill.name,
                    "description": skill.description or "",
                })
            return skills
        except Exception as e:
            log.warning(f"Failed to load skills: {e}")
            return []

    async def stream_chat(
        self,
        engine: QueryEngine,
        message: str,
        stream_callback,
    ) -> dict[str, Any]:
        """Stream chat response from QueryEngine."""
        from openharness.engine.messages import ConversationMessage, TextBlock

        messages = engine.messages + [
            ConversationMessage(role="user", content=[TextBlock(text=message)])
        ]

        try:
            usage_data = {"input_tokens": 0, "output_tokens": 0}

            async for event in engine.stream(messages):
                if isinstance(event, StreamEvent):
                    event_dict = event.to_dict()
                    event_type = event_dict.get("type", "")

                    if event_type == "text_delta":
                        content = event_dict.get("text", "")
                        if content:
                            stream_callback(text_event(content))
                    elif event_type == "tool_use":
                        tool_name = event_dict.get("tool_name", "")
                        tool_args = event_dict.get("tool_args", {})
                        stream_callback(tool_call_event(tool_name, tool_args))
                    elif event_type == "tool_result":
                        tool_name = event_dict.get("tool_name", "")
                        result = event_dict.get("result", "")
                        success = event_dict.get("success", True)
                        stream_callback(tool_result_event(tool_name, result, success))
                    elif event_type == "turn_complete":
                        usage = event_dict.get("usage", {})
                        usage_data = {
                            "input_tokens": usage.get("input_tokens", 0),
                            "output_tokens": usage.get("output_tokens", 0),
                        }

            stream_callback(done_event("", usage_data))
            return usage_data

        except Exception as e:
            log.error(f"Chat error: {e}")
            stream_callback(error_event(str(e)))
            raise

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a single tool."""
        tool = self._tool_registry.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}

        try:
            import asyncio
            from openharness.tools.base import ToolExecutionContext

            context = ToolExecutionContext(
                tool_name=tool_name,
                arguments=args,
                cwd=self._cwd,
            )

            result = asyncio.run(tool.execute(args, context))
            return {"success": True, "result": result.output}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add OpenHarness bridge layer"
```

---

## Task 4: 会话存储

**Files:**
- Create: `oh-api/src/oh_api/services/session_store.py`

- [ ] **Step 1: 创建 session_store.py**

```python
"""Session storage for oh-api."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from oh_api.models.requests import ChatRequest, SessionCreateRequest


class SessionStore:
    """In-memory session store with optional persistence."""

    def __init__(self, storage_dir: Path | None = None):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._storage_dir = storage_dir
        if storage_dir:
            storage_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, request: SessionCreateRequest | None = None) -> dict[str, Any]:
        """Create a new session."""
        session_id = uuid4().hex[:12]
        now = time.time()

        session = {
            "id": session_id,
            "model": request.model if request else None,
            "system_prompt": request.system_prompt if request else None,
            "messages": [],
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }

        self._sessions[session_id] = session
        self._persist_session(session)
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session by ID."""
        if session_id in self._sessions:
            return self._sessions[session_id]

        if self._storage_dir:
            path = self._storage_dir / f"{session_id}.json"
            if path.exists():
                try:
                    with open(path) as f:
                        session = json.load(f)
                        self._sessions[session_id] = session
                        return session
                except Exception:
                    pass
        return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions."""
        sessions = []
        for session in self._sessions.values():
            sessions.append({
                "id": session["id"],
                "created_at": datetime.fromtimestamp(session["created_at"]),
                "updated_at": datetime.fromtimestamp(session["updated_at"]) if session.get("updated_at") else None,
                "message_count": session.get("message_count", 0),
                "model": session.get("model"),
            })
        return sessions

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session."""
        session = self.get_session(session_id)
        if session:
            session["messages"].append({
                "role": role,
                "content": content,
            })
            session["message_count"] = len(session["messages"])
            session["updated_at"] = time.time()
            self._persist_session(session)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

        if self._storage_dir:
            path = self._storage_dir / f"{session_id}.json"
            if path.exists():
                path.unlink()
                return True
        return False

    def _persist_session(self, session: dict[str, Any]) -> None:
        """Persist session to disk."""
        if self._storage_dir:
            path = self._storage_dir / f"{session['id']}.json"
            with open(path, "w") as f:
                json.dump(session, f, indent=2, default=str)
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: add session store"
```

---

## Task 5: Agent Service

**Files:**
- Create: `oh-api/src/oh_api/services/agent_service.py`

- [ ] **Step 1: 创建 agent_service.py**

```python
"""Agent service for oh-api."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from oh_api.config import get_settings
from oh_api.models.events import SSEEvent
from oh_api.services.openharness_bridge import OpenHarnessBridge
from oh_api.services.session_store import SessionStore

log = logging.getLogger(__name__)


class AgentService:
    """Service for managing agent interactions."""

    def __init__(
        self,
        session_store: SessionStore | None = None,
        bridge: OpenHarnessBridge | None = None,
    ):
        self._session_store = session_store or SessionStore()
        settings = get_settings()
        self._bridge = bridge or OpenHarnessBridge(
            permission_mode=settings.permission_mode,
        )

    def create_session(self, model: str | None = None, system_prompt: str | None = None) -> dict[str, Any]:
        """Create a new session."""
        from oh_api.models.requests import SessionCreateRequest

        request = SessionCreateRequest(model=model, system_prompt=system_prompt)
        session = self._session_store.create_session(request)
        return {
            "id": session["id"],
            "created_at": session["created_at"],
        }

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions."""
        return self._session_store.list_sessions()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session with messages."""
        session = self._session_store.get_session(session_id)
        if not session:
            return None

        from datetime import datetime

        return {
            "session": {
                "id": session["id"],
                "created_at": datetime.fromtimestamp(session["created_at"]),
                "updated_at": datetime.fromtimestamp(session["updated_at"]) if session.get("updated_at") else None,
                "message_count": session.get("message_count", 0),
                "model": session.get("model"),
            },
            "messages": session.get("messages", []),
        }

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return self._session_store.delete_session(session_id)

    async def chat_stream(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        stream_callback: Callable[[SSEEvent], None] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Stream chat response."""
        if not session_id:
            session = self._session_store.create_session(
                type("Request", (), {"model": model, "system_prompt": system_prompt})()
            )
            session_id = session["id"]
        else:
            session = self._session_store.get_session(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")

        engine = self._bridge.create_query_engine(
            model=model or session.get("model"),
            system_prompt=system_prompt or session.get("system_prompt"),
        )

        self._session_store.add_message(session_id, "user", message)

        def callback(event: SSEEvent) -> None:
            if stream_callback:
                stream_callback(event)

        usage = await self._bridge.stream_chat(engine, message, callback)

        return session_id, usage

    def list_tools(self) -> list[dict[str, str]]:
        """List available tools."""
        return self._bridge.list_tools()

    def list_skills(self) -> list[dict[str, str]]:
        """List available skills."""
        return self._bridge.list_skills()

    def execute_tool(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool."""
        return self._bridge.execute_tool(tool, args)
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: add agent service"
```

---

## Task 6: API 路由

**Files:**
- Create: `oh-api/src/oh_api/routes/__init__.py`
- Create: `oh-api/src/oh_api/routes/chat.py`
- Create: `oh-api/src/oh_api/routes/sessions.py`
- Create: `oh-api/src/oh_api/routes/tools.py`
- Create: `oh-api/src/oh_api/routes/skills.py`

- [ ] **Step 1: 创建 routes/__init__.py**

```python
"""API routes for oh-api."""

from fastapi import APIRouter

from oh_api.routes import chat, sessions, skills, tools

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(tools.router, tags=["tools"])
api_router.include_router(skills.router, tags=["skills"])

__all__ = ["api_router"]
```

- [ ] **Step 2: 创建 routes/chat.py**

```python
"""Chat endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from oh_api.models.events import SSEEvent, done_event, error_event
from oh_api.models.requests import ChatRequest
from oh_api.services.agent_service import AgentService

router = APIRouter()

_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get or create agent service singleton."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


async def chat_events(request: ChatRequest):
    """Generate SSE events for chat."""
    service = get_agent_service()

    events = []

    def collect_event(event: SSEEvent):
        events.append(event)

    try:
        session_id, usage = await service.chat_stream(
            message=request.message,
            session_id=request.session_id,
            model=request.model,
            system_prompt=request.system_prompt,
            stream_callback=collect_event,
        )

        yield {
            "event": "done",
            "data": f'{{"type": "done", "session_id": "{session_id}"}}',
        }

    except Exception as e:
        yield {
            "event": "error",
            "data": f'{{"type": "error", "message": "{str(e)}"}}',
        }


@router.post("/chat")
async def chat(request: ChatRequest):
    """Send a chat message and stream response."""
    if request.stream:
        return EventSourceResponse(chat_events(request))

    service = get_agent_service()
    try:
        session_id, usage = await service.chat_stream(
            message=request.message,
            session_id=request.session_id,
            model=request.model,
            system_prompt=request.system_prompt,
        )
        return {"session_id": session_id, "usage": usage}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: 创建 routes/sessions.py**

```python
"""Session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from oh_api.models.responses import SessionListResponse, SessionResponse
from oh_api.models.requests import SessionCreateRequest
from oh_api.services.agent_service import AgentService

router = APIRouter()

_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get or create agent service singleton."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions():
    """List all sessions."""
    service = get_agent_service()
    sessions = service.list_sessions()
    return SessionListResponse(sessions=sessions)


@router.post("/sessions", response_model=dict)
def create_session(request: SessionCreateRequest | None = None):
    """Create a new session."""
    service = get_agent_service()
    session = service.create_session(
        model=request.model if request else None,
        system_prompt=request.system_prompt if request else None,
    )
    return session


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """Get session details."""
    service = get_agent_service()
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session."""
    service = get_agent_service()
    if not service.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}
```

- [ ] **Step 4: 创建 routes/tools.py**

```python
"""Tool endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from oh_api.models.requests import ToolExecuteRequest
from oh_api.models.responses import ToolExecuteResponse
from oh_api.services.agent_service import AgentService

router = APIRouter()

_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get or create agent service singleton."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


@router.post("/tools/execute", response_model=ToolExecuteResponse)
def execute_tool(request: ToolExecuteRequest):
    """Execute a tool."""
    service = get_agent_service()
    result = service.execute_tool(request.tool, request.args)
    return ToolExecuteResponse(
        success=result.get("success", False),
        result=result.get("result"),
        error=result.get("error"),
    )
```

- [ ] **Step 5: 创建 routes/skills.py**

```python
"""Skills endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from oh_api.models.responses import SkillListResponse
from oh_api.services.agent_service import AgentService

router = APIRouter()

_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get or create agent service singleton."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


@router.get("/skills", response_model=SkillListResponse)
def list_skills():
    """List all available skills."""
    service = get_agent_service()
    skills = service.list_skills()
    return SkillListResponse(skills=skills)
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: add API routes"
```

---

## Task 7: 主入口和认证

**Files:**
- Create: `oh-api/src/oh_api/auth/__init__.py`
- Create: `oh-api/src/oh_api/auth/api_key.py`
- Create: `oh-api/src/oh_api/main.py`

- [ ] **Step 1: 创建 auth/__init__.py**

```python
"""Authentication for oh-api."""

from oh_api.auth.api_key import api_key_auth

__all__ = ["api_key_auth"]
```

- [ ] **Step 2: 创建 auth/api_key.py**

```python
"""API Key authentication."""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from oh_api.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def api_key_auth(api_key: str | None = Security(api_key_header)) -> str | None:
    """Validate API key."""
    settings = get_settings()

    if settings.api_key is None:
        return None

    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key required. Set X-API-Key header or OPENHARNESS_API_KEY env var.",
        )

    if api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key
```

- [ ] **Step 3: 创建 main.py**

```python
"""Main FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oh_api import __version__
from oh_api.config import get_settings
from oh_api.models.responses import HealthResponse
from oh_api.routes import api_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    log.info("Starting oh-api...")
    yield
    log.info("Shutting down oh-api...")


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title="oh-api",
        description="REST API Server for OpenHarness",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
    async def health():
        """Health check endpoint."""
        return HealthResponse(status="ok", version=__version__)

    return app


app = create_app()


def main():
    """Run the application."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "oh_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: add main entry point and auth"
```

---

## Task 8: README

**Files:**
- Create: `oh-api/README.md`

- [ ] **Step 1: 创建 README.md**

```markdown
# oh-api

REST API Server for OpenHarness - 使 Accio Frontend 能够通过 HTTP/SSE 调用 OpenHarness 的完整 Agent 能力。

## 特性

- **流式响应**: SSE (Server-Sent Events) 支持实时流式输出
- **会话管理**: 支持多会话、会话历史、会话恢复
- **完整 Agent**: 工具调用、Skills、多 Agent 协调
- **权限审批**: WebSocket 实时权限审批
- **插件化架构**: 独立 pip 包，不修改官方 OpenHarness 代码

## 安装

```bash
# 本地开发安装
pip install -e .

# 或安装发布版本
pip install oh-api
```

## 快速开始

### 启动服务

```bash
oh-api
# 或
python -m oh_api.main
```

默认端口 8080，可通过环境变量配置：

```bash
export OPENHARNESS_API_PORT=9000
oh-api
```

### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/chat` | POST | 发送消息 (SSE 流式) |
| `/api/v1/sessions` | GET | 列出会话 |
| `/api/v1/sessions` | POST | 创建会话 |
| `/api/v1/sessions/:id` | GET | 获取会话 |
| `/api/v1/sessions/:id` | DELETE | 删除会话 |
| `/api/v1/tools/execute` | POST | 执行工具 |
| `/api/v1/skills` | GET | 列出 Skills |

### 使用示例

```bash
# 健康检查
curl http://localhost:8080/api/v1/health

# 发送消息 (流式)
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "stream": true}'

# 列出会话
curl http://localhost:8080/api/v1/sessions

# 列出工具
curl http://localhost:8080/api/v1/tools

# 列出 Skills
curl http://localhost:8080/api/v1/skills
```

## 配置

| 环境变量 | 默认值 | 描述 |
|----------|--------|------|
| `OPENHARNESS_API_HOST` | 0.0.0.0 | 监听地址 |
| `OPENHARNESS_API_PORT` | 8080 | 端口 |
| `OPENHARNESS_API_KEY` | (无) | API 密钥 |
| `OPENHARNESS_PERMISSION_MODE` | default | 权限模式 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行服务
python -m oh_api.main
```

## 架构

```
oh-api/
├── main.py          # FastAPI 应用入口
├── config.py        # 配置管理
├── routes/          # API 路由
├── models/          # 数据模型
├── services/        # 业务逻辑
│   ├── agent_service.py       # Agent 服务
│   ├── session_store.py       # 会话存储
│   └── openharness_bridge.py   # OpenHarness 桥接层
└── auth/            # 认证
```

## 与 OpenHarness 独立升级

oh-api 作为独立 pip 包，依赖 `openharness >= 0.1.6`：

```bash
# 升级 OpenHarness
pip install --upgrade openharness

# 升级 oh-api
pip install --upgrade oh-api
```

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "docs: add README"
```

---

## Task 9: 基础测试

**Files:**
- Create: `oh-api/tests/__init__.py`
- Create: `oh-api/tests/test_models.py`
- Create: `oh-api/tests/test_routes.py`

- [ ] **Step 1: 创建 tests/__init__.py**

```python
"""Tests for oh-api."""
```

- [ ] **Step 2: 创建 tests/test_models.py**

```python
"""Tests for data models."""

import pytest
from pydantic import ValidationError

from oh_api.models.requests import ChatRequest, SessionCreateRequest, ToolExecuteRequest
from oh_api.models.events import SSEEvent, text_event, tool_call_event, done_event


def test_chat_request_valid():
    """Test valid chat request."""
    request = ChatRequest(message="Hello")
    assert request.message == "Hello"
    assert request.stream is True


def test_chat_request_with_session():
    """Test chat request with session."""
    request = ChatRequest(message="Hello", session_id="abc123", model="claude-3")
    assert request.session_id == "abc123"
    assert request.model == "claude-3"


def test_chat_request_empty_message():
    """Test chat request with empty message."""
    with pytest.raises(ValidationError):
        ChatRequest(message="")


def test_session_create_request():
    """Test session create request."""
    request = SessionCreateRequest(model="claude-3", system_prompt="You are helpful")
    assert request.model == "claude-3"
    assert request.system_prompt == "You are helpful"


def test_tool_execute_request():
    """Test tool execute request."""
    request = ToolExecuteRequest(tool="Read", args={"path": "test.txt"})
    assert request.tool == "Read"
    assert request.args == {"path": "test.txt"}


def test_sse_event_creation():
    """Test SSE event creation."""
    event = text_event("Hello world")
    assert event.event_type.value == "message"
    assert event.data["content"] == "Hello world"


def test_sse_event_to_sse():
    """Test SSE event to SSE format conversion."""
    event = tool_call_event("Read", {"path": "test.txt"})
    sse_output = event.to_sse()
    assert "event: tool_call" in sse_output
    assert '"tool": "Read"' in sse_output


def test_done_event():
    """Test done event creation."""
    event = done_event("session123", {"input_tokens": 100, "output_tokens": 50})
    assert event.event_type.value == "done"
    assert event.data["session_id"] == "session123"
```

- [ ] **Step 3: 创建 tests/test_routes.py**

```python
"""Tests for API routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from oh_api.main import create_app


@pytest.fixture
def app():
    """Create test app."""
    return create_app()


@pytest.mark.asyncio
async def test_health_endpoint(app):
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_list_sessions(app):
    """Test list sessions endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data


@pytest.mark.asyncio
async def test_create_session(app):
    """Test create session endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "created_at" in data


@pytest.mark.asyncio
async def test_get_session_not_found(app):
    """Test get session with invalid ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_skills(app):
    """Test list skills endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
```

- [ ] **Step 4: 运行测试验证**

```bash
cd oh-api
pip install -e ".[dev]"
pytest tests/ -v
```

预期输出: 测试应该通过

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "test: add basic tests"
```

---

## Task 10: 本地安装测试

- [ ] **Step 1: 安装并测试**

```bash
cd oh-api
pip install -e .

# 验证安装
python -c "from oh_api import __version__; print(f'oh-api version: {__version__}')"

# 测试导入
python -c "from oh_api.main import app; print('App created successfully')"
```

- [ ] **Step 2: 启动服务测试 (后台运行)**

```bash
timeout 5 python -m oh_api.main &
sleep 2

# 测试健康检查
curl http://localhost:8080/api/v1/health

# 测试列出会话
curl http://localhost:8080/api/v1/sessions

# 测试创建会话
curl -X POST http://localhost:8080/api/v1/sessions
```

预期输出: 服务正常响应

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "chore: verify local installation"
```

---

## 总结

完成以上 10 个 Task 后，oh-api 将具备：

1. **基础框架** - FastAPI 应用、健康检查、配置管理
2. **数据模型** - 请求/响应模型、SSE 事件模型
3. **OpenHarness 桥接层** - 封装 OpenHarness QueryEngine、工具注册表、Skills
4. **会话存储** - 内存会话存储 + 可选持久化
5. **Agent 服务** - 对话流处理、会话管理
6. **API 路由** - /chat, /sessions, /tools, /skills 端点
7. **主入口** - FastAPI 应用、API Key 认证
8. **文档** - README
9. **测试** - 基础单元测试
10. **安装验证** - 本地安装和运行测试

**下一步**: Accio Frontend Agent 面板开发（不在本计划范围内）
