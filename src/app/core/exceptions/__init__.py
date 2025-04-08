"""Custom exceptions package."""

from src.app.core.exceptions.base import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from src.app.core.exceptions.custom import (
    InvalidImageError,
    ModelLoadError,
    ProcessingError,
)

__all__ = [
    "ApplicationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "InvalidImageError",
    "ModelLoadError",
    "ProcessingError",
]
