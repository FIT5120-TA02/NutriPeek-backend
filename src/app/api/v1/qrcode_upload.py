from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from src.app.services import qrcode_upload
from src.app.schemas.qrcode_upload import GenerateUploadQRResponse, UploadImageResponse, DetectionResultResponse

router = APIRouter()


@router.post("/generate_upload_qr", response_model=GenerateUploadQRResponse)
def generate_upload_qr(request: Request):
    base_url = "https://nutripeek.pro"
    shortcode, _, qrcode_base64 = qrcode_upload.generate_upload_qr(base_url)
    upload_page_url = f"{base_url}/upload/{shortcode}"
    return GenerateUploadQRResponse(upload_url=upload_page_url, qrcode_base64=qrcode_base64)


@router.post("/upload/{shortcode}", response_model=UploadImageResponse)
async def upload_image(shortcode: str, file: UploadFile = File(...)):
    content = await file.read()
    qrcode_upload.save_uploaded_file(shortcode, content)
    return UploadImageResponse(message="Upload successful")


@router.get("/result/{shortcode}", response_model=DetectionResultResponse)
def get_result(shortcode: str):
    file_data = qrcode_upload.temp_storage.get_file(shortcode)
    if not file_data:
        raise HTTPException(status_code=404, detail="Shortcode not found or expired")

    label, confidence = qrcode_upload.detect_image(file_data)
    qrcode_upload.temp_storage.delete_entry(shortcode)  # One-time use, delete after use
    return DetectionResultResponse(label=label, confidence=confidence)
