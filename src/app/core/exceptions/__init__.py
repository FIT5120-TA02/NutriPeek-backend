"""Custom exceptions package."""

from src.app.core.exceptions.base import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from src.app.core.exceptions.custom import (
    FoodMappingError,
    InvalidImageError,
    InvalidRequestError,
    ModelLoadError,
    ProcessingError,
    ResourceNotFoundError,
)

__all__ = [
    "ApplicationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "FoodMappingError",
    "InvalidImageError",
    "InvalidRequestError",
    "ModelLoadError",
    "ProcessingError",
    "ResourceNotFoundError",
]
