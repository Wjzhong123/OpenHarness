"""Bridge layer to OpenHarness core modules."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Awaitable, Callable

from openharness.config.settings import load_settings
from openharness.engine.query_engine import QueryEngine
from openharness.permissions.checker import PermissionChecker
from openharness.permissions.modes import PermissionMode
from openharness.skills import load_skill_registry
from openharness.tools import create_default_tool_registry

from oh_api.models.events import (
    SSEEvent,
    done_event,
    error_event,
    text_event,
    tool_call_event,
    tool_result_event,
)

log = logging.getLogger(__name__)


def _create_api_client_from_settings(settings):
    """Create API client from settings (same logic as runtime.py)."""

    def _safe_resolve_auth():
        try:
            return settings.resolve_auth()
        except (ValueError, Exception) as e:
            log.warning(f"No API key configured: {e}")
            return None

    nvidia_api_key = os.environ.get("NVIDIA_API_KEY", "")
    if nvidia_api_key:
        from openharness.api.openai_client import OpenAICompatibleClient

        return OpenAICompatibleClient(
            api_key=nvidia_api_key,
            base_url="https://integrate.api.nvidia.com/v1",
            timeout=settings.timeout if hasattr(settings, "timeout") else 120,
        )

    moonshot_api_key = os.environ.get("MOONSHOT_API_KEY", "")
    if moonshot_api_key:
        from openharness.api.openai_client import OpenAICompatibleClient

        model = settings.model or "moonshotai/kimi-k2.5"
        base_url = settings.base_url or "https://api.moonshot.cn/v1"
        return OpenAICompatibleClient(
            api_key=moonshot_api_key,
            base_url=base_url,
            timeout=settings.timeout if hasattr(settings, "timeout") else 120,
        )

    if settings.api_format == "copilot":
        from openharness.api.copilot_client import CopilotClient, COPILOT_DEFAULT_MODEL

        copilot_model = (
            COPILOT_DEFAULT_MODEL
            if settings.model
            in {"claude-sonnet-4-20250514", "claude-sonnet-4-6", "sonnet", "default"}
            else settings.model
        )
        return CopilotClient(model=copilot_model)

    if settings.provider == "openai_codex":
        from openharness.api.codex_client import CodexApiClient

        auth = _safe_resolve_auth()
        if auth:
            return CodexApiClient(
                auth_token=auth.value,
                base_url=settings.base_url,
            )
        return None

    if settings.provider == "anthropic_claude":
        from openharness.api.client import AnthropicApiClient

        auth = _safe_resolve_auth()
        if auth:
            return AnthropicApiClient(
                auth_token=auth.value,
                base_url=settings.base_url,
                claude_oauth=True,
                auth_token_resolver=lambda: settings.resolve_auth().value,
            )
        return None

    if settings.api_format == "openai":
        from openharness.api.openai_client import OpenAICompatibleClient

        auth = _safe_resolve_auth()
        if auth:
            return OpenAICompatibleClient(
                api_key=auth.value,
                base_url=settings.base_url,
                timeout=settings.timeout,
            )
        return None

    from openharness.api.client import AnthropicApiClient

    auth = _safe_resolve_auth()
    if auth:
        return AnthropicApiClient(
            api_key=auth.value,
            base_url=settings.base_url,
        )
    return None


TOOLS_TO_SKIP = set()

DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant. Always respond in Chinese (中文). If the user asks in English, still respond in Chinese. Use Chinese for all your responses, including when using tools and explaining results."


class OpenHarnessBridge:
    """Bridge to OpenHarness core capabilities."""

    def __init__(
        self,
        cwd: str | Path = ".",
        permission_mode: str = "full_auto",
    ):
        self._cwd = Path(cwd).resolve()
        self._settings = load_settings()
        self._tool_registry = create_default_tool_registry()
        for tool_name in TOOLS_TO_SKIP:
            self._tool_registry._tools.pop(tool_name, None)
        from openharness.config.settings import PermissionSettings

        permission_settings = PermissionSettings(mode=PermissionMode(permission_mode))
        self._permission_checker = PermissionChecker(
            settings=permission_settings,
        )

    def create_query_engine(
        self,
        model: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
    ) -> QueryEngine | None:
        """Create a QueryEngine instance."""
        profile_name, profile = self._settings.resolve_profile()
        api_client = _create_api_client_from_settings(self._settings)

        if api_client is None:
            log.warning("Failed to create API client, returning None")
            return None

        resolved_model = model or profile.resolved_model
        if os.environ.get("NVIDIA_API_KEY"):
            resolved_model = model or "meta/llama-3.1-8b-instruct"

        resolved_system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        return QueryEngine(
            api_client=api_client,
            tool_registry=self._tool_registry,
            permission_checker=self._permission_checker,
            cwd=self._cwd,
            model=resolved_model,
            system_prompt=resolved_system_prompt,
            max_tokens=max_tokens,
        )

    def list_tools(self) -> list[dict[str, str]]:
        """List all available tools."""
        tools = []
        for name, tool in self._tool_registry._tools.items():
            tools.append(
                {
                    "name": name,
                    "description": tool.description or "",
                }
            )
        return tools

    def list_skills(self) -> list[dict[str, str]]:
        """List all available skills."""
        try:
            registry = load_skill_registry()
            skills = []
            for skill in registry.list_skills():
                skills.append(
                    {
                        "name": skill.name,
                        "description": skill.description or "",
                    }
                )
            return skills
        except Exception as e:
            log.warning(f"Failed to load skills: {e}")
            return []

    async def stream_chat(
        self,
        engine: QueryEngine,
        message: str,
        stream_callback: Callable[[SSEEvent], None] | Callable[[SSEEvent], Awaitable[None]],
    ) -> dict[str, Any]:
        """Stream chat response from QueryEngine."""
        from openharness.engine.stream_events import (
            AssistantTextDelta,
            AssistantTurnComplete,
            ToolExecutionStarted,
            ToolExecutionCompleted,
            ErrorEvent,
            StatusEvent,
        )
        import inspect

        async def emit(event: SSEEvent) -> None:
            if inspect.iscoroutinefunction(stream_callback):
                await stream_callback(event)
            else:
                stream_callback(event)

        try:
            usage_data = {"input_tokens": 0, "output_tokens": 0}

            async for item in engine.submit_message(message):
                if isinstance(item, tuple):
                    event, usage = item
                else:
                    event = item
                    usage = None

                if isinstance(event, AssistantTextDelta):
                    if event.text:
                        await emit(text_event(event.text))
                elif isinstance(event, ToolExecutionStarted):
                    await emit(tool_call_event(event.tool_name, event.tool_input))
                elif isinstance(event, ToolExecutionCompleted):
                    await emit(tool_result_event(event.tool_name, event.output, not event.is_error))
                elif isinstance(event, AssistantTurnComplete):
                    if event.usage:
                        usage_data = {
                            "input_tokens": getattr(event.usage, "input_tokens", 0),
                            "output_tokens": getattr(event.usage, "output_tokens", 0),
                        }
                elif isinstance(event, ErrorEvent):
                    await emit(error_event(event.message))
                elif isinstance(event, StatusEvent):
                    if event.message:
                        await emit(text_event(f"\n[{event.message}]\n"))

            await emit(done_event("", usage_data))
            return usage_data

        except Exception as e:
            log.error(f"Chat error: {e}")
            await emit(error_event(str(e)))
            raise

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a single tool."""
        tool = self._tool_registry.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}

        try:
            import asyncio
            from openharness.tools.base import ToolExecutionContext

            context = ToolExecutionContext(
                cwd=self._cwd,
            )

            parsed_input = tool.input_model.model_validate(args)
            result = asyncio.run(tool.execute(parsed_input, context))
            return {"success": True, "result": result.output}
        except Exception as e:
            return {"success": False, "error": str(e)}
