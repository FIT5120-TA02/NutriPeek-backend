"""Unit tests for Activity Service."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.activity_mety_level import ActivityMETyLevel
from src.app.services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_get_distinct_activities(test_db: AsyncSession):
    """Test retrieving distinct activities through service."""
    # Arrange
    mock_activities = ["Walking", "Running", "Swimming"]
    # Mock the CRUD method to return predefined activities
    with patch(
        "src.app.crud.crud_activity_mety_levels.activity_mety_level_crud.get_distinct_activities",
        return_value=mock_activities,
    ):
        service = ActivityService(test_db)

        # Act
        result = await service.get_distinct_activities()

        # Assert
        assert result == mock_activities
        assert len(result) == 3
        assert "Walking" in result
        assert "Running" in result
        assert "Swimming" in result


@pytest.mark.asyncio
async def test_get_mety_level_found(test_db: AsyncSession):
    """Test retrieving METy level when found."""
    # Arrange
    mock_record = ActivityMETyLevel(
        id=1,
        age=30,
        specific_activity="Walking",
        activity_category="Walking",
        mety_level=3.5,
    )
    # Mock the CRUD method to return a predefined record
    with patch(
        "src.app.crud.crud_activity_mety_levels.activity_mety_level_crud.get_closest_age_mety_level",
        return_value=mock_record,
    ):
        service = ActivityService(test_db)

        # Act
        result = await service.get_mety_level(age=30, activity="Walking")

        # Assert
        assert result == 3.5


@pytest.mark.asyncio
async def test_get_mety_level_not_found(test_db: AsyncSession):
    """Test retrieving METy level when not found."""
    # Arrange - Mock the CRUD method to return None
    with patch(
        "src.app.crud.crud_activity_mety_levels.activity_mety_level_crud.get_closest_age_mety_level",
        return_value=None,
    ):
        service = ActivityService(test_db)

        # Act
        result = await service.get_mety_level(age=30, activity="NonExistentActivity")

        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_calculate_physical_activity_level_success(test_db: AsyncSession):
    """Test successful calculation of physical activity level."""
    # Arrange
    activities = [
        {"name": "Walking", "hours": 2.0},
        {"name": "Running", "hours": 1.0},
    ]

    # Create mock service with patched get_mety_level method
    service = ActivityService(test_db)
    service.get_mety_level = AsyncMock()

    # Configure mock to return different METy levels for different activities
    async def mock_get_mety_level(age, activity):
        if activity == "Walking":
            return 3.5
        elif activity == "Running":
            return 8.0
        return None

    service.get_mety_level.side_effect = mock_get_mety_level

    # Act
    result = await service.calculate_physical_activity_level(
        age=30, activities=activities
    )

    # Assert
    assert "pal" in result
    assert "total_mety_minutes" in result
    assert "details" in result

    # Check specific values
    # 2 hours walking (3.5 METy) = 420 METy-minutes
    # 1 hour running (8.0 METy) = 480 METy-minutes
    # 21 hours rest (1.0 METy) = 1260 METy-minutes
    # Total: 2160 METy-minutes / 1440 minutes in a day = 1.5 PAL
    assert result["pal"] == 1.5
    assert result["total_mety_minutes"] == 2160.0

    # Check details
    details = result["details"]
    assert len(details) == 3  # 2 activities + rest

    # Check Walking details
    walking = next((item for item in details if item["activity"] == "Walking"), None)
    assert walking is not None
    assert walking["hours"] == 2.0
    assert walking["mety_level"] == 3.5
    assert walking["mety_minutes"] == 420.0

    # Check Running details
    running = next((item for item in details if item["activity"] == "Running"), None)
    assert running is not None
    assert running["hours"] == 1.0
    assert running["mety_level"] == 8.0
    assert running["mety_minutes"] == 480.0

    # Check Rest details
    rest = next(
        (item for item in details if item["activity"] == "Rest/Other Activities"), None
    )
    assert rest is not None
    assert rest["hours"] == 21.0
    assert rest["mety_level"] == 1.0
    assert rest["mety_minutes"] == 1260.0


@pytest.mark.asyncio
async def test_calculate_physical_activity_level_empty_activities(
    test_db: AsyncSession,
):
    """Test calculation with empty activities list."""
    # Arrange
    service = ActivityService(test_db)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.calculate_physical_activity_level(age=30, activities=[])

    assert excinfo.value.status_code == 400
    assert "No activities provided" in excinfo.value.detail


@pytest.mark.asyncio
async def test_calculate_physical_activity_level_activity_not_found(
    test_db: AsyncSession,
):
    """Test calculation when activity is not found."""
    # Arrange
    activities = [
        {"name": "NonExistentActivity", "hours": 2.0},
    ]

    # Create mock service with patched get_mety_level method that returns None
    service = ActivityService(test_db)
    service.get_mety_level = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        await service.calculate_physical_activity_level(age=30, activities=activities)

    assert excinfo.value.status_code == 404
    assert "Activity 'NonExistentActivity' not found" in excinfo.value.detail


@pytest.mark.asyncio
async def test_calculate_physical_activity_level_invalid_hours(test_db: AsyncSession):
    """Test calculation with invalid hours value."""
    # Arrange
    activities = [
        {"name": "Walking", "hours": -1.0},  # Invalid negative hours
        {"name": "Running", "hours": 1.0},  # Valid hours
    ]

    # Create mock service with patched get_mety_level method
    service = ActivityService(test_db)
    service.get_mety_level = AsyncMock(return_value=5.0)

    # Act
    result = await service.calculate_physical_activity_level(
        age=30, activities=activities
    )

    # Assert - Should skip the invalid activity and only process the valid one
    details = result["details"]
    # Should have 2 items: Running and Rest/Other Activities
    assert len(details) == 2

    # Should not include Walking (negative hours)
    walking = next((item for item in details if item["activity"] == "Walking"), None)
    assert walking is None

    # Should include Running
    running = next((item for item in details if item["activity"] == "Running"), None)
    assert running is not None


@pytest.mark.asyncio
async def test_calculate_physical_activity_level_missing_activity_name(
    test_db: AsyncSession,
):
    """Test calculation with missing activity name."""
    # Arrange
    activities = [
        {"hours": 2.0},  # Missing name
        {"name": "Running", "hours": 1.0},  # Valid
    ]

    # Create mock service with patched get_mety_level method
    service = ActivityService(test_db)
    service.get_mety_level = AsyncMock(return_value=5.0)

    # Act
    result = await service.calculate_physical_activity_level(
        age=30, activities=activities
    )

    # Assert - Should skip the invalid activity and only process the valid one
    details = result["details"]
    # Should have 2 items: Running and Rest/Other Activities
    assert len(details) == 2

    # Should include Running
    running = next((item for item in details if item["activity"] == "Running"), None)
    assert running is not None
