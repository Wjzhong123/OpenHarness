"""API routes for oh-api."""

from fastapi import APIRouter

from oh_api.routes import chat, sessions, skills, tools

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(tools.router, tags=["tools"])
api_router.include_router(skills.router, tags=["skills"])

__all__ = ["api_router"]
