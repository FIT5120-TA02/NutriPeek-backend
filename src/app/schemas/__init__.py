"""Pydantic schemas package."""

from src.app.schemas.food import FoodAutocompleteResponse, FoodNutrientResponse
from src.app.schemas.food_detection import (
    DetectionBase,
    FoodDetectionError,
    FoodDetectionResponse,
    FoodItemDetection,
    FoodMappingRequest,
    FoodMappingResponse,
    FoodNutrientSummary,
)
from src.app.schemas.health import HealthCheckResponse
from src.app.schemas.nutrient import (
    ChildProfile,
    NutrientGapRequest,
    NutrientGapResponse,
    NutrientInfo,
)
from src.app.schemas.qrcode_upload import (
    DetectionResultResponse,
    GenerateUploadQRResponse,
    UploadImageResponse,
)

__all__ = [
    "HealthCheckResponse",
    "ChildProfile",
    "DetectionBase",
    "FoodAutocompleteResponse",
    "FoodDetectionError",
    "FoodDetectionResponse",
    "FoodItemDetection",
    "FoodDetectionError",
    "FoodAutocompleteResponse",
    "FoodMappingRequest",
    "FoodMappingResponse",
    "FoodNutrientResponse",
    "FoodNutrientSummary",
    "NutrientGapRequest",
    "NutrientGapResponse",
    "NutrientInfo",
    "DetectionResultResponse",
    "GenerateUploadQRResponse",
    "UploadImageResponse",
]
