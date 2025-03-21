"""Application setup module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api import api_router
from src.app.core.config import settings
from src.app.core.exceptions.handlers import add_exception_handlers
from src.app.core.logger import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    # Set up logging
    setup_logging()

    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="FastAPI backend for onboarding project",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    add_exception_handlers(app)

    # Include routers
    app.include_router(api_router, prefix="/api")

    return app
