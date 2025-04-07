"""Main application module."""
from app.api.v1 import yolo_food_model
from src.app.core.setup import create_app

app = create_app()
app.include_router(yolo_food_model.router)