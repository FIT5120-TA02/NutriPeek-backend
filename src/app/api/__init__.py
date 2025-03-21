"""API package."""

from fastapi import APIRouter

from src.app.api.v1 import api_router as api_v1_router

# Main API router
api_router = APIRouter()

# Include API version routers
api_router.include_router(api_v1_router, prefix="/v1")
