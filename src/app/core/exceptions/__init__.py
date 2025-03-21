"""Custom exceptions package."""

from src.app.core.exceptions.base import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "ApplicationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
]