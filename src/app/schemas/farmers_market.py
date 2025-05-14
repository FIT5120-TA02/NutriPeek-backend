"""Farmers market schemas for request/response validation."""

from datetime import time
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DayOfWeekEnum(str, Enum):
    """Valid day of week values for farmers market operating hours."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class FarmersMarketBase(BaseModel):
    """Base schema with shared Farmers Market attributes."""

    name: str = Field(..., description="Name of the farmers market")
    address: str = Field(..., description="Full address of the farmers market location")
    opening_hours_text: str = Field(
        ..., description="Text description of opening hours"
    )
    region: str = Field(
        ..., description="Geographic region where the market is located"
    )


class FarmersMarketResponse(FarmersMarketBase):
    """Schema for Farmers Market responses."""

    id: UUID = Field(..., description="UUID primary key for the farmers market")

    # Enhanced fields
    city: Optional[str] = Field(None, description="City where the market is located")
    postal_code: Optional[str] = Field(
        None, description="Postal code of the market location"
    )

    # Geolocation coordinates
    latitude: Optional[float] = Field(
        None, description="Geographic latitude coordinate"
    )
    longitude: Optional[float] = Field(
        None, description="Geographic longitude coordinate"
    )

    # Structured opening hours
    primary_day: Optional[DayOfWeekEnum] = Field(
        None, description="Main day of the week when the market operates"
    )
    is_recurring: Optional[bool] = Field(
        None, description="Whether the market operates on a recurring schedule"
    )
    frequency: Optional[str] = Field(
        None, description="How often the market operates (e.g., 'weekly', 'monthly')"
    )
    opening_time: Optional[time] = Field(None, description="Time when the market opens")
    closing_time: Optional[time] = Field(
        None, description="Time when the market closes"
    )

    # Additional information
    website: Optional[str] = Field(
        None, description="URL of the farmers market website"
    )
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    description: Optional[str] = Field(
        None, description="Detailed description of the farmers market"
    )

    model_config = {"from_attributes": True}


class FarmersMarketListResponse(BaseModel):
    """Schema for listing multiple farmers markets."""

    items: List[FarmersMarketResponse]
    total: int = Field(..., description="Total number of farmers markets")
