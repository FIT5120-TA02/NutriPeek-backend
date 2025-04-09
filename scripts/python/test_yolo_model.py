#!/usr/bin/env python
"""
YOLO Model Test Script for Food Detection
=========================================

This script tests the YOLO model for food detection and generates visualized output.

Usage:
    python test_yolo_model.py [--input INPUT_PATH] [--output OUTPUT_DIR]

Arguments:
    --input, -i      Path to the input image (default: test1.jpg in the script directory)
    --output, -o     Path to the output directory (default: same as input image directory)

Requirements:
    - ultralytics package installed (pip install ultralytics)
    - OpenCV installed (pip install opencv-python)
    - YOLO model file (yolo11n.pt) must exist in src/app/core/ml/models/

Outputs:
    - An image with detection visualization (INPUT_FILENAME_detections.jpg)
    - A text file with detection results (INPUT_FILENAME_results.txt)
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

# Add src to the Python path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test YOLO model for food detection.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=str(Path(__file__).parent / "test1.jpg"),
        help="Path to the input image for detection",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to the output directory (defaults to same directory as input image)",
    )

    return parser.parse_args()


def test_model(input_path, output_dir=None):
    """
    Test loading and running inference with the YOLO model.

    Args:
        input_path (str): Path to the input image
        output_dir (str, optional): Directory to save output files.
            If None, uses the same directory as the input image.

    Returns:
        bool: True if the test was successful, False otherwise
    """
    # Convert paths to Path objects
    input_path = Path(input_path)

    # If output directory is not specified, use the input image's directory
    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

    # Define output filenames
    output_image = output_dir / f"{input_path.stem}_detections{input_path.suffix}"
    output_text = output_dir / f"{input_path.stem}_results.txt"

    # Path to the model
    project_root = Path(__file__).parent.parent.parent
    model_path = project_root / "src/app/core/ml/models/yolo11n.pt"

    if not model_path.exists():
        print(f"Error: Model file not found at {model_path}")
        return False

    if not input_path.exists():
        print(f"Error: Input image not found at {input_path}")
        return False

    print(f"Loading model from {model_path}...")
    try:
        # Load model
        model = YOLO(str(model_path))
        print("Model loaded successfully!")

        # Load the test image
        print(f"Reading test image from {input_path}...")
        img = cv2.imread(str(input_path))

        if img is None:
            print(f"Error: Failed to read image from {input_path}")
            return False

        print(f"Image loaded: {img.shape[1]}x{img.shape[0]} pixels")

        print("Running inference on test image...")
        start_time = time.time()

        # Run inference
        results = model(img)

        processing_time = (time.time() - start_time) * 1000
        print(f"Inference completed in {processing_time:.2f} ms")

        # Check results
        result = results[0]
        print(f"Model detected {len(result.boxes)} objects")

        # Open text file for writing results
        with open(output_text, "w") as f:
            f.write("YOLO Detection Results\n")
            f.write("=====================\n\n")
            f.write(f"Input image: {input_path}\n")
            f.write(f"Detection time: {processing_time:.2f} ms\n")
            f.write(f"Objects detected: {len(result.boxes)}\n\n")

            if result.boxes is not None and len(result.boxes) > 0:
                f.write("Detected objects:\n")

                for i, box in enumerate(result.boxes):
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Write to file
                    f.write(
                        f"  {i+1}. Class: {class_name}, Confidence: {confidence:.2f}\n"
                    )
                    f.write(
                        f"     Bounding box: ({x1:.1f}, {y1:.1f}) to ({x2:.1f}, {y2:.1f})\n"
                    )

                # Save the image with detections
                result_plotted = result.plot()
                cv2.imwrite(str(output_image), result_plotted)
                print(f"\nImage with detections saved to {output_image}")
                f.write(f"\nImage with detections saved to {output_image}\n")

            print(f"Results written to {output_text}")

        return True

    except Exception as e:
        print(f"Error testing model: {e}")
        return False


if __name__ == "__main__":
    print("YOLO Model Test Script")
    print("======================")

    args = parse_args()
    success = test_model(args.input, args.output)

    if success:
        print("\nSuccess! The YOLO model is working correctly.")
        sys.exit(0)
    else:
        print("\nFailed! The YOLO model test encountered errors.")
        sys.exit(1)
