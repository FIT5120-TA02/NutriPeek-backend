"""CRUD operations for FoodNutrient model."""

from typing import Any, Dict, List, Tuple

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.food_nutrient import FoodNutrient
from src.app.schemas.food import FoodCategoryAvgNutrients
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

    async def get_avg_nutrients_by_category(
        self, db: AsyncSession, *, exclude_empty: bool = True
    ) -> List[FoodCategoryAvgNutrients]:
        """Get average nutritional values grouped by food category.

        Calculates the average of important nutritional values for each food category.

        Args:
            db: Database session
            exclude_empty: Whether to exclude categories with null/empty values

        Returns:
            List of food categories with their average nutrient values
        """
        # Define the query to get average nutrition values grouped by category
        query = (
            select(
                self.model.food_category,
                func.count(self.model.id).label("count"),
                func.avg(self.model.energy_with_fibre_kj).label("energy_with_fibre_kj"),
                func.avg(self.model.protein_g).label("protein_g"),
                func.avg(self.model.total_fat_g).label("total_fat_g"),
                func.avg(self.model.carbs_with_sugar_alcohols_g).label(
                    "carbs_with_sugar_alcohols_g"
                ),
                func.avg(self.model.dietary_fibre_g).label("dietary_fibre_g"),
                func.avg(self.model.sodium_mg).label("sodium_mg"),
            )
            .where(self.model.food_category.isnot(None))
            .group_by(self.model.food_category)
            .order_by(self.model.food_category)
        )

        # If excluding empty categories, add the filter condition
        if exclude_empty:
            query = query.where(self.model.food_category != "")

        result = await db.execute(query)
        rows = result.all()

        # Convert the query results to a list of FoodCategoryAvgNutrients objects
        category_nutrients = []
        for row in rows:
            category_nutrients.append(
                FoodCategoryAvgNutrients(
                    food_category=row.food_category,
                    count=row.count,
                    energy_with_fibre_kj=row.energy_with_fibre_kj,
                    protein_g=row.protein_g,
                    total_fat_g=row.total_fat_g,
                    carbs_with_sugar_alcohols_g=row.carbs_with_sugar_alcohols_g,
                    dietary_fibre_g=row.dietary_fibre_g,
                    sodium_mg=row.sodium_mg,
                )
            )

        return category_nutrients

    async def get_food_by_nutrient(
        self, db: AsyncSession, *, nutrient_column: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get foods with highest values for a specific nutrient.

        Args:
            db: Database session
            nutrient_column: The nutrient column name to sort by
            limit: Maximum number of results to return

        Returns:
            List of dictionaries containing food id, name, category and all nutrient values

        Raises:
            ValueError: If the nutrient column is invalid
        """
        try:
            # Using text() is necessary for dynamic column names
            # but we should validate the column name to prevent SQL injection
            if not hasattr(self.model, nutrient_column):
                raise ValueError(f"Invalid nutrient column: {nutrient_column}")

            # Get IDs of the foods with highest values for the specified nutrient
            query = text(
                f"""
                SELECT id
                FROM food_nutrient
                WHERE {nutrient_column} IS NOT NULL
                  AND food_category IS NOT NULL
                  AND food_name IS NOT NULL
                ORDER BY {nutrient_column} DESC
                LIMIT :limit
            """
            )

            result = await db.execute(query, {"limit": limit})
            food_ids = [row.id for row in result.fetchall()]

            # If no foods were found, return an empty list
            if not food_ids:
                return []

            # Then fetch all nutrient data for these foods
            query = select(self.model).where(self.model.id.in_(food_ids))
            result = await db.execute(query)
            foods = result.scalars().all()

            # Create a list of dictionaries with all food data
            food_items = []
            for food in foods:
                # Get all attributes of the food item
                food_dict = {
                    "id": food.id,
                    "food_name": food.food_name,
                    "food_category": food.food_category,
                    # Include the specific nutrient value separately for sorting/display
                    "nutrient_value": getattr(food, nutrient_column),
                }

                # Add all nutrient columns to a nested nutrients dictionary
                nutrients = {}
                for attr_name, attr_value in food.__dict__.items():
                    # Skip non-nutrient attributes and null values
                    if (
                        attr_name.startswith("_")
                        or attr_name
                        in [
                            "id",
                            "food_name",
                            "food_category",
                            "food_detail",
                            "created_at",
                            "updated_at",
                        ]
                        or attr_value is None
                    ):
                        continue
                    nutrients[attr_name] = attr_value

                food_dict["nutrients"] = nutrients
                food_items.append(food_dict)

            # Sort the results by the nutrient value in descending order
            # This ensures we maintain the same order as the original query
            return sorted(food_items, key=lambda x: x["nutrient_value"], reverse=True)

        except Exception as e:
            await db.rollback()
            raise ValueError(f"Error fetching foods by nutrient: {str(e)}")


# Create a singleton instance
food_nutrient_crud = FoodNutrientCRUD(FoodNutrient)
