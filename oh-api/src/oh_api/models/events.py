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
    return SSEEvent(SSEEventType.MESSAGE, {"content": content})


def tool_call_event(tool: str, args: dict[str, Any]) -> SSEEvent:
    """Create a tool call event."""
    return SSEEvent(SSEEventType.TOOL_CALL, {"tool": tool, "args": args})


def tool_result_event(tool: str, result: str, success: bool = True) -> SSEEvent:
    """Create a tool result event."""
    return SSEEvent(
        SSEEventType.TOOL_RESULT,
        {"tool": tool, "result": result, "success": success},
    )


def done_event(session_id: str, usage: dict[str, int]) -> SSEEvent:
    """Create a done event."""
    return SSEEvent(
        SSEEventType.DONE,
        {"session_id": session_id, "usage": usage},
    )


def error_event(message: str) -> SSEEvent:
    """Create an error event."""
    return SSEEvent(SSEEventType.ERROR, {"message": message})
