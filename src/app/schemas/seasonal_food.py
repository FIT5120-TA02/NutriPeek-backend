"""Schemas for seasonal food data."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from src.app.schemas.food_detection import FoodNutrientSummary


class Season(str, Enum):
    """Enum for seasons."""

    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"


class SeasonalFoodBase(BaseModel):
    """Base schema for seasonal food items."""

    name: str = Field(..., description="Name of the food item")
    category: str = Field(
        ..., description="Category of the food (e.g., fruit, vegetable)"
    )
    region: str = Field(
        ..., description="Geographic region where the food is in season"
    )
    season: Season = Field(..., description="General season category")
    month: str = Field(..., description="Specific month when the food is in season")
    db_category: str = Field(..., description="Database category of the food")


class SeasonalFoodCreate(SeasonalFoodBase):
    """Schema for creating a seasonal food entry."""

    pass


class SeasonalFoodUpdate(BaseModel):
    """Schema for updating a seasonal food entry."""

    name: Optional[str] = Field(None, description="Name of the food item")
    category: Optional[str] = Field(None, description="Category of the food")
    region: Optional[str] = Field(None, description="Geographic region")
    season: Optional[Season] = Field(None, description="General season category")
    month: Optional[str] = Field(None, description="Specific month")


class SeasonalFoodResponse(SeasonalFoodBase):
    """Schema for seasonal food response."""

    id: str = Field(..., description="Unique identifier for the seasonal food entry")

    class Config:
        """Pydantic config."""

        from_attributes = True


class SeasonalFoodListResponse(BaseModel):
    """Schema for a list of seasonal food items."""

    items: List[SeasonalFoodResponse]
    total: int = Field(..., description="Total number of items")


class SeasonalAvailability(BaseModel):
    """Schema for seasonal availability information."""

    season: Season = Field(..., description="Season when the food is available")
    month: str = Field(..., description="Month when the food is available")
    category: str = Field(..., description="Category of the food")


class SeasonalFoodDetailResponse(BaseModel):
    """Schema for detailed seasonal food information including nutrient data."""

    food_name: str = Field(..., description="Name of the food item")
    region: str = Field(..., description="Geographic region")
    seasonal_availability: List[SeasonalAvailability] = Field(
        ..., description="List of seasons and months when the food is available"
    )
    nutrient_data: Optional[FoodNutrientSummary] = Field(
        None, description="Nutritional information for the food item if available"
    )

    class Config:
        """Pydantic config."""

        from_attributes = True
