"""Food mapping service for matching detected foods to nutrient data."""

from collections import Counter
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db.async_session import get_async_session
from src.app.core.exceptions.custom import FoodMappingError, InvalidRequestError
from src.app.crud.crud_food_nutrients import food_nutrient_crud
from src.app.models.ingredient_inventory import IngredientInventory
from src.app.models.ingredient_nutrient import IngredientNutrient
from src.app.schemas.food_detection import FoodItemQuantity, FoodNutrientSummary


class FoodMappingService:
    """Service for mapping detected food items to nutrient data.

    Provides functionality to match food items detected in images to
    corresponding nutrient data in the database, with options to
    store the results in a user's inventory.
    """

    async def map_food_items(
        self,
        food_names: List[str],
        children_profile_id: Optional[str] = None,
        store_in_inventory: bool = False,
    ) -> Tuple[Dict[str, FoodItemQuantity], List[str]]:
        """Map detected food items to nutrient data with quantities.

        This method maps food names directly to database entries,
        trying the following lookup strategy:
        1. Match as food category (exact)
        2. Match as food category (fuzzy)
        3. Match as food name (fuzzy)

        It also counts duplicates and includes quantity in the result.

        Args:
            food_names: List of food names to map to nutrient data
            children_profile_id: Optional ID of the children's profile for inventory
            store_in_inventory: Whether to store the results in the inventory

        Returns:
            Tuple containing:
                - Dictionary mapping food names to their nutrient data with quantities
                - List of food names that couldn't be mapped

        Raises:
            InvalidRequestError: If profile ID is missing but store_in_inventory is True
            FoodMappingError: If mapping fails for any other reason
        """
        if store_in_inventory and not children_profile_id:
            raise InvalidRequestError(
                "children_profile_id is required when store_in_inventory is True"
            )

        try:
            # Count food items using Counter
            food_counter = Counter(food_names)
            unique_food_names = list(food_counter.keys())

            # Using async context manager
            async with get_async_session() as db:
                # Map unique food names to nutrient data
                nutrient_map, unmapped_items = await food_nutrient_crud.map_food_items(
                    db, food_names=unique_food_names
                )

                # Create result with quantity information
                mapped_items_with_quantity: Dict[str, FoodItemQuantity] = {}
                for food_name, nutrient_data in nutrient_map.items():
                    mapped_items_with_quantity[food_name] = FoodItemQuantity(
                        nutrient_data=nutrient_data, quantity=food_counter[food_name]
                    )

                # Store in inventory if requested
                if (
                    store_in_inventory
                    and mapped_items_with_quantity
                    and children_profile_id
                ):
                    await self._store_in_inventory_with_quantity(
                        db, mapped_items_with_quantity, children_profile_id
                    )

                return mapped_items_with_quantity, unmapped_items

        except Exception as e:
            raise FoodMappingError(f"Failed to map food items: {str(e)}")

    async def _store_in_inventory_with_quantity(
        self,
        db: AsyncSession,
        mapped_items: Dict[str, FoodItemQuantity],
        children_profile_id: str,
    ) -> None:
        """Store mapped food items in the inventory with proper quantities.

        Args:
            db: Database session
            mapped_items: Dictionary mapping food names to their nutrient data with quantities
            children_profile_id: ID of the children's profile for inventory

        Raises:
            FoodMappingError: If storing in inventory fails
        """
        try:
            # Create or get inventory for the profile
            inventory = IngredientInventory(children_profile_id=children_profile_id)
            db.add(inventory)
            await db.flush()

            # Create ingredient nutrients for each mapped item
            for food_name, item_with_quantity in mapped_items.items():
                ingredient_nutrient = IngredientNutrient(
                    food_nutrient_id=item_with_quantity.nutrient_data.id,
                    ingredient_inventory_id=inventory.id,
                    quantity=float(
                        item_with_quantity.quantity
                    ),  # Use the detected quantity
                    unit="serving",  # Default unit
                )
                db.add(ingredient_nutrient)

            await db.commit()
        except Exception as e:
            await db.rollback()
            raise FoodMappingError(f"Failed to store in inventory: {str(e)}")

    # Keep the old method for backward compatibility
    async def _store_in_inventory(
        self,
        db: AsyncSession,
        mapped_items: Dict[str, FoodNutrientSummary],
        children_profile_id: str,
    ) -> None:
        """Store mapped food items in the inventory.

        Args:
            db: Database session
            mapped_items: Dictionary mapping food names to their nutrient data
            children_profile_id: ID of the children's profile for inventory

        Raises:
            FoodMappingError: If storing in inventory fails
        """
        try:
            # Create or get inventory for the profile
            inventory = IngredientInventory(children_profile_id=children_profile_id)
            db.add(inventory)
            await db.flush()

            # Create ingredient nutrients for each mapped item
            for food_name, nutrient_data in mapped_items.items():
                ingredient_nutrient = IngredientNutrient(
                    food_nutrient_id=nutrient_data.id,
                    ingredient_inventory_id=inventory.id,
                    quantity=1.0,  # Default quantity
                    unit="serving",  # Default unit
                )
                db.add(ingredient_nutrient)

            await db.commit()
        except Exception as e:
            await db.rollback()
            raise FoodMappingError(f"Failed to store in inventory: {str(e)}")


# Create a singleton instance
food_mapping_service = FoodMappingService()
