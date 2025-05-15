"""Farmers Market model module."""

import enum
from datetime import time
from typing import Optional

from sqlalchemy import Boolean, Enum, Float, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class DayOfWeek(enum.Enum):
    """Valid day of week values for farmers market operating hours."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class FarmersMarket(Base, UUIDMixin, TimestampMixin):
    """Model representing a farmers market location and details.

    Attributes:
        id: UUID primary key for the farmers market
        name: Name of the farmers market
        address: Full address of the farmers market location
        opening_hours_text: Text description of opening hours
        region: Geographic region where the market is located
        city: City where the market is located
        postal_code: Postal code of the market location
        latitude: Geographic latitude coordinate
        longitude: Geographic longitude coordinate
        primary_day: Main day of the week when the market operates
        is_recurring: Whether the market operates on a recurring schedule
        frequency: How often the market operates (e.g., "weekly", "monthly")
        opening_time: Time when the market opens
        closing_time: Time when the market closes
        website: URL of the farmers market website
        phone: Contact phone number
        email: Contact email address
        description: Detailed description of the farmers market
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """

    __tablename__ = "farmers_market"

    # Essential fields (directly from the dataset)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    opening_hours_text: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Enhanced fields for better structure and searchability
    # Address components (can be populated through geocoding service later)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Geolocation coordinates
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Structured opening hours (requires parsing the text)
    primary_day: Mapped[Optional[DayOfWeek]] = mapped_column(
        Enum(DayOfWeek), nullable=True
    )
    is_recurring: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    opening_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    closing_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Additional useful information (to be populated later)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
