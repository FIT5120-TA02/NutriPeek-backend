"""Unit tests for QR Code Upload API endpoints."""

from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from PIL import Image

from src.app.api.v1.qrcode import get_result
from src.app.core.temp_storage import FileStatus


class TestQRCodeAPI:
    """Test cases for QR Code API endpoints."""

    @pytest.fixture
    def mock_qrcode_service(self):
        """Mock the QR code service."""
        with patch("src.app.api.v1.qrcode.qrcode_service") as mock:
            yield mock

    @pytest.fixture
    def mock_temp_storage(self):
        """Mock the temp storage."""
        with patch("src.app.api.v1.qrcode.temp_storage") as mock:
            yield mock

    @pytest.fixture
    def mock_food_detection_service(self):
        """Mock the food detection service."""
        with patch("src.app.api.v1.qrcode.food_detection_service") as mock:
            # Make process_image an AsyncMock
            mock.process_image = AsyncMock()
            yield mock

    @pytest.mark.asyncio
    async def test_generate_upload_qr_success(
        self, client: AsyncClient, mock_qrcode_service
    ):
        """Test successful QR code generation."""
        # Set up the mock
        mock_qrcode_service.generate_upload_qr.return_value = (
            "abc123",
            "https://example.com/upload/abc123",
            "base64encodedqrcode",
        )

        # Make the request
        response = await client.post("/api/v1/qrcode/generate")

        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["upload_url"] == "https://example.com/upload/abc123"
        assert data["qrcode_base64"] == "base64encodedqrcode"
        assert data["expires_in_seconds"] == 300  # Default value

        # Verify the service was called with the right parameters
        mock_qrcode_service.generate_upload_qr.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_upload_qr_with_custom_expiry(
        self, client: AsyncClient, mock_qrcode_service
    ):
        """Test QR code generation with custom expiry time."""
        # Set up the mock
        mock_qrcode_service.generate_upload_qr.return_value = (
            "abc123",
            "https://example.com/upload/abc123",
            "base64encodedqrcode",
        )

        # Make the request with custom expiry
        response = await client.post(
            "/api/v1/qrcode/generate", data={"expiry_seconds": 600}
        )

        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["expires_in_seconds"] == 600

        # Verify the service was called with the right parameters
        mock_qrcode_service.generate_upload_qr.assert_called_once()
        args, kwargs = mock_qrcode_service.generate_upload_qr.call_args
        assert kwargs["expiry_seconds"] == 600

    @pytest.mark.asyncio
    async def test_generate_upload_qr_service_error(
        self, client: AsyncClient, mock_qrcode_service
    ):
        """Test QR code generation with service error."""
        # Set up the mock to raise an exception
        mock_qrcode_service.generate_upload_qr.side_effect = Exception("Service error")

        # Make the request
        response = await client.post("/api/v1/qrcode/generate")

        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_image_shortcode_not_found(
        self, client: AsyncClient, mock_temp_storage
    ):
        """Test uploading to a non-existent shortcode."""
        # Set up the mock
        mock_temp_storage.exists.return_value = False

        # Create a test image
        img_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(img_bytes, format="PNG")

        # Make the request
        response = await client.post(
            "/api/v1/qrcode/upload/nonexistent",
            files={"file": ("test.png", img_bytes.getvalue(), "image/png")},
        )

        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert (
            "not found" in data["detail"].lower() or "expired" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_upload_image_already_uploaded(
        self, client: AsyncClient, mock_temp_storage, mock_qrcode_service
    ):
        """Test uploading to a shortcode that already has a file."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.UPLOADED, None)

        # Create a test image
        img_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(img_bytes, format="PNG")

        # Make the request
        response = await client.post(
            "/api/v1/qrcode/upload/abc123",
            files={"file": ("test.png", img_bytes.getvalue(), "image/png")},
        )

        # Check the response
        assert response.status_code == 409
        data = response.json()
        assert "already uploaded" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_image_expired(
        self, client: AsyncClient, mock_temp_storage, mock_qrcode_service
    ):
        """Test uploading to an expired shortcode."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.EXPIRED, None)

        # Create a test image
        img_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(img_bytes, format="PNG")

        # Make the request
        response = await client.post(
            "/api/v1/qrcode/upload/abc123",
            files={"file": ("test.png", img_bytes.getvalue(), "image/png")},
        )

        # Check the response
        assert response.status_code == 410
        data = response.json()
        assert "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_image_success(
        self, client: AsyncClient, mock_temp_storage, mock_qrcode_service
    ):
        """Test successful image upload."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.AWAITING_UPLOAD, None)
        mock_qrcode_service.save_uploaded_file.return_value = (True, None)

        # Create a test image
        img_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(img_bytes, format="PNG")

        # Make the request
        response = await client.post(
            "/api/v1/qrcode/upload/abc123",
            files={"file": ("test.png", img_bytes.getvalue(), "image/png")},
        )

        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Upload successful"
        assert data["shortcode"] == "abc123"

        # Verify the service was called
        mock_qrcode_service.save_uploaded_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_image_validation_error(
        self, client: AsyncClient, mock_temp_storage, mock_qrcode_service
    ):
        """Test image upload with validation error."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.AWAITING_UPLOAD, None)

        # Mock the save_uploaded_file method to return validation error
        mock_qrcode_service.save_uploaded_file.return_value = (
            False,
            "Invalid image format",
        )

        # Create a test image
        img_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(img_bytes, format="PNG")
        img_bytes.seek(0)  # Reset the pointer to the beginning of the file

        # Make the request
        response = await client.post(
            "/api/v1/qrcode/upload/abc123",
            files={"file": ("test.png", img_bytes.getvalue(), "image/png")},
        )

        # Check the response
        assert response.status_code == 400
        data = response.json()
        assert "invalid image format" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_image_server_error(
        self, client: AsyncClient, mock_temp_storage, mock_qrcode_service
    ):
        """Test image upload with server error."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.AWAITING_UPLOAD, None)
        mock_qrcode_service.save_uploaded_file.side_effect = Exception("Server error")

        # Create a test image
        img_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(img_bytes, format="PNG")

        # Make the request
        response = await client.post(
            "/api/v1/qrcode/upload/abc123",
            files={"file": ("test.png", img_bytes.getvalue(), "image/png")},
        )

        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "failed to process upload" in data["detail"].lower()

        # Verify error was marked
        mock_qrcode_service.mark_as_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_status_not_found(
        self, client: AsyncClient, mock_qrcode_service
    ):
        """Test getting status for non-existent shortcode."""
        # Set up the mock
        mock_qrcode_service.get_file_status.return_value = (None, None)

        # Make the request
        response = await client.get("/api/v1/qrcode/status/nonexistent")

        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_file_status_success(
        self, client: AsyncClient, mock_qrcode_service
    ):
        """Test getting status successfully."""
        # Set up the mock
        mock_qrcode_service.get_file_status.return_value = (FileStatus.UPLOADED, None)

        # Make the request
        response = await client.get("/api/v1/qrcode/status/abc123")

        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["shortcode"] == "abc123"
        assert data["status"] == "uploaded"
        assert data["error"] is None

    @pytest.mark.asyncio
    async def test_get_file_status_with_error(
        self, client: AsyncClient, mock_qrcode_service
    ):
        """Test getting status with an error."""
        # Set up the mock
        mock_qrcode_service.get_file_status.return_value = (
            FileStatus.FAILED,
            "Processing failed",
        )

        # Make the request
        response = await client.get("/api/v1/qrcode/status/abc123")

        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["shortcode"] == "abc123"
        assert data["status"] == "failed"
        assert data["error"] == "Processing failed"

    @pytest.mark.asyncio
    async def test_get_result_shortcode_not_found(
        self, client: AsyncClient, mock_temp_storage
    ):
        """Test getting result for non-existent shortcode."""
        # Set up the mock
        mock_temp_storage.exists.return_value = False

        # Make the request
        response = await client.get("/api/v1/qrcode/result/nonexistent")

        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert (
            "not found" in data["detail"].lower() or "expired" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_get_result_awaiting_upload(
        self, client: AsyncClient, mock_temp_storage
    ):
        """Test getting result for a shortcode that's awaiting upload."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.AWAITING_UPLOAD, None)

        # Make the request
        response = await client.get("/api/v1/qrcode/result/abc123")

        # Check the response
        assert response.status_code == 400
        data = response.json()
        assert "no file has been uploaded" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_result_expired(self, client: AsyncClient, mock_temp_storage):
        """Test getting result for an expired shortcode."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.EXPIRED, None)

        # Make the request
        response = await client.get("/api/v1/qrcode/result/abc123")

        # Check the response
        assert response.status_code == 410
        data = response.json()
        assert "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_result_failed(self, client: AsyncClient, mock_temp_storage):
        """Test getting result for a failed upload."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.FAILED, "Upload failed")

        # Make the request
        response = await client.get("/api/v1/qrcode/result/abc123")

        # Check the response
        assert response.status_code == 400
        data = response.json()
        assert "failed" in data["detail"].lower()
        assert "upload failed" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_result_processing(self, client: AsyncClient, mock_temp_storage):
        """Test getting result for a shortcode that's being processed."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.PROCESSING, None)

        # Make the request
        response = await client.get("/api/v1/qrcode/result/abc123")

        # Check the response
        assert response.status_code == 409
        data = response.json()
        assert "already being processed" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_result_already_processed(
        self, client: AsyncClient, mock_temp_storage
    ):
        """Test getting result for a shortcode that's already been processed."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.PROCESSED, None)

        # Make the request
        response = await client.get("/api/v1/qrcode/result/abc123")

        # Check the response
        assert response.status_code == 410
        data = response.json()
        assert "already been processed" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_result_file_not_found(
        self,
        client: AsyncClient,
        mock_temp_storage,
        mock_qrcode_service,
        mock_food_detection_service,
    ):
        """Test getting result when the file data is missing."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.UPLOADED, None)
        mock_temp_storage.get_file.return_value = None

        # Make the request through the client
        response = await client.get("/api/v1/qrcode/result/abc123")

        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "file data not found" in data["detail"].lower()

        # Verify error was marked
        mock_qrcode_service.mark_as_failed.assert_called_once_with(
            "abc123", "File data not found"
        )

    @pytest.mark.asyncio
    async def test_get_result_success(
        self,
        client: AsyncClient,
        mock_temp_storage,
        mock_qrcode_service,
        mock_food_detection_service,
    ):
        """Test getting result successfully."""
        # Set up the mocks
        mock_temp_storage.exists.return_value = True
        mock_temp_storage.get_status.return_value = (FileStatus.UPLOADED, None)
        mock_temp_storage.get_file.return_value = b"filedata"

        # Reset call counts
        mock_temp_storage.exists.reset_mock()
        mock_temp_storage.get_status.reset_mock()
        mock_temp_storage.get_file.reset_mock()
        mock_qrcode_service.mark_as_processing.reset_mock()
        mock_qrcode_service.mark_as_processed.reset_mock()
        mock_temp_storage.delete_entry.reset_mock()
        mock_food_detection_service.process_image.reset_mock()

        # Set up detection result with all required fields for the FoodItemDetection schema
        mock_food_detection_service.process_image.return_value = (
            [
                {
                    "class_name": "apple",
                    "confidence": 0.95,
                    "x_min": 50.0,
                    "y_min": 30.0,
                    "x_max": 180.0,
                    "y_max": 160.0,
                }
            ],
            100,  # processing time in ms
            640,  # width
            480,  # height
        )

        # Make the request through the client
        response = await client.get("/api/v1/qrcode/result/abc123")

        # Check the response
        assert (
            response.status_code == 200
        ), f"Expected 200 but got {response.status_code}, response: {response.text}"
        data = response.json()

        assert len(data["detected_items"]) == 1
        assert data["detected_items"][0]["class_name"] == "apple"
        assert data["detected_items"][0]["confidence"] == 0.95
        # Check the bounding box coordinates
        assert data["detected_items"][0]["x_min"] == 50.0
        assert data["detected_items"][0]["y_min"] == 30.0
        assert data["detected_items"][0]["x_max"] == 180.0
        assert data["detected_items"][0]["y_max"] == 160.0
        assert data["processing_time_ms"] == 100
        assert data["image_width"] == 640
        assert data["image_height"] == 480

        mock_qrcode_service.mark_as_processing.assert_called_once_with("abc123")
        mock_food_detection_service.process_image.assert_called_once_with(b"filedata")
        mock_qrcode_service.mark_as_processed.assert_called_once_with("abc123")
        # The temp storage entry should be deleted only once after processing
        mock_temp_storage.delete_entry.assert_called_once_with("abc123")
