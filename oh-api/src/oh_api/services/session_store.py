"""Session storage for oh-api."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class SessionStore:
    """In-memory session store with optional persistence."""

    def __init__(self, storage_dir: Path | None = None):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._storage_dir = storage_dir
        if storage_dir:
            storage_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self, model: str | None = None, system_prompt: str | None = None
    ) -> dict[str, Any]:
        """Create a new session."""
        session_id = uuid4().hex[:12]
        now = time.time()

        session = {
            "id": session_id,
            "model": model,
            "system_prompt": system_prompt,
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
            sessions.append(
                {
                    "id": session["id"],
                    "created_at": datetime.fromtimestamp(session["created_at"]),
                    "updated_at": datetime.fromtimestamp(session["updated_at"])
                    if session.get("updated_at")
                    else None,
                    "message_count": session.get("message_count", 0),
                    "model": session.get("model"),
                }
            )
        return sessions

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session."""
        session = self.get_session(session_id)
        if session:
            session["messages"].append(
                {
                    "role": role,
                    "content": content,
                }
            )
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
