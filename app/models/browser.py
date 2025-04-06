from pydantic import BaseModel
from typing import Optional

class QRResponse(BaseModel):
    success: bool
    qr_image_base64: Optional[str] = None
    auth_complete: bool = False
    message: Optional[str] = None

class AuthStatus(BaseModel):
    auth_complete: bool
    message: Optional[str] = None

class BookingRequest(BaseModel):
    exam_request: dict  # This will be the ExamRequest from chat.py
    auth_token: Optional[str] = None 