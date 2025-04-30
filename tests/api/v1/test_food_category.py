"""Unit tests for food category endpoints."""

from unittest.mock import patch

import pytest
from fastapi import status
from httpx import AsyncClient

from src.app.models.food_category_fun_fact import FoodCategoryFunFact


@pytest.mark.asyncio
async def test_get_food_category_fun_facts_success(client: AsyncClient):
    """Test successful retrieval of multiple food category fun facts."""
    # Arrange - Mock data similar to what would be returned by the CRUD operation
    mock_fun_facts = [
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
    ]

    # Mock the CRUD operation to return our test data
    with patch(
        "src.app.api.v1.food_category.food_category_fun_fact_crud.get_random_fun_facts",
        return_value=mock_fun_facts,
    ):
        # Act
        response = await client.get("/api/v1/food-category/fun-facts")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "fun_facts" in response_data
        assert len(response_data["fun_facts"]) == 2

        # Check structure of returned fun facts
        for fun_fact in response_data["fun_facts"]:
            assert "id" in fun_fact
            assert "category" in fun_fact
            assert "fun_fact" in fun_fact

        # Check specific content - the API transforms food_category (model) to category (schema)
        assert any(fact["category"] == "Apples" for fact in response_data["fun_facts"])
        assert any(fact["category"] == "Bananas" for fact in response_data["fun_facts"])


@pytest.mark.asyncio
async def test_get_food_category_fun_facts_with_categories(client: AsyncClient):
    """Test retrieval of fun facts for specific categories."""
    # Arrange - Mock data for specific categories
    mock_fun_facts = [
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
    ]

    # Mock the CRUD operation to return our test data
    with patch(
        "src.app.api.v1.food_category.food_category_fun_fact_crud.get_fun_facts_by_categories",
        return_value=mock_fun_facts,
    ):
        # Act
        response = await client.get(
            "/api/v1/food-category/fun-facts?categories=Apples&categories=Bananas"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "fun_facts" in response_data
        assert len(response_data["fun_facts"]) == 2

        # Check that the correct categories were returned
        # The API transforms food_category (model) to category (schema)
        categories = [fact["category"] for fact in response_data["fun_facts"]]
        assert "Apples" in categories
        assert "Bananas" in categories


@pytest.mark.asyncio
async def test_get_food_category_fun_facts_empty_result(client: AsyncClient):
    """Test behavior when no fun facts are found."""
    # Mock the CRUD operation to return an empty list
    with patch(
        "src.app.api.v1.food_category.food_category_fun_fact_crud.get_random_fun_facts",
        return_value=[],
    ):
        # Act
        response = await client.get("/api/v1/food-category/fun-facts")

        # Assert - should return 200 with empty list
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "fun_facts" in response_data
        assert len(response_data["fun_facts"]) == 0


@pytest.mark.asyncio
async def test_get_food_category_fun_facts_server_error(client: AsyncClient):
    """Test internal server error handling."""
    # Mock the CRUD operation to raise an exception
    with patch(
        "src.app.api.v1.food_category.food_category_fun_fact_crud.get_random_fun_facts",
        side_effect=Exception("Database error"),
    ):
        # Act
        response = await client.get("/api/v1/food-category/fun-facts")

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.json()
        assert "Error retrieving food category fun facts" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_food_category_fun_fact_by_category_not_found(client: AsyncClient):
    """Test behavior when a fun fact for a specific category is not found."""
    # Mock the CRUD operation to return None (not found)
    with patch(
        "src.app.api.v1.food_category.food_category_fun_fact_crud.get_by_category",
        return_value=None,
    ):
        # Act
        response = await client.get("/api/v1/food-category/fun-facts/NonExistent")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_food_category_fun_fact_by_category_server_error(client: AsyncClient):
    """Test internal server error handling for retrieving a specific category fun fact."""
    # Mock the CRUD operation to raise an exception
    with patch(
        "src.app.api.v1.food_category.food_category_fun_fact_crud.get_by_category",
        side_effect=Exception("Database error"),
    ):
        # Act
        response = await client.get("/api/v1/food-category/fun-facts/Apples")

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.json()
        assert "Error retrieving food category fun fact" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_food_category_fun_facts_parameter_validation(client: AsyncClient):
    """Test validation of query parameters for the fun facts endpoint."""
    # Act - Test with invalid count parameter (below minimum)
    response_below_min = await client.get("/api/v1/food-category/fun-facts?count=0")

    # Act - Test with invalid count parameter (above maximum)
    response_above_max = await client.get("/api/v1/food-category/fun-facts?count=51")

    # Assert
    assert response_below_min.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_above_max.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Check validation error details
    assert "detail" in response_below_min.json()
    assert "detail" in response_above_max.json()

    # Verify the specific validation constraint that was violated
    below_min_errors = response_below_min.json()["detail"]
    above_max_errors = response_above_max.json()["detail"]

    assert any("greater than or equal to" in str(error) for error in below_min_errors)
    assert any("less than or equal to" in str(error) for error in above_max_errors)
