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
