"""Exception handlers module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from src.app.core.exceptions.base import ApplicationError


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to the application.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        request: Request, exc: ApplicationError
    ) -> JSONResponse:
        """Handle ApplicationError exceptions.

        Args:
            request: Request instance.
            exc: ApplicationError instance.

        Returns:
            JSON response with error details.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.message,
                    "details": exc.details or {},
                    "status_code": exc.status_code,
                }
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def handle_validation_error(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        """Handle Pydantic ValidationError exceptions.

        Args:
            request: Request instance.
            exc: ValidationError instance.

        Returns:
            JSON response with error details.
        """
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": "Validation error",
                    "details": {"errors": exc.errors()},
                    "status_code": 400,
                }
            },
        )