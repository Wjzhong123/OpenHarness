"""API Key authentication."""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from oh_api.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def api_key_auth(api_key: str | None = Security(api_key_header)) -> str | None:
    """Validate API key."""
    settings = get_settings()

    if settings.api_key is None:
        return None

    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key required. Set X-API-Key header or OPENHARNESS_API_KEY env var.",
        )

    if api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key
