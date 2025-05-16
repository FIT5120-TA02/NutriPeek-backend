"""Unit tests for nutrient endpoints."""

from unittest.mock import patch

import pytest
from fastapi import status
from httpx import AsyncClient

from src.app.schemas.food import FoodRecommendation, OptimizedFoodRecommendation
from src.app.schemas.nutrient import (
    NutrientGapResponse,
    NutrientInfo,
    NutrientIntakeInfo,
    NutrientIntakeResponse,
)


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


@pytest.mark.asyncio
async def test_get_nutrient_intake_success(client: AsyncClient):
    """Test successful retrieval of required nutrient intake."""
    # Arrange
    test_request_payload = {
        "age": 10,
        "gender": "boy",
    }

    # Prepare mock response
    mock_response = NutrientIntakeResponse(
        nutrient_intakes={
            "Energy(a)": NutrientIntakeInfo(
                name="Energy(a)",
                recommended_intake=8500.0,
                unit="kJ",
                category="Energy",
            ),
            "Protein": NutrientIntakeInfo(
                name="Protein",
                recommended_intake=40.0,
                unit="g",
                category="Macronutrients",
            ),
            "Total Fat(c)": NutrientIntakeInfo(
                name="Total Fat(c)",
                recommended_intake=67.0,
                unit="g",
                category="Macronutrients",
            ),
            "Carbohydrate(c)": NutrientIntakeInfo(
                name="Carbohydrate(c)",
                recommended_intake=230.0,
                unit="g",
                category="Macronutrients",
            ),
            "Dietary Fibre": NutrientIntakeInfo(
                name="Dietary Fibre",
                recommended_intake=24.0,
                unit="g",
                category="Macronutrients",
            ),
        },
    )

    # Mock the service call
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.get_required_nutrient_intake",
        return_value=mock_response,
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/nutrient-intake", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Check response structure
        data = response.json()
        assert "nutrient_intakes" in data

        # Check for required nutrients
        assert "Energy(a)" in data["nutrient_intakes"]
        assert "Protein" in data["nutrient_intakes"]
        assert "Total Fat(c)" in data["nutrient_intakes"]
        assert "Carbohydrate(c)" in data["nutrient_intakes"]
        assert "Dietary Fibre" in data["nutrient_intakes"]

        # Check specific values
        assert data["nutrient_intakes"]["Energy(a)"]["recommended_intake"] == 8500.0
        assert data["nutrient_intakes"]["Protein"]["recommended_intake"] == 40.0
        assert data["nutrient_intakes"]["Total Fat(c)"]["recommended_intake"] == 67.0
        assert (
            data["nutrient_intakes"]["Carbohydrate(c)"]["recommended_intake"] == 230.0
        )
        assert data["nutrient_intakes"]["Dietary Fibre"]["recommended_intake"] == 24.0


