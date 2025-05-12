"""API v1 package."""

from fastapi import APIRouter

from src.app.api.v1 import (
    activity,
    child_energy_requirement,
    file_conversion,
    food,
    food_category,
    food_detection,
    health,
    nutrient,
    seasonal_food,
    websocket,
)

# API v1 router
api_router = APIRouter()

# Include routers
api_router.include_router(activity.router)
api_router.include_router(child_energy_requirement.router)
api_router.include_router(food.router)
api_router.include_router(food_category.router)
api_router.include_router(food_detection.router)
api_router.include_router(health.router)
api_router.include_router(nutrient.router)
api_router.include_router(seasonal_food.router)
api_router.include_router(websocket.router)
api_router.include_router(file_conversion.router)

__all__ = ["api_router"]
