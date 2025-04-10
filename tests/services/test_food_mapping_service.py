"""Unit tests for FoodMappingService."""

from unittest.mock import AsyncMock, patch

import pytest

from src.app.core.exceptions.custom import InvalidRequestError
from src.app.schemas.food_detection import FoodNutrientSummary
from src.app.services.food_mapping_service import food_mapping_service


@pytest.mark.asyncio
async def test_map_food_items_basic():
    """Test the basic functionality of map_food_items method."""
    # Arrange
    food_names = ["Apple", "Banana"]

    # Mock the CRUD operation and database session
    with patch(
        "src.app.services.food_mapping_service.get_async_session"
    ) as mock_get_session:
        # Setup mock session
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_get_session.return_value = mock_session

        # Setup mock CRUD result
        mock_mapped = {
            "Apple": FoodNutrientSummary(
                id="1",
                food_name="Apple",
                food_category="Fruits",
                energy_with_fibre_kj=52.0,
                protein_g=0.3,
                total_fat_g=0.2,
                carbs_with_sugar_alcohols_g=14.0,
                dietary_fibre_g=2.4,
            ),
            "Banana": FoodNutrientSummary(
                id="2",
                food_name="Banana",
                food_category="Fruits",
                energy_with_fibre_kj=89.0,
                protein_g=1.1,
                total_fat_g=0.3,
                carbs_with_sugar_alcohols_g=22.8,
                dietary_fibre_g=2.6,
            ),
        }
        mock_unmapped = []

        with patch(
            "src.app.services.food_mapping_service.food_nutrient_crud.map_food_items"
        ) as mock_map:
            mock_map.return_value = (mock_mapped, mock_unmapped)

            # Act
            mapped_items, unmapped_items = await food_mapping_service.map_food_items(
                food_names
            )

            # Assert
            assert len(mapped_items) == 2
            assert "Apple" in mapped_items
            assert "Banana" in mapped_items
            assert len(unmapped_items) == 0
            mock_map.assert_called_once_with(mock_session, food_names=food_names)


@pytest.mark.asyncio
async def test_map_food_items_missing_profile_id():
    """Test mapping food items with store_in_inventory but missing profile_id."""
    # Arrange
    food_names = ["Apple"]
    children_profile_id = None
    store_in_inventory = True

    # Act & Assert
    with pytest.raises(InvalidRequestError):
        await food_mapping_service.map_food_items(
            food_names, children_profile_id, store_in_inventory
        )
