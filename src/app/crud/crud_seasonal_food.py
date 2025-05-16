"""CRUD operations for seasonal food items."""

from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.seasonal_food import SeasonalFood
from src.app.schemas.seasonal_food import SeasonalFoodCreate, SeasonalFoodUpdate


class CRUDSeasonalFood(
    AsyncCRUDBase[SeasonalFood, SeasonalFoodCreate, SeasonalFoodUpdate]
):
    """CRUD operations for seasonal food items."""

    async def get_distinct_regions(self, db: AsyncSession) -> List[str]:
        """Get distinct regions from the database.

        Args:
            db: Database session.

        Returns:
            List of distinct regions.
        """
        query = select(self.model.region).distinct()
        result = await db.execute(query)
        return result.scalars().all()

    async def get_filtered(
        self,
        db: AsyncSession,
        *,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[SeasonalFood]:
        """Get seasonal food items with filtering.

        Args:
            db: Database session.
            filters: Dictionary of filters to apply.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of seasonal food items.
        """
        query = select(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                if field == "food_name":
                    # Partial matching for food name
                    query = query.where(
                        getattr(self.model, field).like(f"%{value.lower()}%")
                    )
                elif field == "season":
                    # Handle season enum format: capitalize the value
                    # This assumes the enum values are stored with capitalized format (e.g., "Autumn")
                    query = query.where(
                        getattr(self.model, field) == value.capitalize()
                    )
                else:
                    # Exact matching for other fields
                    query = query.where(getattr(self.model, field) == value.lower())

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count_filtered(self, db: AsyncSession, *, filters: Dict[str, Any]) -> int:
        """Count seasonal food items with filtering.

        Args:
            db: Database session.
            filters: Dictionary of filters to apply.

        Returns:
            Count of matching items.
        """
        query = select(func.count()).select_from(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                if field == "food_name":
                    # Partial matching for food name
                    query = query.where(
                        getattr(self.model, field).like(f"%{value.lower()}%")
                    )
                elif field == "season":
                    # Handle season enum format: capitalize the value
                    # This assumes the enum values are stored with capitalized format (e.g., "Autumn")
                    query = query.where(
                        getattr(self.model, field) == value.capitalize()
                    )
                else:
                    # Exact matching for other fields
                    query = query.where(getattr(self.model, field) == value.lower())

        result = await db.execute(query)
        return result.scalar_one()

    async def get_autocomplete_suggestions(
        self, db: AsyncSession, *, query: str, limit: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions for food names.

        Args:
            db: Database session.
            query: The search term to match against food names.
            limit: Maximum number of suggestions to return.

        Returns:
            List of food name suggestions.
        """
        # For autocomplete, we use a prefix match (starts with) instead of contains
        search_term = f"{query.lower()}%"

        # Select distinct food names that start with the query term
        query = (
            select(self.model.food_name)
            .distinct()
            .where(self.model.food_name.like(search_term))
            .limit(limit)
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_seasonal_availability(
        self, db: AsyncSession, *, food_name: str, region: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Get seasonal availability data for a specific food item in a region.

        Retrieves all records matching the food name and region, providing
        information about when the food is in season.

        Args:
            db: Database session
            food_name: Name of the food item to look up
            region: Geographic region

        Returns:
            List of dictionaries containing season and month information
        """
        query = select(self.model).where(
            (self.model.food_name == food_name.lower())
            & (self.model.region == region.lower())
        )

        result = await db.execute(query)
        items = result.scalars().all()

        # Format the results
        availability = []
        for item in items:
            availability.append(
                {
                    "season": item.season,
                    "month": item.month,
                    "category": item.category,
                }
            )

        return (
            availability,
            items[0].db_category,
        )  # return the db_category of the first item


seasonal_food = CRUDSeasonalFood(SeasonalFood)
