"""Ingredient Inventory model module."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class IngredientInventory(Base, UUIDMixin, TimestampMixin):
    """Ingredient Inventory model for tracking ingredients in a children's profile inventory.

    Attributes:
        children_profile_id: The ID of the children's profile (stored in frontend)
        ingredient_nutrients: Relationship to the join table connecting to nutrients
    """

    __tablename__ = "ingredient_inventory"

    children_profile_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # Relationships
    ingredient_nutrients = relationship(
        "IngredientNutrient",
        back_populates="ingredient_inventory",
        cascade="all, delete-orphan",
    )
