"""Food API endpoints for searching and retrieving nutritional information."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.core.exceptions.custom import ResourceNotFoundError
from src.app.crud.crud_food_nutrients import food_nutrient_crud
from src.app.schemas.food import FoodAutocompleteResponse, FoodNutrientResponse

router = APIRouter(prefix="/food", tags=["food"])


@router.get(
    "/autocomplete",
    response_model=List[FoodAutocompleteResponse],
    status_code=status.HTTP_200_OK,
    summary="Autocomplete food search",
    description="Search for foods by name and return basic information for autocomplete suggestions",
)
async def autocomplete_food(
    query: str = Query(..., description="Search term for food items"),
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of results to return"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """Search for foods with names containing the query string.

    This endpoint is designed for autocomplete functionality in the frontend,
    returning a limited set of fields (id and food_name) for display in
    autocomplete suggestions.

    The search prioritizes matching by food_category first, then falls back
    to fuzzy name matching if no results are found by category.

    Args:
        query: Search term to filter food items by name
        limit: Maximum number of results to return (default: 10, max: 50)
        db: Database session dependency

    Returns:
        List of matching food items with id and name only

    Raises:
        HTTPException: If an error occurs during the search
    """
    try:
        # First try exact category match
        results = await food_nutrient_crud.search_by_exact_category(
            db, category=query, limit=limit
        )

        # If no results, try fuzzy category match
        if not results:
            results = await food_nutrient_crud.search_by_fuzzy_category(
                db, category=query, limit=limit
            )

        # If still no results, fall back to fuzzy name search
        if not results:
            results = await food_nutrient_crud.search_by_fuzzy_name(
                db, food_name=query, limit=limit
            )

        return [
            FoodAutocompleteResponse(id=item.id, food_name=item.food_name)
            for item in results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching for food items: {str(e)}",
        )


@router.get(
    "/{food_id}",
    response_model=FoodNutrientResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Food item not found"},
        500: {"description": "Internal server error"},
    },
    summary="Get food nutrient information",
    description="Retrieve detailed nutrient information for a specific food item by ID",
)
async def get_food_nutrient_info(
    food_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve detailed nutrient information for a specific food item.

    This endpoint returns the complete nutrient profile for a food item
    identified by its ID. It uses the same response structure as the
    food-detection/map-nutrients endpoint.

    Args:
        food_id: Unique identifier of the food item
        db: Database session dependency

    Returns:
        Detailed nutrient information for the specified food item

    Raises:
        HTTPException: If the food item is not found or an error occurs
    """
    try:
        food_nutrient = await food_nutrient_crud.get(db, id=food_id)
        if not food_nutrient:
            raise ResourceNotFoundError(f"Food item with ID {food_id} not found")

        # Convert the model to the response schema
        return FoodNutrientResponse(
            id=food_nutrient.id,
            food_name=food_nutrient.food_name,
            food_category=food_nutrient.food_category,
            energy_with_fibre_kj=food_nutrient.energy_with_fibre_kj,
            protein_g=food_nutrient.protein_g,
            total_fat_g=food_nutrient.total_fat_g,
            carbs_with_sugar_alcohols_g=food_nutrient.carbs_with_sugar_alcohols_g,
            dietary_fibre_g=food_nutrient.dietary_fibre_g,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving food nutrient information: {str(e)}",
        )
