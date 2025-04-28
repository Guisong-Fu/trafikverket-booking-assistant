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
        self.llm = ChatOpenAI(model="gpt-4o-mini")

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

            # todo: might not be needed, but I leave it here for now.
            config = BrowserContextConfig(
                # cookies_file="path/to/cookies.json",
                # wait_for_network_idle_page_load_time=3.0,
                # browser_window_size={'width': 1280, 'height': 1100},
                # locale='en-US',
                # user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                # highlight_elements=True,
                # viewport_expansion=500,
                allowed_domains=['fp.trafikverket.se'],
            )

            self.browser_context = BrowserContext(browser=self.browser, config=config)
            await self.browser_context.get_session()
            

    """
    Here is something:
    instead of choosing login, and show the QR, we can go to "meny" and choose "Boka prov" or "Mina prov" directly.
    And once the login session is completed, we can just navigate around
    https://fp.trafikverket.se/Boka/ng/licence
    https://fp.trafikverket.se/Boka/ng/examinations

    I can also use the "Boka prov" button to navigate to the booking page, and then I can use the "Mina prov" button to navigate to the examinations page.

    Or, maybe I can keep the Get QR function, and after authentication, and use Controller to go to `https://fp.trafikverket.se/Boka/ng/examinations` to check if there is already booking booked.
    However, some token will be saved though if we directly get the QR code to the examinations page.

    """



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


        planner_llm = ChatOpenAI(model='gpt-4.1-nano')

        # todo: need to work more on the tasks. -> "new test" and "reschedule test" is different

        # Create and run the agent with the browser context
        # todo: this tasks sort of works, but it does not close the browser after finished


        # todo: really, try with multiple agents, and with specific controller specified


        agent = Agent(                        
            # todo: refine this tasks
            # todo: maybe create several small agents instead of one big one?
            task=f"""
            ### Prompt for Swedish Driving License Booking Agent 

            **Objective:**
            Visit [Trafikverket](https://fp.trafikverket.se/Boka/ng/licence), click the desired license type, then in the actual booking page(url started with https://fp.trafikverket.se/Boka/ng/search/ ), fill in the information accordingly and see if there is any slot that meets user's requirment, if so, return the time information of that slot , if not, do nothing.

            **Important:**
            - The site is all in Swedish, but the request from user can be in whatever language they want. You need to be able to understand it. 
            - Wait for each element to load before interacting
            - Make sure all the information is correctly set, license type, exam location, type of rental car.
            - Scroll only if it's needed
            ---

            Here are the specific steps:

            ---

            ### Step 1: Navigate to the booking page
            - Go to [Trafikverket](https://fp.trafikverket.se/Boka/ng/licence)

            ####Expected Result 
            - all types of licenses are displayed

            ---

            ### Step 2: Choose the desired license type

            choose and click the specific {exam_request.license_type} type of exam, the exam type needs to match exactly {exam_request.test_type}


            ####Expected Result 
            - Once done, you should be nevigated to a page with URL started with `https://fp.trafikverket.se/Boka/ng/search/`. Make sure the selected option from `Vad vill du boka?` matches exactly {exam_request.test_type}, if not, click the section block and choose the right one.
            - The exact {exam_request.license_type} is chosen



            ---
            ### Step 3: Choose the desired test type(practical driving test or theory test)


            in "Välj prov", choose {exam_request.test_type} type of test
            The options can be Practical Driving test or Theory test. 


            ####Expected Result 
            - The exact {exam_request.test_type} is chosen

            ---
            ### Step 4: Fill in the diesred test location


            - click "Var vill du göra provet?", and it will pop out a inside window `Välj provort`, in `Filtrera på ort`, type in `Sok ort` with choose {', '.join(exam_request.location)}  one by one, if it's gets displayed, then click that location, once clicked, the background of that location will be turned into dark red, and "right arrow icon" will become "right icon", and `Välj provort (0/4)` will be `Välj provort (1/4)` or `Välj provort (2/4)` up to `Välj provort (4/4)`



            ####Expected Result 
            - all desired locations for test are correctly selected.
            - only the desired ones are chosen, nothing more

            ---
            ### Step 5: Confirm chosen location
            Click `bekräfta`, once done, that window shall be closed, and the locations dispayed in `Var vill du göra provet?` match exactly {', '.join(exam_request.location)}.
            If not matched, then repat Step 4.

            ####Expected Result 
            - locations dispayed in `Var vill du göra provet?` match exactly {', '.join(exam_request.location)}


            ---
            ### Step 6: Choose the desired rental car type(automatic or manual)
            in "Välj bil att hyra från Trafikverket.", choose {exam_request.transmission_type} 


            ####Expected Result 
            - The exact {exam_request.transmission_type} is chosen

            ---
            ### Step 7: Check and see if there is the time slot 

            Under `Lediga provtider`, ta list of available slots will be displaed
            - see if there is a slot that matches the preferred time mentioned in the {', '.join(exam_request.time_preference)}, if so, return that result


            ####Expected Result 
            - if there is such slot that matches the the time perference, then return that time information of that slot
            - if no, then return not found

            ---
            ### Step 8: log out
            - click "Logga ut"
            - Then click "Ja, logga ut"


            ####Expected Result 
            - Successfully logged out
            """,
            llm=self.llm,
            # planner_llm=planner_llm,
            message_context="Please note the official site is in Swedish, but the request from user can be in English. You will need to do some translation work. No need to scroll the page",
            browser=self.browser,
            browser_context=self.browser_context
        )
        
        result = await agent.run(max_steps=30)




        # todo: this can be tested in a simple browser use test
        # print(result.urls())              # List of visited URLs
        # print(result.screenshots())       # List of screenshot paths
        # print(result.action_names())      # Names of executed actions
        # print(result.extracted_content()) # Content extracted during execution
        # print(result.errors())           # Any errors that occurred
        # print(result.model_actions())     # All actions with their parameters

        # print(result.final_result())
        # print(result.is_done())
        # print(result.has_errors())
        # print(result.model_thoughts())
        # print(result.action_results())

        await self.browser.close()
        return result

    # todo: not in use. probably can be removed?
    async def cleanup(self):
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

    asyncio.run(main())