"""API v1 package."""

from fastapi import APIRouter

from src.app.api.v1.food import router as food_router
from src.app.api.v1.food_detection import router as food_detection_router
from src.app.api.v1.health import router as health_router
from src.app.api.v1.nutrient import router as nutrient_router
from src.app.api.v1.qrcode_upload import router as qrcode_upload_router

api_router = APIRouter()

# Include all routers
api_router.include_router(health_router)
api_router.include_router(food_detection_router)
api_router.include_router(qrcode_upload_router)
api_router.include_router(food_router)
api_router.include_router(nutrient_router)
