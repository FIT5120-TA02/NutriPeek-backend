"""Unit tests for nutrient endpoints."""

from unittest.mock import patch

import pytest
from fastapi import status
from httpx import AsyncClient

from src.app.schemas.nutrient import NutrientGapResponse, NutrientInfo


@pytest.mark.asyncio
async def test_calculate_nutrient_gap_success(client: AsyncClient):
    """Test successful calculation of nutrient gaps."""
    # Arrange
    test_request_payload = {
        "child_profile": {"age": 10, "gender": "boy"},
        "ingredient_ids": ["1", "2"],
    }

    # Prepare mock response
    mock_response = NutrientGapResponse(
        nutrient_gaps={
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
        missing_nutrients=[],
        excess_nutrients=[],
        total_calories=202.0,
    )

    # Mock the service call
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.calculate_nutrient_gaps",
        return_value=mock_response,
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/calculate-gap", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Check response structure
        data = response.json()
        assert "nutrient_gaps" in data
        assert "missing_nutrients" in data
        assert "excess_nutrients" in data
        assert "total_calories" in data

        # Check specific values
        assert data["total_calories"] == 202.0
        assert len(data["nutrient_gaps"]) == 2
        assert "Calcium" in data["nutrient_gaps"]
        assert "Iron" in data["nutrient_gaps"]
        assert data["nutrient_gaps"]["Calcium"]["gap"] == 680.0
        assert data["nutrient_gaps"]["Iron"]["gap"] == 7.4


@pytest.mark.asyncio
async def test_calculate_nutrient_gap_validation_error(client: AsyncClient):
    """Test validation error when invalid data is provided."""
    # Test cases with invalid data
    invalid_payloads = [
        # Missing required fields
        {},
        # Missing child_profile
        {"ingredient_ids": ["1"]},
        # Missing ingredient_ids
        {"child_profile": {"age": 10, "gender": "boy"}},
        # Missing age in child_profile
        {"child_profile": {"gender": "boy"}, "ingredient_ids": ["1"]},
        # Missing gender in child_profile
        {"child_profile": {"age": 10}, "ingredient_ids": ["1"]},
        # Invalid age (negative)
        {"child_profile": {"age": -5, "gender": "boy"}, "ingredient_ids": ["1"]},
        # Invalid age (too high)
        {"child_profile": {"age": 19, "gender": "boy"}, "ingredient_ids": ["1"]},
        # Invalid gender (not in enum)
        {"child_profile": {"age": 10, "gender": "invalid"}, "ingredient_ids": ["1"]},
        # Empty ingredient list
        {"child_profile": {"age": 10, "gender": "boy"}, "ingredient_ids": []},
    ]

    for payload in invalid_payloads:
        # Act
        response = await client.post("/api/v1/nutrient/calculate-gap", json=payload)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Ensure response contains validation error details
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_calculate_nutrient_gap_not_found(client: AsyncClient):
    """Test resource not found error handling."""
    # Arrange
    test_request_payload = {
        "child_profile": {"age": 10, "gender": "boy"},
        "ingredient_ids": ["999"],  # Non-existent ID
    }

    # Mock service to raise ResourceNotFoundError
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.calculate_nutrient_gaps",
        side_effect=Exception("The following ingredients were not found: 999"),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/calculate-gap", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_calculate_nutrient_gap_internal_error(client: AsyncClient):
    """Test internal server error handling."""
    # Arrange
    test_request_payload = {
        "child_profile": {"age": 10, "gender": "boy"},
        "ingredient_ids": ["1", "2"],
    }

    # Mock service to raise an unexpected error
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.calculate_nutrient_gaps",
        side_effect=Exception("Unexpected error"),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/calculate-gap", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
