"""Food detection API endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.app.core.exceptions.custom import (
    InvalidImageError,
    ModelLoadError,
    ProcessingError,
)
from src.app.schemas.food_detection import FoodDetectionError, FoodDetectionResponse
from src.app.services.food_detection import food_detection_service

router = APIRouter(prefix="/food-detection", tags=["food-detection"])


@router.post(
    "/detect",
    response_model=FoodDetectionResponse,
    responses={
        400: {"model": FoodDetectionError, "description": "Invalid image provided"},
        500: {"model": FoodDetectionError, "description": "Processing error"},
    },
    status_code=status.HTTP_200_OK,
    summary="Detect food items in an image",
    description="Upload an image to detect food items using YOLO object detection",
)
async def detect_food_items(image: UploadFile = File(...)):
    """Detect food items in an uploaded image.

    Args:
        image: Uploaded image file

    Returns:
        Detection results including bounding boxes and confidence scores

    Raises:
        HTTPException: If processing fails or image is invalid
    """
    # Validate image
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    try:
        # Process the image
        (
            detections,
            processing_time_ms,
            width,
            height,
        ) = await food_detection_service.process_image(image)

        # Return detection results
        return FoodDetectionResponse(
            detected_items=detections,
            processing_time_ms=processing_time_ms,
            image_width=width,
            image_height=height,
        )

    except InvalidImageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except (ModelLoadError, ProcessingError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
