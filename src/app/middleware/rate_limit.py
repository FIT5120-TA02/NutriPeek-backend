"""Rate limiting middleware module.

This module provides rate limiting middleware to protect against DoS attacks.
It uses a sliding window algorithm to track and limit request rates.
"""

import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Tuple

from fastapi import FastAPI, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests based on IP address.

    This middleware uses a sliding window algorithm to track request rates
    and limit requests exceeding the defined threshold.
    """

    def __init__(
        self,
        app: FastAPI,
        rate_limit_per_minute: int = 100,
        window_size: int = 60,  # 60 seconds window
        exclude_paths: list = None,
    ):
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            rate_limit_per_minute: Maximum requests per minute
            window_size: Time window in seconds for rate limiting
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.window_size = window_size
        self.exclude_paths = exclude_paths or [
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ]

        # Track requests: IP -> deque of timestamps
        self.request_history: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=rate_limit_per_minute + 1)
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request, apply rate limiting, and pass to next middleware.

        Args:
            request: Incoming request
            call_next: Next middleware handler

        Returns:
            Response from next middleware

        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Skip rate limiting in development mode or for excluded paths
        if settings.is_development or any(
            request.url.path.startswith(path) for path in self.exclude_paths
        ):
            return await call_next(request)

        # Get client IP from forwarded header if behind proxy, else direct IP
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        if client_ip and "," in client_ip:  # Handle multiple IPs in X-Forwarded-For
            client_ip = client_ip.split(",")[0].strip()

        # Apply rate limiting
        is_rate_limited, retry_after = self._is_rate_limited(client_ip)
        if is_rate_limited:
            headers = {"Retry-After": str(retry_after)}
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers=headers,
            )

        # Process the request
        return await call_next(request)

    def _is_rate_limited(self, client_ip: str) -> Tuple[bool, int]:
        """Check if the client IP is rate limited.

        Args:
            client_ip: Client IP address

        Returns:
            Tuple of (is_rate_limited, retry_after_seconds)
        """
        now = time.time()
        request_history = self.request_history[client_ip]

        # Remove timestamps outside the window
        while request_history and request_history[0] < now - self.window_size:
            request_history.popleft()

        # Check if rate limit is exceeded
        if len(request_history) >= self.rate_limit:
            # Calculate time until oldest request expires from window
            oldest_timestamp = request_history[0]
            retry_after = int(self.window_size - (now - oldest_timestamp))
            return True, max(1, retry_after)  # Ensure retry_after is at least 1 second

        # Record this request
        request_history.append(now)
        return False, 0


def setup_rate_limit_middleware(
    app: FastAPI,
    rate_limit_per_minute: int = 100,
    exclude_paths: list = None,
) -> None:
    """Set up rate limiting middleware for FastAPI application.

    Args:
        app: FastAPI application
        rate_limit_per_minute: Maximum requests per minute
        exclude_paths: List of paths to exclude from rate limiting
    """
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit_per_minute=rate_limit_per_minute,
        exclude_paths=exclude_paths,
    )
