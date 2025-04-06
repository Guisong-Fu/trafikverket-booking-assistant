import streamlit as st
import requests
import base64
from PIL import Image
import io
import time
import json

# API configuration
API_BASE_URL = "http://localhost:8000"

# response = requests.get(f"{API_BASE_URL}/api/browser/qr")
# print(response.json())

response = requests.get(f"{API_BASE_URL}/api/browser/status")
print(response.json())