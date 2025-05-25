from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

from langchain_openai import ChatOpenAI
import asyncio
import base64
import os
from app.models.data_models import ExamRequest

class BrowserService:
    def __init__(self):
        self.current_qr_base64 = None
        self.auth_complete = False
        self.browser = None
        self.browser_context = None
        self.browser_task = None
        self.llm = ChatOpenAI(model="gpt-4.1-mini") # o4-mini, gpt-4.1-mini

        self.qr_started = False

    async def initialize_browser(self):

        if not self.browser_context:
            browser_config = BrowserConfig(
                # headless=True,
                # proxy <-> Standard Playwright proxy settings for using external proxy services. Might be useful for the furture
                # wss_url (default: None) WebSocket URL for connecting to external browser providers (e.g., anchorbrowser.io, steel.dev, browserbase.com, browserless.io, TestingBot). -> Maybe we can use this for production
                disable_security=True
            )
            self.browser = Browser(config=browser_config)

            config = BrowserContextConfig(
                allowed_domains=['fp.trafikverket.se'],
            )

            self.browser_context = BrowserContext(browser=self.browser, config=config)
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

        # Create and run the agent with the browser context


        agent = Agent(
            task = f"""
            ### Prompt for Swedish Driving-License Booking Agent

            **Objective:**  
            Automate booking driving-license exam on Trafikverket. 
            Navigate from login through to the slot list, fill in exactly what the user requested, then reserve the best matching slot and proceed to payment.

            **Global Instructions:**  
            - The site text is Swedish; user requests may be in any language. Interpret correctly.  
            - ALWAYS wait for each UI element to appear (buttons, dropdowns, modals) before interacting.  
            - After every selection or click, VERIFY the UI reflects the choice.  
            - Scroll only if the target element is not in view.  
            - On any irrecoverable error (e.g. town not found), abort and return an error message.

            ---

            ## Step 1: Log In & Navigate  
            1. **Go to** `https://fp.trafikverket.se/Boka/ng/licence`.  
            2. **(If not already)** log in via e-ID/BankID.  
            3. **After success**, WAIT for the dashboard with the "Boka prov" card.

            **Expected:** The "Boka prov" button is visible.

            ---

            ## Step 2: Click "Boka prov"  
            1. **Click** the "Boka prov" card/button.  
            2. WAIT until the URL begins with `https://fp.trafikverket.se/Boka/ng/search/`.

            **Expected:** You see a form with fields:  
            - "Vad vill du boka?"  
            - "Välj prov"  
            - "Var vill du göra provet?"  
            - "Välj bil att hyra…" (for driving) or "Välj språk" (for theory)

            ---

            ## Step 3: Select License Category  
            1. **In** the "Vad vill du boka?" dropdown, **select** the option exactly equal to `{exam_request.license_type}` (e.g. "B – Personbil").  
            2. WAIT for the dropdown to reflect your choice.

            **Expected:** Field reads `{exam_request.license_type}`.

            ---

            ## Step 4: Select Test Type  
            1. **Open** the "Välj prov" dropdown.  
            2. **Click** the item exactly matching `{exam_request.test_type}` ("Körprov" or "Teoriprov").  
            3. WAIT for the selection to stick.

            **Expected:** Field reads `{exam_request.test_type}`.

            ---

            ## Step 5: (Driving Only) Choose Car Transmission  
            **If** `{exam_request.test_type}` == "Körprov":  
            1. **Open** the "Välj bil att hyra från Trafikverket" dropdown.  
            2. **Select** `{exam_request.transmission_type}` ("Manuell bil" or "Automat").  
            3. WAIT for the field to update.  

            **Expected:** Field reads `{exam_request.transmission_type}`.

            ---

            ## Step 6: Pick Test Location(s)

            1. **Click** the "Var vill du göra provet?" field.  
            2. WAIT until the "Välj provort" modal appears and the "Sök ort" input is visible.

            3. **For each** town in `{exam_request.location}` **(in order)**:  
                a. **Type** the full town name into "Sök ort."  
                b. WAIT for the suggestion list to refresh.  
                c. **Click** the suggestion whose text exactly equals the town.  
                d. VERIFY:  
                    - That item's background turns dark red with a ✔️ icon.  
                    - The counter increments from "Välj provort (n/4)" to "Välj provort (n+1/4)."  
                e. **If** no exact suggestion appears within 5 s, ABORT with "Location `<town>` not found."

            4. **Click** the "Bekräfta" button.  
            5. WAIT for the modal to close.  
            6. VERIFY the main field now lists exactly `{', '.join(exam_request.location)}` (comma-separated).

            ---

            ## Step 7: Retrieve Available Slots & Reserve
            1. **Wait** for the "Lediga provtider" header or container to be visible on the page.  
            2. **Extract** the list of slots (date, time, and the associated "Välj" button element or selector).  
            3. **From** that list, pick the slot whose date/time best matches `{exam_request.time_preference}`.  
            4. **Click** the chosen slot's "Välj" button.
            5. Ignore "Gå vidare" button, we will go to the payment page later.
            
            ---

            ## Step 8: Navigate to Meny and proceed to payment
            1. Go to `https://fp.trafikverket.se/Boka/ng/reservation`
            2. **Click** "Logga ut" in the header.  
            3. WAIT for the confirmation dialog, then click "Ja, logga ut."  
            4. VERIFY you're back at the landing page.

            """,
            llm=self.llm,
            message_context="Please note the official site is in Swedish, but the request from user can be in English. You will need to do some translation work. No need to scroll the page",
            browser=self.browser,
            browser_context=self.browser_context
        )
        
        # <class 'browser_use.agent.views.AgentHistoryList'>
        result = await agent.run(max_steps=30)
        
        # Debug information available:
        # result.urls(), result.screenshots(), result.action_names()
        # result.extracted_content(), result.errors(), result.model_actions()

        await self.browser.close()
        return result


    async def iterator_test(self):
        if not self.auth_complete:
            raise Exception("User not authenticated")

        agent_go_to_booking = Agent(
            task="""
            Click "Meny", then in the dropdown, click "Boka prov"
            """,
            browser_context=self.browser_context,
            llm=self.llm,
        )

        agent_book_b = Agent(
            task="""
                Select "B – Personbil"
            """,
            browser_context=self.browser_context,
            llm=self.llm,
        )

        await agent_go_to_booking.run()
        await agent_book_b.run()

    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None 


    async def local_test_authenticate(self):
        page = await self.browser_context.get_current_page()
        await page.goto("https://fp.trafikverket.se/Boka/#/", wait_until="networkidle")
        login_button = await page.query_selector("text=Logga in")
        if login_button:
            await login_button.click()
            print("Clicked login button")
            await page.wait_for_load_state("networkidle")

        continue_button = await page.query_selector("text=Fortsätt")
        if continue_button:
            await continue_button.click()
            print("Clicked Fortsätt button")
            await page.wait_for_load_state("networkidle")            
        



# For local testing
# uv run -m app.services.browser_service
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    exam_request = ExamRequest(
        license_type="B",  
        test_type="practical driving",  
        location=["Uppsala"],  
        transmission_type="Manuell bil",  
        time_preference=["earliest available in June"]  
    )

    browser_service = BrowserService()

    async def main():
        await browser_service.initialize_browser()
        await browser_service.local_test_authenticate()
        
        while not (await browser_service.get_auth_status())["auth_complete"]:   
            print("Waiting for authentication to complete...")
            await asyncio.sleep(1)

        await browser_service.start_booking(exam_request)
        # await browser_service.iterator_test()
    asyncio.run(main())