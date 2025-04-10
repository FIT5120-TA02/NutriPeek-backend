"""Food detection API endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.core.exceptions.custom import (
    InvalidImageError,
    InvalidRequestError,
    ModelLoadError,
    ProcessingError,
)
from src.app.schemas.food_detection import (
    FoodDetectionError,
    FoodDetectionResponse,
    FoodMappingRequest,
    FoodMappingResponse,
)
from src.app.services.food_detection_service import food_detection_service
from src.app.services.food_mapping_service import food_mapping_service

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


@router.post(
    "/map-nutrients",
    response_model=FoodMappingResponse,
    responses={
        400: {"model": FoodDetectionError, "description": "Invalid request parameters"},
        500: {"model": FoodDetectionError, "description": "Mapping error"},
    },
    status_code=status.HTTP_200_OK,
    summary="Map detected food items to nutrient data with quantities",
    description="Match detected food items to nutritional information in the database, counting duplicates and providing quantity information",
)
async def map_food_to_nutrients(
    request: FoodMappingRequest, db: AsyncSession = Depends(get_async_db)
):
    """Map detected food items to nutrient data in the database with quantity information.

    This endpoint takes a list of food item names (usually from detection results)
    and attempts to match them to nutritional data in the database using the following strategy:

    1. First try to match each food item as a category (exact match on food_category)
    2. If not found, try fuzzy matching on food_category
    3. If still not found, try fuzzy matching on food_name

    It counts duplicate items and includes quantity information in the response.
    It can optionally store the results in a user's inventory.

    Args:
        request: Food mapping request with detected items and storage options
        db: Database session

    Returns:
        Mapping of food items to nutrient data with quantities and list of unmapped items

    Raises:
        HTTPException: If mapping fails or request is invalid
    """
    try:
        if not request.detected_items:
            raise InvalidRequestError("No food items provided to map")

        # Map each food item using the hierarchical search approach
        # The service now handles counting duplicates
        mapped_items, unmapped_items = await food_mapping_service.map_food_items(
            food_names=request.detected_items,
            children_profile_id=request.children_profile_id,
            store_in_inventory=request.store_in_inventory,
        )

        # Return mapping results
        return FoodMappingResponse(
            mapped_items=mapped_items,
            unmapped_items=unmapped_items,
        )

    except InvalidRequestError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error mapping nutrients: {str(e)}",
        )
