from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from langchain_openai import ChatOpenAI
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def main():

    browser_config = BrowserConfig(
        disable_security=True
    )
    browser = Browser(config=browser_config)

    browser_context = BrowserContext(browser=browser)
    llm=ChatOpenAI(model="gpt-4o-mini")
    agent_login = Agent(
        # task="""
        # 1. go to  https://fp.trafikverket.se/Boka/ng/
        # 2. Click on the "Logga in" button
        # 3. Select "Mobilt BankID" as the authentication method
        # 4. wait for me to scan the QR code to authenticate
        # 5. Click book test
        # 6. choose B96 type of exam
        # 7. choose practical driving test
        # 8. choose Uppsala as test location
        # 9. If there is a slot available in April, print the date and time of the slot
        # """,

        task="""
        1. go to  https://fp.trafikverket.se/Boka/ng/
        2. Click on the "Logga in" button
        3. Select "Mobilt BankID" as the authentication method
        4. wait for me to scan the QR code to authenticate
        """,
        browser_context=browser_context,
        llm=llm,
    )

    agent_go_to_booking = Agent(
        task="""
        Click "Meny", then in the dropdown, click "Boka prov"
        """,
        browser_context=browser_context,
        llm=llm,
    )

    agent_book_b = Agent(
        task="""
            Select "B – Personbil"
        """,
        browser_context=browser_context,
        llm=llm,
    )

    await agent_login.run()

    # while True:
    await agent_go_to_booking.run()
    await agent_book_b.run()




asyncio.run(main())