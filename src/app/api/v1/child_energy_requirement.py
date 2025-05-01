"""Child Energy Requirement API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.crud import child_energy_requirement
from src.app.schemas import FindNearestPALRequest, FindNearestPALResponse
from src.app.schemas.child_energy_requirement import Gender

router = APIRouter(
    prefix="/child-energy-requirements", tags=["child-energy-requirements"]
)


@router.post(
    "/find-nearest-pal",
    response_model=FindNearestPALResponse,
    status_code=status.HTTP_200_OK,
    summary="Find nearest PAL value and energy requirement",
    description="Given an input physical activity level (PAL), age, and gender, "
    "finds the nearest PAL value in the database and returns the "
    "corresponding estimated energy requirement.",
)
async def find_nearest_pal(
    request: FindNearestPALRequest, db: AsyncSession = Depends(get_async_db)
) -> FindNearestPALResponse:
    """Find nearest physical activity level and return the estimated energy requirement.

    Args:
        request: FindNearestPALRequest containing PAL, age, and gender
        db: Database session

    Returns:
        FindNearestPALResponse containing energy requirement information

    Raises:
        HTTPException: If no matching data is found or an error occurs
    """
    # Convert Gender enum to string value for database query
    gender_value = request.gender.value

    result = await child_energy_requirement.find_nearest_pal(
        db=db,
        target_pal=request.physical_activity_level,
        age=request.age,
        gender=gender_value,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No energy requirement data found for age {request.age}, "
            f"gender {gender_value} with closest PAL to {request.physical_activity_level}",
        )

    # Convert string gender from DB to Gender enum for response
    gender_enum = Gender(result.gender)

    return FindNearestPALResponse(
        input_physical_activity_level=request.physical_activity_level,
        matched_physical_activity_level=result.physical_activity_level,
        age=result.age,
        gender=gender_enum,
        unit=result.unit,
        estimated_energy_requirement=result.estimated_energy_requirement,
    )
