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
        "src.app.services.food_detection.food_detection_service.process_image",
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
        "src.app.services.food_detection.food_detection_service.process_image",
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
