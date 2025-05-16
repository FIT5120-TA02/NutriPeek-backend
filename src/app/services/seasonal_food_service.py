"""Service layer for seasonal food operations."""

from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_seasonal_food import seasonal_food
from src.app.schemas.seasonal_food import (
    SeasonalAvailability,
    SeasonalFoodDetailResponse,
    SeasonalFoodListResponse,
    SeasonalFoodResponse,
)
from src.app.services.food_mapping_service import food_mapping_service


class SeasonalFoodService:
    """Service for handling seasonal food operations.

    This service provides an abstraction layer between the API endpoints and
    CRUD operations, handling the conversion between SQLAlchemy models
    and Pydantic schemas.
    """

    async def get_seasonal_food_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: Dict[str, Optional[str]],
        skip: int = 0,
        limit: int = 100,
    ) -> SeasonalFoodListResponse:
        """Get seasonal food items with filtering.

        Args:
            db: Database session
            filters: Dictionary of filters to apply
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of seasonal food items matching the filters
        """
        # Get database items
        items = await seasonal_food.get_filtered(
            db, filters=filters, skip=skip, limit=limit
        )
        total = await seasonal_food.count_filtered(db, filters=filters)

        # Convert SQLAlchemy models to Pydantic schema
        pydantic_items = [
            SeasonalFoodResponse(
                id=item.id,
                name=item.food_name,
                category=item.category,
                db_category=item.db_category,
                region=item.region,
                season=item.season,
                month=item.month,
            )
            for item in items
        ]

        return SeasonalFoodListResponse(items=pydantic_items, total=total)

    async def get_seasonal_food_by_id(
        self, db: AsyncSession, *, id: int
    ) -> Optional[SeasonalFoodResponse]:
        """Get a seasonal food item by ID.

        Args:
            db: Database session
            id: Seasonal food item ID

        Returns:
            The seasonal food item or None if not found
        """
        item = await seasonal_food.get(db, id)
        if not item:
            return None

        return SeasonalFoodResponse(
            id=item.id,
            name=item.food_name,
            category=item.category,
            region=item.region,
            season=item.season,
            month=item.month,
        )

    async def get_distinct_regions(self, db: AsyncSession) -> List[str]:
        """Get distinct regions from the database.

        Args:
            db: Database session

        Returns:
            List of distinct regions
        """
        return await seasonal_food.get_distinct_regions(db)

    async def get_autocomplete_suggestions(
        self, db: AsyncSession, *, query: str, limit: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions for food names.

        Args:
            db: Database session
            query: The search term to match against food names
            limit: Maximum number of suggestions to return

        Returns:
            List of food name suggestions
        """
        return await seasonal_food.get_autocomplete_suggestions(
            db, query=query, limit=limit
        )

    async def get_seasonal_food_details(
        self, db: AsyncSession, *, food_name: str, region: str
    ) -> SeasonalFoodDetailResponse:
        """Get detailed seasonal food information including seasonal availability and nutrient data.

        Retrieves all months when the specified food is in season for the given region,
        and maps the food name to nutritional data.

        Args:
            db: Database session
            food_name: Name of the food item
            region: Geographic region

        Returns:
            SeasonalFoodDetailResponse object containing seasonal availability and nutrient information
        """
        # Get seasonal availability data
        seasonal_data, db_category = await seasonal_food.get_seasonal_availability(
            db, food_name=food_name, region=region
        )

        # Convert to Pydantic models
        seasonal_availability = [SeasonalAvailability(**item) for item in seasonal_data]

        # Map food name to nutrient data using the singular form
        mapped_items, unmapped = await food_mapping_service.map_food_items(
            food_names=[db_category]
        )

        # Extract nutrient data if available
        nutrient_data = None
        if db_category in mapped_items:
            nutrient_data = mapped_items[db_category].nutrient_data

        # Create and return the response object
        return SeasonalFoodDetailResponse(
            food_name=food_name,
            region=region,
            seasonal_availability=seasonal_availability,
            nutrient_data=nutrient_data,
        )


# Create a singleton instance
seasonal_food_service = SeasonalFoodService()
