"""Tests for API routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from oh_api.main import create_app


@pytest.fixture
def app():
    """Create test app."""
    return create_app()


@pytest.mark.asyncio
async def test_health_endpoint(app):
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_list_sessions(app):
    """Test list sessions endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data


@pytest.mark.asyncio
async def test_create_session(app):
    """Test create session endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "created_at" in data


@pytest.mark.asyncio
async def test_get_session_not_found(app):
    """Test get session with invalid ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_skills(app):
    """Test list skills endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
