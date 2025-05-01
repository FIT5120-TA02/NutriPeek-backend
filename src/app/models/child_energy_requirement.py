"""Child Energy Requirement model module."""

from sqlalchemy import Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class ChildEnergyRequirement(Base, UUIDMixin, TimestampMixin):
    """Child Energy Requirement model for storing estimated energy requirements for children.

    Attributes:
        age: The age of the child in years
        gender: The gender of the child (boy/girl)
        unit: The unit of measurement for energy (kcal/day, kJ/day)
        physical_activity_level: The physical activity level (numeric value, e.g. 1.0, 1.2, 1.4)
        estimated_energy_requirement: The estimated energy requirement value
    """

    __tablename__ = "child_energy_requirement"

    age: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    gender: Mapped[str] = mapped_column(
        Enum("boy", "girl", name="gender_enum", create_type=False),
        nullable=False,
        index=True,
    )
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    physical_activity_level: Mapped[float] = mapped_column(
        Float, nullable=False, index=True
    )
    estimated_energy_requirement: Mapped[float] = mapped_column(Float, nullable=False)

    # Ensure uniqueness for the combination of age, gender, and physical activity level
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )
