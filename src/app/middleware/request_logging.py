"""Request logging middleware module.

This module provides middleware for logging requests and responses
with unique request IDs to help with security auditing and traceability.
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Get logger
logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses with request IDs.

    This middleware:
    - Assigns a unique request ID to each request
    - Logs request information (method, path, client IP, headers)
    - Logs response information (status code, processing time)
    - Adds the request ID to the response headers
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request, log details, and add request ID.

        Args:
            request: Incoming request
            call_next: Next middleware handler

        Returns:
            Response with request ID header
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for access in route handlers
        request.state.request_id = request_id

        # Get client IP (handling proxies)
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Log request details
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"| Client: {client_ip} | ID: {request_id}"
        )

        # Log detailed headers at debug level (sensitive info should be filtered)
        headers_dict = dict(request.headers.items())
        # Filter out sensitive headers
        for header in ["Authorization", "Cookie"]:
            if header in headers_dict:
                headers_dict[header] = "[FILTERED]"
        logger.debug(f"Request headers: {headers_dict}")

        # Process the request and measure time
        start_time = time.time()
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log response details
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"| Status: {response.status_code} "
                f"| Time: {process_time:.3f}s | ID: {request_id}"
            )

            return response
        except Exception as e:
            # Log exceptions
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"| Error: {str(e)} | Time: {process_time:.3f}s | ID: {request_id}"
            )
            raise


def setup_request_logging_middleware(app: FastAPI) -> None:
    """Set up request logging middleware for FastAPI application.

    Args:
        app: FastAPI application
    """
    app.add_middleware(RequestLoggingMiddleware)
