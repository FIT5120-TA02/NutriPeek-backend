"""Unit tests for food category fun fact CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_food_category_fun_facts import food_category_fun_fact_crud
from src.app.models.food_category_fun_fact import FoodCategoryFunFact


@pytest.mark.asyncio
async def test_get_by_category(test_db: AsyncSession, mock_food_category_fun_facts):
    """Test retrieving fun fact by food category."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act
    result = await food_category_fun_fact_crud.get_by_category(
        test_db, category="Apples"
    )

    # Assert
    assert result is not None
    assert result.food_category == "Apples"
    assert "float" in result.fun_fact


@pytest.mark.asyncio
async def test_get_by_category_case_insensitive(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving fun fact by food category with case-insensitive matching."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act - use lowercase
    result_lower = await food_category_fun_fact_crud.get_by_category(
        test_db, category="apples"
    )
    # Act - use uppercase
    result_upper = await food_category_fun_fact_crud.get_by_category(
        test_db, category="APPLES"
    )
    # Act - use mixed case
    result_mixed = await food_category_fun_fact_crud.get_by_category(
        test_db, category="aPPleS"
    )

    # Assert all variations return the same result
    assert result_lower is not None
    assert result_upper is not None
    assert result_mixed is not None
    assert result_lower.id == result_upper.id == result_mixed.id
    assert result_lower.food_category == "Apples"


@pytest.mark.asyncio
async def test_get_by_category_no_result(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving fun fact by food category with no match."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act
    result = await food_category_fun_fact_crud.get_by_category(
        test_db, category="NonExistent"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_random_fun_facts(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving random food category fun facts."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act
    results = await food_category_fun_fact_crud.get_random_fun_facts(test_db, count=2)

    # Assert
    assert len(results) == 2
    assert all(isinstance(result, FoodCategoryFunFact) for result in results)
    # Ensure results are valid fun facts from our test data
    result_ids = set(result.id for result in results)
    assert len(result_ids) == 2  # Should be unique
    assert all(
        result_id in [fact.id for fact in mock_food_category_fun_facts]
        for result_id in result_ids
    )


@pytest.mark.asyncio
async def test_get_random_fun_facts_count_exceeds_available(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving random fun facts when count exceeds available records."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)
    total_available = len(mock_food_category_fun_facts)

    # Act - request more than available
    results = await food_category_fun_fact_crud.get_random_fun_facts(
        test_db, count=total_available + 5
    )

    # Assert - should return all available
    assert len(results) == total_available
    assert all(isinstance(result, FoodCategoryFunFact) for result in results)


@pytest.mark.asyncio
async def test_get_fun_facts_by_categories(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving fun facts for specific food categories."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act
    results = await food_category_fun_fact_crud.get_fun_facts_by_categories(
        test_db, categories=["Apples", "Bananas"]
    )

    # Assert
    assert len(results) == 2
    assert all(isinstance(result, FoodCategoryFunFact) for result in results)
    food_categories = {result.food_category for result in results}
    assert food_categories == {"Apples", "Bananas"}


@pytest.mark.asyncio
async def test_get_fun_facts_by_categories_case_insensitive(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving fun facts for specific food categories with case-insensitive matching."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act - use mixed case
    results = await food_category_fun_fact_crud.get_fun_facts_by_categories(
        test_db, categories=["aPPleS", "BANanas"]
    )

    # Assert
    assert len(results) == 2
    assert all(isinstance(result, FoodCategoryFunFact) for result in results)
    food_categories = {result.food_category for result in results}
    assert food_categories == {"Apples", "Bananas"}


@pytest.mark.asyncio
async def test_get_fun_facts_by_categories_empty_list(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving fun facts with empty categories list."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act
    results = await food_category_fun_fact_crud.get_fun_facts_by_categories(
        test_db, categories=[]
    )

    # Assert - should return empty list
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_fun_facts_by_categories_non_existent(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving fun facts for non-existent categories."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act
    results = await food_category_fun_fact_crud.get_fun_facts_by_categories(
        test_db, categories=["NonExistent1", "NonExistent2"]
    )

    # Assert - should return empty list
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_fun_facts_by_categories_mixed_existence(
    test_db: AsyncSession, mock_food_category_fun_facts
):
    """Test retrieving fun facts for a mix of existing and non-existing categories."""
    # Arrange
    await _seed_test_data(test_db, mock_food_category_fun_facts)

    # Act
    results = await food_category_fun_fact_crud.get_fun_facts_by_categories(
        test_db, categories=["Apples", "NonExistent"]
    )

    # Assert - should return only the existing one
    assert len(results) == 1
    assert results[0].food_category == "Apples"


# Helper function to seed test data
async def _seed_test_data(db_session: AsyncSession, mock_fun_facts):
    """Seed the database with test food category fun facts."""
    for fun_fact in mock_fun_facts:
        db_session.add(fun_fact)
    await db_session.commit()


@pytest.fixture
def mock_food_category_fun_facts():
    """Create mock food category fun fact data for testing."""
    return [
        FoodCategoryFunFact(
            id="1",
            food_category="Apples",
            fun_fact="Apples float in water because 25% of their volume is air.",
        ),
        FoodCategoryFunFact(
            id="2",
            food_category="Bananas",
            fun_fact="Bananas are berries, but strawberries aren't.",
        ),
        FoodCategoryFunFact(
            id="3",
            food_category="Carrots",
            fun_fact="Carrots were originally purple before they were bred orange.",
        ),
        FoodCategoryFunFact(
            id="4",
            food_category="Spinach",
            fun_fact="Spinach is an excellent source of iron, helping your blood carry oxygen.",
        ),
        FoodCategoryFunFact(
            id="5",
            food_category="Tomatoes",
            fun_fact="Tomatoes are technically fruits because they contain seeds and grow from the flower of the plant.",
        ),
    ]
