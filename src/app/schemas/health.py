"""Health check schemas."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check response schema.

    Attributes:
        status: Overall health status.
        version: Application version.
        environment: Environment name.
        timestamp: Current timestamp.
        uptime: Response time in seconds.
        dependencies: Status of dependencies.
        system_info: System information.
    """

    status: str = Field(..., description="Overall health status of the application")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    timestamp: str = Field(..., description="Current timestamp in ISO format")
    uptime: Optional[float] = Field(None, description="Response time in seconds")
    dependencies: Dict[str, Any] = Field(
        ..., description="Status of application dependencies"
    )
    system_info: Optional[Dict[str, str]] = Field(
        None, description="System information"
    )
