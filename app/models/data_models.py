from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# todo: double check those models

# Chat messages
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    message: str
    chat_history: List[ChatMessage]
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None

class ConfirmationRequest(BaseModel):
    confirmed: bool
    chat_history: List[ChatMessage]

class ExamRequest(BaseModel):
    license_type: str
    test_type: str
    transmission_type: str
    location: List[str]
    time_preference: List[Dict[str, Any]]

# Browser models
class QRResponse(BaseModel):
    success: bool
    qr_image_base64: Optional[str] = None
    auth_complete: bool = False
    message: Optional[str] = None

class AuthStatus(BaseModel):
    auth_complete: bool
    message: Optional[str] = None