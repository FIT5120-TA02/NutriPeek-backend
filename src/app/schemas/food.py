"""Schemas for food API endpoints."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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
    food_name: str = Field(..., description="Name of the food item")
    food_category: str = Field(
        ..., description="Category of the food item for icon display"
    )
    nutrient_value: float = Field(..., description="Value of the specified nutrient")
    nutrients: Dict[str, float] = Field(
        {}, description="Complete nutritional profile of the food item"
    )

    class ConfigDict:
        """Pydantic configuration."""

        from_attributes = True


class OptimizedFoodRecommendationRequest(BaseModel):
    """Request for optimized food recommendations based on nutrient gaps."""

    nutrient_name: str = Field(
        ...,
        description="Column name of the nutrient (e.g., 'iron_mg', 'protein_g')",
        example="protein_g",
    )
    target_amount: float = Field(
        ...,
        description="The target amount of the nutrient to reach",
        example=20.0,
        gt=0,
    )
    current_amount: float = Field(
        0.0,
        description="The current amount of the nutrient already consumed",
        example=5.0,
        ge=0,
    )
    limit: int = Field(
        10, ge=1, le=50, description="Maximum number of food recommendations to return"
    )


class OptimizedFoodRecommendation(FoodRecommendation):
    """Optimized food recommendation with gap satisfaction information."""

    amount_needed: float = Field(
        ...,
        description="Amount of this food needed to reach target nutrient level",
        example=100.0,
    )
    gap_satisfaction_percentage: float = Field(
        ...,
        description="Percentage of the nutrient gap this food satisfies",
        example=85.5,
    )


class SeasonalFoodRecommendationRequest(BaseModel):
    """Request for seasonal food recommendations based on nutrient content."""

    nutrient_name: str = Field(
        ...,
        description="Column name of the nutrient (e.g., 'iron_mg', 'protein_g')",
        example="protein_g",
    )
    region: str = Field(
        ...,
        description="Geographic region for seasonal availability",
        example="australia",
    )
    month: Optional[str] = Field(
        None,
        description="Specific month for seasonal filtering (mutually exclusive with season)",
        example="january",
    )
    season: Optional[str] = Field(
        None,
        description="Season for filtering (mutually exclusive with month)",
        example="Summer",
    )
    limit: int = Field(
        10, ge=1, le=50, description="Maximum number of food recommendations to return"
    )

    @field_validator("season")
    def validate_not_both_month_and_season(cls, v, values):
        """Validate that only one of month or season is provided."""
        if v and "month" in values.data and values.data["month"]:
            raise ValueError(
                "Cannot provide both month and season. Please specify only one."
            )
        return v

    @field_validator("month")
    def validate_not_both_season_and_month(cls, v, values):
        """Validate that only one of month or season is provided."""
        if v and "season" in values.data and values.data["season"]:
            raise ValueError(
                "Cannot provide both month and season. Please specify only one."
            )
        return v
