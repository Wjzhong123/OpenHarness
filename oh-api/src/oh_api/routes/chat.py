"""Chat endpoint."""

from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from oh_api.models.events import SSEEvent
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
    import asyncio

    service = get_agent_service()
    session_id = None
    queue: asyncio.Queue[SSEEvent | None] = asyncio.Queue()

    async def collect_event(event: SSEEvent):
        await queue.put(event)

    async def event_generator():
        nonlocal session_id
        while True:
            event = await queue.get()
            if event is None:
                break
            yield {
                "event": event.event_type.value,
                "data": json.dumps(event.to_dict()),
            }

    async def run_chat():
        nonlocal session_id
        try:
            session_id, usage = await service.chat_stream(
                message=request.message,
                session_id=request.session_id,
                model=request.model,
                system_prompt=request.system_prompt,
                stream_callback=collect_event,
            )
        finally:
            await queue.put(None)

    chat_task = asyncio.create_task(run_chat())

    async for event in event_generator():
        yield event

    await chat_task


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