@pytest.mark.asyncio
async def test_get_nutrient_intake_validation_error(client: AsyncClient):
    """Test validation error when invalid data is provided for nutrient intake."""
    # Test cases with invalid data
    invalid_payloads = [
        # Missing required fields
        {},
        # Missing age
        {"gender": "boy"},
        # Missing gender
        {"age": 10},
        # Invalid age (negative)
        {"age": -5, "gender": "boy"},
        # Invalid age (too high)
        {"age": 19, "gender": "boy"},
        # Invalid gender (not in enum)
        {"age": 10, "gender": "invalid"},
    ]

    for payload in invalid_payloads:
        # Act
        response = await client.post("/api/v1/nutrient/nutrient-intake", json=payload)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Ensure response contains validation error details
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_nutrient_intake_not_found(client: AsyncClient):
    """Test resource not found error handling for nutrient intake."""
    # Arrange
    test_request_payload = {
        "age": 99,  # Age without data
        "gender": "boy",
    }

    # Mock service to raise ResourceNotFoundError
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.get_required_nutrient_intake",
        side_effect=Exception(
            "No recommended nutrient intake data found for age 99 and gender boy"
        ),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/nutrient-intake", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_nutrient_intake_internal_error(client: AsyncClient):
    """Test internal server error handling for nutrient intake."""
    # Arrange
    test_request_payload = {
        "age": 10,
        "gender": "boy",
    }

    # Mock service to raise an unexpected error
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.get_required_nutrient_intake",
        side_effect=Exception("Unexpected error"),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/nutrient-intake", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_recommend_food_success(client: AsyncClient):
    """Test successful recommendation of foods rich in a specific nutrient."""
    # Mock response data
    mock_response = [
        FoodRecommendation(
            id="1",
            food_name="Salmon, Atlantic, farmed",
            food_category="Fish/Seafood",
            nutrient_value=20.5,
            nutrients={
                "protein_g": 20.5,
                "total_fat_g": 12.3,
                "energy_with_fibre_kj": 840,
                "iron_mg": 0.3,
            },
        ),
        FoodRecommendation(
            id="2",
            food_name="Beef, lean",
            food_category="Meat",
            nutrient_value=18.7,
            nutrients={
                "protein_g": 18.7,
                "total_fat_g": 6.8,
                "energy_with_fibre_kj": 650,
                "iron_mg": 2.1,
            },
        ),
    ]

    # Mock the service call
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_food_by_nutrient",
        return_value=mock_response,
    ):
        # Act
        response = await client.get(
            "/api/v1/nutrient/recommend-food?nutrient_name=protein_g&limit=2"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Check structure of returned data
        assert "id" in data[0]
        assert "food_name" in data[0]
        assert "food_category" in data[0]
        assert "nutrient_value" in data[0]
        assert "nutrients" in data[0]

        # Check specific values
        assert data[0]["food_name"] == "Salmon, Atlantic, farmed"
        assert data[0]["nutrient_value"] == 20.5
        assert data[1]["food_name"] == "Beef, lean"
        assert data[1]["nutrient_value"] == 18.7


@pytest.mark.asyncio
async def test_recommend_food_validation_error(client: AsyncClient):
    """Test validation error for food recommendation endpoint."""
    # Test with missing required parameter
    response = await client.get("/api/v1/nutrient/recommend-food")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with invalid limit
    response = await client.get(
        "/api/v1/nutrient/recommend-food?nutrient_name=protein_g&limit=100"
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_recommend_food_bad_request(client: AsyncClient):
    """Test bad request error handling for food recommendation."""
    # Mock service to raise ValueError
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_food_by_nutrient",
        side_effect=ValueError("Invalid nutrient column: invalid_nutrient"),
    ):
        # Act
        response = await client.get(
            "/api/v1/nutrient/recommend-food?nutrient_name=invalid_nutrient"
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_recommend_food_internal_error(client: AsyncClient):
    """Test internal server error handling for food recommendation."""
    # Mock service to raise an unexpected error
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_food_by_nutrient",
        side_effect=Exception("Database connection error"),
    ):
        # Act
        response = await client.get(
            "/api/v1/nutrient/recommend-food?nutrient_name=protein_g"
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_recommend_optimized_food_success(client: AsyncClient):
    """Test successful recommendation of optimized foods for a nutrient gap."""
    # Arrange
    test_request_payload = {
        "nutrient_name": "protein_g",
        "target_amount": 20.0,
        "current_amount": 5.0,
        "limit": 2,
    }

    # Mock response data
    mock_response = [
        OptimizedFoodRecommendation(
            id="1",
            food_name="Chicken breast",
            food_category="Poultry",
            nutrient_value=22.3,
            amount_needed=67.3,
            gap_satisfaction_percentage=149.0,
            nutrients={
                "protein_g": 22.3,
                "total_fat_g": 1.2,
                "energy_with_fibre_kj": 450,
            },
        ),
        OptimizedFoodRecommendation(
            id="2",
            food_name="Greek yogurt",
            food_category="Dairy",
            nutrient_value=10.0,
            amount_needed=150.0,
            gap_satisfaction_percentage=66.7,
            nutrients={
                "protein_g": 10.0,
                "total_fat_g": 5.0,
                "energy_with_fibre_kj": 350,
            },
        ),
    ]

    # Mock the service call
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_optimized_food",
        return_value=mock_response,
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-optimized-food", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Check structure of returned data
        assert "id" in data[0]
        assert "food_name" in data[0]
        assert "food_category" in data[0]
        assert "nutrient_value" in data[0]
        assert "amount_needed" in data[0]
        assert "gap_satisfaction_percentage" in data[0]
        assert "nutrients" in data[0]

        # Check specific values
        assert data[0]["food_name"] == "Chicken breast"
        assert data[0]["amount_needed"] == 67.3
        assert data[1]["food_name"] == "Greek yogurt"
        assert data[1]["gap_satisfaction_percentage"] == 66.7


@pytest.mark.asyncio
async def test_recommend_optimized_food_validation_error(client: AsyncClient):
    """Test validation error for optimized food recommendation endpoint."""
    # Test cases with invalid data
    invalid_payloads = [
        # Missing required fields
        {},
        # Missing nutrient_name
        {"target_amount": 20.0, "current_amount": 5.0},
        # Missing target_amount
        {"nutrient_name": "protein_g", "current_amount": 5.0},
        # Invalid target_amount (negative)
        {"nutrient_name": "protein_g", "target_amount": -5.0, "current_amount": 5.0},
        # Invalid current_amount (negative)
        {"nutrient_name": "protein_g", "target_amount": 20.0, "current_amount": -5.0},
        # Invalid limit (too high)
        {"nutrient_name": "protein_g", "target_amount": 20.0, "limit": 100},
    ]

    for payload in invalid_payloads:
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-optimized-food", json=payload
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Ensure response contains validation error details
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_recommend_optimized_food_bad_request(client: AsyncClient):
    """Test bad request error handling for optimized food recommendation."""
    # Arrange
    test_request_payload = {
        "nutrient_name": "invalid_nutrient",
        "target_amount": 20.0,
        "current_amount": 5.0,
    }

    # Mock service to raise ValueError
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_optimized_food",
        side_effect=ValueError("Invalid nutrient column: invalid_nutrient"),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-optimized-food", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_recommend_optimized_food_internal_error(client: AsyncClient):
    """Test internal server error handling for optimized food recommendation."""
    # Arrange
    test_request_payload = {
        "nutrient_name": "protein_g",
        "target_amount": 20.0,
        "current_amount": 5.0,
    }

    # Mock service to raise an unexpected error
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_optimized_food",
        side_effect=Exception("Database connection error"),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-optimized-food", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_recommend_seasonal_food_success(client: AsyncClient):
    """Test successful recommendation of seasonal foods rich in a specific nutrient."""
    # Arrange
    test_request_payload = {
        "nutrient_name": "vitamin_c_mg",
        "region": "australia",
        "month": "january",
        "limit": 2,
    }

    # Mock response data
    mock_response = [
        FoodRecommendation(
            id="1",
            food_name="Oranges",
            food_category="Fruit",
            nutrient_value=45.0,
            nutrients={
                "vitamin_c_mg": 45.0,
                "total_fat_g": 0.1,
                "energy_with_fibre_kj": 160,
            },
        ),
        FoodRecommendation(
            id="2",
            food_name="Strawberries",
            food_category="Fruit",
            nutrient_value=40.0,
            nutrients={
                "vitamin_c_mg": 40.0,
                "total_fat_g": 0.3,
                "energy_with_fibre_kj": 120,
            },
        ),
    ]

    # Mock the service call
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_seasonal_food",
        return_value=mock_response,
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-seasonal-food", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Check structure of returned data
        assert "id" in data[0]
        assert "food_name" in data[0]
        assert "food_category" in data[0]
        assert "nutrient_value" in data[0]
        assert "nutrients" in data[0]

        # Check specific values
        assert data[0]["food_name"] == "Oranges"
        assert data[0]["nutrient_value"] == 45.0
        assert data[1]["food_name"] == "Strawberries"
        assert data[1]["nutrient_value"] == 40.0


@pytest.mark.asyncio
async def test_recommend_seasonal_food_with_season(client: AsyncClient):
    """Test successful recommendation of seasonal foods using season instead of month."""
    # Arrange
    test_request_payload = {
        "nutrient_name": "vitamin_c_mg",
        "region": "australia",
        "season": "Summer",
        "limit": 2,
    }

    # Mock response data - same as above test
    mock_response = [
        FoodRecommendation(
            id="1",
            food_name="Oranges",
            food_category="Fruit",
            nutrient_value=45.0,
            nutrients={
                "vitamin_c_mg": 45.0,
                "total_fat_g": 0.1,
                "energy_with_fibre_kj": 160,
            },
        ),
        FoodRecommendation(
            id="2",
            food_name="Strawberries",
            food_category="Fruit",
            nutrient_value=40.0,
            nutrients={
                "vitamin_c_mg": 40.0,
                "total_fat_g": 0.3,
                "energy_with_fibre_kj": 120,
            },
        ),
    ]

    # Mock the service call
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_seasonal_food",
        return_value=mock_response,
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-seasonal-food", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2


@pytest.mark.asyncio
async def test_recommend_seasonal_food_validation_error(client: AsyncClient):
    """Test validation error for seasonal food recommendation endpoint."""
    # Test cases with invalid data
    invalid_payloads = [
        # Missing required fields
        {},
        # Missing nutrient_name
        {"region": "australia", "month": "january"},
        # Missing region
        {"nutrient_name": "vitamin_c_mg", "month": "january"},
        # Invalid limit (too high)
        {"nutrient_name": "vitamin_c_mg", "region": "australia", "limit": 100},
        # Both month and season provided (mutually exclusive)
        {
            "nutrient_name": "vitamin_c_mg",
            "region": "australia",
            "month": "january",
            "season": "Summer",
        },
    ]

    for payload in invalid_payloads:
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-seasonal-food", json=payload
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Ensure response contains validation error details
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_recommend_seasonal_food_bad_request(client: AsyncClient):
    """Test bad request error handling for seasonal food recommendation."""
    # Arrange
    test_request_payload = {
        "nutrient_name": "invalid_nutrient",
        "region": "australia",
        "month": "january",
    }

    # Mock service to raise ValueError
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_seasonal_food",
        side_effect=ValueError("Invalid nutrient column: invalid_nutrient"),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-seasonal-food", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_recommend_seasonal_food_internal_error(client: AsyncClient):
    """Test internal server error handling for seasonal food recommendation."""
    # Arrange
    test_request_payload = {
        "nutrient_name": "vitamin_c_mg",
        "region": "australia",
        "month": "january",
    }

    # Mock service to raise an unexpected error
    with patch(
        "src.app.api.v1.nutrient.nutrient_service.recommend_seasonal_food",
        side_effect=Exception("Database connection error"),
    ):
        # Act
        response = await client.post(
            "/api/v1/nutrient/recommend-seasonal-food", json=test_request_payload
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.json()
