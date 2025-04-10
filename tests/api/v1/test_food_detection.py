"""Food detection API endpoint tests."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_detect_apples(client: AsyncClient) -> None:
    """Test food detection endpoint with an image containing apples.

    This test verifies that:
    1. The endpoint returns a successful response
    2. The response includes 3 detected apple items
    3. The detection has the expected structure

    Args:
        client: Test client.
    """
    # Path to test image
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    test_image_path = current_dir / "../../core/ml/test_images/apple_test.jpeg"

    # Mock food detection service response
    mock_detections = [
        {
            "class_name": "apple",
            "confidence": 0.91,
            "x_min": 50.0,
            "y_min": 30.0,
            "x_max": 180.0,
            "y_max": 160.0,
        },
        {
            "class_name": "apple",
            "confidence": 0.88,
            "x_min": 210.0,
            "y_min": 40.0,
            "x_max": 340.0,
            "y_max": 170.0,
        },
        {
            "class_name": "apple",
            "confidence": 0.85,
            "x_min": 370.0,
            "y_min": 50.0,
            "x_max": 500.0,
            "y_max": 180.0,
        },
    ]

    # Open test image file
    with open(test_image_path, "rb") as f:
        image_data = f.read()

    # Mock the food detection service
    with patch(
        "src.app.services.food_detection_service.food_detection_service.process_image",
        new_callable=AsyncMock,
    ) as mock_process:
        # Configure mock to return our test data
        mock_process.return_value = (
            mock_detections,  # Detected items
            150.5,  # Processing time (ms)
            640,  # Image width
            480,  # Image height
        )

        # Send request to the endpoint
        response = await client.post(
            "/api/v1/food-detection/detect",
            files={"image": ("apple_test.jpeg", image_data, "image/jpeg")},
        )

        # Verify the request was sent correctly
        mock_process.assert_called_once()

        # Verify response status
        assert response.status_code == 200

        # Verify response data
        data = response.json()
        assert "detected_items" in data
        assert len(data["detected_items"]) == 3

        # Check that all items are apples
        for item in data["detected_items"]:
            assert item["class_name"] == "apple"
            assert 0 <= item["confidence"] <= 1

        # Verify other response fields
        assert "processing_time_ms" in data
        assert "image_width" in data
        assert "image_height" in data
        assert data["image_width"] == 640
        assert data["image_height"] == 480


@pytest.mark.asyncio
async def test_detect_invalid_image_format(client: AsyncClient) -> None:
    """Test food detection endpoint with an invalid image format.

    Args:
        client: Test client.
    """
    # Create a text file and try to pass it as an image
    invalid_data = b"This is not an image file"

    # Send request to the endpoint
    response = await client.post(
        "/api/v1/food-detection/detect",
        files={"image": ("test.txt", invalid_data, "text/plain")},
    )

    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "File must be an image" in data["detail"]


@pytest.mark.asyncio
async def test_detect_processing_error(client: AsyncClient) -> None:
    """Test food detection endpoint handling processing errors.

    Args:
        client: Test client.
    """
    # Path to test image
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    test_image_path = current_dir / "../../core/ml/test_images/apple_test.jpeg"

    # Open test image file
    with open(test_image_path, "rb") as f:
        image_data = f.read()

    # Mock the food detection service to raise a ProcessingError
    with patch(
        "src.app.services.food_detection_service.food_detection_service.process_image",
        new_callable=AsyncMock,
    ) as mock_process:
        from src.app.core.exceptions.custom import ProcessingError

        mock_process.side_effect = ProcessingError("Failed to process image")

        # Send request to the endpoint
        response = await client.post(
            "/api/v1/food-detection/detect",
            files={"image": ("apple_test.jpeg", image_data, "image/jpeg")},
        )

        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to process image" in data["detail"]


@pytest.mark.asyncio
async def test_map_food_to_nutrients_success(client: AsyncClient) -> None:
    """Test mapping food items to nutrients with successful response.

    This test verifies that:
    1. The endpoint returns a successful response
    2. The mapped items contain the expected nutrient data
    3. The unmapped items are correctly reported

    Args:
        client: Test client.
    """
    # Create test request data
    request_data = {
        "detected_items": ["apple", "banana", "orange"],
        "children_profile_id": "test-profile-123",
        "store_in_inventory": False,
    }

    # Mock food mapping service response
    mock_mapped_items = {
        "apple": {
            "id": "1",
            "food_name": "Apple",
            "food_category": "Fruits",
            "energy_with_fibre_kj": 52.0,
            "protein_g": 0.3,
            "total_fat_g": 0.2,
            "carbs_with_sugar_alcohols_g": 14.0,
            "dietary_fibre_g": 2.4,
        },
        "banana": {
            "id": "2",
            "food_name": "Banana",
            "food_category": "Fruits",
            "energy_with_fibre_kj": 89.0,
            "protein_g": 1.1,
            "total_fat_g": 0.3,
            "carbs_with_sugar_alcohols_g": 22.8,
            "dietary_fibre_g": 2.6,
        },
    }
    mock_unmapped_items = ["orange"]

    # Mock the food mapping service
    with patch(
        "src.app.services.food_mapping_service.food_mapping_service.map_food_items",
        new_callable=AsyncMock,
    ) as mock_map:
        # Configure mock to return our test data
        mock_map.return_value = (mock_mapped_items, mock_unmapped_items)

        # Send request to the endpoint
        response = await client.post(
            "/api/v1/food-detection/map-nutrients",
            json=request_data,
        )

        # Verify the request was sent correctly
        mock_map.assert_called_once_with(
            food_names=request_data["detected_items"],
            children_profile_id=request_data["children_profile_id"],
            store_in_inventory=request_data["store_in_inventory"],
        )

        # Verify response status
        assert response.status_code == 200

        # Verify response data
        data = response.json()
        assert "mapped_items" in data
        assert "unmapped_items" in data

        # Check mapped items
        assert len(data["mapped_items"]) == 2
        assert "apple" in data["mapped_items"]
        assert "banana" in data["mapped_items"]

        # Verify nutrient data is present
        assert data["mapped_items"]["apple"]["food_name"] == "Apple"
        assert data["mapped_items"]["apple"]["food_category"] == "Fruits"
        assert "energy_with_fibre_kj" in data["mapped_items"]["apple"]
        assert "protein_g" in data["mapped_items"]["apple"]

        # Check unmapped items
        assert len(data["unmapped_items"]) == 1
        assert "orange" in data["unmapped_items"]


@pytest.mark.asyncio
async def test_map_food_to_nutrients_empty_items(client: AsyncClient) -> None:
    """Test mapping with no food items provided.

    Args:
        client: Test client.
    """
    # Create test request with empty detected items
    request_data = {
        "detected_items": [],
        "children_profile_id": "test-profile-123",
        "store_in_inventory": False,
    }

    # Send request to the endpoint
    response = await client.post(
        "/api/v1/food-detection/map-nutrients",
        json=request_data,
    )

    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "No food items provided" in data["detail"]


@pytest.mark.asyncio
async def test_map_food_to_nutrients_invalid_profile(client: AsyncClient) -> None:
    """Test mapping with store_in_inventory=True but missing profile ID.

    Args:
        client: Test client.
    """
    # Create test request with store_in_inventory=True but no profile ID
    request_data = {
        "detected_items": ["apple", "banana"],
        "children_profile_id": None,
        "store_in_inventory": True,
    }

    # Mock the food mapping service to raise an InvalidRequestError
    with patch(
        "src.app.services.food_mapping_service.food_mapping_service.map_food_items",
        new_callable=AsyncMock,
    ) as mock_map:
        from src.app.core.exceptions.custom import InvalidRequestError

        mock_map.side_effect = InvalidRequestError(
            "children_profile_id is required when store_in_inventory is True"
        )

        # Send request to the endpoint
        response = await client.post(
            "/api/v1/food-detection/map-nutrients",
            json=request_data,
        )

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "children_profile_id is required" in data["detail"]


@pytest.mark.asyncio
async def test_map_food_to_nutrients_server_error(client: AsyncClient) -> None:
    """Test mapping with a server-side error.

    Args:
        client: Test client.
    """
    # Create test request
    request_data = {
        "detected_items": ["apple", "banana"],
        "children_profile_id": "test-profile-123",
        "store_in_inventory": False,
    }

    # Mock the food mapping service to raise a general exception
    with patch(
        "src.app.services.food_mapping_service.food_mapping_service.map_food_items",
        new_callable=AsyncMock,
    ) as mock_map:
        mock_map.side_effect = Exception("Database connection error")

        # Send request to the endpoint
        response = await client.post(
            "/api/v1/food-detection/map-nutrients",
            json=request_data,
        )

        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error mapping nutrients" in data["detail"]
