"""Service for converting image files between formats."""

import io
import logging
import os
from typing import Tuple

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener

# Register HEIF/HEIC opener with Pillow
register_heif_opener()

# Configure logging
logger = logging.getLogger(__name__)

# List of supported input formats
SUPPORTED_INPUT_FORMATS = {
    "image/heic": ".heic",
    "image/heif": ".heif",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
    "image/bmp": ".bmp",
    "image/gif": ".gif",
}

# Map of supported output formats
SUPPORTED_OUTPUT_FORMATS = {
    "JPEG": {"mime": "image/jpeg", "ext": ".jpg"},
    "PNG": {"mime": "image/png", "ext": ".png"},
    "WEBP": {"mime": "image/webp", "ext": ".webp"},
    "GIF": {"mime": "image/gif", "ext": ".gif"},
    "BMP": {"mime": "image/bmp", "ext": ".bmp"},
}

# Default output format
DEFAULT_OUTPUT_FORMAT = "JPEG"
DEFAULT_OUTPUT_MIME = "image/jpeg"
DEFAULT_OUTPUT_EXT = ".jpg"

# Quality for JPEG compression
DEFAULT_JPEG_QUALITY = 90


class FileConversionService:
    """Service for converting image files between formats."""

    def __init__(self):
        """Initialize the file conversion service."""
        pass

    async def convert_image_if_needed(
        self,
        image_file: UploadFile,
        target_format: str = DEFAULT_OUTPUT_FORMAT,
        quality: int = DEFAULT_JPEG_QUALITY,
    ) -> Tuple[bytes, str, str]:
        """Convert image to target format if it's not already in that format.

        Args:
            image_file: The uploaded image file
            target_format: The desired output format (default: JPEG)
            quality: Quality for lossy formats like JPEG (1-100)

        Returns:
            Tuple containing:
                - Image bytes in the target format
                - New MIME type
                - New filename with correct extension
        """
        # Normalize target format
        target_format = target_format.upper()
        if target_format not in SUPPORTED_OUTPUT_FORMATS:
            logger.warning(
                f"Unsupported target format: {target_format}. Using JPEG instead."
            )
            target_format = DEFAULT_OUTPUT_FORMAT

        # Ensure quality is in valid range
        quality = max(1, min(100, quality))

        # Get MIME type and determine if conversion is needed
        mime_type = image_file.content_type or "application/octet-stream"
        logger.info(
            f"Processing file: {image_file.filename}, MIME type: {mime_type}, Target format: {target_format}"
        )

        # Check if conversion is needed
        needs_conversion = self._needs_conversion(mime_type, target_format)

        if not needs_conversion:
            # If no conversion needed, read and return the file as-is
            logger.info(f"No conversion needed for {image_file.filename}")
            contents = await image_file.read()
            return contents, mime_type, image_file.filename or "image.jpg"

        # Perform conversion
        logger.info(
            f"Converting {image_file.filename} from {mime_type} to {target_format}"
        )
        try:
            # Read image data
            image_bytes = await image_file.read()

            # Convert image
            converted_bytes, new_mime_type, new_filename = await self._convert_image(
                image_bytes,
                image_file.filename or "image",
                mime_type,
                target_format,
                quality,
            )

            return converted_bytes, new_mime_type, new_filename

        except Exception as e:
            # Log the error
            logger.error(f"Error converting image: {str(e)}")

            # If conversion fails, return the original image
            await image_file.seek(0)
            original_bytes = await image_file.read()
            return original_bytes, mime_type, image_file.filename or "image.jpg"

    async def _convert_image(
        self,
        image_bytes: bytes,
        original_filename: str,
        original_mime: str,
        target_format: str,
        quality: int,
    ) -> Tuple[bytes, str, str]:
        """Convert image bytes to target format.

        Args:
            image_bytes: The raw image data
            original_filename: Original filename
            original_mime: Original MIME type
            target_format: Target format (JPEG, PNG, etc.)
            quality: Quality for lossy formats

        Returns:
            Tuple of (converted bytes, new MIME type, new filename)
        """
        output_buffer = io.BytesIO()

        try:
            # Open the image with Pillow (will use registered HEIF opener if needed)
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert to RGB if image has alpha channel and target is JPEG
                if target_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # For WEBP, ensure the mode is compatible
                elif target_format == "WEBP" and img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if img.mode == "LA" else "RGB")

                # Save with appropriate parameters for each format
                save_params = {}

                if target_format == "JPEG":
                    save_params["quality"] = quality
                    save_params["optimize"] = True
                elif target_format == "PNG":
                    save_params["optimize"] = True
                elif target_format == "WEBP":
                    save_params["quality"] = quality
                    save_params["method"] = 6  # Highest compression method

                # Save to target format
                img.save(output_buffer, format=target_format, **save_params)

                # Get the converted image bytes
                output_buffer.seek(0)
                converted_bytes = output_buffer.read()

                # Create a new filename with the correct extension
                base_name = os.path.splitext(original_filename)[0]
                new_extension = SUPPORTED_OUTPUT_FORMATS[target_format]["ext"]
                new_filename = f"{base_name}{new_extension}"

                # Get new MIME type
                new_mime_type = SUPPORTED_OUTPUT_FORMATS[target_format]["mime"]

                return converted_bytes, new_mime_type, new_filename

        except UnidentifiedImageError:
            logger.error(
                f"Could not identify image format in file: {original_filename}"
            )
            raise
        except Exception as e:
            logger.error(f"Error in conversion process: {str(e)}")
            raise
        finally:
            output_buffer.close()

    def _needs_conversion(self, mime_type: str, target_format: str) -> bool:
        """Determine if conversion is needed based on mime type and target format.

        Args:
            mime_type: Current MIME type
            target_format: Desired output format

        Returns:
            True if conversion is needed, False otherwise
        """
        # HEIC/HEIF always need conversion for browser compatibility
        if mime_type.lower() in ["image/heic", "image/heif"]:
            return True

        # If not a known supported format, attempt conversion
        if mime_type.lower() not in SUPPORTED_INPUT_FORMATS:
            return True

        # Convert if current format doesn't match target format
        current_format = self._get_format_from_mime(mime_type)
        return current_format != target_format

    def _get_format_from_mime(self, mime_type: str) -> str:
        """Convert MIME type to Pillow format string."""
        mime_map = {
            "image/jpeg": "JPEG",
            "image/jpg": "JPEG",
            "image/png": "PNG",
            "image/webp": "WEBP",
            "image/heic": "HEIF",
            "image/heif": "HEIF",
            "image/tiff": "TIFF",
            "image/bmp": "BMP",
            "image/gif": "GIF",
        }
        return mime_map.get(mime_type.lower(), "JPEG")

    def is_conversion_needed(
        self, mime_type: str, target_format: str = DEFAULT_OUTPUT_FORMAT
    ) -> bool:
        """Check if a file with this MIME type needs conversion to target format."""
        return self._needs_conversion(mime_type, target_format.upper())

    def get_supported_formats(self) -> dict:
        """Get a dictionary of supported input and output formats."""
        return {
            "input": list(SUPPORTED_INPUT_FORMATS.keys()),
            "output": list(SUPPORTED_OUTPUT_FORMATS.keys()),
        }


# Create a singleton instance
file_conversion_service = FileConversionService()
