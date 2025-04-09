"""Health check endpoints."""

import logging
import platform
import sys
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.app.core.config import settings
from src.app.core.db.session import get_db
from src.app.schemas.health import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health of the application and its dependencies.",
)
def health_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Check the health of the application and its dependencies.

    Args:
        db: Database session.

    Returns:
        Health status information.
    """
    start_time = datetime.now()

    # Check database connection
    db_status = "healthy"
    db_message = "Connected successfully"
    try:
        # Execute a simple query to check database connection
        db.execute(text("SELECT 1"))
        logger.info("Database health check passed")
    except Exception as e:
        db_status = "unhealthy"
        db_message = str(e)
        logger.warning(f"Database health check failed: {e}")

    # Calculate response time
    response_time = (datetime.now() - start_time).total_seconds()

    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now().isoformat(),
        uptime=response_time,
        dependencies={
            "database": {
                "status": db_status,
                "message": db_message,
            }
        },
        system_info={
            "python_version": sys.version,
            "platform": platform.platform(),
        },
    )


@router.get(
    "/ping",
    status_code=status.HTTP_200_OK,
    summary="Simple health check",
    description="Simple health check that doesn't require a database connection.",
)
def ping() -> dict:
    """Simple health check that doesn't require a database connection.

    Returns:
        Basic health status information.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
    }
