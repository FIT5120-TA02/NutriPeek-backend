"""Schemas for food detection API."""

from typing import List

from pydantic import BaseModel, Field


class DetectionBase(BaseModel):
    """Base schema for detection results."""

    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class FoodItemDetection(DetectionBase):
    """Schema for a single detected food item."""

    class ConfigDict:
        """Pydantic configuration."""

        from_attributes = True


class FoodDetectionResponse(BaseModel):
    """Schema for food detection response."""

    detected_items: List[FoodItemDetection] = Field(
        default_factory=list, description="List of detected food items"
    )
    processing_time_ms: float = Field(
        ..., description="Processing time in milliseconds"
    )
    image_width: int = Field(..., description="Width of the processed image")
    image_height: int = Field(..., description="Height of the processed image")


class FoodDetectionError(BaseModel):
    """Schema for food detection errors."""

    detail: str
