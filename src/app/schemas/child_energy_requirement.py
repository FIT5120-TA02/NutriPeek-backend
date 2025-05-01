"""Pydantic schemas for ChildEnergyRequirement model."""

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Gender(str, Enum):
    """Valid gender values for child profiles."""

    BOY = "boy"
    GIRL = "girl"


class ChildEnergyRequirementBase(BaseModel):
    """Base schema for ChildEnergyRequirement.

    Shared attributes for all ChildEnergyRequirement schemas.
    """

    age: int = Field(..., ge=0, le=18, description="Age of child in years (0-18)")
    gender: Gender = Field(..., description="Gender of child (boy/girl)")
    unit: str = Field(..., description="Unit of measurement (kcal/day, kJ/day)")
    physical_activity_level: float = Field(
        ..., gt=0, description="Physical activity level"
    )
    estimated_energy_requirement: float = Field(
        ..., gt=0, description="Estimated energy requirement value"
    )


class ChildEnergyRequirementCreate(ChildEnergyRequirementBase):
    """Schema for creating a new ChildEnergyRequirement."""

    pass


class ChildEnergyRequirementUpdate(BaseModel):
    """Schema for updating a ChildEnergyRequirement.

    All fields are optional for updates.
    """

    age: Optional[int] = Field(None, ge=0, le=18)
    gender: Optional[Gender] = None
    unit: Optional[str] = None
    physical_activity_level: Optional[float] = Field(None, gt=0)
    estimated_energy_requirement: Optional[float] = Field(None, gt=0)


class ChildEnergyRequirementInDB(ChildEnergyRequirementBase):
    """Schema for ChildEnergyRequirement stored in database.

    Includes database-specific fields like UUID and timestamps.
    """

    id: UUID

    class Config:
        """Pydantic config for ORM mode."""

        from_attributes = True


class ChildEnergyRequirementResponse(ChildEnergyRequirementInDB):
    """Schema for ChildEnergyRequirement API responses."""

    pass


class FindNearestPALRequest(BaseModel):
    """Schema for request to find nearest physical activity level."""

    physical_activity_level: float = Field(
        ..., gt=0, description="Physical activity level to find nearest match for"
    )
    age: int = Field(..., ge=0, le=18, description="Age of child in years (0-18)")
    gender: Gender = Field(..., description="Gender of child (boy/girl)")


class FindNearestPALResponse(BaseModel):
    """Schema for response from find nearest PAL endpoint."""

    input_physical_activity_level: float = Field(
        ..., description="Input physical activity level"
    )
    matched_physical_activity_level: float = Field(
        ..., description="Nearest matched physical activity level"
    )
    age: int = Field(..., description="Age of child")
    gender: Gender = Field(..., description="Gender of child")
    unit: str = Field(..., description="Unit of measurement")
    estimated_energy_requirement: float = Field(
        ..., description="Estimated energy requirement"
    )
