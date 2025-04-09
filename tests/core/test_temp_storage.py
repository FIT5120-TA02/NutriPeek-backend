"""Unit tests for TempStorage."""

import threading
import time

import pytest

from src.app.core.temp_storage import FileStatus, TempStorage


@pytest.fixture
def storage():
    """Create a TempStorage instance for testing."""
    return TempStorage(max_file_size_mb=1)  # 1MB max file size for tests


def test_init(storage):
    """Test initialization of TempStorage."""
    assert storage._storage == {}
    assert storage._lock is not None
    assert storage.max_file_size == 1 * 1024 * 1024  # 1MB


def test_create_entry(storage):
    """Test creating a new entry."""
    storage.create_entry("test_code", expiry_seconds=60)

    # Verify entry was created
    assert "test_code" in storage._storage
    entry = storage._storage["test_code"]
    assert "timestamp" in entry
    assert "expiry" in entry
    assert entry["file"] is None
    assert entry["status"] == FileStatus.AWAITING_UPLOAD
    assert entry["error"] is None

    # Verify expiry time is set
    assert entry["expiry"] > time.time()
    assert entry["expiry"] <= time.time() + 60


def test_save_file_shortcode_not_found(storage):
    """Test saving a file for a non-existent shortcode."""
    success, error = storage.save_file("nonexistent", b"testdata")

    # Should fail
    assert not success
    assert "not found" in error


def test_save_file_expired(storage):
    """Test saving a file for an expired shortcode."""
    # Create an expired entry
    storage.create_entry("expired", expiry_seconds=60)
    storage._storage["expired"]["expiry"] = time.time() - 10  # 10 seconds in the past
    storage._storage["expired"]["status"] = FileStatus.EXPIRED

    # Try to save the file
    success, error = storage.save_file("expired", b"testdata")

    # Should fail
    assert not success
    assert "expired" in error


def test_save_file_too_large(storage):
    """Test saving a file that exceeds the max size."""
    # Create an entry
    storage.create_entry("test_code")

    # Create a file that's too large
    large_file = b"x" * (storage.max_file_size + 1)

    # Try to save the file
    success, error = storage.save_file("test_code", large_file)

    # Should fail
    assert not success
    assert "exceeds maximum allowed size" in error

    # Status should be marked as failed
    assert storage._storage["test_code"]["status"] == FileStatus.FAILED
    assert "exceeds maximum allowed size" in storage._storage["test_code"]["error"]


def test_save_file_success(storage):
    """Test successfully saving a file."""
    # Create an entry
    storage.create_entry("test_code")

    # Save a file
    success, error = storage.save_file("test_code", b"testdata")

    # Should succeed
    assert success
    assert error is None

    # File should be saved
    assert storage._storage["test_code"]["file"] == b"testdata"
    assert storage._storage["test_code"]["status"] == FileStatus.UPLOADED


def test_get_file_not_found(storage):
    """Test getting a file that doesn't exist."""
    # Get a non-existent file
    file_data = storage.get_file("nonexistent")

    # Should return None
    assert file_data is None


def test_get_file_expired(storage):
    """Test getting an expired file."""
    # Create an expired entry with a file
    storage.create_entry("expired")
    storage._storage["expired"]["file"] = b"testdata"
    storage._storage["expired"]["expiry"] = time.time() - 10  # 10 seconds in the past

    # Get the file
    file_data = storage.get_file("expired")

    # Should return None
    assert file_data is None

    # Status should be marked as expired
    assert storage._storage["expired"]["status"] == FileStatus.EXPIRED


def test_get_file_success(storage):
    """Test successfully getting a file."""
    # Create an entry with a file
    storage.create_entry("test_code")
    storage._storage["test_code"]["file"] = b"testdata"

    # Get the file
    file_data = storage.get_file("test_code")

    # Should return the file
    assert file_data == b"testdata"


