"""CRUD package."""

from src.app.crud.crud_activity_mety_levels import activity_mety_level_crud
from src.app.crud.crud_child_energy_requirement import child_energy_requirement
from src.app.crud.crud_daily_nutrient_intake import daily_nutrient_intake_crud
from src.app.crud.crud_food_category_fun_facts import food_category_fun_fact_crud
from src.app.crud.crud_food_nutrients import food_nutrient_crud
from src.app.crud.crud_seasonal_food import seasonal_food

__all__ = [
    "activity_mety_level_crud",
    "child_energy_requirement",
    "daily_nutrient_intake_crud",
    "food_category_fun_fact_crud",
    "food_nutrient_crud",
    "seasonal_food",
]
