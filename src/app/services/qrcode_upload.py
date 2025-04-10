import base64
import qrcode
import threading
import time
import uuid
from io import BytesIO
from src.app.core.temp_storage import temp_storage

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

def save_detection_result(shortcode: str, label: str, confidence: float):
    result = f"{label}|{confidence}"
    temp_storage.save_file(shortcode, result.encode('utf-8'))
    threading.Thread(target=auto_delete_shortcode, args=(shortcode,), daemon=True).start()
