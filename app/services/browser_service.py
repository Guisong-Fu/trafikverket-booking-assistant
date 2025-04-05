from browser_use import Agent
from browser_use.browser.context import BrowserContext
from browser_use.browser.browser import Browser, BrowserConfig
from langchain_openai import ChatOpenAI
import asyncio
import base64
import os
from dotenv import load_dotenv

load_dotenv()

class BrowserService:
    def __init__(self):
        self.current_qr_base64 = None
        self.auth_complete = False
        self.browser_context = None
        self.browser_task = None
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    async def initialize_browser(self):
        if not self.browser_context:
            browser_config = BrowserConfig()
            browser = Browser(config=browser_config)
            self.browser_context = BrowserContext(browser=browser)
            await self.browser_context.get_session()
            # Initialize the QR code when browser is first created
            await self._refresh_qr_code()

    async def _refresh_qr_code(self):
        """Internal method to refresh the QR code without creating a new browser context"""
        print("Refreshing QR code")
        if not self.browser_context:
            await self.initialize_browser()
            return
        
        try:
            page = await self.browser_context.get_current_page()
            current_url = page.url
            
            # If we're not on the booking page, navigate there first
            if not current_url.startswith("https://fp.trafikverket.se/Boka/"):
                await page.goto("https://fp.trafikverket.se/Boka/#/", wait_until="networkidle")
            
            try:
                # Check if we're already authenticated by looking for the logout button
                logout_button = await page.wait_for_selector("[data-bs-toggle='dropdown']", timeout=1000)
                if logout_button:
                    button_text = await logout_button.text_content()
                    if "Logga ut" in button_text:
                        print("Found logout button - authenticated!")
                        self.auth_complete = True
                        return
            except Exception as e:
                print("Not authenticated, proceeding with login flow")
            
            # Look for QR code
            try:
                qr_element = await page.query_selector(".qrcode")
                if not qr_element:
                    # Click login button if visible
                    login_button = await page.query_selector("text=Logga in")
                    if login_button:
                        await login_button.click()
                        await page.wait_for_load_state("networkidle")
                    
                    # Click continue button if visible
                    continue_button = await page.query_selector("text=Fortsätt")
                    if continue_button:
                        await continue_button.click()
                        await page.wait_for_load_state("networkidle")
                    
                    # Wait for QR code with longer timeout
                    await page.wait_for_selector(".qrcode", timeout=20000)
                    qr_element = await page.query_selector(".qrcode")
                
                if qr_element:
                    # Get a fresh screenshot of the QR code
                    qr_bytes = await qr_element.screenshot()
                    self.current_qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
                    
                    # Check for successful login by waiting for the logout button
                    try:
                        print("Checking for authentication...")
                        await page.wait_for_selector("#desktop-logout-button", timeout=30000)
                        print("Found logout button")
                        button = await page.query_selector("#desktop-logout-button")
                        if button:
                            print("Button found")
                            text = await button.text_content()
                            if "Logga ut" in text:
                                print("Authentication successful!")
                                self.auth_complete = True
                            else:
                                self.auth_complete = False
                    except Exception as e:
                        print(f"Not authenticated yet: {e}")
                        self.auth_complete = False
            except Exception as e:
                print(f"Error in login flow: {e}")
                self.auth_complete = False
                
        except Exception as e:
            print(f"Error refreshing QR code: {e}")
            if "Target page, context or browser has been closed" in str(e):
                print("Browser context was closed, reinitializing...")
                self.browser_context = None
                await self.initialize_browser()

    async def get_qr_code(self):
        """Get the current QR code, refreshing it if needed"""
        # Always refresh the QR code to get the latest one
        await self._refresh_qr_code()
        
        return {
            "success": True,
            "qr_image_base64": self.current_qr_base64,
            "auth_complete": self.auth_complete
        }

    async def get_auth_status(self):
        return {
            "auth_complete": self.auth_complete,
            "message": "Authenticated" if self.auth_complete else "Not authenticated"
        }

    async def start_booking(self, exam_request):
        if not self.auth_complete:
            raise Exception("User not authenticated")

        # Create and run the agent with the browser context
        agent = Agent(
            # task=f"""
            # 1. Click book test
            # 2. choose {exam_request['license_type']} type of exam
            # 3. choose {exam_request['test_type']}
            # 4. choose {', '.join(exam_request['location'])} as test location
            # 5. If there is a slot available in the preferred time, book it
            # """,
            task=f"""
            Click book test
            """,
            llm=self.llm,
            browser_context=self.browser_context
        )
        
        result = await agent.run()
        return result

    async def cleanup(self):
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None 