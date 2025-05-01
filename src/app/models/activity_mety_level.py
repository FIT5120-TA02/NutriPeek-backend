"""Activity METy Level model module."""

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class ActivityMETyLevel(Base, UUIDMixin, TimestampMixin):
    """Activity METy Level model for storing metabolic equivalent task values for activities by age.

    Attributes:
        activity_category: The category of the physical activity
        specific_activity: The specific activity description
        age: The age for which the METy level is applicable
        mety_level: The metabolic equivalent task level value
    """

    __tablename__ = "activity_mety_level"

    activity_category: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    specific_activity: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    mety_level: Mapped[float] = mapped_column(Float, nullable=False)

    # Ensure uniqueness for the combination of activity and age
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )
