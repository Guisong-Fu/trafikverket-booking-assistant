from fastapi import APIRouter, HTTPException
from app.models.data_models import ChatRequest, ChatResponse, ConfirmationRequest, ExamRequest
from app.services.chatbot import DriverLicenseExamBot
import os
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()
chatbot = DriverLicenseExamBot(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/message", response_model=ChatResponse)
async def process_message(request: ChatRequest):
    try:
        logger.info(f"Processing message: {request.message}")
        logger.info(f"Current chat history: {request.chat_history}")
        
        response = chatbot.chat(request.message)
        logger.info(f"Chatbot response: {response}")
        
        # Convert chat history to the required format
        chat_history = []
        for msg in chatbot.memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                chat_history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                chat_history.append({"role": "assistant", "content": msg.content})
        logger.info(f"Updated chat history: {chat_history}")
        
        # Check if we need confirmation
        requires_confirmation = "Is this information correct?" in response
        
        return ChatResponse(
            message=response,
            chat_history=chat_history,
            requires_confirmation=requires_confirmation,
            confirmation_message=response if requires_confirmation else None
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

@router.post("/confirm", response_model=ChatResponse)
async def confirm_booking(request: ConfirmationRequest):
    try:
        logger.info(f"Processing confirmation: {request.confirmed}")
        logger.info(f"Current chat history: {request.chat_history}")
        
        if request.confirmed:
            # Get the collected information
            exam_info = chatbot.get_collected_info()
            logger.info(f"Collected exam info: {exam_info}")
            
            # Reset the chatbot for the next conversation
            chatbot.collected_info = ExamRequest()
            chatbot.memory.clear()
            
            return ChatResponse(
                message="Great! I'll start the booking process. Please scan the QR code to authenticate.",
                chat_history=request.chat_history,
                requires_confirmation=False
            )
        else:
            # Reset and continue the conversation
            chatbot.collected_info = ExamRequest()
            return ChatResponse(
                message="I apologize for the misunderstanding. Could you please provide more details?",
                chat_history=request.chat_history,
                requires_confirmation=False
            )
    except Exception as e:
        logger.error(f"Error processing confirmation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing confirmation: {str(e)}"
        ) 