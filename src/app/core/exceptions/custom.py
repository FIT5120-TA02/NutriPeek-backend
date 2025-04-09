"""Custom exceptions for application modules."""

from typing import Any, Dict, Optional

from src.app.core.exceptions.base import ApplicationError


class ModelLoadError(ApplicationError):
    """Exception raised when ML model fails to load.

    This could be due to missing model files, incompatible versions,
    or other issues related to loading machine learning models.
    """

    def __init__(
        self,
        message: str = "Failed to load ML model",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ModelLoadError.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message=message, status_code=500, details=details)


class ProcessingError(ApplicationError):
    """Exception raised when image or data processing fails.

    This could be due to corrupted images, unsupported formats,
    insufficient memory, or other processing related issues.
    """

    def __init__(
        self,
        message: str = "Failed to process image or data",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ProcessingError.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message=message, status_code=500, details=details)


class InvalidImageError(ApplicationError):
    """Exception raised when an invalid image is provided.

    This could be due to corrupted image data, unsupported format,
    or empty image file.
    """

    def __init__(
        self,
        message: str = "Invalid image provided",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize InvalidImageError.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message=message, status_code=400, details=details)
