"""Unit tests for Child Energy Requirement CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_child_energy_requirement import child_energy_requirement
from src.app.models.child_energy_requirement import ChildEnergyRequirement


@pytest.mark.asyncio
async def test_get_unique_activity_levels(
    test_db: AsyncSession, mock_child_energy_requirements
):
    """Test retrieving unique physical activity levels.

    Args:
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act
    result = await child_energy_requirement.get_unique_activity_levels(test_db)

    # Assert
    assert len(result) == 3
    assert 1.0 in result
    assert 1.4 in result
    assert 1.8 in result


@pytest.mark.asyncio
async def test_find_nearest_pal_exact_match(
    test_db: AsyncSession, mock_child_energy_requirements
):
    """Test finding nearest PAL with exact match.

    Args:
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act
    result = await child_energy_requirement.find_nearest_pal(
        db=test_db, target_pal=1.4, age=8, gender="boy"
    )

    # Assert
    assert result is not None
    assert result.age == 8
    assert result.gender == "boy"
    assert result.physical_activity_level == 1.4
    assert result.estimated_energy_requirement == 1800.0


@pytest.mark.asyncio
async def test_find_nearest_pal_approximate_match(
    test_db: AsyncSession, mock_child_energy_requirements
):
    """Test finding nearest PAL with approximate match.

    Args:
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act - PAL 1.2 doesn't exist, should get PAL 1.0 or 1.4 as closest
    result = await child_energy_requirement.find_nearest_pal(
        db=test_db, target_pal=1.2, age=8, gender="boy"
    )

    # Assert
    assert result is not None
    assert result.age == 8
    assert result.gender == "boy"
    # Should return the closest PAL value (either 1.0 or 1.4)
    assert result.physical_activity_level in [1.0, 1.4]


@pytest.mark.asyncio
async def test_find_nearest_pal_higher_pal(
    test_db: AsyncSession, mock_child_energy_requirements
):
    """Test finding nearest PAL when higher PAL is closer.

    Args:
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act - PAL 1.6 doesn't exist, should get PAL 1.8 as closest
    result = await child_energy_requirement.find_nearest_pal(
        db=test_db, target_pal=1.6, age=8, gender="boy"
    )

    # Assert
    assert result is not None
    assert result.age == 8
    assert result.gender == "boy"
    assert result.physical_activity_level == 1.8
    assert result.estimated_energy_requirement == 2200.0


@pytest.mark.asyncio
async def test_find_nearest_pal_no_matching_age_gender(
    test_db: AsyncSession, mock_child_energy_requirements
):
    """Test finding nearest PAL with no matching age and gender.

    Args:
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act - No data for age 15
    result = await child_energy_requirement.find_nearest_pal(
        db=test_db, target_pal=1.4, age=15, gender="boy"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_find_nearest_pal_no_matching_gender(
    test_db: AsyncSession, mock_child_energy_requirements
):
    """Test finding nearest PAL with no matching gender.

    Args:
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act - No data for gender "invalid"
    result = await child_energy_requirement.find_nearest_pal(
        db=test_db, target_pal=1.4, age=8, gender="invalid"
    )

    # Assert
    assert result is None


# Helper function to seed test data
async def _seed_test_data(db_session: AsyncSession, mock_data):
    """Seed the database with test child energy requirement data.

    Args:
        db_session: Database session
        mock_data: Mock data to seed
    """
    for item in mock_data:
        db_session.add(item)
    await db_session.commit()


@pytest.fixture
def mock_child_energy_requirements():
    """Create mock child energy requirement data for testing.

    Returns:
        List of ChildEnergyRequirement instances
    """
    return [
        # Boys data
        ChildEnergyRequirement(
            age=8,
            gender="boy",
            unit="kcal/day",
            physical_activity_level=1.0,
            estimated_energy_requirement=1400.0,
        ),
        ChildEnergyRequirement(
            age=8,
            gender="boy",
            unit="kcal/day",
            physical_activity_level=1.4,
            estimated_energy_requirement=1800.0,
        ),
        ChildEnergyRequirement(
            age=8,
            gender="boy",
            unit="kcal/day",
            physical_activity_level=1.8,
            estimated_energy_requirement=2200.0,
        ),
        # Girls data
        ChildEnergyRequirement(
            age=8,
            gender="girl",
            unit="kcal/day",
            physical_activity_level=1.0,
            estimated_energy_requirement=1300.0,
        ),
        ChildEnergyRequirement(
            age=8,
            gender="girl",
            unit="kcal/day",
            physical_activity_level=1.4,
            estimated_energy_requirement=1700.0,
        ),
        ChildEnergyRequirement(
            age=8,
            gender="girl",
            unit="kcal/day",
            physical_activity_level=1.8,
            estimated_energy_requirement=2100.0,
        ),
        # Different age data
        ChildEnergyRequirement(
            age=10,
            gender="boy",
            unit="kcal/day",
            physical_activity_level=1.0,
            estimated_energy_requirement=1600.0,
        ),
        ChildEnergyRequirement(
            age=10,
            gender="boy",
            unit="kcal/day",
            physical_activity_level=1.4,
            estimated_energy_requirement=2000.0,
        ),
        ChildEnergyRequirement(
            age=10,
            gender="boy",
            unit="kcal/day",
            physical_activity_level=1.8,
            estimated_energy_requirement=2400.0,
        ),
    ]
