"""Activity schema module."""

from typing import List

from pydantic import BaseModel, Field, model_validator


class ActivityItem(BaseModel):
    """Schema representing a single activity with duration."""

    name: str = Field(..., description="Name of the specific activity")
    hours: float = Field(..., gt=0, description="Duration of the activity in hours")

    @model_validator(mode="after")
    def validate_hours(self) -> "ActivityItem":
        """Validate that hours is positive and within reasonable limits.

        Returns:
            Validated ActivityItem
        """
        if self.hours > 24:
            raise ValueError("Activity duration cannot be more than 24 hours")
        return self


class PALCalculationRequest(BaseModel):
    """Request schema for Physical Activity Level calculation."""

    age: int = Field(..., gt=0, lt=100, description="Age of the person")
    activities: List[ActivityItem] = Field(
        ..., description="List of activities with their durations"
    )

    @model_validator(mode="after")
    def validate_total_hours(self) -> "PALCalculationRequest":
        """Validate that total activity hours don't exceed 24.

        Returns:
            Validated PALCalculationRequest
        """
        total_hours = sum(activity.hours for activity in self.activities)
        if total_hours > 24:
            raise ValueError("Total activity hours cannot exceed 24 hours")
        return self


class ActivityDetailResponse(BaseModel):
    """Schema for activity detail in PAL calculation response."""

    activity: str = Field(..., description="Name of the activity")
    hours: float = Field(..., description="Duration of the activity in hours")
    mety_level: float = Field(..., description="METy level for the activity")
    mety_minutes: float = Field(..., description="METy-minutes for the activity")


class PALCalculationResponse(BaseModel):
    """Response schema for Physical Activity Level calculation."""

    pal: float = Field(..., description="Physical Activity Level (PAL)")
    total_mety_minutes: float = Field(
        ..., description="Total METy-minutes for all activities"
    )
    details: List[ActivityDetailResponse] = Field(
        ..., description="Details of each activity's contribution"
    )


class ActivitiesResponse(BaseModel):
    """Response schema for getting the list of available activities."""

    activities: List[str] = Field(..., description="List of available activities")


class METyLevelResponse(BaseModel):
    """Response schema for retrieving a METy level."""

    activity: str = Field(..., description="Name of the activity")
    age: int = Field(..., description="Age for the METy level")
    mety_level: float = Field(..., description="METy level value")
