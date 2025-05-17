"""SQL injection protection middleware module.

This module provides middleware to scan request parameters and body
for common SQL injection patterns and block suspicious requests.
"""

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Pattern

from fastapi import FastAPI, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

# Get logger
logger = logging.getLogger("app.security")


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware for detecting and blocking SQL injection attempts.

    This middleware scans request parameters, path components, and request body
    for patterns commonly associated with SQL injection attacks.
    """

    def __init__(
        self,
        app: FastAPI,
        exclude_paths: Optional[List[str]] = None,
    ):
        """Initialize SQL injection protection middleware.

        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from checking
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ]
        self.sql_patterns = self._compile_sql_patterns()

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Process request, check for SQL injection patterns, and handle accordingly.

        Args:
            request: Incoming request
            call_next: Next middleware handler

        Returns:
            Response from next middleware

        Raises:
            HTTPException: If SQL injection pattern is detected
        """
        # Skip checks for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Check URL parameters
        query_params = dict(request.query_params)
        if query_params and self._check_dict_for_sql_injection(query_params):
            client_ip = request.headers.get("X-Forwarded-For", request.client.host)
            logger.warning(
                f"Potential SQL injection in query parameters from {client_ip}: "
                f"{request.url.path}?{request.url.query}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request parameters",
            )

        # Check path components
        path_components = request.url.path.split("/")
        for component in path_components:
            if component and self._check_string_for_sql_injection(component):
                client_ip = request.headers.get("X-Forwarded-For", request.client.host)
                logger.warning(
                    f"Potential SQL injection in path component from {client_ip}: "
                    f"{request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request path",
                )

        # Check request body for POST/PUT/PATCH requests
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                # Read request body
                body_bytes = await request.body()
                await request._receive()  # Reset stream position

                # Skip empty bodies
                if body_bytes:
                    # Check if body is JSON
                    try:
                        json_body = await request.json()
                        if isinstance(
                            json_body, dict
                        ) and self._check_dict_for_sql_injection(json_body):
                            client_ip = request.headers.get(
                                "X-Forwarded-For", request.client.host
                            )
                            logger.warning(
                                f"Potential SQL injection in request body from {client_ip}: "
                                f"{request.url.path}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid request body",
                            )
                    except json.JSONDecodeError:
                        # If body is not valid JSON, check raw content
                        if self._check_bytes_for_sql_injection(body_bytes):
                            client_ip = request.headers.get(
                                "X-Forwarded-For", request.client.host
                            )
                            logger.warning(
                                f"Potential SQL injection in non-JSON body from {client_ip}: "
                                f"{request.url.path}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid request body",
                            )
            except (RuntimeError, ValueError, TypeError) as e:
                # Catch specific exceptions that might occur during body parsing
                logger.debug(f"Error processing request body: {str(e)}")
                # Continue processing as this is not necessarily an attack

        # Process the request
        return await call_next(request)

    def _compile_sql_patterns(self) -> List[Pattern]:
        """Compile regex patterns for SQL injection detection.

        Returns:
            List of compiled regex patterns
        """
        # List of SQL injection patterns to detect
        patterns = [
            # Basic SQL commands
            r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b",
            # UNION-based SQL injection
            r"(?i)\bUNION\s+(ALL\s+)?SELECT\b",
            # Comments that might be used to terminate statements
            r"(?i)(--|#|\/\*).*(\bOR\b|\bAND\b)",
            # Boolean-based blind SQL injection
            r"(?i)'\s*(\|\||OR|\&\&|AND)\s*[0-9]+'?\s*=\s*[0-9]+'?",
            # Error-based SQL injection
            r"(?i)'\s*(;|--|#|\/\*|\+)",
            # Time-based blind SQL injection
            r"(?i)(SLEEP|BENCHMARK|PG_SLEEP|WAITFOR\s+DELAY)",
            # Other common SQL injection patterns
            r"(?i)(\%27|\')(\s|;|--)",
            r"(?i)((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
        ]

        # Compile patterns for better performance
        return [re.compile(pattern) for pattern in patterns]

    def _check_string_for_sql_injection(self, value: str) -> bool:
        """Check if a string contains SQL injection patterns.

        Args:
            value: String to check

        Returns:
            True if SQL injection pattern found, False otherwise
        """
        if not value:
            return False

        for pattern in self.sql_patterns:
            if pattern.search(value):
                return True

        return False

    def _check_bytes_for_sql_injection(self, value: bytes) -> bool:
        """Check if bytes contain SQL injection patterns.

        Args:
            value: Bytes to check

        Returns:
            True if SQL injection pattern found, False otherwise
        """
        if not value:
            return False

        try:
            # Try to decode bytes to string
            decoded_value = value.decode("utf-8")
            return self._check_string_for_sql_injection(decoded_value)
        except UnicodeDecodeError:
            # If decoding fails due to invalid Unicode, log and return False
            logger.debug("Failed to decode request body as UTF-8")
            return False

    def _check_dict_for_sql_injection(self, data: Dict) -> bool:
        """Recursively check dict values for SQL injection patterns.

        Args:
            data: Dictionary to check

        Returns:
            True if SQL injection pattern found, False otherwise
        """
        if not data:
            return False

        for key, value in data.items():
            # Check the key itself
            if isinstance(key, str) and self._check_string_for_sql_injection(key):
                return True

            # Check value based on type
            if isinstance(value, str) and self._check_string_for_sql_injection(value):
                return True
            elif isinstance(value, dict) and self._check_dict_for_sql_injection(value):
                return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and self._check_string_for_sql_injection(
                        item
                    ):
                        return True
                    elif isinstance(item, dict) and self._check_dict_for_sql_injection(
                        item
                    ):
                        return True

        return False


def setup_injection_protection_middleware(
    app: FastAPI,
    exclude_paths: Optional[List[str]] = None,
) -> None:
    """Set up SQL injection protection middleware for FastAPI application.

    Args:
        app: FastAPI application
        exclude_paths: List of paths to exclude from checking
    """
    app.add_middleware(
        SQLInjectionProtectionMiddleware,
        exclude_paths=exclude_paths,
    )
