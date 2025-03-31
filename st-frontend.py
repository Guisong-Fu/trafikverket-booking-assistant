import streamlit as st
from typing import List, Optional

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_input' not in st.session_state:
    st.session_state.current_input = ""
if 'confirmation_mode' not in st.session_state:
    st.session_state.confirmation_mode = False
if 'confirmation_message' not in st.session_state:
    st.session_state.confirmation_message = ""

# Sample hints - these would come from your backend later
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
        
        # Here you would normally process the input with your AI agent
        # For now, we'll just simulate the agent behavior
        st.session_state.confirmation_mode = True
        st.session_state.confirmation_message = f"Is my understanding correct, that you want to {st.session_state.current_input.lower()}?"
        
        # Clear the input
        st.session_state.current_input = ""

def handle_confirmation(confirmed: bool):
    if confirmed:
        st.session_state.chat_history.append({"role": "assistant", "content": "Great! I'll start processing your request."})
        # Here you would trigger your backend processes
    else:
        st.session_state.chat_history.append({"role": "assistant", "content": "I apologize for the misunderstanding. Could you please provide more details?"})
    
    st.session_state.confirmation_mode = False
    st.session_state.confirmation_message = ""

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
        st.text_area("You:", value=message["content"], height=50, disabled=True, key=f"msg_{id(message)}")
    else:
        st.text_area("Assistant:", value=message["content"], height=50, disabled=True, key=f"msg_{id(message)}")

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
