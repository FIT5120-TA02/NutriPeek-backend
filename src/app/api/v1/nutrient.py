"""Nutrient API endpoints for calculating nutritional gaps."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.core.exceptions.custom import ResourceNotFoundError
from src.app.schemas.food import (
    FoodRecommendation,
    OptimizedFoodRecommendation,
    OptimizedFoodRecommendationRequest,
    SeasonalFoodRecommendationRequest,
)
from src.app.schemas.nutrient import (
    ChildProfile,
    NutrientGapRequest,
    NutrientGapResponse,
    NutrientIntakeResponse,
)
from src.app.services.nutrient_service import nutrient_service

router = APIRouter(prefix="/nutrient", tags=["nutrient"])


@router.post(
    "/calculate-gap",
    response_model=NutrientGapResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate nutritional gaps for a child",
    description="Calculate the nutritional gaps between recommended intake and what's provided by selected ingredients",
    responses={
        422: {"description": "Validation error in request data"},
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


@router.post(
    "/nutrient-intake",
    response_model=NutrientIntakeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get required nutrient intake for a child",
    description="Get the required daily nutrient intake for a child based on their age and gender for key nutrients",
    responses={
        422: {"description": "Validation error in request data"},
        404: {"description": "No recommended intake for the specified age/gender"},
        500: {"description": "Internal server error"},
    },
)
async def get_nutrient_intake(
    child_profile: ChildProfile,
    db: AsyncSession = Depends(get_async_db),
) -> NutrientIntakeResponse:
    """Get the required daily nutrient intake for a child based on their profile.

    This endpoint returns the recommended daily intake for key nutrients
    (Energy, Protein, Total Fat, Carbohydrate, and Dietary Fibre)
    based on the child's age and gender.

    Args:
        child_profile: Child profile data with age and gender
        db: Database session dependency

    Returns:
        Required nutrient intake information for key nutrients

    Raises:
        HTTPException: If there's no recommended intake data for the child's age and gender
    """
    try:
        # Get child profile data
        age = child_profile.age
        gender = child_profile.gender

        # Use the nutrient service to get the required nutrient intake
        return await nutrient_service.get_required_nutrient_intake(
            db, age=age, gender=gender
        )

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving required nutrient intake: {str(e)}",
        )


@router.get(
    "/recommend-food",
    response_model=List[FoodRecommendation],
    status_code=status.HTTP_200_OK,
    summary="Recommend foods rich in a specific nutrient with complete nutritional profiles",
    description=(
        "Returns a list of food items with the highest values for the specified nutrient. "
        "The food_category is used for displaying icons in the frontend, while food_name "
        "provides the actual food name to be shown to users. "
        "Each food item includes its complete nutritional profile in the 'nutrients' field, "
        "allowing for comprehensive nutritional analysis beyond just the requested nutrient."
    ),
    responses={
        400: {"description": "Invalid nutrient column name provided"},
        422: {"description": "Validation error in request parameters"},
        500: {"description": "Internal server error"},
    },
)
async def recommend_food(
    nutrient_name: str = Query(
        ...,
        description="Column name of the nutrient (e.g., 'iron_mg', 'vitamin_c_mg', 'protein_g')",
        example="protein_g",
    ),
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of food recommendations to return"
    ),
    db: AsyncSession = Depends(get_async_db),
) -> List[FoodRecommendation]:
    """Recommend foods rich in a specific nutrient with their complete nutritional profiles.

    This endpoint analyzes the food database and returns food items
    that have the highest values for the specified nutrient along with
    their complete nutritional information.

    The response includes:
    - food_name: The actual name of the food for display
    - food_category: Category for icon representation in the frontend
    - nutrient_value: Value of the specified nutrient used for sorting
    - nutrients: A dictionary containing all available nutritional information

    This comprehensive data allows users to consider the complete nutritional
    profile of each food, not just its content of the selected nutrient.

    Args:
        nutrient_name: Column name of the nutrient (e.g., 'iron_mg')
        limit: Maximum number of results to return
        db: Database session dependency

    Returns:
        List of food recommendations with their IDs, names, categories,
        nutrient values, and complete nutritional profiles.

    Raises:
        HTTPException 400: If the nutrient column is invalid
        HTTPException 500: If there's an unexpected error retrieving the data
    """
    try:
        return await nutrient_service.recommend_food_by_nutrient(
            db=db,
            nutrient_column=nutrient_name,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recommend food: {str(e)}",
        )


@router.post(
    "/recommend-optimized-food",
    response_model=List[OptimizedFoodRecommendation],
    status_code=status.HTTP_200_OK,
    summary="Recommend foods optimized to fill a specific nutrient gap",
    description=(
        "Returns foods with nutrient amounts that most efficiently help reach the target "
        "nutrient level. Each recommendation includes how much of the food would be needed "
        "to close the gap and what percentage of the gap it satisfies with a standard serving. "
        "Foods are ranked by how practical they are to consume, prioritizing those that can "
        "satisfy the gap with reasonable portion sizes."
    ),
    responses={
        400: {"description": "Invalid nutrient column name or parameters provided"},
        422: {"description": "Validation error in request parameters"},
        500: {"description": "Internal server error"},
    },
)
async def recommend_optimized_food(
    request: OptimizedFoodRecommendationRequest,
    db: AsyncSession = Depends(get_async_db),
) -> List[OptimizedFoodRecommendation]:
    """Recommend foods optimized to fill specific nutrient gaps.

    This endpoint analyzes foods in the database and finds those with nutrient amounts
    that would most efficiently help close the gap between current and target nutrient levels.
    It calculates how much of each food would be needed and prioritizes foods that can
    satisfy the gap with reasonable serving sizes (typically 50-200g).

    The response includes:
    - food_name: The name of the food
    - food_category: Category for icon representation
    - nutrient_value: Value of the specified nutrient per 100g
    - amount_needed: How much of this food is needed to reach target (in grams)
    - gap_satisfaction_percentage: What percentage of the gap one serving (100g) fills
    - nutrients: Complete nutritional profile

    Args:
        request: Request containing nutrient name, target amount, and current amount
        db: Database session dependency

    Returns:
        List of optimized food recommendations sorted by practicality for consumption

    Raises:
        HTTPException 400: If the nutrient column is invalid or parameters are invalid
        HTTPException 500: If there's an unexpected error
    """
    try:
        return await nutrient_service.recommend_optimized_food(
            db=db,
            nutrient_column=request.nutrient_name,
            target_amount=request.target_amount,
            current_amount=request.current_amount,
            limit=request.limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recommend optimized food: {str(e)}",
        )


@router.post(
    "/recommend-seasonal-food",
    response_model=List[FoodRecommendation],
    status_code=status.HTTP_200_OK,
    summary="Recommend foods rich in a specific nutrient based on seasonal availability",
    description=(
        "Returns seasonal foods that have the highest values for the specified nutrient. "
        "Foods are filtered by region and either month or season to ensure they are currently "
        "in season. Each recommendation includes the food's complete nutritional profile."
    ),
    responses={
        400: {
            "description": "Invalid nutrient column name, region, or seasonal parameters provided"
        },
        404: {"description": "No seasonal foods found for the given criteria"},
        422: {"description": "Validation error in request parameters"},
        500: {"description": "Internal server error"},
    },
)
async def recommend_seasonal_food(
    request: SeasonalFoodRecommendationRequest,
    db: AsyncSession = Depends(get_async_db),
) -> List[FoodRecommendation]:
    """Recommend foods that are in season and rich in a specific nutrient.

    This endpoint combines seasonal food availability with nutrient optimization.
    It first finds foods that are currently in season based on the provided region
    and either month or season, then identifies those with the highest values
    for the specified nutrient.

    The response includes:
    - food_name: The name of the food
    - food_category: Category for icon representation in the frontend
    - nutrient_value: Value of the specified nutrient
    - nutrients: Complete nutritional profile

    Args:
        request: Request containing nutrient name, region, seasonal filters, and limit
        db: Database session dependency

    Returns:
        List of seasonal food recommendations rich in the specified nutrient

    Raises:
        HTTPException 400: If parameters are invalid or no seasonal foods are found
        HTTPException 500: If there's an unexpected error processing the request
    """
    try:
        return await nutrient_service.recommend_seasonal_food(
            db=db,
            nutrient_column=request.nutrient_name,
            region=request.region,
            month=request.month,
            season=request.season,
            limit=request.limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recommend seasonal food: {str(e)}",
        )
