"""API v1 package."""

from fastapi import APIRouter

from src.app.api.v1.food_detection import router as food_detection_router
from src.app.api.v1.health import router as health_router

api_router = APIRouter()

# Include all routers
api_router.include_router(health_router)
api_router.include_router(food_detection_router)
