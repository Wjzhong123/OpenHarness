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


@router.get("/tools", tags=["tools"])
def list_tools():
    """List all available tools."""
    service = get_agent_service()
    return {"tools": service.list_tools()}


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
