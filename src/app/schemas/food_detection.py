"""Schemas for food detection API."""

from typing import Dict, List, Optional

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


class FoodNutrientSummary(BaseModel):
    """Summary schema for food nutrient data."""

    id: str
    food_name: str
    food_category: Optional[str] = None
    energy_with_fibre_kj: Optional[float] = None
    protein_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    carbs_with_sugar_alcohols_g: Optional[float] = None
    dietary_fibre_g: Optional[float] = None

    class ConfigDict:
        """Pydantic configuration."""

        from_attributes = True


class FoodMappingRequest(BaseModel):
    """Request schema for mapping detected food items to nutrient data."""

    detected_items: List[str] = Field(
        ..., description="List of food item class names to map to nutrient data"
    )
    children_profile_id: Optional[str] = Field(
        None,
        description="Profile ID for associating with inventory (if storing results)",
    )
    store_in_inventory: bool = Field(
        False, description="Whether to store the results in the inventory"
    )


class FoodMappingResponse(BaseModel):
    """Response schema for food mapping."""

    mapped_items: Dict[str, FoodNutrientSummary] = Field(
        default_factory=dict,
        description="Mapping of detected food item names to nutrient data",
    )
    unmapped_items: List[str] = Field(
        default_factory=list,
        description="List of food items that couldn't be mapped to nutrient data",
    )
