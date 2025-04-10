"""Import all models here to ensure they are registered with SQLAlchemy."""

from src.app.core.db.base_class import Base  # noqa
from src.app.models.daily_nutrient_intake import DailyNutrientIntake  # noqa
from src.app.models.ingredient_inventory import IngredientInventory  # noqa
from src.app.models.food_nutrient import FoodNutrient  # noqa
from src.app.models.ingredient_nutrient import IngredientNutrient  # noqa