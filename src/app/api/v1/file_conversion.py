"""File conversion API endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from src.app.schemas.file_conversion import (
    FileConversionFormatsResponse,
    FileConversionResponse,
)
from src.app.services.file_conversion_service import file_conversion_service

router = APIRouter(prefix="/file-conversion", tags=["file-conversion"])


@router.post(
    "/convert",
    response_model=FileConversionResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert image files to standard formats",
    description="Convert images like HEIC to standard web formats like JPEG. Returns converted file info.",
)
async def convert_image(
    image: UploadFile = File(...),
    target_format: str = "JPEG",
    quality: int = 90,
):
    """Convert an image file to a standard format like JPEG or PNG.

    This endpoint is especially useful for handling HEIC files from iOS devices.

    Args:
        image: The image file to convert
        target_format: Target format (default: JPEG)
        quality: Image quality for lossy formats (1-100)

    Returns:
        Information about the converted file

    Raises:
        HTTPException: If processing fails or image is invalid
    """
    # Validate file is an image
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    try:
        # Get original content type
        original_type = image.content_type

        # Convert the image if needed
        converted_bytes, new_mime_type, new_filename = (
            await file_conversion_service.convert_image_if_needed(
                image, target_format, quality
            )
        )

        # Check if conversion actually happened
        was_converted = original_type.lower() != new_mime_type.lower()

        # Return success response with file info
        response = FileConversionResponse(
            converted=was_converted,
            file_name=new_filename,
            content_type=new_mime_type,
            original_type=original_type,
            message=(
                "File successfully converted"
                if was_converted
                else "No conversion needed"
            ),
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting image: {str(e)}",
        )


@router.post(
    "/convert-download",
    status_code=status.HTTP_200_OK,
    summary="Convert image and download result",
    description="Convert images like HEIC to standard web formats and return the binary content",
)
async def convert_image_download(
    image: UploadFile = File(...),
    target_format: str = "JPEG",
    quality: int = 90,
):
    """Convert an image file and return the converted binary.

    This endpoint is similar to /convert but returns the actual file content
    instead of just file information.

    Args:
        image: The image file to convert
        target_format: Target format (default: JPEG)
        quality: Image quality for lossy formats (1-100)

    Returns:
        StreamingResponse with the converted image binary

    Raises:
        HTTPException: If processing fails or image is invalid
    """
    # Validate file is an image
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    try:
        # Convert the image if needed
        converted_bytes, new_mime_type, new_filename = (
            await file_conversion_service.convert_image_if_needed(
                image, target_format, quality
            )
        )

        # Return the image as a response
        return StreamingResponse(
            iter([converted_bytes]),
            media_type=new_mime_type,
            headers={"Content-Disposition": f"attachment; filename={new_filename}"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting image: {str(e)}",
        )


@router.get(
    "/formats",
    response_model=FileConversionFormatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get supported conversion formats",
    description="Returns lists of supported input and output formats for the conversion service",
)
async def get_supported_formats():
    """Get lists of supported input and output formats.

    This endpoint is useful for clients to check which formats can be
    processed and which output formats are available.

    Returns:
        Dictionary with input and output formats
    """
    formats = file_conversion_service.get_supported_formats()
    return FileConversionFormatsResponse(
        input_formats=formats["input"],
        output_formats=formats["output"],
    )
