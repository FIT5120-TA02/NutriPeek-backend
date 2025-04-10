"""Test module for the food detection service."""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi import UploadFile

from src.app.services.food_detection_service import FoodDetectionService


@pytest.mark.asyncio
async def test_food_detection_service_integration():
    """Test the food detection service with a real image.

    This is an integration test that uses the actual model and processing
    pipeline to verify the complete functionality.
    """
    # Initialize the service
    service = FoodDetectionService()

    # Get test image
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    test_image_path = current_dir / "../core/ml/test_images/apple_test.jpeg"

    # Ensure test image exists
    assert test_image_path.exists(), f"Test image not found at {test_image_path}"

    # Read image data
    with open(test_image_path, "rb") as f:
        file_content = f.read()

    # Create a SpooledTemporaryFile with the image data
    spooled_file = tempfile.SpooledTemporaryFile()
    spooled_file.write(file_content)
    spooled_file.seek(0)

    # Create UploadFile with the SpooledTemporaryFile
    upload_file = UploadFile(filename="apple_test.jpeg", file=spooled_file)

    detections, processing_time, width, height = await service.process_image(
        upload_file
    )
    # Basic assertions (these might need adjustment based on your model's performance)
    # We're not checking for exact number of detections because it depends on the model
    assert len(detections) > 0, "Expected at least one detection"

    # Check if at least one apple was detected
    apple_detections = [d for d in detections if d.class_name.lower() == "apple"]
    assert len(apple_detections) > 0, "Expected at least one apple to be detected"

    # Check that all detections have reasonable confidence scores
    for detection in detections:
        assert (
            0 < detection.confidence <= 1
        ), f"Confidence should be between 0-1, got {detection.confidence}"

    # Check that all bounding boxes are within image dimensions
    for detection in detections:
        assert (
            0 <= detection.x_min < width
        ), f"x_min should be within image width, got {detection.x_min}"
        assert (
            0 <= detection.y_min < height
        ), f"y_min should be within image height, got {detection.y_min}"
        assert (
            detection.x_min < detection.x_max <= width
        ), f"x_max should be within image width, got {detection.x_max}"
        assert (
            detection.y_min < detection.y_max <= height
        ), f"y_max should be within image height, got {detection.y_max}"

    # Check that processing time is reasonable
    assert processing_time > 0, "Processing time should be positive"
