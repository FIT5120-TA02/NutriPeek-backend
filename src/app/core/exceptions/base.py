"""Base exceptions module."""

from typing import Any, Dict, Optional


class ApplicationError(Exception):
    """Base exception for all application errors.

    Attributes:
        message: Error message.
        status_code: HTTP status code.
        details: Additional error details.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ApplicationError.

        Args:
            message: Error message.
            status_code: HTTP status code.
            details: Additional error details.
        """
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Validation error exception.

    Raised when input data fails validation.
    """

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message=message, status_code=400, details=details)


class AuthenticationError(ApplicationError):
    """Authentication error exception.

    Raised when authentication fails.
    """

    def __init__(
        self,
        message: str = "Authentication error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize AuthenticationError.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message=message, status_code=401, details=details)


class AuthorizationError(ApplicationError):
    """Authorization error exception.

    Raised when user is not authorized to perform an action.
    """

    def __init__(
        self,
        message: str = "Authorization error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize AuthorizationError.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message=message, status_code=403, details=details)


class NotFoundError(ApplicationError):
    """Not found error exception.

    Raised when a requested resource is not found.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize NotFoundError.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message=message, status_code=404, details=details)