"""Agent service for oh-api."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

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

    def create_session(
        self, model: str | None = None, system_prompt: str | None = None
    ) -> dict[str, Any]:
        """Create a new session."""
        session = self._session_store.create_session(
            model=model,
            system_prompt=system_prompt,
        )
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

        return {
            "session": {
                "id": session["id"],
                "created_at": datetime.fromtimestamp(session["created_at"]),
                "updated_at": datetime.fromtimestamp(session["updated_at"])
                if session.get("updated_at")
                else None,
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
        stream_callback: Callable[[SSEEvent], None]
        | Callable[[SSEEvent], Awaitable[None]]
        | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Stream chat response."""
        if not session_id:
            session = self._session_store.create_session(
                model=model,
                system_prompt=system_prompt,
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

        async def callback(event: SSEEvent) -> None:
            if stream_callback:
                import inspect

                if inspect.iscoroutinefunction(stream_callback):
                    await stream_callback(event)
                else:
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
