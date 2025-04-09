import threading
import time
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class FileStatus(Enum):
    """Enum for tracking the status of uploaded files."""

    AWAITING_UPLOAD = "awaiting_upload"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    EXPIRED = "expired"


class TempStorage:
    """Thread-safe temporary storage for uploaded files.

    This class provides temporary in-memory storage for uploaded files with status tracking,
    automatic expiration, and thread safety.
    """

    def __init__(self, max_file_size_mb: int = 10):
        """Initialize TempStorage.

        Args:
            max_file_size_mb: Maximum allowed file size in megabytes
        """
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes

    def create_entry(self, shortcode: str, expiry_seconds: int = 300) -> None:
        """Create a new shortcode entry.

        Args:
            shortcode: Unique identifier for the file
            expiry_seconds: Time in seconds before entry expires
        """
        with self._lock:
            self._storage[shortcode] = {
                "timestamp": time.time(),
                "expiry": time.time() + expiry_seconds,
                "file": None,
                "status": FileStatus.AWAITING_UPLOAD,
                "error": None,
            }

    def save_file(self, shortcode: str, file_data: bytes) -> Tuple[bool, Optional[str]]:
        """Save file data to the corresponding shortcode.

        Args:
            shortcode: Unique identifier for the file
            file_data: Binary content of the file

        Returns:
            Tuple of (success, error_message)
        """
        with self._lock:
            if shortcode not in self._storage:
                return False, "Shortcode not found"

            if self._storage[shortcode]["status"] == FileStatus.EXPIRED:
                return False, "Shortcode has expired"

            if len(file_data) > self.max_file_size:
                self._storage[shortcode]["status"] = FileStatus.FAILED
                self._storage[shortcode]["error"] = "File exceeds maximum allowed size"
                return False, "File exceeds maximum allowed size"

            # All checks passed, save the file
            self._storage[shortcode]["file"] = file_data
            self._storage[shortcode]["status"] = FileStatus.UPLOADED
            return True, None

    def get_file(self, shortcode: str) -> Optional[bytes]:
        """Get file data for the given shortcode.

        Args:
            shortcode: Unique identifier for the file

        Returns:
            File data as bytes or None if not found
        """
        with self._lock:
            if not self.exists(shortcode):
                return None

            entry = self._storage[shortcode]
            # Check if entry has expired
            if time.time() > entry["expiry"]:
                entry["status"] = FileStatus.EXPIRED
                return None

            return entry.get("file")

    def update_status(
        self, shortcode: str, status: FileStatus, error: Optional[str] = None
    ) -> bool:
        """Update the status of a file.

        Args:
            shortcode: Unique identifier for the file
            status: New status to set
            error: Optional error message

        Returns:
            True if successful, False if shortcode not found
        """
        with self._lock:
            if not self.exists(shortcode):
                return False

            self._storage[shortcode]["status"] = status
            if error:
                self._storage[shortcode]["error"] = error
            return True

    def get_status(self, shortcode: str) -> Tuple[Optional[FileStatus], Optional[str]]:
        """Get the current status of a file.

        Args:
            shortcode: Unique identifier for the file

        Returns:
            Tuple of (status, error_message) or (None, None) if not found
        """
        with self._lock:
            if not self.exists(shortcode):
                return None, None

            entry = self._storage[shortcode]
            # Check if entry has expired
            if time.time() > entry["expiry"]:
                entry["status"] = FileStatus.EXPIRED

            return entry["status"], entry.get("error")

    def delete_entry(self, shortcode: str) -> bool:
        """Delete shortcode record.

        Args:
            shortcode: Unique identifier to delete

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if shortcode in self._storage:
                del self._storage[shortcode]
                return True
            return False

    def exists(self, shortcode: str) -> bool:
        """Check if shortcode exists.

        Args:
            shortcode: Unique identifier to check

        Returns:
            True if exists, False otherwise
        """
        with self._lock:
            return shortcode in self._storage

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        count = 0

        with self._lock:
            expired = [
                code for code, data in self._storage.items() if now > data["expiry"]
            ]

            for code in expired:
                del self._storage[code]
                count += 1

        return count


# Create a global singleton instance
temp_storage = TempStorage()
