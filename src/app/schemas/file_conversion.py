"""Schemas for file conversion API."""

from typing import List
from pydantic import BaseModel


class FileConversionResponse(BaseModel):
    """Response for image conversion endpoint."""

    converted: bool
    file_name: str
    content_type: str
    original_type: str
    message: str


class FileConversionFormatsResponse(BaseModel):
    """Response for supported formats endpoint."""

    input_formats: List[str]
    output_formats: List[str]
