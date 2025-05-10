"""Schemas for WebSocket session management."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Status of a WebSocket session."""

    CREATED = "created"
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"


class FileTransferStatus(str, Enum):
    """Status of a file transfer operation."""

    PENDING = "pending"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"


class MealType(str, Enum):
    """Type of meal for the uploaded food image."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class CreateSessionResponse(BaseModel):
    """Response schema for session creation."""

    session_id: str = Field(..., description="Unique session identifier")
    qrcode_base64: str = Field(..., description="Base64-encoded QR code image")
    expires_in_seconds: int = Field(
        300, description="Time in seconds before the session expires"
    )
    join_url: str = Field(..., description="URL for joining the session")


class SessionStatusResponse(BaseModel):
    """Response schema for session status check."""

    session_id: str = Field(..., description="Session identifier")
    status: SessionStatus = Field(..., description="Current status of the session")
    connected_clients: int = Field(0, description="Number of connected clients")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    error: Optional[str] = Field(None, description="Error message if any")


class JoinSessionResponse(BaseModel):
    """Response schema for joining a session."""

    session_id: str = Field(..., description="Session identifier")
    status: SessionStatus = Field(..., description="Current status of the session")
    message: str = Field(..., description="Status message")


class FileInfo(BaseModel):
    """Information about a transferred file."""

    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    status: FileTransferStatus = Field(..., description="Status of the file transfer")
    uploaded_at: datetime = Field(..., description="Timestamp of upload completion")
    meal_type: Optional[MealType] = Field(
        None, description="Type of meal (breakfast, lunch, dinner)"
    )


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""

    file_id: str = Field(..., description="Unique file identifier")
    session_id: str = Field(..., description="Session identifier")
    status: FileTransferStatus = Field(..., description="Status of the file upload")
    message: str = Field(..., description="Status message")
    meal_type: Optional[MealType] = Field(
        None, description="Type of meal (breakfast, lunch, dinner)"
    )


class FilesListResponse(BaseModel):
    """Response schema for listing files in a session."""

    session_id: str = Field(..., description="Session identifier")
    files: List[FileInfo] = Field(default_factory=list, description="List of files")


class WebSocketMessage(BaseModel):
    """Base schema for WebSocket messages."""

    type: str = Field(..., description="Message type")
    session_id: str = Field(..., description="Session identifier")


class FileUploadedMessage(WebSocketMessage):
    """WebSocket message for notifying about a new file upload."""

    type: str = "file_uploaded"
    file_info: FileInfo = Field(..., description="Information about the uploaded file")


class SessionUpdateMessage(WebSocketMessage):
    """WebSocket message for notifying about session status changes."""

    type: str = "session_update"
    status: SessionStatus = Field(..., description="New session status")
    connected_clients: int = Field(..., description="Number of connected clients")
    message: Optional[str] = Field(None, description="Additional message")
