"""Unit tests for QRCodeService."""

import base64
import uuid
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from src.app.core.temp_storage import FileStatus
from src.app.services.qrcode_service import QRCodeService


@pytest.fixture
def service():
    """Create a QRCodeService instance for testing."""
    # Initialize with a short cleanup interval for testing
    service = QRCodeService(cleanup_interval=1)
    yield service
    # Make sure to stop the cleanup thread after tests
    service.stop_cleanup_thread()


@pytest.fixture
def mock_temp_storage():
    """Mock the temp_storage to avoid side effects."""
    with patch("src.app.services.qrcode_service.temp_storage") as mock:
        yield mock


def test_init(service):
    """Test initialization of the service."""
    assert service._cleanup_interval == 1
    assert service._cleanup_thread is not None
    assert service._stop_cleanup is not None
    assert "image/jpeg" in service._allowed_mime_types
    assert "image/png" in service._allowed_mime_types
    assert "jpeg" in service._file_signatures
    assert "png" in service._file_signatures


def test_start_cleanup_thread(service):
    """Test starting the cleanup thread."""
    # Stop the existing thread from the fixture
    service.stop_cleanup_thread()
    # Create a mock thread
    with patch("threading.Thread") as mock_thread:
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        # Start the thread
        service._start_cleanup_thread()
        # Verify the thread was started with the right parameters
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()


def test_stop_cleanup_thread(service):
    """Test stopping the cleanup thread."""
    # Mock the thread
    mock_thread = Mock()
    service._cleanup_thread = mock_thread
    # Stop the thread
    service.stop_cleanup_thread()
    # Verify it was stopped
    assert service._stop_cleanup.is_set()
    mock_thread.join.assert_called_once_with(timeout=5)


def test_generate_upload_qr_success(service, mock_temp_storage):
    """Test successful QR code generation."""
    # Mock uuid to get a consistent shortcode
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
    ):
        shortcode, upload_url, qrcode_base64 = service.generate_upload_qr(
            "https://example.com", expiry_seconds=60
        )
        # Verify the shortcode is as expected
        assert shortcode == "12345678"
        # Verify the URL is constructed correctly
        assert upload_url == "https://example.com/upload/12345678"
        # Verify the base64 string is non-empty and valid base64
        assert qrcode_base64
        # Try to decode as base64 - should not raise
        base64.b64decode(qrcode_base64)
        # Verify temp storage was used
        mock_temp_storage.create_entry.assert_called_once_with(
            "12345678", expiry_seconds=60
        )


def test_validate_image_too_small(service):
    """Test image validation with a file that's too small."""
    # Create a very small "file"
    file_data = b"abc"
    # Validate - should fail
    is_valid, error = service.validate_image(file_data)
    assert not is_valid
    assert "too small" in error


def test_validate_image_invalid_format(service):
    """Test image validation with an invalid format."""
    # Create a file without valid image signatures
    file_data = b"abcdefghijklmnopqrstuvwxyz" * 10
    # Validate - should fail
    is_valid, error = service.validate_image(file_data)
    assert not is_valid
    assert "Unsupported file format" in error


def test_validate_image_jpeg_success(service):
    """Test image validation with a valid JPEG."""
    # Create a minimal valid JPEG
    with BytesIO() as buf:
        Image.new("RGB", (10, 10)).save(buf, format="JPEG")
        file_data = buf.getvalue()
    # Validate - should succeed
    is_valid, error = service.validate_image(file_data)
    assert is_valid
    assert error is None


def test_validate_image_png_success(service):
    """Test image validation with a valid PNG."""
    # Create a minimal valid PNG
    with BytesIO() as buf:
        Image.new("RGB", (10, 10)).save(buf, format="PNG")
        file_data = buf.getvalue()
    # Validate - should succeed
    is_valid, error = service.validate_image(file_data)
    assert is_valid
    assert error is None


def test_validate_image_corrupted(service):
    """Test image validation with corrupted image data."""
    # Create a corrupted image (valid signature but invalid content)
    file_data = b"\xff\xd8\xff" + b"corrupt" * 20
    # Validate - should fail
    is_valid, error = service.validate_image(file_data)
    assert not is_valid
    assert "Invalid image" in error


@patch("src.app.services.qrcode_service.QRCodeService.validate_image")
def test_save_uploaded_file_invalid_image(mock_validate, service, mock_temp_storage):
    """Test saving an invalid image."""
    # Set up mock to indicate an invalid image
    mock_validate.return_value = (False, "Invalid image")
    # Try to save the file
    success, error = service.save_uploaded_file("shortcode", b"data")
    # Should fail validation
    assert not success
    assert error == "Invalid image"
    # Should update status
    mock_temp_storage.update_status.assert_called_once_with(
        "shortcode", FileStatus.FAILED, "Invalid image"
    )
    # Should not attempt to save
    mock_temp_storage.save_file.assert_not_called()


@patch("src.app.services.qrcode_service.QRCodeService.validate_image")
def test_save_uploaded_file_save_failure(mock_validate, service, mock_temp_storage):
    """Test failure to save a valid image."""
    # Set up mocks
    mock_validate.return_value = (True, None)
    mock_temp_storage.save_file.return_value = (False, "Storage error")
    # Try to save the file
    success, error = service.save_uploaded_file("shortcode", b"data")
    # Should pass validation but fail saving
    assert not success
    assert error == "Storage error"
    # Should not update status
    mock_temp_storage.update_status.assert_not_called()


@patch("src.app.services.qrcode_service.QRCodeService.validate_image")
def test_save_uploaded_file_success(mock_validate, service, mock_temp_storage):
    """Test successfully saving a valid image."""
    # Set up mocks
    mock_validate.return_value = (True, None)
    mock_temp_storage.save_file.return_value = (True, None)
    # Try to save the file
    success, error = service.save_uploaded_file("shortcode", b"data")
    # Should succeed
    assert success
    assert error is None
    # Should save the file
    mock_temp_storage.save_file.assert_called_once_with("shortcode", b"data")


def test_get_file_status(service, mock_temp_storage):
    """Test getting file status."""
    # Set up mock
    mock_temp_storage.get_status.return_value = (FileStatus.UPLOADED, None)
    # Get status
    status, error = service.get_file_status("shortcode")
    # Should return the status from temp_storage
    assert status == FileStatus.UPLOADED
    assert error is None
    mock_temp_storage.get_status.assert_called_once_with("shortcode")


def test_mark_as_processing(service, mock_temp_storage):
    """Test marking a file as processing."""
    # Set up mock
    mock_temp_storage.update_status.return_value = True
    # Mark as processing
    result = service.mark_as_processing("shortcode")
    # Should update status
    assert result is True
    mock_temp_storage.update_status.assert_called_once_with(
        "shortcode", FileStatus.PROCESSING
    )


def test_mark_as_processed(service, mock_temp_storage):
    """Test marking a file as processed."""
    # Set up mock
    mock_temp_storage.update_status.return_value = True
    # Mark as processed
    result = service.mark_as_processed("shortcode")
    # Should update status
    assert result is True
    mock_temp_storage.update_status.assert_called_once_with(
        "shortcode", FileStatus.PROCESSED
    )


def test_mark_as_failed(service, mock_temp_storage):
    """Test marking a file as failed."""
    # Set up mock
    mock_temp_storage.update_status.return_value = True
    # Mark as failed
    result = service.mark_as_failed("shortcode", "Error message")
    # Should update status
    assert result is True
    mock_temp_storage.update_status.assert_called_once_with(
        "shortcode", FileStatus.FAILED, "Error message"
    )
