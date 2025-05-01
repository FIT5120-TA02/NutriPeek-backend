"""Unit tests for Activity METy Level CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_activity_mety_levels import activity_mety_level_crud
from src.app.models.activity_mety_level import ActivityMETyLevel


@pytest.mark.asyncio
async def test_get_distinct_activities(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving distinct activities."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act
    result = await activity_mety_level_crud.get_distinct_activities(test_db)

    # Assert
    assert len(result) == 3
    assert "Walking" in result
    assert "Running" in result
    assert "Swimming" in result


@pytest.mark.asyncio
async def test_get_mety_level_by_age_and_activity_exact_match(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving METy level with exact age and activity match."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act
    result = await activity_mety_level_crud.get_mety_level_by_age_and_activity(
        test_db, age=30, specific_activity="Walking"
    )

    # Assert
    assert result is not None
    assert result.age == 30
    assert result.specific_activity == "Walking"
    assert result.mety_level == 3.5


@pytest.mark.asyncio
async def test_get_mety_level_by_age_and_activity_no_match(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving METy level with no matching age and activity."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act
    result = await activity_mety_level_crud.get_mety_level_by_age_and_activity(
        test_db, age=99, specific_activity="Walking"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_mety_level_by_age_and_activity_no_such_activity(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving METy level with non-existent activity."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act
    result = await activity_mety_level_crud.get_mety_level_by_age_and_activity(
        test_db, age=30, specific_activity="NonExistentActivity"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_closest_age_mety_level_exact_match(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving closest age METy level when exact match exists."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act
    result = await activity_mety_level_crud.get_closest_age_mety_level(
        test_db, age=30, specific_activity="Walking"
    )

    # Assert
    assert result is not None
    assert result.age == 30
    assert result.specific_activity == "Walking"
    assert result.mety_level == 3.5


@pytest.mark.asyncio
async def test_get_closest_age_mety_level_approximate_match(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving closest age METy level when approximate match exists."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act - Age 32 doesn't exist, should get age 30 as closest
    result = await activity_mety_level_crud.get_closest_age_mety_level(
        test_db, age=32, specific_activity="Walking"
    )

    # Assert
    assert result is not None
    assert result.age == 30  # Closest available age
    assert result.specific_activity == "Walking"
    assert result.mety_level == 3.5


@pytest.mark.asyncio
async def test_get_closest_age_mety_level_older_age(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving closest age METy level when older age is closest."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act - Age 55 doesn't exist, should get age 60 as closest for Running
    result = await activity_mety_level_crud.get_closest_age_mety_level(
        test_db, age=55, specific_activity="Running"
    )

    # Assert
    assert result is not None
    assert result.age == 60  # Closest available age
    assert result.specific_activity == "Running"
    assert result.mety_level == 7.0


@pytest.mark.asyncio
async def test_get_closest_age_mety_level_no_such_activity(
    test_db: AsyncSession, mock_activity_mety_levels
):
    """Test retrieving closest age METy level with non-existent activity."""
    # Arrange
    await _seed_test_data(test_db, mock_activity_mety_levels)

    # Act
    result = await activity_mety_level_crud.get_closest_age_mety_level(
        test_db, age=30, specific_activity="NonExistentActivity"
    )

    # Assert
    assert result is None


# Helper function to seed test data
async def _seed_test_data(db_session: AsyncSession, mock_data):
    """Seed the database with test activity METy level data."""
    for item in mock_data:
        db_session.add(item)
    await db_session.commit()


@pytest.fixture
def mock_activity_mety_levels():
    """Create mock activity METy level data for testing."""
    return [
        ActivityMETyLevel(
            id=1,
            age=30,
            specific_activity="Walking",
            activity_category="Walking",
            mety_level=3.5,
        ),
        ActivityMETyLevel(
            id=2,
            age=30,
            specific_activity="Running",
            activity_category="Running",
            mety_level=8.0,
        ),
        ActivityMETyLevel(
            id=3,
            age=30,
            specific_activity="Swimming",
            activity_category="Swimming",
            mety_level=6.0,
        ),
        ActivityMETyLevel(
            id=4,
            age=60,
            specific_activity="Walking",
            activity_category="Walking",
            mety_level=3.0,
        ),
        ActivityMETyLevel(
            id=5,
            age=60,
            specific_activity="Running",
            activity_category="Running",
            mety_level=7.0,
        ),
        ActivityMETyLevel(
            id=6,
            age=60,
            specific_activity="Swimming",
            activity_category="Swimming",
            mety_level=5.0,
        ),
    ]
