from ultralytics import YOLO
from pathlib import Path
from typing import List

# Load YOLOv8 classification model
model_path = Path(__file__).resolve().parent.parent / "models" / "yolov8n-cls.pt"
model = YOLO(str(model_path))


def predict(image_path: str) -> List[str]:

    """
    Predict the food items from the input image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        List[str]: A list of predicted food item names.
    """
    results = model.predict(image_path)
    predictions = []

    for result in results:
        names = result.names  # class name mapping
        classes = result.probs.top5  # get top 5 predicted classes
        for class_id in classes:
            predictions.append(names[class_id])

    return predictions
