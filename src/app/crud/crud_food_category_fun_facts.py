"""CRUD operations for food category fun facts."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.food_category_fun_fact import FoodCategoryFunFact
from src.app.schemas.food_category import (
    FoodCategoryFunFactCreate,
    FoodCategoryFunFactUpdate,
)


class CRUDFoodCategoryFunFact(
    AsyncCRUDBase[
        FoodCategoryFunFact, FoodCategoryFunFactCreate, FoodCategoryFunFactUpdate
    ]
):
    """CRUD operations for food category fun facts."""

    async def get_by_category(
        self, db: AsyncSession, *, category: str
    ) -> Optional[FoodCategoryFunFact]:
        """Get a fun fact by food category.

        Args:
            db: Database session
            category: Food category name

        Returns:
            The food category fun fact or None if not found
        """
        result = await db.execute(
            select(FoodCategoryFunFact).where(
                func.lower(FoodCategoryFunFact.food_category) == func.lower(category)
            )
        )
        return result.scalars().first()

    async def get_random_fun_facts(
        self, db: AsyncSession, *, count: int = 5
    ) -> List[FoodCategoryFunFact]:
        """Get a specified number of random food category fun facts.

        Args:
            db: Database session
            count: Number of fun facts to retrieve (default: 5)

        Returns:
            List of random food category fun facts
        """
        # Use SQL's random() function to get random records directly from the database
        result = await db.execute(
            select(FoodCategoryFunFact).order_by(func.random()).limit(count)
        )
        return result.scalars().all()

    async def get_fun_facts_by_categories(
        self, db: AsyncSession, *, categories: List[str]
    ) -> List[FoodCategoryFunFact]:
        """Get fun facts for specified food categories.

        Args:
            db: Database session
            categories: List of food category names

        Returns:
            List of food category fun facts for the specified categories
        """
        if not categories:
            return []

        # Convert categories to lowercase for case-insensitive comparison
        lower_categories = [cat.lower() for cat in categories]

        result = await db.execute(
            select(FoodCategoryFunFact).where(
                func.lower(FoodCategoryFunFact.food_category).in_(lower_categories)
            )
        )
        return result.scalars().all()


# Create a singleton instance
food_category_fun_fact_crud = CRUDFoodCategoryFunFact(FoodCategoryFunFact)
