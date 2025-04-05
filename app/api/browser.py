from fastapi import APIRouter, HTTPException
from app.models.browser import QRResponse, AuthStatus, BookingRequest
from app.services.browser_service import BrowserService
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
browser_service = BrowserService()

@router.get("/qr", response_model=QRResponse)
async def get_qr_code():
    try:
        qr_data = await browser_service.get_qr_code()
        return QRResponse(
            success=True,
            qr_image_base64=qr_data["qr_image_base64"],
            auth_complete=qr_data["auth_complete"]
        )
    except Exception as e:
        return QRResponse(
            success=False,
            message=str(e)
        )

@router.get("/status", response_model=AuthStatus)
async def get_auth_status():
    try:
        status = await browser_service.get_auth_status()
        return AuthStatus(
            auth_complete=status["auth_complete"],
            message=status.get("message")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/book", response_model=dict)
async def start_booking(request: BookingRequest):
    try:
        # Start the booking process
        result = await browser_service.start_booking(request.exam_request)
        return {
            "success": True,
            "message": "Booking process started",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 