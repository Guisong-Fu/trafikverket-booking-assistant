import streamlit as st
import requests
import base64
from PIL import Image
import io
import time
import json

# API configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_input' not in st.session_state:
    st.session_state.current_input = ""
if 'confirmation_mode' not in st.session_state:
    st.session_state.confirmation_mode = False
if 'confirmation_message' not in st.session_state:
    st.session_state.confirmation_message = ""
if 'show_qr' not in st.session_state:
    st.session_state.show_qr = False
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
            st.session_state.confirmation_message = data["confirmation_message"]
            
            if st.session_state.confirmation_mode:
                st.session_state.show_qr = True
        
        # Clear the input
        st.session_state.current_input = ""

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
        st.session_state.confirmation_message = ""
        
        if confirmed:
            # Start polling for QR code
            st.session_state.show_qr = True

def check_auth_status():
    response = requests.get(f"{API_BASE_URL}/api/browser/status")
    if response.status_code == 200:
        data = response.json()
        st.session_state.auth_complete = data["auth_complete"]
        return data["auth_complete"]
    return False

# UI Layout
st.title("Swedish Driving Test Booking Assistant")

# Hints section
st.subheader("Quick Hints")
hint_cols = st.columns(len(HINTS))
for idx, hint in enumerate(HINTS):
    with hint_cols[idx]:
        st.button(
            f"Hint {idx + 1}",
            key=f"hint_{idx}",
            help=hint,
            on_click=copy_hint_to_input,
            args=(hint,)
        )

# Chat history display
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
    st.write(st.session_state.confirmation_message)
    col1, col2 = st.columns(2)
    with col1:
        st.button("Yes", on_click=handle_confirmation, args=(True,), type="primary")
    with col2:
        st.button("No", on_click=handle_confirmation, args=(False,))

# QR Code section
# if st.session_state.show_qr:
if True:
    st.write("---")
    st.subheader("Authentication")
    
    # Create a placeholder for the QR code
    qr_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Function to update the QR code display
    def update_qr_display():
        response = requests.get(f"{API_BASE_URL}/api/browser/qr")
        print("Response", response.json())
        if response.status_code == 200:
            data = response.json()
            if data["success"] and data["qr_image_base64"]:
                # Update the QR code image
                qr_image = Image.open(io.BytesIO(base64.b64decode(data["qr_image_base64"])))
                qr_placeholder.image(qr_image, caption="Scan this QR code with your BankID app")
                
                # Check authentication status
                if data["auth_complete"]:
                    status_placeholder.success("Authentication successful! Starting booking process...")
                    st.session_state.show_qr = False
                    st.session_state.qr_image_base64 = None
                    return True
                else:
                    status_placeholder.info("Waiting for authentication...")
                    return False
            else:
                status_placeholder.error("Failed to get QR code. Please try again.")
                return False
        return False
    
    # Initial QR code display
    if st.session_state.qr_image_base64 is None:
        update_qr_display()
    
    # Set up auto-refresh using Streamlit's auto-refresh feature
    if not st.session_state.get("auth_complete", False):
        # This will refresh the page every 2 seconds
        time.sleep(2)
        st.rerun()
