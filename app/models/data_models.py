from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any



# todo: how are thoese models used?
class ExamRequest(BaseModel):
    license_type: str = Field(None, description="Type of license (e.g., A, A1, B, BE)")
    test_type: str = Field(
        None, description="Type of test (practical driving test or theory test)"
    )
    # todo: add support for language preference
    transmission_type: Optional[str] = Field(
        default=None,
        description="Transmission type (manual or automatic)",
        examples=["manual", "automatic"]
    )
    location: List[str] = Field(
        default_factory=list, description="Preferred test locations (up to 4)"
    )

    # todo: double think about this. Do we need priority here?
    time_preference: List[str] = Field(
        default_factory=list, description="Time preferences"
    )

    # time_preference: List[Dict[str, Any]] = Field(
    #     default_factory=lambda: [{"preference": "as early as possible"}], 
    #     description="Time preferences with priorities"
    # )


# todo: double check those models. Are they really needed?

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

    exam_request: Optional[ExamRequest] = None

class ConfirmationRequest(BaseModel):
    confirmed: bool
    chat_history: List[ChatMessage]




# Browser models
class QRResponse(BaseModel):
    success: bool
    qr_image_base64: Optional[str] = None
    auth_complete: bool = False
    message: Optional[str] = None

class AuthStatus(BaseModel):
    auth_complete: bool
    message: Optional[str] = None