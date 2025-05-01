"""API endpoints for activity-related operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.crud.crud_activity_mety_levels import activity_mety_level_crud
from src.app.schemas.activity import (
    ActivitiesResponse,
    PALCalculationRequest,
    PALCalculationResponse,
)
from src.app.services.activity_service import ActivityService

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get(
    "/activities",
    response_model=ActivitiesResponse,
    summary="Get list of available activities",
    description="Returns a list of all distinct activities available in the database",
    responses={
        500: {"description": "Internal server error"},
    },
)
async def get_activities(
    db: AsyncSession = Depends(get_async_db),
) -> ActivitiesResponse:
    """Get list of all available activities.

    Args:
        db: Database session

    Returns:
        List of activity names

    Raises:
        HTTPException: If an error occurs during database retrieval
    """
    try:
        activities = await activity_mety_level_crud.get_distinct_activities(db)
        return ActivitiesResponse(activities=activities)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving activities: {str(e)}",
        )


@router.post(
    "/calculate-pal",
    response_model=PALCalculationResponse,
    summary="Calculate Physical Activity Level (PAL)",
    description=(
        "Calculates the Physical Activity Level (PAL) based on "
        "age and a list of activities with their durations.\n\n"
        "PAL = Sum of (METy x duration for each activity) ÷ Total minutes in a day (1440)"
    ),
    responses={
        400: {"description": "Bad request"},
        404: {"description": "Activity not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def calculate_pal(
    request: PALCalculationRequest,
    db: AsyncSession = Depends(get_async_db),
) -> PALCalculationResponse:
    """Calculate Physical Activity Level (PAL) based on activities and their durations.

    Args:
        request: PALCalculationRequest with age and activities
        db: Database session

    Returns:
        PALCalculationResponse with calculated PAL and details

    Raises:
        HTTPException: If input validation fails or activities are not found
    """
    try:
        # Validate request
        if not request.activities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one activity must be provided",
            )

        activities_dict = [
            {"name": activity.name, "hours": activity.hours}
            for activity in request.activities
        ]

        # Create service with db session
        activity_service = ActivityService(db)

        result = await activity_service.calculate_physical_activity_level(
            request.age, activities_dict
        )

        return PALCalculationResponse(
            pal=result["pal"],
            total_mety_minutes=result["total_mety_minutes"],
            details=result["details"],
        )
    except HTTPException:
        raise
    except Exception as e:
        # Handle service-level exceptions
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating PAL: {error_message}",
        )
