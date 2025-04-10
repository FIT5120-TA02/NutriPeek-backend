"""Food API endpoint tests."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_autocomplete_food_exact_category_results(client: AsyncClient) -> None:
    """Test autocomplete endpoint with exact category match results.

    This test verifies that:
    1. The endpoint returns a successful response
    2. Exact category search is attempted first
    3. Results are formatted correctly

    Args:
        client: Test client.
    """
    # Test search query
    query = "fruits"

    # Mock search results
    mock_results = [
        AsyncMock(
            id="1",
            food_name="Apple",
            food_category="Fruits",
        ),
        AsyncMock(
            id="2",
            food_name="Banana",
            food_category="Fruits",
        ),
    ]

    # Mock the CRUD methods
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_exact_category",
        new_callable=AsyncMock,
    ) as mock_exact_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_category",
        new_callable=AsyncMock,
    ) as mock_fuzzy_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_name",
        new_callable=AsyncMock,
    ) as mock_fuzzy_name:
        # Configure mocks
        mock_exact_category.return_value = mock_results
        mock_fuzzy_category.return_value = []
        mock_fuzzy_name.return_value = []

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/autocomplete?query={query}")

        # Verify the mocks were called correctly
        mock_exact_category.assert_called_once_with(
            mock_exact_category.call_args[0][0], category=query, limit=10
        )
        mock_fuzzy_category.assert_not_called()
        mock_fuzzy_name.assert_not_called()

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response data
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "1"
        assert data[0]["food_name"] == "Apple"
        assert data[1]["id"] == "2"
        assert data[1]["food_name"] == "Banana"
        # Verify food_category is not included
        assert "food_category" not in data[0]


@pytest.mark.asyncio
async def test_autocomplete_food_fuzzy_category_results(client: AsyncClient) -> None:
    """Test autocomplete endpoint with fuzzy category match results.

    This test verifies that:
    1. The endpoint returns a successful response
    2. Fuzzy category search is attempted when exact category returns no results
    3. Results are formatted correctly

    Args:
        client: Test client.
    """
    # Test search query
    query = "veg"

    # Mock search results
    mock_results = [
        AsyncMock(
            id="3",
            food_name="Carrot",
            food_category="Vegetables",
        ),
        AsyncMock(
            id="4",
            food_name="Broccoli",
            food_category="Vegetables",
        ),
    ]

    # Mock the CRUD methods
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_exact_category",
        new_callable=AsyncMock,
    ) as mock_exact_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_category",
        new_callable=AsyncMock,
    ) as mock_fuzzy_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_name",
        new_callable=AsyncMock,
    ) as mock_fuzzy_name:
        # Configure mocks
        mock_exact_category.return_value = []
        mock_fuzzy_category.return_value = mock_results
        mock_fuzzy_name.return_value = []

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/autocomplete?query={query}")

        # Verify the mocks were called correctly
        mock_exact_category.assert_called_once_with(
            mock_exact_category.call_args[0][0], category=query, limit=10
        )
        mock_fuzzy_category.assert_called_once_with(
            mock_fuzzy_category.call_args[0][0], category=query, limit=10
        )
        mock_fuzzy_name.assert_not_called()

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response data
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "3"
        assert data[0]["food_name"] == "Carrot"
        assert data[1]["id"] == "4"
        assert data[1]["food_name"] == "Broccoli"


@pytest.mark.asyncio
async def test_autocomplete_food_fuzzy_name_results(client: AsyncClient) -> None:
    """Test autocomplete endpoint with fuzzy name match results.

    This test verifies that:
    1. The endpoint returns a successful response
    2. Fuzzy name search is attempted when both category searches return no results
    3. Results are formatted correctly

    Args:
        client: Test client.
    """
    # Test search query
    query = "chick"

    # Mock search results
    mock_results = [
        AsyncMock(
            id="5",
            food_name="Chicken breast",
            food_category="Poultry",
        ),
        AsyncMock(
            id="6",
            food_name="Chickpeas",
            food_category="Legumes",
        ),
    ]

    # Mock the CRUD methods
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_exact_category",
        new_callable=AsyncMock,
    ) as mock_exact_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_category",
        new_callable=AsyncMock,
    ) as mock_fuzzy_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_name",
        new_callable=AsyncMock,
    ) as mock_fuzzy_name:
        # Configure mocks
        mock_exact_category.return_value = []
        mock_fuzzy_category.return_value = []
        mock_fuzzy_name.return_value = mock_results

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/autocomplete?query={query}")

        # Verify the mocks were called correctly
        mock_exact_category.assert_called_once_with(
            mock_exact_category.call_args[0][0], category=query, limit=10
        )
        mock_fuzzy_category.assert_called_once_with(
            mock_fuzzy_category.call_args[0][0], category=query, limit=10
        )
        mock_fuzzy_name.assert_called_once_with(
            mock_fuzzy_name.call_args[0][0], food_name=query, limit=10
        )

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response data
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "5"
        assert data[0]["food_name"] == "Chicken breast"
        assert data[1]["id"] == "6"
        assert data[1]["food_name"] == "Chickpeas"


@pytest.mark.asyncio
async def test_autocomplete_food_no_results(client: AsyncClient) -> None:
    """Test autocomplete endpoint with no results.

    This test verifies that:
    1. The endpoint returns a successful response with empty list
    2. All search methods are attempted in the correct order

    Args:
        client: Test client.
    """
    # Test search query
    query = "nonexistentfood"

    # Mock the CRUD methods
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_exact_category",
        new_callable=AsyncMock,
    ) as mock_exact_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_category",
        new_callable=AsyncMock,
    ) as mock_fuzzy_category, patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_fuzzy_name",
        new_callable=AsyncMock,
    ) as mock_fuzzy_name:
        # Configure mocks to return empty results
        mock_exact_category.return_value = []
        mock_fuzzy_category.return_value = []
        mock_fuzzy_name.return_value = []

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/autocomplete?query={query}")

        # Verify the mocks were called correctly in the right order
        mock_exact_category.assert_called_once()
        mock_fuzzy_category.assert_called_once()
        mock_fuzzy_name.assert_called_once()

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response data is an empty list
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


@pytest.mark.asyncio
async def test_autocomplete_food_error(client: AsyncClient) -> None:
    """Test autocomplete endpoint error handling.

    This test verifies that:
    1. The endpoint handles exceptions properly
    2. The response includes appropriate error details

    Args:
        client: Test client.
    """
    # Test search query
    query = "fruits"

    # Mock the CRUD method to raise an exception
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.search_by_exact_category",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.side_effect = Exception("Database error")

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/autocomplete?query={query}")

        # Verify response status
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Verify response contains error detail
        data = response.json()
        assert "detail" in data
        assert "Error searching for food items" in data["detail"]


@pytest.mark.asyncio
async def test_get_food_nutrient_info_success(client: AsyncClient) -> None:
    """Test get food nutrient info endpoint with successful response.

    This test verifies that:
    1. The endpoint returns a successful response
    2. The response includes the correct nutrient data
    3. The data is formatted according to FoodNutrientResponse schema

    Args:
        client: Test client.
    """
    # Test food ID
    food_id = "123"

    # Mock food nutrient data
    mock_food = AsyncMock(
        id=food_id,
        food_name="Banana",
        food_category="Fruits",
        energy_with_fibre_kj=89.0,
        protein_g=1.1,
        total_fat_g=0.3,
        carbs_with_sugar_alcohols_g=22.8,
        dietary_fibre_g=2.6,
    )

    # Mock the CRUD method
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.get",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_food

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/{food_id}")

        # Verify the mock was called correctly
        mock_get.assert_called_once_with(mock_get.call_args[0][0], id=food_id)

        # Verify response status
        assert response.status_code == status.HTTP_200_OK

        # Verify response data
        data = response.json()
        assert data["id"] == food_id
        assert data["food_name"] == "Banana"
        assert data["food_category"] == "Fruits"
        assert data["energy_with_fibre_kj"] == 89.0
        assert data["protein_g"] == 1.1
        assert data["total_fat_g"] == 0.3
        assert data["carbs_with_sugar_alcohols_g"] == 22.8
        assert data["dietary_fibre_g"] == 2.6


@pytest.mark.asyncio
async def test_get_food_nutrient_info_not_found(client: AsyncClient) -> None:
    """Test get food nutrient info endpoint with food not found.

    This test verifies that:
    1. The endpoint returns a 404 response when food is not found
    2. The response includes appropriate error details

    Args:
        client: Test client.
    """
    # Test food ID
    food_id = "nonexistent"

    # Mock the CRUD method
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.get",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = None

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/{food_id}")

        # Verify response status
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify response contains error detail
        data = response.json()
        assert "detail" in data
        assert f"Food item with ID {food_id} not found" in data["detail"]


@pytest.mark.asyncio
async def test_get_food_nutrient_info_error(client: AsyncClient) -> None:
    """Test get food nutrient info endpoint error handling.

    This test verifies that:
    1. The endpoint handles exceptions properly
    2. The response includes appropriate error details

    Args:
        client: Test client.
    """
    # Test food ID
    food_id = "123"

    # Mock the CRUD method to raise an exception
    with patch(
        "src.app.crud.crud_food_nutrients.food_nutrient_crud.get",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.side_effect = Exception("Database error")

        # Send request to the endpoint
        response = await client.get(f"/api/v1/food/{food_id}")

        # Verify response status
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Verify response contains error detail
        data = response.json()
        assert "detail" in data
        assert "Error retrieving food nutrient information" in data["detail"]
        assert "Error retrieving food nutrient information" in data["detail"]
