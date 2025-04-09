"""Unit tests for NutrientService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.core.exceptions.custom import ResourceNotFoundError
from src.app.models.daily_nutrient_intake import DailyNutrientIntake
from src.app.models.food_nutrient import FoodNutrient
from src.app.schemas.nutrient import NutrientInfo
from src.app.services.nutrient_service import nutrient_service


@pytest.mark.asyncio
async def test_calculate_nutrient_gaps_success():
    """Test successful calculation of nutrient gaps."""
    # Arrange
    mock_db = AsyncMock()
    age = 10
    gender = "boy"
    ingredient_ids = ["1", "2"]

    # Mock recommended intakes
    mock_recommended_intakes = [
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
    ]

    # Mock food nutrients
    mock_food_nutrients = [
        FoodNutrient(
            id="1",
            food_name="Apple",
            calcium_mg=20.0,
            iron_mg=0.5,
            energy_with_fibre_kj=52.0,
        ),
        FoodNutrient(
            id="2",
            food_name="Milk",
            calcium_mg=300.0,
            iron_mg=0.1,
            energy_with_fibre_kj=150.0,
        ),
    ]

    with patch(
        "src.app.services.nutrient_service.daily_nutrient_intake_crud.get_by_age_and_gender",
        return_value=mock_recommended_intakes,
    ) as mock_get_recommended, patch(
        "src.app.services.nutrient_service.NutrientService.get_food_nutrients_by_ids",
        return_value=(mock_food_nutrients, []),
    ) as mock_get_nutrients, patch(
        "src.app.services.nutrient_service.NutrientService.calculate_nutrient_intakes",
        return_value={
            "Calcium": {"amount": 320.0, "unit": "mg"},
            "Iron": {"amount": 0.6, "unit": "mg"},
            "Energy(a)": {"amount": 202.0, "unit": "kJ"},
        },
    ) as mock_calc_intakes, patch(
        "src.app.services.nutrient_service.NutrientService.calculate_gaps",
        return_value=(
            {
                "Calcium": NutrientInfo(
                    name="Calcium",
                    recommended_intake=1000.0,
                    current_intake=320.0,
                    unit="mg",
                    gap=680.0,
                    gap_percentage=68.0,
                    category="Minerals",
                ),
                "Iron": NutrientInfo(
                    name="Iron",
                    recommended_intake=8.0,
                    current_intake=0.6,
                    unit="mg",
                    gap=7.4,
                    gap_percentage=92.5,
                    category="Minerals",
                ),
            },
            [],
            [],
            202.0,
        ),
    ) as mock_calc_gaps:
        # Act
        result = await nutrient_service.calculate_nutrient_gaps(
            mock_db, age=age, gender=gender, ingredient_ids=ingredient_ids
        )

        # Assert
        mock_get_recommended.assert_called_once_with(mock_db, age=age, gender=gender)
        mock_get_nutrients.assert_called_once_with(mock_db, ingredient_ids)
        mock_calc_intakes.assert_called_once_with(mock_food_nutrients)

        # Verify the result structure
        assert "nutrient_gaps" in result.model_dump()
        assert "missing_nutrients" in result.model_dump()
        assert "excess_nutrients" in result.model_dump()
        assert "total_calories" in result.model_dump()

        # Verify specific values
        assert result.total_calories == 202.0
        assert len(result.nutrient_gaps) == 2
        assert "Calcium" in result.nutrient_gaps
        assert "Iron" in result.nutrient_gaps
        assert result.nutrient_gaps["Calcium"].gap == 680.0
        assert result.nutrient_gaps["Iron"].gap == 7.4


@pytest.mark.asyncio
async def test_calculate_nutrient_gaps_no_recommended_intakes():
    """Test calculation of nutrient gaps when no recommended intakes are found."""
    # Arrange
    mock_db = AsyncMock()
    age = 20  # Age not in our mock data
    gender = "boy"
    ingredient_ids = ["1", "2"]

    with patch(
        "src.app.services.nutrient_service.daily_nutrient_intake_crud.get_by_age_and_gender",
        return_value=[],  # Empty list means no recommendations found
    ):
        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as excinfo:
            await nutrient_service.calculate_nutrient_gaps(
                mock_db, age=age, gender=gender, ingredient_ids=ingredient_ids
            )

        assert "No recommended nutrient intake data found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_calculate_nutrient_gaps_missing_ingredients():
    """Test calculation of nutrient gaps when some ingredients are not found."""
    # Arrange
    mock_db = AsyncMock()
    age = 10
    gender = "boy"
    ingredient_ids = ["1", "999"]  # 999 doesn't exist

    # Mock recommended intakes
    mock_recommended_intakes = [
        DailyNutrientIntake(
            id="1",
            nutrient="Calcium",
            unit="mg",
            age=10,
            gender="boy",
            intake=1000.0,
            category="Minerals",
        ),
    ]

    with patch(
        "src.app.services.nutrient_service.daily_nutrient_intake_crud.get_by_age_and_gender",
        return_value=mock_recommended_intakes,
    ), patch(
        "src.app.services.nutrient_service.NutrientService.get_food_nutrients_by_ids",
        return_value=(
            [FoodNutrient(id="1", food_name="Apple")],
            ["999"],
        ),  # One ingredient found, one missing
    ):
        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as excinfo:
            await nutrient_service.calculate_nutrient_gaps(
                mock_db, age=age, gender=gender, ingredient_ids=ingredient_ids
            )

        assert "The following ingredients were not found: 999" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_food_nutrients_by_ids():
    """Test retrieving food nutrients by IDs."""
    # Arrange
    mock_db = AsyncMock()
    ingredient_ids = ["1", "2", "999"]  # 999 doesn't exist

    # Mock the CRUD method
    mock_get = AsyncMock()
    mock_get.side_effect = lambda db, id: (
        FoodNutrient(id=id, food_name=f"Food {id}") if id != "999" else None
    )

    with patch("src.app.services.nutrient_service.food_nutrient_crud.get", mock_get):
        # Act
        found, missing = await nutrient_service.get_food_nutrients_by_ids(
            mock_db, ingredient_ids
        )

        # Assert
        assert len(found) == 2
        assert len(missing) == 1
        assert missing[0] == "999"
        assert found[0].id == "1"
        assert found[1].id == "2"
        assert mock_get.call_count == 3


def test_calculate_nutrient_intakes():
    """Test calculation of nutrient intakes from food nutrients."""
    # Arrange
    food_nutrients = [
        # Create a FoodNutrient with some nutrient values
        MagicMock(
            spec=FoodNutrient,
            calcium_mg=200.0,
            iron_mg=1.5,
            vitamin_c_mg=30.0,
            protein_g=5.0,
            energy_with_fibre_kj=150.0,
        ),
        # Create another FoodNutrient with different values
        MagicMock(
            spec=FoodNutrient,
            calcium_mg=100.0,
            iron_mg=0.5,
            vitamin_c_mg=10.0,
            protein_g=3.0,
            energy_with_fibre_kj=100.0,
        ),
    ]

    # Act
    result = nutrient_service.calculate_nutrient_intakes(food_nutrients)

    # Assert
    assert "Calcium" in result
    assert "Iron" in result
    assert "Vitamin C" in result
    assert "Protein" in result
    assert "Energy(a)" in result

    assert result["Calcium"]["amount"] == 300.0
    assert result["Iron"]["amount"] == 2.0
    assert result["Vitamin C"]["amount"] == 40.0
    assert result["Protein"]["amount"] == 8.0
    assert result["Energy(a)"]["amount"] == 250.0


def test_calculate_gaps():
    """Test calculation of gaps between recommended and actual intakes."""
    # Arrange
    recommended_intakes = [
        MagicMock(
            nutrient="Calcium",
            intake=1000.0,
            unit="mg",
            category="Minerals",
        ),
        MagicMock(
            nutrient="Iron",
            intake=8.0,
            unit="mg",
            category="Minerals",
        ),
        MagicMock(
            nutrient="Vitamin C",
            intake=45.0,
            unit="mg",
            category="Vitamins",
        ),
    ]

    nutrient_intakes = {
        "Calcium": {"amount": 300.0, "unit": "mg"},
        "Iron": {"amount": 10.0, "unit": "mg"},  # Exceeds recommendation
        "Vitamin C": {"amount": 0.0, "unit": "mg"},  # Missing (zero intake)
        "Energy(a)": {"amount": 250.0, "unit": "kJ"},
    }

    # Act
    nutrient_gaps, missing_nutrients, excess_nutrients, total_calories = (
        nutrient_service.calculate_gaps(recommended_intakes, nutrient_intakes)
    )

    # Assert
    assert len(nutrient_gaps) == 3
    assert len(missing_nutrients) == 1
    assert len(excess_nutrients) == 1
    assert total_calories == 250.0

    # Check missing nutrients
    assert "Vitamin C" in missing_nutrients

    # Check excess nutrients
    assert "Iron" in excess_nutrients

    # Check gap calculations
    assert nutrient_gaps["Calcium"].gap == 700.0
    assert nutrient_gaps["Calcium"].gap_percentage == 70.0

    assert nutrient_gaps["Iron"].gap == -2.0  # Negative gap (excess)
    assert nutrient_gaps["Iron"].gap_percentage == -25.0

    assert nutrient_gaps["Vitamin C"].gap == 45.0  # Full gap (missing)
    assert nutrient_gaps["Vitamin C"].gap_percentage == 100.0
