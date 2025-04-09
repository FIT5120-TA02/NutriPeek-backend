"""Ingredient Nutrient join table model module."""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db.base_class import Base, TimestampMixin


class IngredientNutrient(Base, TimestampMixin):
    """Ingredient Nutrient join table model for linking food nutrients to ingredient inventory.

    This is a join table that associates ingredients in an inventory with
    food nutrients, along with quantity and unit information.

    Attributes:
        food_nutrient_id: Foreign key to the food nutrient
        ingredient_inventory_id: Foreign key to the ingredient inventory
        quantity: The quantity of the ingredient
        unit: The unit of measurement for the quantity
        food_nutrient: Relationship to the food nutrient
        ingredient_inventory: Relationship to the ingredient inventory
    """

    __tablename__ = "ingredient_nutrients"

    food_nutrient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("food_nutrient.id"), primary_key=True
    )
    ingredient_inventory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingredient_inventory.id"), primary_key=True
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    food_nutrient = relationship("FoodNutrient", back_populates="ingredient_nutrients")
    ingredient_inventory = relationship(
        "IngredientInventory", back_populates="ingredient_nutrients"
    )
