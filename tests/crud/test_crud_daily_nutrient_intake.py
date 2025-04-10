"""Unit tests for DailyNutrientIntakeCRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_daily_nutrient_intake import daily_nutrient_intake_crud
from src.app.models.daily_nutrient_intake import DailyNutrientIntake


@pytest.mark.asyncio
async def test_get_by_age_and_gender(
    test_db: AsyncSession, mock_daily_nutrient_intakes
):
    """Test retrieving daily nutrient intakes by age and gender."""
    # Arrange
    await _seed_test_data(test_db, mock_daily_nutrient_intakes)

    # Act
    results = await daily_nutrient_intake_crud.get_by_age_and_gender(
        test_db, age=10, gender="boy"
    )

    # Assert
    assert len(results) == 2
    assert all(result.age == 10 for result in results)
    assert all(result.gender == "boy" for result in results)


@pytest.mark.asyncio
async def test_get_by_age_and_gender_no_results(
    test_db: AsyncSession, mock_daily_nutrient_intakes
):
    """Test retrieving daily nutrient intakes by age and gender with no matches."""
    # Arrange
    await _seed_test_data(test_db, mock_daily_nutrient_intakes)

    # Act
    results = await daily_nutrient_intake_crud.get_by_age_and_gender(
        test_db, age=20, gender="boy"  # Age 20 not in test data
    )

    # Assert
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_by_nutrient_age_and_gender(
    test_db: AsyncSession, mock_daily_nutrient_intakes
):
    """Test retrieving a specific nutrient intake by nutrient name, age, and gender."""
    # Arrange
    await _seed_test_data(test_db, mock_daily_nutrient_intakes)

    # Act
    result = await daily_nutrient_intake_crud.get_by_nutrient_age_and_gender(
        test_db, nutrient="Calcium", age=10, gender="boy"
    )

    # Assert
    assert result is not None
    assert result.nutrient == "Calcium"
    assert result.age == 10
    assert result.gender == "boy"
    assert result.intake == 1000.0
    assert result.unit == "mg"


@pytest.mark.asyncio
async def test_get_by_nutrient_age_and_gender_no_result(
    test_db: AsyncSession, mock_daily_nutrient_intakes
):
    """Test retrieving a nutrient intake with no match."""
    # Arrange
    await _seed_test_data(test_db, mock_daily_nutrient_intakes)

    # Act
    result = await daily_nutrient_intake_crud.get_by_nutrient_age_and_gender(
        test_db, nutrient="NonExistent", age=10, gender="boy"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_all_nutrients(test_db: AsyncSession, mock_daily_nutrient_intakes):
    """Test retrieving all distinct nutrient names."""
    # Arrange
    await _seed_test_data(test_db, mock_daily_nutrient_intakes)

    # Act
    nutrients = await daily_nutrient_intake_crud.get_all_nutrients(test_db)

    # Assert
    assert len(nutrients) == 3
    assert "Calcium" in nutrients
    assert "Iron" in nutrients
    assert "Vitamin C" in nutrients


@pytest.mark.asyncio
async def test_get_multiple_results(test_db: AsyncSession, mock_daily_nutrient_intakes):
    """Test the generic get_multi method from the base class."""
    # Arrange
    await _seed_test_data(test_db, mock_daily_nutrient_intakes)

    # Act
    results = await daily_nutrient_intake_crud.get_multi(test_db, skip=0, limit=10)

    # Assert
    assert len(results) == 5
    assert all(isinstance(result, DailyNutrientIntake) for result in results)


# Helper function to seed test data
async def _seed_test_data(db_session: AsyncSession, mock_nutrients):
    """Seed the database with test nutrient intake data."""
    for nutrient in mock_nutrients:
        db_session.add(nutrient)
    await db_session.commit()


@pytest.fixture
def mock_daily_nutrient_intakes():
    """Create mock daily nutrient intake data for testing."""
    return [
        DailyNutrientIntake(
            id="1",
            nutrient="Calcium",
            unit="mg",
            age=10,
            gender="boy",
            intake=1000.0,
            category="Minerals",
        ),
        DailyNutrientIntake(
            id="2",
            nutrient="Iron",
            unit="mg",
            age=10,
            gender="boy",
            intake=8.0,
            category="Minerals",
        ),
        DailyNutrientIntake(
            id="3",
            nutrient="Calcium",
            unit="mg",
            age=10,
            gender="girl",
            intake=1200.0,
            category="Minerals",
        ),
        DailyNutrientIntake(
            id="4",
            nutrient="Iron",
            unit="mg",
            age=12,
            gender="girl",
            intake=15.0,
            category="Minerals",
        ),
        DailyNutrientIntake(
            id="5",
            nutrient="Vitamin C",
            unit="mg",
            age=8,
            gender="boy",
            intake=45.0,
            category="Vitamins",
        ),
    ]
