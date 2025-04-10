"""Service for QR code generation and file upload."""

import base64
import logging
import threading
import uuid
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import qrcode
from PIL import Image

from src.app.core.temp_storage import FileStatus, temp_storage

# Configure logging
logger = logging.getLogger(__name__)


class QRCodeService:
    """Service for QR code generation and file upload.

    This service handles operations related to generating QR codes for file uploads,
    storing uploaded files, and managing temporary storage for uploads.
    """

    def __init__(self, cleanup_interval: int = 300):
        """Initialize QRCodeService.

        Args:
            cleanup_interval: Interval in seconds for running cleanup tasks
        """
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()

        # Set of allowed mime types for uploaded images
        self._allowed_mime_types = {"image/jpeg", "image/jpg", "image/png"}

        # Common image file signatures (magic numbers) for validation
        self._file_signatures: Dict[str, List[bytes]] = {
            "jpeg": [b"\xff\xd8\xff"],
            "png": [b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"],
        }

    def _start_cleanup_thread(self) -> None:
        """Start a thread that periodically cleans up expired entries."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._stop_cleanup.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_task,
            daemon=True,
        )
        self._cleanup_thread.start()

    def _cleanup_task(self) -> None:
        """Background task to clean up expired entries."""
        while not self._stop_cleanup.is_set():
            try:
                count = temp_storage.cleanup_expired()
                if count > 0:
                    logger.info(f"Cleaned up {count} expired entries")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")

            # Wait for next cleanup interval or until stopped
            self._stop_cleanup.wait(self._cleanup_interval)

    def stop_cleanup_thread(self) -> None:
        """Stop the cleanup thread gracefully."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)

    def generate_upload_qr(
        self, base_url: str, expiry_seconds: int = 300
    ) -> Tuple[str, str, str]:
        """Generate a QR code for file upload with a short link.

        Args:
            base_url: Base URL for the upload endpoint
            expiry_seconds: Time in seconds before the upload link expires

        Returns:
            Tuple containing:
                - shortcode: Unique identifier for the upload
                - upload_url: Full URL for uploading files
                - qr_code_base64: Base64-encoded QR code image
        """
        # Generate a short but unique identifier
        shortcode = str(uuid.uuid4())[:8]
        # Create entry in temp storage with specified expiry time
        temp_storage.create_entry(shortcode, expiry_seconds=expiry_seconds)

        # Generate the upload URL
        upload_url = f"{base_url}/QRUpload?code={shortcode}"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(upload_url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert QR code to base64-encoded string
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        qr_code_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        logger.info(f"Generated QR code with shortcode: {shortcode}")
        return shortcode, upload_url, qr_code_base64

    def validate_image(self, file_data: bytes) -> Tuple[bool, Optional[str]]:
        """Validate that the uploaded file is a valid image.

        Args:
            file_data: Binary file data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size (minimal check)
        if len(file_data) < 50:
            return False, "File is too small to be a valid image"

        # Check file signature (magic numbers)
        is_valid = False
        for file_type, signatures in self._file_signatures.items():
            for signature in signatures:
                if file_data.startswith(signature):
                    is_valid = True
                    break

        if not is_valid:
            return (
                False,
                "Unsupported file format. Please upload JPEG or PNG images only.",
            )

        # Additional validation with PIL
        try:
            img = Image.open(BytesIO(file_data))
            img.verify()  # Verify image integrity
            return True, None
        except Exception as e:
            return False, f"Invalid image: {str(e)}"

    def save_uploaded_file(
        self, shortcode: str, file_data: bytes
    ) -> Tuple[bool, Optional[str]]:
        """Save uploaded file data.

        Args:
            shortcode: Shortcode identifier for the upload
            file_data: Binary data of the uploaded file

        Returns:
            Tuple of (success, error_message)
        """
        # First validate the image
        is_valid, error = self.validate_image(file_data)
        if not is_valid:
            temp_storage.update_status(shortcode, FileStatus.FAILED, error)
            return False, error

        # Save file data
        success, error = temp_storage.save_file(shortcode, file_data)
        if not success:
            logger.error(f"Failed to save file for shortcode {shortcode}: {error}")
            return False, error

        logger.info(f"Successfully saved file for shortcode {shortcode}")
        return True, None

    def get_file_status(
        self, shortcode: str
    ) -> Tuple[Optional[FileStatus], Optional[str]]:
        """Get the status of an uploaded file.

        Args:
            shortcode: Shortcode identifier for the upload

        Returns:
            Tuple of (status, error_message) or (None, None) if not found
        """
        return temp_storage.get_status(shortcode)

    def mark_as_processing(self, shortcode: str) -> bool:
        """Mark a file as being processed.

        Args:
            shortcode: Shortcode identifier for the upload

        Returns:
            True if successful, False if shortcode not found
        """
        return temp_storage.update_status(shortcode, FileStatus.PROCESSING)

    def mark_as_processed(self, shortcode: str) -> bool:
        """Mark a file as successfully processed.

        Args:
            shortcode: Shortcode identifier for the upload

        Returns:
            True if successful, False if shortcode not found
        """
        return temp_storage.update_status(shortcode, FileStatus.PROCESSED)

    def mark_as_failed(self, shortcode: str, error: str) -> bool:
        """Mark a file as failed processing.

        Args:
            shortcode: Shortcode identifier for the upload
            error: Error message describing the failure

        Returns:
            True if successful, False if shortcode not found
        """
        return temp_storage.update_status(shortcode, FileStatus.FAILED, error)


# Create a singleton instance
qrcode_service = QRCodeService()
