"""Main FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oh_api import __version__
from oh_api.config import get_settings
from oh_api.models.responses import HealthResponse
from oh_api.routes import api_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    log.info("Starting oh-api...")
    yield
    log.info("Shutting down oh-api...")


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title="oh-api",
        description="REST API Server for OpenHarness",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
    async def health():
        """Health check endpoint."""
        return HealthResponse(status="ok", version=__version__)

    return app


app = create_app()


def main():
    """Run the application."""
    import uvicorn
    import sys

    settings = get_settings()
    reload = "--reload" in sys.argv
    uvicorn.run(
        "oh_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
