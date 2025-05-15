"""API endpoints for seasonal food."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.schemas.seasonal_food import (
    SeasonalFoodDetailResponse,
    SeasonalFoodListResponse,
    SeasonalFoodResponse,
)
from src.app.services.seasonal_food_service import seasonal_food_service

router = APIRouter(prefix="/seasonal-food", tags=["seasonal-food"])


@router.get("/", response_model=SeasonalFoodListResponse)
async def get_seasonal_food(
    region: Optional[str] = None,
    season: Optional[str] = Query(
        None,
        description="Filter by season. Accepted values: spring, summer, autumn, winter (case insensitive)",
    ),
    month: Optional[str] = Query(
        None,
        description="Filter by month. Accepted values: january, february, etc. (case insensitive)",
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by food category (case insensitive)",
    ),
    food_name: Optional[str] = Query(
        None,
        description="Search by food name (partial match, case insensitive)",
    ),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of items to return"
    ),
    db: AsyncSession = Depends(get_async_db),
) -> SeasonalFoodListResponse:
    """Get seasonal food items with optional filtering.

    This endpoint returns seasonal food items and supports filtering by various criteria.
    All string filters are case-insensitive.

    Args:
        region: Optional region filter (e.g., "Australia", "Europe")
        season: Optional season filter (spring, summer, autumn, winter)
        month: Optional month filter (january, february, etc.)
        category: Optional category filter (e.g., "fruit", "vegetable")
        food_name: Optional food name for partial search
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of seasonal food items matching the filters along with total count
    """
    # Build filters dict from provided parameters
    filters: Dict[str, Optional[str]] = {}
    if region:
        filters["region"] = region
    if season:
        filters["season"] = season
    if month:
        filters["month"] = month
    if category:
        filters["category"] = category
    if food_name:
        filters["food_name"] = food_name

    # Get filtered items using service layer
    return await seasonal_food_service.get_seasonal_food_with_filters(
        db, filters=filters, skip=skip, limit=limit
    )


@router.get("/regions", response_model=List[str])
async def get_regions(
    db: AsyncSession = Depends(get_async_db),
) -> List[str]:
    """Get all available regions.

    Returns a list of distinct regions available in the database.

    Args:
        db: Database session

    Returns:
        List of distinct regions
    """
    return await seasonal_food_service.get_distinct_regions(db)


@router.get("/autocomplete", response_model=List[str])
async def autocomplete_food_name(
    query: str = Query(..., min_length=1, description="Search term for autocomplete"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_async_db),
) -> List[str]:
    """Get autocomplete suggestions for food names.

    Returns a list of food name suggestions that begin with the provided query.

    Args:
        query: The search term to match against food names (case-insensitive prefix match)
        limit: Maximum number of suggestions to return
        db: Database session

    Returns:
        List of matching food name suggestions
    """
    return await seasonal_food_service.get_autocomplete_suggestions(
        db, query=query, limit=limit
    )


@router.get("/{id}", response_model=SeasonalFoodResponse)
async def get_seasonal_food_by_id(
    id: int,
    db: AsyncSession = Depends(get_async_db),
) -> SeasonalFoodResponse:
    """Get a seasonal food item by ID.

    Retrieves a specific seasonal food item by its unique identifier.

    Args:
        id: Seasonal food item ID
        db: Database session

    Returns:
        The seasonal food item

    Raises:
        HTTPException: If the item is not found (404)
    """
    db_obj = await seasonal_food_service.get_seasonal_food_by_id(db, id=id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seasonal food item not found",
        )
    return db_obj


@router.get("/details/{food_name}", response_model=SeasonalFoodDetailResponse)
async def get_seasonal_food_details(
    food_name: str,
    region: str = Query(..., description="Region for seasonal availability data"),
    db: AsyncSession = Depends(get_async_db),
) -> SeasonalFoodDetailResponse:
    """Get detailed information about a seasonal food item including nutrient data.

    This endpoint retrieves comprehensive information about a food item, including:
    1. All months when the food is in season for the specified region
    2. Nutritional information for the food item if available

    Args:
        food_name: Name of the food item to look up
        region: Geographic region for seasonal availability data
        db: Database session

    Returns:
        Detailed food information including seasonal availability and nutrients

    Raises:
        HTTPException: If no seasonal data is found for the specified food and region
    """
    result = await seasonal_food_service.get_seasonal_food_details(
        db, food_name=food_name, region=region
    )

    return result
