import base64
import qrcode
import uuid
from io import BytesIO
from src.app.core.temp_storage import temp_storage

def generate_upload_qr(base_url: str):
    """Generate short link QR code"""
    shortcode = str(uuid.uuid4())[:8]  # Get the first 8 characters as shortcode
    temp_storage.create_entry(shortcode)
    upload_url = f"{base_url}/upload/{shortcode}"
    qr = qrcode.make(upload_url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    qrcode_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return shortcode, upload_url, qrcode_base64

def save_uploaded_file(shortcode: str, file_data: bytes):
    """Save uploaded image data"""
    temp_storage.save_file(shortcode, file_data)

def detect_image(file_data: bytes):
    """Call your model for image recognition (using dummy data for now)"""
    label = "apple"
    confidence = 0.95
    return label, confidence