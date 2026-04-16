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
