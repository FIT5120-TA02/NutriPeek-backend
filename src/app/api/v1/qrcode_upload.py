from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from src.app.services import qrcode_upload
from src.app.schemas.qrcode_upload import GenerateUploadQRResponse, UploadImageResponse, DetectionResultResponse
from src.app.services.food_detection import detect_image

router = APIRouter()


@router.post("/generate_upload_qr", response_model=GenerateUploadQRResponse)
def generate_upload_qr(request: Request):
    base_url = "https://nutripeek.pro"
    shortcode, _, qrcode_base64 = qrcode_upload.generate_upload_qr(base_url)
    return GenerateUploadQRResponse(upload_url=f"{base_url}/upload/{shortcode}", qrcode_base64=qrcode_base64)


@router.post("/upload/{shortcode}", response_model=UploadImageResponse)
async def upload_image(shortcode: str, file: UploadFile = File(...)):
    content = await file.read()
    label, confidence = detect_image(content)
    qrcode_upload.save_detection_result(shortcode, label, confidence)
    return UploadImageResponse(message="Upload successful")


@router.get("/result/{shortcode}", response_model=DetectionResultResponse)
def get_result(shortcode: str):
    result = qrcode_upload.temp_storage.get_file(shortcode)
    if not result:
        raise HTTPException(status_code=404, detail="Shortcode not found or expired")

    label, confidence = result.decode('utf-8').split("|")
    qrcode_upload.temp_storage.delete_entry(shortcode)
    return DetectionResultResponse(label=label, confidence=float(confidence))
