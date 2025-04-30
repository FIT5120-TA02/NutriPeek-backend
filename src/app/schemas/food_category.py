"""Food Category Fun Fact schemas for request and response validation."""

from typing import List, Optional

from pydantic import BaseModel, Field


class FoodCategoryFunFactBase(BaseModel):
    """Base schema for food category fun facts with shared attributes."""

    category: str = Field(..., description="The food category name")
    fun_fact: str = Field(..., description="A fun fact about the food category")


class FoodCategoryFunFactCreate(FoodCategoryFunFactBase):
    """Schema for creating food category fun facts."""

    pass


class FoodCategoryFunFactUpdate(FoodCategoryFunFactBase):
    """Schema for updating food category fun facts."""

    category: Optional[str] = Field(None, description="The food category name")
    fun_fact: Optional[str] = Field(
        None, description="A fun fact about the food category"
    )


class FoodCategoryFunFactResponse(FoodCategoryFunFactBase):
    """Schema for food category fun fact responses."""

    id: str = Field(..., description="Unique identifier for the food category fun fact")

    class Config:
        """Pydantic configuration for ORM compatibility."""

        from_attributes = True


class FoodCategoryFunFactsResponse(BaseModel):
    """Schema for multiple food category fun facts response."""

    fun_facts: List[FoodCategoryFunFactResponse] = Field(
        ..., description="List of food category fun facts"
    )
