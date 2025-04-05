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

    # todo: the QR code refreshes dynamically, so we need to get it every time
    async def get_qr_code(self):

        print("Getting QR code")
        if not self.browser_context:
            await self.initialize_browser()

        print("Navigating to Trafikverket booking page")   
        page = await self.browser_context.get_current_page()
        
        # Navigate to Trafikverket booking page
        await page.goto("https://fp.trafikverket.se/Boka/#/")
        
        
        # Click login button
        await page.wait_for_selector("text=Logga in", timeout=15000)
        await page.click("text=Logga in")
        
        # Click continue button
        await page.wait_for_selector("text=Fortsätt", timeout=15000)
        await page.click("text=Fortsätt")
        
        # Wait for QR code
        await page.wait_for_selector(".qrcode", timeout=20000)
        
        # Capture QR code
        qr_element = await page.query_selector(".qrcode")
        if qr_element:
            qr_bytes = await qr_element.screenshot()
            self.current_qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
            
            # Check for successful login
            try:
                await page.wait_for_selector("#desktop-logout-button", timeout=30000)
                self.auth_complete = True
            except:
                self.auth_complete = False

        return {
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