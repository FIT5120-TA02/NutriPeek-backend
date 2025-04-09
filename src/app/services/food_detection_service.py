"""Food detection service using Ultralytics YOLO model."""

import time
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from fastapi import UploadFile
from ultralytics import YOLO

from src.app.core.exceptions.custom import ModelLoadError, ProcessingError
from src.app.schemas.food_detection import FoodItemDetection


class FoodDetectionService:
    """Service for detecting food items in images using YOLO model."""

    # Base directory for ML models
    MODEL_BASE_DIR = Path("src/app/core/ml/models")

    # Default model to use if none specified
    DEFAULT_MODEL = "yolo11n.pt"

    def __init__(
        self,
        model_name: Optional[str] = None,
        confidence_threshold: float = 0.35,
    ):
        """Initialize the food detection service.

        Args:
            model_name: Name of the model file to use (e.g., "yolo11n.pt").
                        If None, uses the default model.
            confidence_threshold: Minimum confidence threshold for detections (0-1).
        """
        self.MODEL_BASE_DIR.mkdir(parents=True, exist_ok=True)

        model_filename = model_name if model_name else self.DEFAULT_MODEL
        self.model_path = self.MODEL_BASE_DIR / model_filename

        self._model = None
        self._confidence_threshold = confidence_threshold
        self._model_name = model_filename

    @property
    def model(self) -> YOLO:
        """Lazy-load the YOLO model when first needed."""
        if self._model is None:
            try:
                if not self.model_path.exists():
                    raise ModelLoadError(f"Model file not found at: {self.model_path}")

                self._model = YOLO(str(self.model_path))
            except Exception as e:
                raise ModelLoadError(f"Failed to load YOLO model: {str(e)}")
        return self._model

    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model_name

    async def process_image(
        self, image_file: UploadFile
    ) -> Tuple[List[FoodItemDetection], float, int, int]:
        """Process an uploaded image and detect food items.

        Args:
            image_file: Uploaded image file

        Returns:
            Tuple containing:
                - List of food item detections
                - Processing time in milliseconds
                - Image width
                - Image height

        Raises:
            ProcessingError: If image processing fails
        """
        try:
            # Read image from upload
            contents = await image_file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise ProcessingError("Failed to decode image")

            # Get image dimensions
            height, width = img.shape[:2]

            # Start timing
            start_time = time.time()

            # Perform detection
            results = self.model(img, verbose=False)

            # Process results
            detections = []

            # First result (batch size is 1)
            result = results[0]

            # Extract boxes, confidences, and class ids
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    confidence = float(box.conf[0])

                    # Skip low confidence detections
                    if confidence < self._confidence_threshold:
                        continue

                    # Get class name
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]

                    # Get coordinates (normalized format)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Create detection object
                    detection = FoodItemDetection(
                        class_name=class_name,
                        confidence=confidence,
                        x_min=x1,
                        y_min=y1,
                        x_max=x2,
                        y_max=y2,
                    )

                    detections.append(detection)

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            return detections, processing_time_ms, width, height

        except Exception as e:
            raise ProcessingError(f"Error processing image: {str(e)}")


# Create a singleton instance with default settings
food_detection_service = FoodDetectionService()
