"""WebSocket session management service."""

import asyncio
import base64
import io
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import qrcode
from fastapi import UploadFile, WebSocket

from src.app.core.session_storage import session_storage
from src.app.schemas.websocket_session import FileTransferStatus, SessionStatus

# Configure logging
logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for WebSocket session management.

    This service provides functionality for creating and managing WebSocket sessions,
    generating QR codes for session joining, and handling file transfers between clients.
    """

    def __init__(self):
        """Initialize WebSocketService."""
        # Valid image MIME types
        self._allowed_mime_types = {"image/jpeg", "image/jpg", "image/png"}

    def generate_session_qr(
        self, base_url: str, expiry_seconds: int = 300
    ) -> Tuple[str, str, str]:
        """Generate a QR code for joining a WebSocket session.

        Args:
            base_url: Base URL for the join endpoint
            expiry_seconds: Time in seconds before the session expires

        Returns:
            Tuple containing:
                - session_id: Unique session identifier
                - join_url: URL for joining the session
                - qr_code_base64: Base64-encoded QR code image
        """
        # Create a new session
        session_id = session_storage.create_session(expiry_seconds=expiry_seconds)

        # Generate the join URL
        join_url = f"{base_url}/session/join?id={session_id}"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(join_url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert QR code to base64-encoded string
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_code_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return session_id, join_url, qr_code_base64

    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get the status of a session.

        Args:
            session_id: Unique session identifier

        Returns:
            Optional[Dict]: Session status information or None if not found
        """
        session = session_storage.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session["session_id"],
            "status": session["status"],
            "connected_clients": session["connected_clients"],
            "created_at": session["created_at"],
            "expires_at": session["expires_at"],
            "error": session.get("error"),
        }

    def join_session(self, session_id: str) -> Tuple[bool, str, SessionStatus]:
        """Join a WebSocket session.

        Args:
            session_id: Unique session identifier

        Returns:
            Tuple containing:
                - success: True if joining was successful
                - message: Status or error message
                - status: Current session status
        """
        session = session_storage.get_session(session_id)
        if not session:
            return False, "Session not found", SessionStatus.CLOSED

        status = session["status"]
        if status == SessionStatus.EXPIRED:
            return False, "Session has expired", status

        # Check if session is active or created (can be joined)
        if status in [SessionStatus.ACTIVE, SessionStatus.CREATED]:
            return True, "Session joined successfully", status

        return False, f"Session is in an invalid state: {status}", status

    async def connect_websocket(self, session_id: str, websocket: WebSocket) -> bool:
        """Connect a WebSocket client to a session.

        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection

        Returns:
            bool: True if connection was successful
        """
        success = await session_storage.connect_client(session_id, websocket)
        if success:
            # Broadcast connection event to all clients in the session
            session = session_storage.get_session(session_id)
            if session:
                await self.broadcast_session_update(
                    session_id,
                    SessionStatus.ACTIVE,
                    session["connected_clients"],
                    "New client connected",
                )
        return success

    async def disconnect_websocket(self, session_id: str, websocket: WebSocket) -> bool:
        """Disconnect a WebSocket client from a session.

        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection

        Returns:
            bool: True if disconnection was successful
        """
        success = await session_storage.disconnect_client(session_id, websocket)
        if success:
            # Check if there are still clients connected
            session = session_storage.get_session(session_id)
            if session and session["connected_clients"] > 0:
                # Broadcast disconnection event
                await self.broadcast_session_update(
                    session_id,
                    SessionStatus.ACTIVE,
                    session["connected_clients"],
                    "Client disconnected",
                )
        return success

    async def broadcast_session_update(
        self,
        session_id: str,
        status: SessionStatus,
        connected_clients: int,
        message: Optional[str] = None,
    ) -> bool:
        """Broadcast session status update to all connected clients.

        Args:
            session_id: Unique session identifier
            status: Current session status
            connected_clients: Number of connected clients
            message: Optional message to include

        Returns:
            bool: True if broadcast was successful
        """
        update_message = {
            "type": "session_update",
            "session_id": session_id,
            "status": status.value,
            "connected_clients": connected_clients,
        }

        if message:
            update_message["message"] = message

        return await session_storage.broadcast_message(session_id, update_message)

    async def broadcast_file_uploaded(self, session_id: str, file_info: Dict) -> bool:
        """Broadcast file upload notification to all connected clients.

        Args:
            session_id: Unique session identifier
            file_info: Information about the uploaded file (should not contain content)

        Returns:
            bool: True if broadcast was successful
        """
        # Create a copy of the file_info to ensure we don't modify the original
        broadcast_file_info = file_info.copy()

        # Make sure content is not included in the broadcast
        if "content" in broadcast_file_info:
            del broadcast_file_info["content"]

        upload_message = {
            "type": "file_uploaded",
            "session_id": session_id,
            "file_info": broadcast_file_info,
        }

        return await session_storage.broadcast_message(session_id, upload_message)

    async def handle_file_upload(
        self, session_id: str, file: UploadFile, meal_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Handle file upload to a session.

        Args:
            session_id: Unique session identifier
            file: Uploaded file
            meal_type: Optional meal type (breakfast, lunch, dinner)

        Returns:
            Tuple containing:
                - success: True if upload was successful
                - file_id: File identifier if successful, None otherwise
                - file_info: File information if successful, None otherwise
        """
        # Check if session exists
        session = session_storage.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found for file upload")
            return False, None, None

        # Check if session is active
        if session["status"] != SessionStatus.ACTIVE:
            logger.error(
                f"Session {session_id} is not active, current status: {session['status']}"
            )
            return False, None, None

        # Check file content type
        content_type = file.content_type or ""
        if content_type.lower() not in self._allowed_mime_types:
            logger.error(
                f"Unsupported file type: {content_type} for session {session_id}"
            )
            return False, None, None

        try:
            # Read file content
            content = await file.read()
            file_size = len(content)

            # Generate file ID
            file_id = str(uuid.uuid4())

            # Encode content to base64
            content_b64 = base64.b64encode(content).decode("utf-8")

            # Create file info
            file_info = {
                "file_id": file_id,
                "filename": file.filename,
                "size": file_size,
                "content_type": content_type,
                "status": FileTransferStatus.COMPLETED.value,
                "uploaded_at": datetime.now().isoformat(),  # Use string for JSON compatibility
                "content": content_b64,  # Store file content as base64
                "meal_type": meal_type,
            }

            # Ensure the content field is preserved in the original file_info
            original_file_info = file_info.copy()

            # Add file to session
            result_file_id = session_storage.add_file(
                session_id, file_id, original_file_info
            )
            if not result_file_id:
                logger.error(f"Failed to add file {file_id} to session {session_id}")
                return False, None, None

            # Create a separate copy of file_info without the content for broadcasting
            broadcast_info = {k: v for k, v in file_info.items() if k != "content"}

            # Broadcast file upload notification
            await self.broadcast_file_uploaded(session_id, broadcast_info)

            # Verify file was properly stored
            stored_file = session_storage.get_file(session_id, file_id)
            if not stored_file:
                logger.error(
                    f"File {file_id} not found in session {session_id} after adding"
                )
                return False, None, None

            return True, file_id, file_info

        except Exception as e:
            logger.error(
                f"Error handling file upload for session {session_id}: {str(e)}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, None, None

    def get_file(self, session_id: str, file_id: str) -> Optional[Dict]:
        """Get file information and content.

        Args:
            session_id: Unique session identifier
            file_id: Unique file identifier

        Returns:
            Optional[Dict]: File information including content, or None if not found
        """
        # Get the session directly to access the file
        session = session_storage.get_session(session_id)
        if not session:
            logger.error(
                f"Session {session_id} not found when requesting file {file_id}"
            )
            return None

        # Check if the session has files
        if "files" not in session or not session["files"]:
            logger.error(f"Session {session_id} has no files dictionary or it's empty")
            return None

        # Check if the file exists in the session
        if file_id not in session["files"]:
            logger.error(f"File {file_id} not found in session {session_id}")
            return None

        # Access the file directly from the session and create a deep copy
        file_info = session["files"][file_id].copy()

        # Check if content field exists
        if "content" not in file_info:
            logger.error(f"File {file_id} found but has no content field")

            # Try to get the content directly from the session
            if "content" in session["files"][file_id]:
                file_info["content"] = session["files"][file_id]["content"]
            else:
                logger.error("Content not found in original file either")
                return None

        return file_info

    def list_files(self, session_id: str) -> List[Dict]:
        """List all files in a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List[Dict]: List of file information dictionaries (without content)
        """
        files = session_storage.get_files(session_id)

        # Remove content from file info
        for file_info in files:
            file_info.pop("content", None)

        return files

    def close_session(self, session_id: str) -> bool:
        """Close a session.

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if successful, False if session not found
        """
        # Get session to check connected clients count before closing
        session = session_storage.get_session(session_id)
        if not session:
            logger.warning(f"Cannot close session {session_id}: not found")
            return False

        # Update the session status
        success = session_storage.update_session_status(
            session_id, SessionStatus.CLOSED
        )

        if success and session["connected_clients"] > 0:
            # Use asyncio to run the async broadcast function
            loop = asyncio.get_event_loop()
            try:
                loop.create_task(
                    self.broadcast_session_update(
                        session_id,
                        SessionStatus.CLOSED,
                        session["connected_clients"],
                        "Session closed by host",
                    )
                )
            except Exception as e:
                logger.error(
                    f"Error scheduling broadcast for session closure: {str(e)}"
                )

        return success

    def extend_session(self, session_id: str, additional_seconds: int) -> bool:
        """Extend the expiry time of a session.

        Args:
            session_id: Unique session identifier
            additional_seconds: Additional time in seconds

        Returns:
            bool: True if successful, False if session not found
        """
        return session_storage.extend_session(session_id, additional_seconds)


# Create a singleton instance
websocket_service = WebSocketService()
