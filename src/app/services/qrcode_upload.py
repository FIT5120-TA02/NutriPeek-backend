"""Service for QR code generation and file upload."""

import base64
import threading
import time
import uuid
from io import BytesIO
from typing import Tuple

import qrcode

from src.app.core.temp_storage import temp_storage


class QRCodeUploadService:
    """Service for QR code generation and file upload.

    This service handles operations related to generating QR codes for file uploads,
    storing uploaded files, and managing temporary storage for uploads.
    """

    @staticmethod
    def generate_upload_qr(base_url: str) -> Tuple[str, str, str]:
        """Generate a QR code for file upload with a short link.

        Args:
            base_url: Base URL for the upload endpoint

        Returns:
            Tuple containing:
                - shortcode: Unique identifier for the upload
                - upload_url: Full URL for uploading files
                - qr_code_base64: Base64-encoded QR code image
        """
        shortcode = str(uuid.uuid4())[:8]
        temp_storage.create_entry(shortcode)
        upload_url = f"{base_url}/upload/{shortcode}"
        qr = qrcode.make(upload_url)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        qr_code_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return shortcode, upload_url, qr_code_base64

    @staticmethod
    def auto_delete_shortcode(shortcode: str, delay: int = 300) -> None:
        """Auto delete the shortcode after a delay.

        Args:
            shortcode: Shortcode to delete
            delay: Time in seconds before deletion (default: 300 seconds / 5 minutes)
        """
        time.sleep(delay)
        if temp_storage.exists(shortcode):
            temp_storage.delete_entry(shortcode)

    @staticmethod
    def save_uploaded_file(shortcode: str, file_data: bytes) -> None:
        """Save uploaded file data and schedule automatic deletion.

        Args:
            shortcode: Shortcode identifier for the upload
            file_data: Binary data of the uploaded file
        """
        temp_storage.save_file(shortcode, file_data)
        threading.Thread(
            target=QRCodeUploadService.auto_delete_shortcode,
            args=(shortcode,),
            daemon=True,
        ).start()


# Create a singleton instance
qrcode_upload_service = QRCodeUploadService()
