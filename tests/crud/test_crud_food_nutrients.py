"""Unit tests for FoodNutrientCRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_food_nutrients import food_nutrient_crud
from src.app.models.food_nutrient import FoodNutrient


@pytest.mark.asyncio
async def test_search_by_exact_category(test_db: AsyncSession, mock_food_nutrients):
    """Test searching for food nutrients by exact category."""
    # Arrange
    await _seed_test_data(test_db, mock_food_nutrients)

    # Act
    results = await food_nutrient_crud.search_by_exact_category(
        test_db, category="Fruits"
    )

    # Assert
    assert len(results) > 0
    assert all(result.food_category.lower() == "fruits" for result in results)


@pytest.mark.asyncio
async def test_search_by_exact_category_no_results(
    test_db: AsyncSession, mock_food_nutrients
):
    """Test searching for food nutrients by exact category with no matches."""
    # Arrange
    await _seed_test_data(test_db, mock_food_nutrients)

    # Act
    results = await food_nutrient_crud.search_by_exact_category(
        test_db, category="NonExistentCategory"
    )

    # Assert
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_by_fuzzy_category(test_db: AsyncSession, mock_food_nutrients):
    """Test searching for food nutrients by fuzzy category matching."""
    # Arrange
    await _seed_test_data(test_db, mock_food_nutrients)

    # Act
    results = await food_nutrient_crud.search_by_fuzzy_category(
        test_db, category="Veg"  # Should match "Vegetables"
    )

    # Assert
    assert len(results) > 0
    assert all("veg" in result.food_category.lower() for result in results)


@pytest.mark.asyncio
async def test_search_by_fuzzy_name(test_db: AsyncSession, mock_food_nutrients):
    """Test searching for food nutrients by fuzzy name matching."""
    # Arrange
    await _seed_test_data(test_db, mock_food_nutrients)

    # Act
    results = await food_nutrient_crud.search_by_fuzzy_name(
        test_db, food_name="App"  # Should match "Apple"
    )

    # Assert
    assert len(results) > 0
    assert any("app" in result.food_name.lower() for result in results)


@pytest.mark.asyncio
async def test_map_food_items(test_db: AsyncSession, mock_food_nutrients):
    """Test mapping food names to nutrient data."""
    # Arrange
    await _seed_test_data(test_db, mock_food_nutrients)
    food_names = ["Apple", "Carrot", "NonExistentFood"]

    # Act
    mapped_items, unmapped_items = await food_nutrient_crud.map_food_items(
        test_db, food_names=food_names
    )

    # Assert
    assert len(mapped_items) == 2  # Apple and Carrot should be mapped
    assert "Apple" in mapped_items
    assert "Carrot" in mapped_items
    assert len(unmapped_items) == 1
    assert "NonExistentFood" in unmapped_items


@pytest.mark.asyncio
async def test_map_food_items_fuzzy_category_match(
    test_db: AsyncSession, mock_food_nutrients
):
    """Test mapping food names using fuzzy category matching."""
    # Arrange
    await _seed_test_data(test_db, mock_food_nutrients)
    food_names = ["Fruit"]  # Should match "Fruits" category

    # Act
    mapped_items, unmapped_items = await food_nutrient_crud.map_food_items(
        test_db, food_names=food_names
    )

    # Assert
    assert len(mapped_items) == 1
    assert "Fruit" in mapped_items
    assert len(unmapped_items) == 0


@pytest.mark.asyncio
async def test_map_food_items_fuzzy_name_match(
    test_db: AsyncSession, mock_food_nutrients
):
    """Test mapping food names using fuzzy name matching."""
    # Arrange
    await _seed_test_data(test_db, mock_food_nutrients)
    food_names = ["Ban"]  # Should match "Banana" via fuzzy name match

    # Act
    mapped_items, unmapped_items = await food_nutrient_crud.map_food_items(
        test_db, food_names=food_names
    )

    # Assert
    assert len(mapped_items) == 1
    assert "Ban" in mapped_items
    assert len(unmapped_items) == 0


# Helper function to seed test data
async def _seed_test_data(db_session: AsyncSession, mock_food_nutrients):
    """Seed the database with test data."""
    for nutrient in mock_food_nutrients:
        db_session.add(nutrient)
    await db_session.commit()


@pytest.fixture
def mock_food_nutrients():
    """Create mock food nutrient data for testing."""
    return [
        FoodNutrient(
            id="1",
            food_name="Apple",
            food_category="Fruits",
            energy_with_fibre_kj=52.0,
            protein_g=0.3,
            total_fat_g=0.2,
            carbs_with_sugar_alcohols_g=14.0,
            dietary_fibre_g=2.4,
            food_detail="Fresh red apple",
        ),
        FoodNutrient(
            id="2",
            food_name="Banana",
            food_category="Fruits",
            energy_with_fibre_kj=89.0,
            protein_g=1.1,
            total_fat_g=0.3,
            carbs_with_sugar_alcohols_g=22.8,
            dietary_fibre_g=2.6,
            food_detail="Yellow ripe banana",
        ),
        FoodNutrient(
            id="3",
            food_name="Carrot",
            food_category="Vegetables",
            energy_with_fibre_kj=41.0,
            protein_g=0.9,
            total_fat_g=0.2,
            carbs_with_sugar_alcohols_g=9.6,
            dietary_fibre_g=2.8,
            food_detail="Fresh orange carrot",
        ),
        FoodNutrient(
            id="4",
            food_name="Broccoli",
            food_category="Vegetables",
            energy_with_fibre_kj=34.0,
            protein_g=2.8,
            total_fat_g=0.4,
            carbs_with_sugar_alcohols_g=6.6,
            dietary_fibre_g=2.6,
            food_detail="Fresh green broccoli",
        ),
    ]
