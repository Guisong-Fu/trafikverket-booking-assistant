from pydantic import BaseModel, Field
from typing import List, Optional


class ExamRequest(BaseModel):
    """Model for driving license exam booking request."""
    
    license_type: str = Field(None, description="Type of license (e.g., A, A1, B, BE)")
    test_type: str = Field(
        None, description="Type of test (practical driving test or theory test)"
    )
    theory_test_language: Optional[str] = Field(
        default=None,
        description="Language preference for the theory test",
        examples=["Swedish", "English"]
    )
    transmission_type: Optional[str] = Field(
        default=None,
        description="Transmission type (manual or automatic)",
        examples=["manual", "automatic"]
    )
    location: List[str] = Field(
        default_factory=list, 
        description="Preferred test locations (up to 4)"
    )
    time_preference: List[str] = Field(
        default_factory=list, 
        description="Time preferences"
    )

class ChatMessage(BaseModel):
    """Model for chat messages."""
    
    role: str
    content: str


class ChatRequest(BaseModel):
    """Model for chat request."""
    
    message: str
    chat_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    """Model for chat response."""
    
    message: str
    chat_history: List[ChatMessage]
    requires_confirmation: bool = False
    exam_request: Optional[ExamRequest] = None


class ConfirmationRequest(BaseModel):
    """Model for confirmation request."""
    
    confirmed: bool
    chat_history: List[ChatMessage]


class QRResponse(BaseModel):
    """Model for QR code response."""
    
    success: bool
    qr_image_base64: Optional[str] = None
    auth_complete: bool = False
    message: Optional[str] = None


class AuthStatus(BaseModel):
    """Model for authentication status."""
    
    auth_complete: bool
    message: Optional[str] = None