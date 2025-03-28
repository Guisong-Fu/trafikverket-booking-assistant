import base64
import time
import threading
import os

from flask import Flask, jsonify, request, send_file, render_template
from playwright.sync_api import sync_playwright

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

def automate_browser():
    """
    This is the main automation logic that runs in the background:
    1) Launch browser + navigate to booking site
    2) Initiate BankID login
    3) Continuously capture QR code screenshot
    4) Detect success and mark auth_complete
    """
    global current_qr_base64, auth_complete

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1) Go to Trafikverket booking start page
        page.goto("https://fp.trafikverket.se/Boka/#/")

        # NOTE: You will likely need to wait for or accept cookies, or click through,
        # depending on the actual site DOM. Example:
        # page.click("button#accept-cookies")  # example placeholder

        # 2) Click "Logga in" (Login) – adapt selector to the site
        #    The actual site might have a different ID, text, or role.
        page.wait_for_selector("text=Logga in", timeout=15000)
        page.click("text=Logga in")

        # Wait for the "pop up" or overlay with BankID option
        page.wait_for_selector("text=Fortsätt", timeout=15000)
        page.click("text=Fortsätt")
        
        # At this point, the site typically displays the rotating BankID QR code.
        page.wait_for_selector(".qrcode", timeout=20000)  # Wait for QR code container

        print("QR code element found, starting capture loop...")

        while True:
            if auth_complete:
                print("Authentication completed, keeping session alive...")
                # Keep the browser session alive but exit the QR capture loop
                break

            try:
                qr_element = page.query_selector(".qrcode")
                if qr_element:
                    # Capture the QR code canvas
                    qr_bytes = qr_element.screenshot()
                    current_qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
                    
                    # Check for successful login by looking for elements that appear after auth
                    if page.is_visible("text=Logga ut") or "authenticated" in page.url.lower():
                        auth_complete = True
                        print("Authentication detected!")
                        continue
                else:
                    current_qr_base64 = None
                    print("QR element not found - page may have changed")
            except Exception as e:
                print(f"Error capturing QR: {e}")
                current_qr_base64 = None

            time.sleep(2)  # Capture every 2 seconds

        # After authentication, keep the session alive
        print("Maintaining authenticated session...")
        while True:
            try:
                # Periodically check if we're still logged in
                if not page.is_visible("text=Logga ut"):
                    print("Session appears to be logged out")
                    auth_complete = False
                    break
                time.sleep(5)
            except Exception as e:
                print(f"Error checking session: {e}")
                break

        # Don't close the browser - keep session alive
        print("Browser session remains active")


def main():
    """
    Main entry point: start the browser automation in background,
    then run our Flask server so front-end can retrieve QR data.
    """
    global browser_thread
    
    # Run browser automation in a separate thread
    browser_thread = threading.Thread(target=automate_browser, daemon=True)
    browser_thread.start()

    # Start Flask server WITHOUT debug mode
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()