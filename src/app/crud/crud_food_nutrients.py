"""CRUD operations for FoodNutrient model."""

from typing import Dict, List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.food_nutrient import FoodNutrient
from src.app.schemas.food_detection import FoodNutrientSummary


class FoodNutrientCRUD(AsyncCRUDBase[FoodNutrient, None, None]):
    """CRUD operations for FoodNutrient model.

    This class extends the base CRUD operations with methods specific to
    food nutrients, including search by category and name with fuzzy matching.
    """

    async def search_by_exact_category(
        self, db: AsyncSession, *, category: str, limit: int = 10
    ) -> List[FoodNutrient]:
        """Search for food nutrients by exact category match.

        Args:
            db: Database session
            category: Food category to search for
            limit: Maximum number of results to return

        Returns:
            List of matching FoodNutrient objects
        """
        # Convert category to lowercase for case-insensitive matching
        category_lower = category.lower()

        query = select(self.model).where(
            func.lower(self.model.food_category) == category_lower
        )
        result = await db.execute(query.limit(limit))
        return result.scalars().all()

    async def search_by_fuzzy_category(
        self, db: AsyncSession, *, category: str, limit: int = 10
    ) -> List[FoodNutrient]:
        """Search for food nutrients by fuzzy category matching.

        Uses partial string matching to find items with similar categories.

        Args:
            db: Database session
            category: Food category to search for
            limit: Maximum number of results to return

        Returns:
            List of matching FoodNutrient objects
        """
        # Convert category to lowercase for case-insensitive matching
        category_lower = category.lower()

        # Split the search term into words for more flexible matching
        search_terms = category_lower.split()

        # Create conditions for each word
        conditions = []
        for term in search_terms:
            conditions.append(func.lower(self.model.food_category).contains(term))

        # Combine conditions with OR
        query = select(self.model).where(or_(*conditions))

        # Order by relevance (simplified - counting the number of matches)
        result = await db.execute(query.limit(limit))
        return result.scalars().all()

    async def search_by_fuzzy_name(
        self, db: AsyncSession, *, food_name: str, limit: int = 10
    ) -> List[FoodNutrient]:
        """Search for food nutrients by fuzzy name matching.

        Uses partial string matching to find items with similar food names.

        Args:
            db: Database session
            food_name: Food name to search for
            limit: Maximum number of results to return

        Returns:
            List of matching FoodNutrient objects
        """
        # Convert food_name to lowercase for case-insensitive matching
        food_name_lower = food_name.lower()

        # Split the search term into words for more flexible matching
        search_terms = food_name_lower.split()

        # Create conditions for each word
        conditions = []
        for term in search_terms:
            conditions.append(func.lower(self.model.food_name).contains(term))
            if term and len(term) > 2:  # Skip very short terms for food_detail
                conditions.append(func.lower(self.model.food_detail).contains(term))

        # Combine conditions with OR
        query = select(self.model).where(or_(*conditions))
        result = await db.execute(query.limit(limit))
        return result.scalars().all()

    async def map_food_items(
        self, db: AsyncSession, *, food_names: List[str]
    ) -> Tuple[Dict[str, FoodNutrientSummary], List[str]]:
        """Map food names to food nutrient data.

        First tries to match each name to a food category,
        then falls back to fuzzy matching by food name.

        Args:
            db: Database session
            food_names: List of food names to map

        Returns:
            Tuple containing:
                - Dict mapping food names to their nutrient data
                - List of food names that couldn't be mapped
        """
        mapped_items = {}
        unmapped_items = []

        for food_name in food_names:
            # First try to match as a category
            foods_by_category = await self.search_by_exact_category(
                db, category=food_name, limit=1
            )

            if foods_by_category:
                # Use the first match from the category
                nutrient = foods_by_category[0]
                mapped_items[food_name] = self._create_nutrient_summary(nutrient)
                continue

            # Try fuzzy category match if no exact category match
            fuzzy_category_matches = await self.search_by_fuzzy_category(
                db, category=food_name, limit=1
            )

            if fuzzy_category_matches:
                # Use the first fuzzy category match
                nutrient = fuzzy_category_matches[0]
                mapped_items[food_name] = self._create_nutrient_summary(nutrient)
                continue

            # If not found as category, try as food name
            fuzzy_name_matches = await self.search_by_fuzzy_name(
                db, food_name=food_name, limit=1
            )

            if fuzzy_name_matches:
                # Use the first fuzzy name match
                nutrient = fuzzy_name_matches[0]
                mapped_items[food_name] = self._create_nutrient_summary(nutrient)
            else:
                # If no match found, add to unmapped list
                unmapped_items.append(food_name)

        return mapped_items, unmapped_items

    def _create_nutrient_summary(self, nutrient: FoodNutrient) -> FoodNutrientSummary:
        """Create a FoodNutrientSummary from a FoodNutrient object.

        Args:
            nutrient: FoodNutrient object

        Returns:
            FoodNutrientSummary object
        """
        return FoodNutrientSummary(
            id=nutrient.id,
            food_name=nutrient.food_name,
            food_category=nutrient.food_category,
            energy_with_fibre_kj=nutrient.energy_with_fibre_kj,
            protein_g=nutrient.protein_g,
            total_fat_g=nutrient.total_fat_g,
            carbs_with_sugar_alcohols_g=nutrient.carbs_with_sugar_alcohols_g,
            dietary_fibre_g=nutrient.dietary_fibre_g,
        )


# Create a singleton instance
food_nutrient_crud = FoodNutrientCRUD(FoodNutrient)
