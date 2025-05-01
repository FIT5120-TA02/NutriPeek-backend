"""Child Energy Requirement API endpoint tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.child_energy_requirement import ChildEnergyRequirement


@pytest.mark.asyncio
async def test_find_nearest_pal_success(
    client: AsyncClient, test_db: AsyncSession, mock_child_energy_requirements
):
    """Test find nearest PAL endpoint with valid data.

    Args:
        client: Test client
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": 1.4, "age": 8, "gender": "boy"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["input_physical_activity_level"] == 1.4
    assert data["matched_physical_activity_level"] == 1.4
    assert data["age"] == 8
    assert data["gender"] == "boy"
    assert data["unit"] == "kcal/day"
    assert data["estimated_energy_requirement"] == 1800.0


@pytest.mark.asyncio
async def test_find_nearest_pal_approximate_match(
    client: AsyncClient, test_db: AsyncSession, mock_child_energy_requirements
):
    """Test find nearest PAL endpoint with approximate match.

    Args:
        client: Test client
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": 1.5, "age": 8, "gender": "boy"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["input_physical_activity_level"] == 1.5
    # Should get closest match (1.4)
    assert data["matched_physical_activity_level"] == 1.4
    assert data["age"] == 8
    assert data["gender"] == "boy"
    assert data["unit"] == "kcal/day"
    assert data["estimated_energy_requirement"] == 1800.0


@pytest.mark.asyncio
async def test_find_nearest_pal_different_gender(
    client: AsyncClient, test_db: AsyncSession, mock_child_energy_requirements
):
    """Test find nearest PAL endpoint with different gender.

    Args:
        client: Test client
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": 1.4, "age": 8, "gender": "girl"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["input_physical_activity_level"] == 1.4
    assert data["matched_physical_activity_level"] == 1.4
    assert data["age"] == 8
    assert data["gender"] == "girl"
    assert data["unit"] == "kcal/day"
    assert data["estimated_energy_requirement"] == 1700.0


@pytest.mark.asyncio
async def test_find_nearest_pal_different_age(
    client: AsyncClient, test_db: AsyncSession, mock_child_energy_requirements
):
    """Test find nearest PAL endpoint with different age.

    Args:
        client: Test client
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": 1.4, "age": 10, "gender": "boy"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["input_physical_activity_level"] == 1.4
    assert data["matched_physical_activity_level"] == 1.4
    assert data["age"] == 10
    assert data["gender"] == "boy"
    assert data["unit"] == "kcal/day"
    assert data["estimated_energy_requirement"] == 2000.0


@pytest.mark.asyncio
async def test_find_nearest_pal_not_found(
    client: AsyncClient, test_db: AsyncSession, mock_child_energy_requirements
):
    """Test find nearest PAL endpoint with no matching data.

    Args:
        client: Test client
        test_db: Test database session
        mock_child_energy_requirements: Mock data for testing
    """
    # Arrange
    await _seed_test_data(test_db, mock_child_energy_requirements)

    # Act - No data for age 15
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": 1.4, "age": 15, "gender": "boy"},
    )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "No energy requirement data found" in data["detail"]


@pytest.mark.asyncio
async def test_find_nearest_pal_validation_error_age(
    client: AsyncClient, test_db: AsyncSession
):
    """Test find nearest PAL endpoint with invalid age.

    Args:
        client: Test client
        test_db: Test database session
    """
    # Act - Invalid age (negative)
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": 1.4, "age": -1, "gender": "boy"},
    )

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_find_nearest_pal_validation_error_gender(
    client: AsyncClient, test_db: AsyncSession
):
    """Test find nearest PAL endpoint with invalid gender.

    Args:
        client: Test client
        test_db: Test database session
    """
    # Act - Invalid gender
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": 1.4, "age": 8, "gender": "invalid"},
    )

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_find_nearest_pal_validation_error_pal(
    client: AsyncClient, test_db: AsyncSession
):
    """Test find nearest PAL endpoint with invalid PAL.

    Args:
        client: Test client
        test_db: Test database session
    """
    # Act - Invalid PAL (negative)
    response = await client.post(
        "/api/v1/child-energy-requirements/find-nearest-pal",
        json={"physical_activity_level": -1.0, "age": 8, "gender": "boy"},
    )

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


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
