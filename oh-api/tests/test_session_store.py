"""Tests for session store."""

import pytest

from oh_api.services.session_store import SessionStore


def test_create_session():
    """Test creating a new session."""
    store = SessionStore()
    session = store.create_session(model="claude-3")
    assert session["id"] is not None
    assert session["model"] == "claude-3"
    assert session["message_count"] == 0


def test_get_session():
    """Test getting a session."""
    store = SessionStore()
    session = store.create_session()
    retrieved = store.get_session(session["id"])
    assert retrieved is not None
    assert retrieved["id"] == session["id"]


def test_get_nonexistent_session():
    """Test getting a non-existent session."""
    store = SessionStore()
    result = store.get_session("nonexistent")
    assert result is None


def test_list_sessions():
    """Test listing sessions."""
    store = SessionStore()
    store.create_session()
    store.create_session()
    sessions = store.list_sessions()
    assert len(sessions) == 2


def test_add_message():
    """Test adding a message to session."""
    store = SessionStore()
    session = store.create_session()
    store.add_message(session["id"], "user", "Hello")
    store.add_message(session["id"], "assistant", "Hi there")
    updated = store.get_session(session["id"])
    assert len(updated["messages"]) == 2
    assert updated["message_count"] == 2


def test_delete_session():
    """Test deleting a session."""
    store = SessionStore()
    session = store.create_session()
    result = store.delete_session(session["id"])
    assert result is True
    assert store.get_session(session["id"]) is None
