from typing import Optional

from pydantic import BaseModel, Field


class GenerateUploadQRResponse(BaseModel):
    """Response schema for QR code generation endpoint."""

    upload_url: str = Field(..., description="URL for uploading images")
    qrcode_base64: str = Field(..., description="Base64-encoded QR code image")
    expires_in_seconds: int = Field(
        300, description="Time in seconds before the upload link expires"
    )


class UploadImageResponse(BaseModel):
    """Response schema for image upload endpoint."""

    message: str = Field(..., description="Status message")
    shortcode: Optional[str] = Field(
        None, description="Shortcode for tracking the upload"
    )


class FileStatusResponse(BaseModel):
    """Response schema for file status endpoint."""

    shortcode: str = Field(..., description="Shortcode for the upload")
    status: str = Field(..., description="Current status of the file")
    error: Optional[str] = Field(None, description="Error message if processing failed")
