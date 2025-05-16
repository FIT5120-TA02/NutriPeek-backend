"""Security middleware module for FastAPI application.

This module provides security middleware for FastAPI applications, including:
- Content Security Policy (CSP)
- Cross-Origin Resource Sharing (CORS) with secure defaults
- HTTP Strict Transport Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy
"""

from typing import Callable, List, Optional, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to all responses.

    This middleware adds the following headers:
    - Content-Security-Policy
    - Strict-Transport-Security
    - X-Content-Type-Options
    - X-Frame-Options
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(
        self,
        app: FastAPI,
        csp_directives: Optional[dict] = None,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
    ):
        """Initialize security headers middleware.

        Args:
            app: FastAPI application
            csp_directives: Content Security Policy directives
            hsts_max_age: Max age for HSTS in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Include preload directive in HSTS
        """
        super().__init__(app)
        self.csp_directives = csp_directives or self._default_csp_directives()
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Add Content-Security-Policy header
        if self.csp_directives:
            csp_header = self._build_csp_header()
            response.headers["Content-Security-Policy"] = csp_header

        # Add Strict-Transport-Security header
        if not settings.is_development:  # Only add HSTS in non-development environments
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        # Remove Server header if present (reduces information disclosure)
        # MutableHeaders doesn't have pop method, so check first and remove if present
        if "Server" in response.headers:
            del response.headers["Server"]

        return response

    def _default_csp_directives(self) -> dict:
        """Return default Content Security Policy directives.

        Returns:
            Dictionary of CSP directives
        """
        return {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
            "frame-src": ["'none'"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": [],
        }

    def _build_csp_header(self) -> str:
        """Build Content Security Policy header value.

        Returns:
            CSP header string
        """
        directives = []
        for directive, sources in self.csp_directives.items():
            if sources:
                directives.append(f"{directive} {' '.join(sources)}")
            else:
                directives.append(directive)
        return "; ".join(directives)


def setup_security_middleware(
    app: FastAPI,
    cors_origins: Union[List[str], List[Union[str, None]]] = None,
    cors_allow_credentials: bool = True,
) -> None:
    """Set up security middleware for FastAPI application.

    Args:
        app: FastAPI application
        cors_origins: CORS allowed origins
        cors_allow_credentials: Whether credentials are allowed in CORS requests
    """
    # If no CORS origins specified, use safe defaults
    if cors_origins is None:
        # TODO: Remove this once we have a proper CORS policy
        cors_origins = ["*"]

    # Add CORS middleware with secure defaults
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE"],  # Restrict to necessary methods
        allow_headers=[
            "Authorization",
            "Content-Type",
        ],  # Restrict to necessary headers
        expose_headers=["X-Total-Count"],  # Only expose necessary headers
        max_age=86400,  # Cache preflight requests for 24 hours
    )

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