def test_update_status_not_found(storage):
    """Test updating status for a non-existent shortcode."""
    # Update non-existent shortcode
    result = storage.update_status("nonexistent", FileStatus.PROCESSING)

    # Should fail
    assert not result


def test_update_status_success(storage):
    """Test successfully updating status."""
    # Create an entry
    storage.create_entry("test_code")

    # Update status
    result = storage.update_status(
        "test_code", FileStatus.PROCESSING, "Processing started"
    )

    # Should succeed
    assert result

    # Status should be updated
    assert storage._storage["test_code"]["status"] == FileStatus.PROCESSING
    assert storage._storage["test_code"]["error"] == "Processing started"


def test_get_status_not_found(storage):
    """Test getting status for a non-existent shortcode."""
    # Get status for non-existent shortcode
    status, error = storage.get_status("nonexistent")

    # Should return None, None
    assert status is None
    assert error is None


def test_get_status_expired(storage):
    """Test getting status for an expired shortcode."""
    # Create an expired entry
    storage.create_entry("expired")
    storage._storage["expired"]["expiry"] = time.time() - 10  # 10 seconds in the past

    # Get status
    status, error = storage.get_status("expired")

    # Should return expired status
    assert status == FileStatus.EXPIRED
    assert error is None

    # Entry should be marked as expired
    assert storage._storage["expired"]["status"] == FileStatus.EXPIRED


def test_get_status_success(storage):
    """Test successfully getting status."""
    # Create an entry with an error
    storage.create_entry("test_code")
    storage._storage["test_code"]["status"] = FileStatus.FAILED
    storage._storage["test_code"]["error"] = "Processing failed"

    # Get status
    status, error = storage.get_status("test_code")

    # Should return status and error
    assert status == FileStatus.FAILED
    assert error == "Processing failed"


def test_delete_entry_not_found(storage):
    """Test deleting a non-existent entry."""
    # Delete non-existent entry
    result = storage.delete_entry("nonexistent")

    # Should return False
    assert not result


def test_delete_entry_success(storage):
    """Test successfully deleting an entry."""
    # Create an entry
    storage.create_entry("test_code")

    # Delete the entry
    result = storage.delete_entry("test_code")

    # Should succeed
    assert result

    # Entry should be deleted
    assert "test_code" not in storage._storage


def test_exists(storage):
    """Test checking if an entry exists."""
    # Create an entry
    storage.create_entry("test_code")

    # Check existence
    assert storage.exists("test_code")
    assert not storage.exists("nonexistent")


def test_cleanup_expired(storage):
    """Test cleaning up expired entries."""
    # Create some entries, some expired
    storage.create_entry("active")

    storage.create_entry("expired1")
    storage._storage["expired1"]["expiry"] = time.time() - 10

    storage.create_entry("expired2")
    storage._storage["expired2"]["expiry"] = time.time() - 20

    # Run cleanup
    count = storage.cleanup_expired()

    # Should remove 2 entries
    assert count == 2

    # Only active entry should remain
    assert "active" in storage._storage
    assert "expired1" not in storage._storage
    assert "expired2" not in storage._storage


def test_thread_safety(storage):
    """Test thread safety of the storage."""
    # We'll use this to track any exceptions in the worker threads
    exceptions = []

    def worker():
        try:
            # Each thread creates its own entry and then tries to read/write others
            thread_id = threading.get_ident()
            key = f"thread_{thread_id}"

            # Create an entry
            storage.create_entry(key)

            # Write to our entry
            storage.save_file(key, f"data_{thread_id}".encode())

            # Try to read other entries
            for i in range(10):
                other_key = f"thread_{thread_id + i}"
                storage.get_file(other_key)

            # Update our status
            storage.update_status(key, FileStatus.PROCESSED)

            # Delete our entry
            storage.delete_entry(key)
        except Exception as e:
            exceptions.append(e)

    # Start a bunch of threads
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    # Wait for all threads to finish
    for t in threads:
        t.join()

    # Check for exceptions
    assert not exceptions, f"Worker threads had exceptions: {exceptions}"
