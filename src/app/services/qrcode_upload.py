import base64
import qrcode
import threading
import time
import uuid
import os
from io import BytesIO
from src.app.core.temp_storage import temp_storage

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.path.join(BASE_DIR, 'temp_files')
os.makedirs(TEMP_DIR, exist_ok=True)


def generate_upload_qr(base_url: str):
    shortcode = str(uuid.uuid4())[:8]
    temp_storage.create_entry(shortcode)
    upload_url = f"{base_url}/upload/{shortcode}"
    qr = qrcode.make(upload_url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    qr_code_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return shortcode, upload_url, qr_code_base64


def auto_delete_shortcode(shortcode: str, delay: int = 300):
    time.sleep(delay)
    if temp_storage.exists(shortcode):
        temp_storage.delete_entry(shortcode)


def save_uploaded_file(shortcode: str, file_data: bytes) -> None:
    temp_storage.save_file(shortcode, file_data)
    threading.Thread(target=auto_delete_shortcode, args=(shortcode,), daemon=True).start()


def save_detection_result(shortcode: str, label: str, confidence: float) -> None:
    """Save detection result after upload"""
    result = f"{label}|{confidence}"
    temp_storage.save_file(shortcode, result.encode('utf-8'))
