from fastapi import APIRouter, UploadFile, File
from app.services.predict import predict
import shutil
import os
import uuid

router = APIRouter(
    prefix="/food",
    tags=["Food Recognition"]
)

UPLOAD_DIR = "uploads"  # Define upload directory

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/predict")
async def predict_food(file: UploadFile = File(...)):
    """
    Upload an image and predict the food items.
    """
    # Save uploaded file
    file_extension = file.filename.split(".")[-1]
    temp_filename = f"{uuid.uuid4()}.{file_extension}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename)

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Predict
    predictions = predict(temp_path)

    # Clean up temp file
    os.remove(temp_path)

    return {
        "predictions": predictions
    }

