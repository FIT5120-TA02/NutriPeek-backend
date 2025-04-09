"""Nutrient API endpoints for calculating nutritional gaps."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.core.exceptions.custom import ResourceNotFoundError
from src.app.schemas.nutrient import NutrientGapRequest, NutrientGapResponse
from src.app.services.nutrient_service import nutrient_service

router = APIRouter(prefix="/nutrient", tags=["nutrient"])


@router.post(
    "/calculate-gap",
    response_model=NutrientGapResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate nutritional gaps for a child",
    description="Calculate the nutritional gaps between recommended intake and what's provided by selected ingredients",
    responses={
        404: {
            "description": "Ingredient not found or no recommended intake for age/gender"
        },
        500: {"description": "Internal server error"},
    },
)
async def calculate_nutrient_gap(
    request: NutrientGapRequest,
    db: AsyncSession = Depends(get_async_db),
) -> NutrientGapResponse:
    """Calculate nutritional gaps for a child based on their profile and chosen ingredients.

    This endpoint compares the nutritional content of the selected ingredients
    with the recommended daily intake for the child's age and gender, and
    calculates the gaps for each nutrient.

    Args:
        request: Request containing child profile and ingredient IDs
        db: Database session dependency

    Returns:
        Nutritional gap information for each nutrient

    Raises:
        HTTPException: If ingredients are not found or if there's no recommended
            intake data for the child's age and gender
    """
    try:
        # Get child profile data
        age = request.child_profile.age
        gender = request.child_profile.gender

        # Validate gender value
        if gender not in ["boy", "girl"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gender must be either 'boy' or 'girl'",
            )

        # Use the nutrient service to calculate the nutrient gaps
        return await nutrient_service.calculate_nutrient_gaps(
            db, age=age, gender=gender, ingredient_ids=request.ingredient_ids
        )

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating nutrient gaps: {str(e)}",
        )
