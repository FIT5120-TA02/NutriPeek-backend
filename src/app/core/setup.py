"""Application setup module."""

from fastapi import FastAPI

from src.app.api import api_router
from src.app.core.config import settings
from src.app.core.exceptions.handlers import add_exception_handlers
from src.app.core.logger import setup_logging
from src.app.middleware.request_logging import setup_request_logging_middleware
from src.app.middleware.security import setup_security_middleware

# TODO: Uncomment when ready
# from src.app.middleware.injection_protection import (
#     setup_injection_protection_middleware,
# )
# from src.app.middleware.rate_limit import setup_rate_limit_middleware


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

    # Add request logging middleware (should be first to log all requests)
    setup_request_logging_middleware(app)

    # Add security middleware (includes CORS and security headers)
    setup_security_middleware(app)

    # TODO: Add SQL injection protection middleware
    # setup_injection_protection_middleware(
    #     app,
    #     exclude_paths=["/api/docs", "/api/redoc", "/api/openapi.json"],
    # )

    # TODO: Add rate limiting middleware
    # setup_rate_limit_middleware(
    #     app,
    #     rate_limit_per_minute=300,  # Adjust rate limit as needed
    #     exclude_paths=["/api/docs", "/api/redoc", "/api/openapi.json"],
    # )

    # Add exception handlers
    add_exception_handlers(app)

    # Include routers
    app.include_router(api_router, prefix="/api")

    return app
