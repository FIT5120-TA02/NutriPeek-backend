"""Schemas for nutrient API endpoints."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Gender(str, Enum):
    """Valid gender values for child profiles."""

    BOY = "boy"
    GIRL = "girl"


class ChildProfile(BaseModel):
    """Schema for child profile data."""

    age: int = Field(..., ge=0, le=18, description="Age of the child (0-18 years)")
    gender: Gender = Field(..., description="Gender of the child (boy/girl)")

    class ConfigDict:
        """Pydantic configuration."""

        json_schema_extra = {"example": {"age": 10, "gender": "boy"}}


class NutrientGapRequest(BaseModel):
    """Request schema for calculating nutritional gaps."""

    child_profile: ChildProfile = Field(..., description="Child profile data")
    ingredient_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of ingredient IDs (food_nutrient.id) chosen by the user",
    )

    class ConfigDict:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "child_profile": {"age": 10, "gender": "boy"},
                "ingredient_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001",
                ],
            }
        }


class NutrientInfo(BaseModel):
    """Schema for nutrient information."""

    name: str = Field(..., description="Name of the nutrient")
    recommended_intake: float = Field(
        ..., description="Recommended daily intake amount"
    )
    current_intake: float = Field(
        ..., description="Current intake from selected ingredients"
    )
    unit: str = Field(..., description="Unit of measurement")
    gap: float = Field(..., description="Gap between recommended and current intake")
    gap_percentage: float = Field(
        ..., description="Gap as percentage of recommended intake"
    )
    category: Optional[str] = Field(None, description="Category of the nutrient")


class NutrientGapResponse(BaseModel):
    """Response schema for nutritional gap calculation."""

    nutrient_gaps: Dict[str, NutrientInfo] = Field(
        ..., description="Map of nutrient names to their gap information"
    )
    missing_nutrients: List[str] = Field(
        default_factory=list,
        description="List of nutrients with no intake from selected ingredients",
    )
    excess_nutrients: List[str] = Field(
        default_factory=list,
        description="List of nutrients exceeding recommended intake",
    )
    total_calories: float = Field(
        0.0, description="Total calories (energy) from selected ingredients"
    )


class NutrientIntakeInfo(BaseModel):
    """Schema for nutrient intake information."""

    name: str = Field(..., description="Name of the nutrient")
    recommended_intake: float = Field(
        ..., description="Recommended daily intake amount"
    )
    unit: str = Field(..., description="Unit of measurement")
    category: Optional[str] = Field(None, description="Category of the nutrient")


class NutrientIntakeResponse(BaseModel):
    """Response schema for required nutrient intake."""

    nutrient_intakes: Dict[str, NutrientIntakeInfo] = Field(
        ..., description="Map of nutrient names to their recommended intake information"
    )

    class ConfigDict:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "nutrient_intakes": {
                    "Energy(a)": {
                        "name": "Energy(a)",
                        "recommended_intake": 8500.0,
                        "unit": "kJ",
                        "category": "Energy",
                    },
                    "Protein": {
                        "name": "Protein",
                        "recommended_intake": 40.0,
                        "unit": "g",
                        "category": "Macronutrients",
                    },
                    "Total Fat(c)": {
                        "name": "Total Fat(c)",
                        "recommended_intake": 67.0,
                        "unit": "g",
                        "category": "Macronutrients",
                    },
                    "Carbohydrate(c)": {
                        "name": "Carbohydrate(c)",
                        "recommended_intake": 230.0,
                        "unit": "g",
                        "category": "Macronutrients",
                    },
                    "Dietary Fibre": {
                        "name": "Dietary Fibre",
                        "recommended_intake": 24.0,
                        "unit": "g",
                        "category": "Macronutrients",
                    },
                }
            }
        }
