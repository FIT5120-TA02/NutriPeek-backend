"""WebSocket session storage module."""

import logging
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import WebSocket

from src.app.schemas.websocket_session import FileTransferStatus, SessionStatus

# Configure logging
logger = logging.getLogger(__name__)


class WebSocketSessionStorage:
    """Storage for WebSocket sessions.

    This class provides functionality to store and manage WebSocket sessions,
    including their connected clients and transferred files.
    """

    def __init__(self, cleanup_interval: int = 60):
        """Initialize WebSocketSessionStorage.

        Args:
            cleanup_interval: Interval in seconds for running cleanup tasks
        """
        # Session data storage
        self._sessions: Dict[str, Dict] = {}
        # Active WebSocket connections for each session
        self._connections: Dict[str, List[WebSocket]] = {}
        # Lock for thread-safe operations
        self._lock = threading.RLock()
        # Cleanup thread
        self._cleanup_interval = cleanup_interval
        self._stop_cleanup = threading.Event()
        self._cleanup_thread = None
        # Start cleanup thread
        self._start_cleanup_thread()

    def _start_cleanup_thread(self) -> None:
        """Start a thread that periodically cleans up expired sessions."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._stop_cleanup.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_task,
            daemon=True,
        )
        self._cleanup_thread.start()

    def _cleanup_task(self) -> None:
        """Background task to clean up expired sessions."""
        while not self._stop_cleanup.is_set():
            try:
                with self._lock:
                    current_time = datetime.now()
                    expired_sessions = [
                        session_id
                        for session_id, session in self._sessions.items()
                        if session["expires_at"] < current_time
                        and session["status"] != SessionStatus.EXPIRED
                    ]

                    # Mark sessions as expired
                    for session_id in expired_sessions:
                        self._sessions[session_id]["status"] = SessionStatus.EXPIRED

                        # Check if there are connected clients to notify
                        if (
                            session_id in self._connections
                            and self._connections[session_id]
                        ):
                            # Broadcast the expired status to connected clients
                            # We need to use a background task for this since we're in a sync context
                            try:
                                # Create a message to broadcast
                                update_message = {
                                    "type": "session_update",
                                    "session_id": session_id,
                                    "status": SessionStatus.EXPIRED,
                                    "connected_clients": len(
                                        self._connections[session_id]
                                    ),
                                    "message": "Session has expired",
                                }

                                # Schedule the background broadcast task
                                # We can't use asyncio.create_task directly in this sync method
                                import asyncio

                                asyncio.run_coroutine_threadsafe(
                                    self.broadcast_message(session_id, update_message),
                                    asyncio.get_event_loop(),
                                )
                            except Exception as e:
                                logger.error(
                                    f"Failed to schedule broadcast for expired session {session_id}: {str(e)}"
                                )

                    # Remove very old sessions (expired for more than 24 hours)
                    old_time = current_time - timedelta(hours=24)
                    old_sessions = [
                        session_id
                        for session_id, session in self._sessions.items()
                        if session["expires_at"] < old_time
                    ]

                    for session_id in old_sessions:
                        if session_id in self._sessions:
                            del self._sessions[session_id]
                            if session_id in self._connections:
                                del self._connections[session_id]
            except Exception as e:
                logger.error(f"Error during session cleanup: {str(e)}")

            # Wait for next cleanup interval or until stopped
            self._stop_cleanup.wait(self._cleanup_interval)

    def stop_cleanup_thread(self) -> None:
        """Stop the cleanup thread gracefully."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)

    def create_session(self, expiry_seconds: int = 300) -> str:
        """Create a new WebSocket session.

        Args:
            expiry_seconds: Time in seconds before the session expires

        Returns:
            str: Unique session identifier
        """
        with self._lock:
            session_id = str(uuid.uuid4())
            created_at = datetime.now()
            expires_at = created_at + timedelta(seconds=expiry_seconds)

            self._sessions[session_id] = {
                "session_id": session_id,
                "status": SessionStatus.CREATED,
                "created_at": created_at,
                "expires_at": expires_at,
                "files": {},
                "connected_clients": 0,
            }

            self._connections[session_id] = []
            return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID.

        Args:
            session_id: Unique session identifier

        Returns:
            Optional[Dict]: Session data or None if not found
        """
        with self._lock:
            return self._sessions.get(session_id)

    def update_session_status(
        self, session_id: str, status: SessionStatus, error: Optional[str] = None
    ) -> bool:
        """Update the status of a session.

        Args:
            session_id: Unique session identifier
            status: New session status
            error: Optional error message

        Returns:
            bool: True if successful, False if session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                return False

            self._sessions[session_id]["status"] = status
            if error:
                self._sessions[session_id]["error"] = error
            return True

    def extend_session(self, session_id: str, additional_seconds: int) -> bool:
        """Extend the expiry time of a session.

        Args:
            session_id: Unique session identifier
            additional_seconds: Additional time in seconds

        Returns:
            bool: True if successful, False if session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                return False

            current_expires_at = self._sessions[session_id]["expires_at"]
            new_expires_at = current_expires_at + timedelta(seconds=additional_seconds)
            self._sessions[session_id]["expires_at"] = new_expires_at
            return True

    async def connect_client(self, session_id: str, websocket: WebSocket) -> bool:
        """Connect a client to a session.

        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection

        Returns:
            bool: True if successful, False if session not found or expired
        """
        with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]
            # Check if session is expired
            if session["status"] == SessionStatus.EXPIRED:
                return False

            # Accept the WebSocket connection
            await websocket.accept()

            # Add to connections
            self._connections[session_id].append(websocket)

            # Update session status and client count
            session["status"] = SessionStatus.ACTIVE
            session["connected_clients"] = len(self._connections[session_id])

            return True

    async def disconnect_client(self, session_id: str, websocket: WebSocket) -> bool:
        """Disconnect a client from a session.

        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection

        Returns:
            bool: True if successful, False if session or connection not found
        """
        with self._lock:
            if session_id not in self._sessions or session_id not in self._connections:
                return False

            if websocket in self._connections[session_id]:
                self._connections[session_id].remove(websocket)

                # Update client count
                self._sessions[session_id]["connected_clients"] = len(
                    self._connections[session_id]
                )

                return True
            return False

    async def broadcast_message(self, session_id: str, message: Dict) -> bool:
        """Broadcast a message to all clients connected to a session.

        Args:
            session_id: Unique session identifier
            message: Message to broadcast

        Returns:
            bool: True if successful, False if session not found
        """
        with self._lock:
            if session_id not in self._connections:
                return False

            # Get all active connections for this session
            connections = self._connections[session_id]

            if not connections:
                logger.warning(f"No active connections for session {session_id}")
                return True

            # List of exceptions during broadcast
            exceptions = []

            for websocket in connections[
                :
            ]:  # Create a copy to safely modify during iteration
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    exceptions.append(e)
                    # Remove failed connection
                    try:
                        self._connections[session_id].remove(websocket)
                    except ValueError:
                        pass  # Connection already removed

            if exceptions:
                logger.warning(
                    f"Errors during broadcast to session {session_id}: {len(exceptions)} failures"
                )

            # Update connected clients count
            self._sessions[session_id]["connected_clients"] = len(
                self._connections[session_id]
            )

            return True

    def add_file(self, session_id: str, file_id: str, file_info: Dict) -> Optional[str]:
        """Add a file to a session.

        Args:
            session_id: Unique session identifier
            file_id: Unique file identifier or None to generate one
            file_info: File information

        Returns:
            Optional[str]: File ID if successful, None if session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                logger.error(
                    f"Session {session_id} not found when adding file {file_id}"
                )
                return None

            if not file_id:
                file_id = str(uuid.uuid4())

            # Ensure the files dictionary exists
            if "files" not in self._sessions[session_id]:
                self._sessions[session_id]["files"] = {}

            # Ensure content field exists
            if "content" not in file_info:
                logger.error(f"File {file_id} has no content field")
                return None

            # Create a separate deep copy for storing to prevent reference issues
            file_copy = {k: v for k, v in file_info.items()}

            # Make sure content is explicitly copied
            if "content" in file_info:
                content_value = file_info["content"]
                file_copy["content"] = content_value

            # Add file to session
            self._sessions[session_id]["files"][file_id] = file_copy

            # Verify the file was added correctly
            if file_id in self._sessions[session_id]["files"]:
                has_content = "content" in self._sessions[session_id]["files"][file_id]

                if not has_content:
                    logger.error(
                        f"File {file_id} lost content after storing in session {session_id}"
                    )
                    return None

                return file_id
            else:
                logger.error(f"Failed to add file {file_id} to session {session_id}")
                return None

    def get_file(self, session_id: str, file_id: str) -> Optional[Dict]:
        """Get file info from a session.

        Args:
            session_id: Unique session identifier
            file_id: Unique file identifier

        Returns:
            Optional[Dict]: File info or None if not found
        """
        with self._lock:
            if session_id not in self._sessions:
                logger.error(
                    f"Session {session_id} not found when retrieving file {file_id}"
                )
                return None

            if "files" not in self._sessions[session_id]:
                logger.error(f"Session {session_id} has no files dictionary")
                return None

            if file_id not in self._sessions[session_id]["files"]:
                logger.error(f"File {file_id} not found in session {session_id}")
                return None

            # Get the file directly from the session and make a deep copy to avoid reference issues
            file_info = self._sessions[session_id]["files"][file_id].copy()

            # Verify content exists in the original
            original_has_content = (
                "content" in self._sessions[session_id]["files"][file_id]
            )

            # Verify content exists in the copy
            if "content" not in file_info:
                logger.error(f"File {file_id} has no content field")
                # Check if content exists in the original but was lost in copying
                if original_has_content:
                    logger.error("Content exists in original but was lost in copying")
                    # Directly copy the content field to ensure it's preserved
                    file_info["content"] = self._sessions[session_id]["files"][file_id][
                        "content"
                    ]
                else:
                    logger.error("Content missing in both original and copy")

            return file_info

    def update_file_status(
        self,
        session_id: str,
        file_id: str,
        status: FileTransferStatus,
        error: Optional[str] = None,
    ) -> bool:
        """Update the status of a file.

        Args:
            session_id: Unique session identifier
            file_id: Unique file identifier
            status: New file status
            error: Optional error message

        Returns:
            bool: True if successful, False if session or file not found
        """
        with self._lock:
            if (
                session_id not in self._sessions
                or "files" not in self._sessions[session_id]
                or file_id not in self._sessions[session_id]["files"]
            ):
                return False

            self._sessions[session_id]["files"][file_id]["status"] = status
            if error:
                self._sessions[session_id]["files"][file_id]["error"] = error
            return True

    def get_files(self, session_id: str) -> List[Dict]:
        """Get all files in a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List[Dict]: List of file info dictionaries (without content to reduce payload size)
        """
        with self._lock:
            if (
                session_id not in self._sessions
                or "files" not in self._sessions[session_id]
            ):
                return []

            # Create a deep copy of the files list to avoid modifying the originals
            files = []
            for file_id, file_info in self._sessions[session_id]["files"].items():
                file_copy = file_info.copy()
                # Remove content from the copy (not from the original) to reduce payload size
                if "content" in file_copy:
                    del file_copy["content"]
                files.append(file_copy)

            return files

    def delete_file(self, session_id: str, file_id: str) -> bool:
        """Delete a file from a session.

        Args:
            session_id: Unique session identifier
            file_id: Unique file identifier

        Returns:
            bool: True if successful, False if session or file not found
        """
        with self._lock:
            if (
                session_id not in self._sessions
                or "files" not in self._sessions[session_id]
                or file_id not in self._sessions[session_id]["files"]
            ):
                return False

            del self._sessions[session_id]["files"][file_id]
            return True

    def get_active_sessions_count(self) -> int:
        """Get the number of active sessions.

        Returns:
            int: Number of active sessions
        """
        with self._lock:
            return sum(
                1
                for session in self._sessions.values()
                if session["status"] == SessionStatus.ACTIVE
            )


# Create a singleton instance
session_storage = WebSocketSessionStorage()
