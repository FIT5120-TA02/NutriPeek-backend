"""Schemas for food API endpoints."""

from typing import List, Optional

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


class FoodCategoryAvgNutrients(BaseModel):
    """Response schema for food category with average nutrient values.

    Contains the category name and average nutritional values of all foods
    in that category, useful for visualization in the frontend.
    """

    food_category: str = Field(..., description="Category of the food items")
    count: int = Field(..., description="Number of food items in this category")
    energy_with_fibre_kj: Optional[float] = Field(
        None, description="Average energy content with fibre in kilojoules"
    )
    protein_g: Optional[float] = Field(
        None, description="Average protein content in grams"
    )
    total_fat_g: Optional[float] = Field(
        None, description="Average total fat content in grams"
    )
    carbs_with_sugar_alcohols_g: Optional[float] = Field(
        None, description="Average carbohydrates content with sugar alcohols in grams"
    )
    dietary_fibre_g: Optional[float] = Field(
        None, description="Average dietary fibre content in grams"
    )
    sodium_mg: Optional[float] = Field(
        None, description="Average sodium content in milligrams"
    )

    class ConfigDict:
        """Pydantic configuration."""

        from_attributes = True


class FoodCategoriesResponse(BaseModel):
    """Response schema for list of food categories with average nutrient values."""

    categories: List[FoodCategoryAvgNutrients] = Field(
        ..., description="List of food categories with their average nutrient values"
    )


class FoodRecommendation(BaseModel):
    """Schema for food recommended based on specific nutrient content."""

    id: str = Field(..., description="Unique identifier of the food item")
    food_category: str = Field(..., description="Name of the food item")
