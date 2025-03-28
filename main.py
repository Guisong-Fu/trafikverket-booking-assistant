from langchain_openai import ChatOpenAI
from browser_use import Agent
from browser_use.browser.context import BrowserContext
from browser_use.browser.browser import Browser, BrowserConfig
import asyncio
import nest_asyncio

import base64
import time
import threading
import os
import multiprocessing

from flask import Flask, jsonify, request, send_file, render_template
from playwright.async_api import async_playwright

from dotenv import load_dotenv
load_dotenv()

# Enable nested event loops
nest_asyncio.apply()

# -------------------------------------------------------------------
# GLOBALS to hold current QR code data + authentication status
# -------------------------------------------------------------------
current_qr_base64 = None   # Will hold the latest screenshot of the QR code area
auth_complete = False      # Will be True once user is authenticated in BankID
browser_thread = None      # To track our browser automation thread

app = Flask(__name__)

# Ensure the template directory is correctly set
template_dir = os.path.abspath(os.path.dirname(__file__))
app.template_folder = template_dir

@app.route("/")
def index():
    """Serve the main page"""
    return send_file('index.html')

@app.route("/qr")
def get_qr():
    """
    Returns the latest QR code image as a base64-encoded PNG.
    The front-end can poll this endpoint (or use SSE/WebSockets).
    """
    if current_qr_base64 is None:
        return jsonify({"success": False, "msg": "QR not ready"}), 404

    return jsonify({
        "success": True,
        "qr_image_base64": current_qr_base64,
        "auth_complete": auth_complete
    })

@app.route("/status")
def get_status():
    """
    Returns simple status about whether user is logged in or not.
    """
    return jsonify({
        "auth_complete": auth_complete
    })

async def automate_browser_async():
    """
    This is the main automation logic that runs in the background
    """
    global current_qr_base64, auth_complete

    # Create browser config and browser
    browser_config = BrowserConfig()
    browser = Browser(config=browser_config)
    browser_context = BrowserContext(browser=browser)
    page = await browser_context.get_current_page()

    # 1) Go to Trafikverket booking start page
    await page.goto("https://fp.trafikverket.se/Boka/#/")

    # 2) Click "Logga in" (Login)
    await page.wait_for_selector("text=Logga in", timeout=15000)
    await page.click("text=Logga in")

    # Wait for the "pop up" or overlay with BankID option
    await page.wait_for_selector("text=Fortsätt", timeout=15000)
    await page.click("text=Fortsätt")
    
    # At this point, the site typically displays the rotating BankID QR code.
    await page.wait_for_selector(".qrcode", timeout=20000)  # Wait for QR code container

    print("QR code element found, starting capture loop...")

    while True:
        if auth_complete:
            print("Authentication completed, starting browser-use agent...")
            # Create and run the agent with the same browser context
            agent = Agent(
                task="""
                1. Click book test
                2. choose B96 type of exam
                3. choose practical driving test
                4. choose Uppsala as test location
                5. If there is a slot available in April, print the date and time of the slot
                """,
                llm=ChatOpenAI(model="gpt-4o-mini"),
                browser_context=browser_context
            )
            await agent.run()
            break

        try:
            qr_element = await page.query_selector(".qrcode")
            if qr_element:
                # Capture the QR code canvas
                qr_bytes = await qr_element.screenshot()
                current_qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
                # Check for successful login by looking for elements that appear after auth
                
                try:
                    await page.wait_for_selector("#desktop-logout-button", timeout=30000)
                    auth_complete = True
                    print("Authentication detected!")
                except:
                    print("Logout button never appeared – not authenticated yet?")
            else:
                current_qr_base64 = None
                print("QR element not found - page may have changed")
        except Exception as e:
            print(f"Error capturing QR: {e}")
            current_qr_base64 = None

        await asyncio.sleep(2)  # Capture every 2 seconds

    # Keep the browser session alive
    print("Browser session remains active")
    
    # Keep the browser open
    while True:
        await asyncio.sleep(5)

def run_browser_async():
    """Run the browser automation in an async context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(automate_browser_async())
    finally:
        loop.close()

def main():
    """
    Main entry point: start the browser automation in background,
    then run our Flask server so front-end can retrieve QR data.
    """
    global browser_thread
    
    # Run browser automation in a separate thread
    browser_thread = threading.Thread(target=run_browser_async, daemon=True)
    browser_thread.start()

    # Start Flask server WITHOUT debug mode
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    # Required for multiprocessing on Windows
    multiprocessing.freeze_support()
    main()