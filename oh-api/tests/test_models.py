"""Tests for data models."""

import pytest
from pydantic import ValidationError

from oh_api.models.requests import ChatRequest, SessionCreateRequest, ToolExecuteRequest
from oh_api.models.events import SSEEvent, SSEEventType, text_event, tool_call_event, done_event


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
    assert event.event_type == SSEEventType.MESSAGE
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
    assert event.event_type == SSEEventType.DONE
    assert event.data["session_id"] == "session123"
