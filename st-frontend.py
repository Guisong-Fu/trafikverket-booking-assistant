import streamlit as st
import requests
import base64
from PIL import Image
import io
import time
import json
from app.models.data_models import ExamRequest
from typing import Union, Dict

# API configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_input' not in st.session_state:
    st.session_state.current_input = ""
if 'confirmation_mode' not in st.session_state:
    st.session_state.confirmation_mode = False
if 'exam_request' not in st.session_state:
    st.session_state.exam_request = None    
if 'show_qr' not in st.session_state:
    st.session_state.show_qr = False
if 'qr_showed' not in st.session_state:
    st.session_state.qr_showed = False    
if 'auth_complete' not in st.session_state:
    st.session_state.auth_complete = False
if 'qr_image_base64' not in st.session_state:
    st.session_state.qr_image_base64 = None
if 'last_auth_check' not in st.session_state:
    st.session_state.last_auth_check = 0

# Sample hints
HINTS = [
    "I want to book B driver license test in Uppsala, as earlier as possible",
    "I want to book B driver license test in Uppsala, every Tuesday morning would be good",
    "I want to book B driver license test in Stockholm, as earlier as possible"
]


def copy_hint_to_input(hint: str):
    st.session_state.current_input = hint

def handle_chat_submit():
    if st.session_state.current_input.strip():
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": st.session_state.current_input})
        
        # Send message to backend
        # todo: that chat_history is stored everywhere. Is it really needed?
        response = requests.post(
            f"{API_BASE_URL}/api/chat/message",
            json={
                "message": st.session_state.current_input,
                "chat_history": st.session_state.chat_history
            }
        )
        
        if response.status_code == 200:

            data = response.json()
            
            st.session_state.chat_history = data["chat_history"]
            st.session_state.confirmation_mode = data["requires_confirmation"]
            st.session_state.exam_request = data["exam_request"]
                    
        # Clear the input
        st.session_state.current_input = ""


# todo: also, here is the response is hardcoded.
def create_summary(exam_request: Union[Dict, ExamRequest]) -> str:
    """Create a human-readable summary of the collected information."""
    # Convert dictionary to ExamRequest if needed
    if isinstance(exam_request, dict):
        exam_request = ExamRequest(**exam_request)

    summary = "Here's a summary of your exam request:\n\n"
    
    # License Type
    if exam_request.license_type:
        summary += f"License Type: {exam_request.license_type}\n"
    else:
        summary += "License Type: Not specified\n"
        
    # Test Type
    if exam_request.test_type:
        summary += f"Test Type: {exam_request.test_type}\n"
    else:
        summary += "Test Type: Not specified\n"
        
    # Transmission Type
    if exam_request.transmission_type:
        summary += f"Transmission Type: {exam_request.transmission_type}\n"
    else:
        summary += "Transmission Type: Not specified\n"
        
    # Location
    if exam_request.location:
        locations_str = ", ".join(exam_request.location)
        summary += f"Location: {locations_str}\n"
    else:
        summary += "Location: Not specified\n"
        
    # Time Preference
    if exam_request.time_preference:
        time_prefs = []
        for pref in exam_request.time_preference:
            if isinstance(pref, dict) and "preference" in pref:
                time_prefs.append(pref["preference"])
            else:
                time_prefs.append(str(pref))
        summary += f"Time Preference: {', '.join(time_prefs)}\n"
    else:
        summary += "Time Preference: Not specified\n"
    
    return summary



# todo: confirm part is not working
def handle_confirmation(confirmed: bool):
    # Send confirmation to backend

    response = requests.post(
        f"{API_BASE_URL}/api/chat/confirm",
        json={
            "confirmed": confirmed,
            "chat_history": st.session_state.chat_history
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        st.session_state.chat_history = data["chat_history"]
        st.session_state.confirmation_mode = False
        
        if confirmed:
            st.session_state.show_qr = True




# UI Layout
st.title("Swedish Driving Test Booking Assistant")

# Hints section
st.subheader("Quick Hints")
hint_cols = st.columns(len(HINTS))
for idx, hint in enumerate(HINTS):
    with hint_cols[idx]:
        st.button(
            hint,
            key=f"hint_{idx}",
            help=hint,
            on_click=copy_hint_to_input,
            args=(hint,)
        )

# Chat history display
# todo: if `confirmation_mode` is true, then this message shall not be displayed in `chat`
st.subheader("Chat")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.text_area("You:", value=message["content"], height=70, disabled=True, key=f"msg_{id(message)}")
    else:
        st.text_area("Assistant:", value=message["content"], height=70, disabled=True, key=f"msg_{id(message)}")

# Input section
input_placeholder = "Type your booking request here..."
st.text_area("Your request:", key="current_input", value=st.session_state.current_input, height=100, placeholder=input_placeholder)
st.button("Send", on_click=handle_chat_submit)

# Confirmation section
if st.session_state.confirmation_mode:
    st.write("---")

    print("Exam Request", st.session_state.exam_request)

    st.write(create_summary(st.session_state.exam_request))

    col1, col2 = st.columns(2)
    with col1:
        st.button("Yes", on_click=handle_confirmation, args=(True,))
    with col2:
        st.button("No", on_click=handle_confirmation, args=(False,))


# QR Code section
#if st.session_state.show_qr:
if False:
    st.write("---")
    st.subheader("Authentication")
    
    # Create a placeholder for the QR code
    qr_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Function to update the QR code display
    def update_qr_display():
        response = requests.get(f"{API_BASE_URL}/api/browser/qr")
        print("QR Response", response.json())
        if response.status_code == 200:
            data = response.json()
            if data["success"] and data["qr_image_base64"]:
                # Update the QR code image
                qr_image = Image.open(io.BytesIO(base64.b64decode(data["qr_image_base64"])))
                qr_placeholder.image(qr_image, caption="Scan this QR code with your BankID app")
                
            else:
                status_placeholder.error("Failed to get QR code. Please try again.")
    
    def run_qr_code_flow():

        # todo: this is the start session
        if not st.session_state.qr_showed:
            update_qr_display()
            st.session_state.qr_showed = True

        response = requests.get(f"{API_BASE_URL}/api/browser/status")
        print("Auth Status Response", response.json())
        if response.status_code == 200:
            data = response.json()
            if not data["auth_complete"]:
                update_qr_display()
                print("Updating QR code display")
                
            else:
                status_placeholder.success("Authentication successful! Starting booking process...")
                st.session_state.show_qr = False
                st.session_state.qr_image_base64 = None
                st.session_state.auth_complete = True
    
    # run_qr_code_flow()
    while not st.session_state.get("auth_complete", False):
        run_qr_code_flow()
        time.sleep(1)
    
    
if st.session_state.auth_complete:

    # Handle both dictionary and ExamRequest objects
    exam_request_data = st.session_state.exam_request
    if not isinstance(exam_request_data, dict):
        exam_request_data = exam_request_data.model_dump()
        
    response = requests.post(f"{API_BASE_URL}/api/browser/book", json=exam_request_data)
    print("Book Response", response.json())
