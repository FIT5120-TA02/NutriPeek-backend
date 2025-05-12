"""Database models package."""

# For Alembic to detect models
from src.app.models.activity_mety_level import ActivityMETyLevel
from src.app.models.child_energy_requirement import ChildEnergyRequirement
from src.app.models.daily_nutrient_intake import DailyNutrientIntake
from src.app.models.food_category_fun_fact import FoodCategoryFunFact
from src.app.models.food_nutrient import FoodNutrient
from src.app.models.ingredient_inventory import IngredientInventory
from src.app.models.ingredient_nutrient import IngredientNutrient
from src.app.models.seasonal_food import SeasonalFood

__all__ = [
    "ActivityMETyLevel",
    "ChildEnergyRequirement",
    "DailyNutrientIntake",
    "FoodCategoryFunFact",
    "IngredientInventory",
    "FoodNutrient",
    "IngredientNutrient",
    "SeasonalFood",
]
