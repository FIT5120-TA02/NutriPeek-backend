"""Database models package."""

# For Alembic to detect models
from src.app.models.daily_nutrient_intake import DailyNutrientIntake
from src.app.models.food_nutrient import FoodNutrient
from src.app.models.ingredient_inventory import IngredientInventory
from src.app.models.ingredient_nutrient import IngredientNutrient

__all__ = [
    "DailyNutrientIntake",
    "IngredientInventory",
    "FoodNutrient",
    "IngredientNutrient",
]
