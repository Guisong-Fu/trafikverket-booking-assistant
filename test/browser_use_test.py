from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def main():
    agent = Agent(
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

        # task="""
        # 1. go to  https://fp.trafikverket.se/Boka/ng/
        # 2. Click on the "Logga in" button
        # 3. Select "Mobilt BankID" as the authentication method
        # 4. wait for me to scan the QR code to authenticate
        # 5. Click "Boka prov"
        # 6. Click "Logga ut"
        # 7. Click "Ja, logga ut"
        # """,

        task="""
        1. go to https://www.google.com/
        """,


        llm=ChatOpenAI(model="gpt-4o-mini"),
    )
    await agent.run()

asyncio.run(main())