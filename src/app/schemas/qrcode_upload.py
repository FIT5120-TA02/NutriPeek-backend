from pydantic import BaseModel


class GenerateUploadQRResponse(BaseModel):
    upload_url: str
    qrcode_base64: str


class UploadImageResponse(BaseModel):
    message: str


class DetectionResultResponse(BaseModel):
    label: str
    confidence: float
