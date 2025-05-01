"""Unit tests for activity endpoints."""

from unittest.mock import patch

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_activities_success(client: AsyncClient):
    """Test successful retrieval of available activities."""
    # Arrange - Mock data similar to what would be returned by the service
    mock_activities = ["Walking", "Running", "Swimming"]

    # Mock the CRUD operation to return our test data
    with patch(
        "src.app.crud.crud_activity_mety_levels.activity_mety_level_crud.get_distinct_activities",
        return_value=mock_activities,
    ):
        # Act
        response = await client.get("/api/v1/activity/activities")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "activities" in response_data
        assert response_data["activities"] == mock_activities
        assert len(response_data["activities"]) == 3


@pytest.mark.asyncio
async def test_get_activities_empty_result(client: AsyncClient):
    """Test behavior when no activities are found."""
    # Mock the CRUD operation to return an empty list
    with patch(
        "src.app.crud.crud_activity_mety_levels.activity_mety_level_crud.get_distinct_activities",
        return_value=[],
    ):
        # Act
        response = await client.get("/api/v1/activity/activities")

        # Assert - should return 200 with empty list
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "activities" in response_data
        assert response_data["activities"] == []
        assert len(response_data["activities"]) == 0


@pytest.mark.asyncio
async def test_get_activities_server_error(client: AsyncClient):
    """Test internal server error handling for activities endpoint."""
    # Mock the CRUD operation to raise an exception
    with patch(
        "src.app.crud.crud_activity_mety_levels.activity_mety_level_crud.get_distinct_activities",
        side_effect=Exception("Database error"),
    ):
        # Act
        response = await client.get("/api/v1/activity/activities")

        # Assert - should return 500 with error detail
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.json()
        assert "Error retrieving activities" in response.json()["detail"]


@pytest.mark.asyncio
async def test_calculate_pal_success(client: AsyncClient):
    """Test successful calculation of Physical Activity Level (PAL)."""
    # Arrange - Mock data for the request
    request_data = {
        "age": 30,
        "activities": [
            {"name": "Walking", "hours": 2.0},
            {"name": "Running", "hours": 1.0},
        ],
    }

    # Mock result that would be returned by the service
    mock_result = {
        "pal": 1.5,
        "total_mety_minutes": 2160.0,
        "details": [
            {
                "activity": "Walking",
                "hours": 2.0,
                "mety_level": 3.5,
                "mety_minutes": 420.0,
            },
            {
                "activity": "Running",
                "hours": 1.0,
                "mety_level": 8.0,
                "mety_minutes": 480.0,
            },
            {
                "activity": "Rest/Other Activities",
                "hours": 21.0,
                "mety_level": 1.0,
                "mety_minutes": 1260.0,
            },
        ],
    }

    # Mock the service method
    with patch(
        "src.app.services.activity_service.ActivityService.calculate_physical_activity_level",
        return_value=mock_result,
    ):
        # Act
        response = await client.post(
            "/api/v1/activity/calculate-pal", json=request_data
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        # Check structure and values of the response
        assert "pal" in response_data
        assert "total_mety_minutes" in response_data
        assert "details" in response_data

        assert response_data["pal"] == 1.5
        assert response_data["total_mety_minutes"] == 2160.0
        assert len(response_data["details"]) == 3


@pytest.mark.asyncio
async def test_calculate_pal_validation_error(client: AsyncClient):
    """Test validation error handling in PAL calculation endpoint."""
    # Test cases with invalid request data
    test_cases = [
        # Missing age
        {
            "activities": [
                {"name": "Walking", "hours": 2.0},
            ]
        },
        # Age too low
        {
            "age": -5,
            "activities": [
                {"name": "Walking", "hours": 2.0},
            ],
        },
        # Missing activities field
        {
            "age": 30,
        },
        # Empty activities list - 400 bad request with explicit validation now
        {"age": 30, "activities": []},
        # Invalid activity structure (missing hours)
        {"age": 30, "activities": [{"name": "Walking"}]},
        # Invalid activity structure (missing name)
        {"age": 30, "activities": [{"hours": 2.0}]},
        # Negative hours
        {"age": 30, "activities": [{"name": "Walking", "hours": -2.0}]},
    ]

    for i, test_case in enumerate(test_cases):
        # Act
        response = await client.post("/api/v1/activity/calculate-pal", json=test_case)

        # Assert - check if the test case index is 3, which is the empty activities list
        if i == 3:  # Empty activities list
            assert (
                response.status_code == status.HTTP_400_BAD_REQUEST
            ), f"Test case {i} failed"
        else:
            assert (
                response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            ), f"Test case {i} failed"

        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_calculate_pal_service_error(client: AsyncClient):
    """Test service error handling in PAL calculation endpoint."""
    # Arrange - Valid request data
    request_data = {
        "age": 30,
        "activities": [
            {"name": "Walking", "hours": 2.0},
        ],
    }

    # Mock the service to raise an exception
    with patch(
        "src.app.services.activity_service.ActivityService.calculate_physical_activity_level",
        side_effect=Exception("Service error"),
    ):
        # Act
        response = await client.post(
            "/api/v1/activity/calculate-pal", json=request_data
        )

        # Assert - should return 500 with error detail
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = response.json()
        assert "detail" in response_data
        assert "Error calculating PAL" in response_data["detail"]


@pytest.mark.asyncio
async def test_calculate_pal_activity_not_found(client: AsyncClient):
    """Test activity not found handling in PAL calculation endpoint."""
    # Arrange - Valid request data
    request_data = {
        "age": 30,
        "activities": [
            {"name": "NonExistentActivity", "hours": 2.0},
        ],
    }

    # Mock the service to raise an exception with 'not found' message
    with patch(
        "src.app.services.activity_service.ActivityService.calculate_physical_activity_level",
        side_effect=Exception("Activity 'NonExistentActivity' not found"),
    ):
        # Act
        response = await client.post(
            "/api/v1/activity/calculate-pal", json=request_data
        )

        # Assert - should get a 404 error now
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert "detail" in response_data
        assert "not found" in response_data["detail"].lower()
