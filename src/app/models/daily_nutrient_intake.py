"""Daily Nutrient Intake model module."""

from sqlalchemy import Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class DailyNutrientIntake(Base, UUIDMixin, TimestampMixin):
    """Daily Nutrient Intake model for tracking recommended daily nutrient intake by age and gender.

    Attributes:
        nutrient: The name of the nutrient
        unit: The unit of measurement for the nutrient
        age: The age for which this intake is recommended
        gender: The gender for which this intake is recommended (boy/girl)
        intake: The recommended intake amount
        category: The category of the nutrient
    """

    __tablename__ = "daily_nutrient_intake"

    nutrient: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(
        Enum("boy", "girl", name="gender_enum"), nullable=False
    )
    intake: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
