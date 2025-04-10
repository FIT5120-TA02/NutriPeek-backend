"""Schemas for food API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class FoodAutocompleteResponse(BaseModel):
    """Response schema for food autocomplete search results.

    Simplified version of food data for autocomplete suggestions
    containing only the ID and food name.
    """

    id: str = Field(..., description="Unique identifier for the food item")
    food_name: str = Field(..., description="Name of the food item")


class FoodNutrientResponse(BaseModel):
    """Response schema for food nutrient information.

    This schema is identical to FoodNutrientSummary in food_detection.py
    to maintain consistency with the food-detection/map-nutrients endpoint.
    """

    id: str = Field(..., description="Unique identifier for the food item")
    food_name: str = Field(..., description="Name of the food item")
    food_category: Optional[str] = Field(None, description="Category of the food item")
    energy_with_fibre_kj: Optional[float] = Field(
        None, description="Energy content with fibre in kilojoules"
    )
    protein_g: Optional[float] = Field(None, description="Protein content in grams")
    total_fat_g: Optional[float] = Field(None, description="Total fat content in grams")
    carbs_with_sugar_alcohols_g: Optional[float] = Field(
        None, description="Carbohydrates content with sugar alcohols in grams"
    )
    dietary_fibre_g: Optional[float] = Field(
        None, description="Dietary fibre content in grams"
    )

    class ConfigDict:
        """Pydantic configuration."""

        from_attributes = True
