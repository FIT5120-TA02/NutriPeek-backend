"""CRUD package."""

from src.app.crud.crud_activity_mety_levels import activity_mety_level_crud
from src.app.crud.crud_daily_nutrient_intake import daily_nutrient_intake_crud
from src.app.crud.crud_food_category_fun_facts import food_category_fun_fact_crud
from src.app.crud.crud_food_nutrients import food_nutrient_crud

__all__ = [
    "activity_mety_level_crud",
    "daily_nutrient_intake_crud",
    "food_category_fun_fact_crud",
    "food_nutrient_crud",
]
