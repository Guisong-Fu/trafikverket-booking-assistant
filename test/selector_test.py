from browser_use.browser.context import BrowserContext
from browser_use.browser.browser import Browser, BrowserConfig
import asyncio
import base64

async def test_auth_detection():
    """
    Test script to verify if the authentication detection logic works correctly.
    This script will:
    1. Open the browser and navigate to the Trafikverket booking page
    2. Click on login and continue to BankID
    3. Display the QR code
    4. Monitor for successful authentication
    """
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

    print("QR code element found, starting authentication detection...")

    # Test the authentication detection logic
    try:
        # Wait for the logout button to appear (indicates successful authentication)
        await page.wait_for_selector("#desktop-logout-button", timeout=30000)
        print("Authentication detected! The selector '#desktop-logout-button' was found.")
    except Exception as e:
        print(f"Authentication not detected: {e}")
        print("The selector '#desktop-logout-button' was not found within the timeout period.")
    
    # Keep the browser open for a while to allow manual inspection
    print("Browser will remain open for 30 seconds for inspection...")
    await asyncio.sleep(30)
    
    # Close the browser
    await browser.close()
    print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(test_auth_detection())