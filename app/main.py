from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import chat, browser
from app.services.chatbot import DriverLicenseExamBot
from app.services.browser_service import BrowserService
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Trafikverket Booking Assistant",
    description="API for driver's license test booking automation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chatbot = DriverLicenseExamBot(api_key=os.getenv("OPENAI_API_KEY"))
browser_service = BrowserService()

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(browser.router, prefix="/api/browser", tags=["browser"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An error occurred: {str(exc)}"}
    )

@app.get("/")
async def root():
    return {"message": "Trafikverket Booking Assistant API"} 