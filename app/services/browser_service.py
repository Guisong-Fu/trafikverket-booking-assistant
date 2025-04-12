from browser_use import Agent
from browser_use.browser.context import BrowserContext
from browser_use.browser.browser import Browser, BrowserConfig
from langchain_openai import ChatOpenAI
import asyncio
import base64
import os
from app.models.data_models import ExamRequest

class BrowserService:
    def __init__(self):
        self.current_qr_base64 = None
        self.auth_complete = False
        self.browser_context = None
        self.browser_task = None
        self.llm = ChatOpenAI(model="gpt-4o-mini")

        self.qr_started = False

    async def initialize_browser(self):
        if not self.browser_context:
            browser_config = BrowserConfig()
            browser = Browser(config=browser_config)
            self.browser_context = BrowserContext(browser=browser)
            await self.browser_context.get_session()
            

    async def get_qr_code(self):
        """Get the current QR code, refreshing it if needed"""
        print("Getting QR code")
        # Initialize browser if not already initialized
        if not self.browser_context:
            await self.initialize_browser()
            
        try:
            page = await self.browser_context.get_current_page()
            current_url = page.url
            
            # If we're not on the booking page, navigate there first
            if not current_url.startswith("https://fp.trafikverket.se/Boka/"):
                print("Navigating to booking page")
                await page.goto("https://fp.trafikverket.se/Boka/#/", wait_until="networkidle")
            
            # Look for QR code
            try:
                qr_element = await page.query_selector(".qrcode")

                # if not qr_element:
                if not self.qr_started:
                    # Click login button if visible
                    login_button = await page.query_selector("text=Logga in")
                    if login_button:
                        await login_button.click()
                        print("Clicked login button")
                        await page.wait_for_load_state("networkidle")
                    
                    # Click continue button if visible
                    continue_button = await page.query_selector("text=Fortsätt")
                    if continue_button:
                        await continue_button.click()
                        print("Clicked Fortsätt button")
                        await page.wait_for_load_state("networkidle")
                    
                    # Wait for QR code with longer timeout
                    await page.wait_for_selector(".qrcode", timeout=20000)
                    qr_element = await page.query_selector(".qrcode")
                    self.qr_started = True
                
                # if qr_element:
                if self.qr_started:
                    # Get a fresh screenshot of the QR code
                    qr_bytes = await qr_element.screenshot()
                    # todo: maybe I should double check the QR code is the same?
                    self.current_qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
                    
            except Exception as e:
                print(f"Error in login flow: {e}")
                self.auth_complete = False
                
        except Exception as e:
            print(f"Error refreshing QR code: {e}")
            if "Target page, context or browser has been closed" in str(e):
                print("Browser context was closed, reinitializing...")
                self.browser_context = None
                await self.initialize_browser()
        
        return {
            "success": True,
            "qr_image_base64": self.current_qr_base64,
            "auth_complete": self.auth_complete
        }

    async def get_auth_status(self):
            
        page = await self.browser_context.get_current_page()
        # Check for successful login by looking for the logout button
        try:
            print("Checking for authentication...")
            # Use query_selector instead of wait_for_selector for immediate response
            button = await page.query_selector("#desktop-logout-button")
            
            if button:
                print("Logout button found")
                text = await button.text_content()
                if "Logga ut" in text:
                    print("Authentication successful!")
                    self.auth_complete = True
            else:
                print("Logout button not found - not authenticated")
        except Exception as e:
            print(f"Error checking authentication: {e}")

        return {
            "auth_complete": self.auth_complete,
            "message": "Authenticated" if self.auth_complete else "Not authenticated"
        }

    async def start_booking(self, exam_request: ExamRequest):
        if not self.auth_complete:
            raise Exception("User not authenticated")

        # todo: need to work more on the tasks. -> "new test" and "reschedule test" is different

        # Create and run the agent with the browser context
        # todo: this tasks sort of works, but it does not close the browser after finished
        agent = Agent(
            # task=f"""
            # 1. Click book test
            # 2. choose {exam_request['license_type']} type of exam
            # 3. choose {exam_request['test_type']}
            # 4. choose {', '.join(exam_request['location'])} as test location
            # 5. If there is a slot available in the preferred time, book it
            # """,
            task=f"""
            1. Click "Boka prov"
            2. Click "Logga ut"
            3. Then click "Ja, logga ut"
            4. close the browser
            """,
            llm=self.llm,
            browser_context=self.browser_context
        )
        
        result = await agent.run()
        return result

    # todo: not in use. probably can be removed?
    async def cleanup(self):
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None 