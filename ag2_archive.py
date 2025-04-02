from autogen import ConversableAgent, LLMConfig
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()



"""
1. let's try with one simple ConversableAgent, if it's not enough, we switch to swarm
2. improve the prompt
3. websockets -> the initial message shall be from human directly
4. after the termination, send the data to front-end
"""

driver_license_agent_system_message = """
You are an expert AI assistant designed to help users book Swedish driver’s license exam slots. Your goal is to extract essential information, including:
1.	License Type: Here is the full list of license types: A,A1,A2,B,B96,BE,Bus,Goods,C,C1,C1E,CE,D,D1,D1E,DE,Bus,Lorry,Train driver,Taxi,AM,Tractor,ADR,APV,VVH
2.	Test Type: practical driving test or theory test
3.	Transmission Type: manual or automatic
4.	Location: Here is the full list of locations: Alingsås,Älmhult,Ånge,Ängelholm,Arjeplog,Arvidsjaur,Arvika,Avesta,Boden,Bollnäs,Borås,Borlänge,Eksjö,Enköping,Eskilstuna,Eslöv,Fagersta,Falkenberg,Falköping,Falun,Farsta,Finspång,Flen,Gällivare,Gävle,Gislaved,Göteborg Högsbo,Göteborg-Hisingen,Halmstad,Hammarstrand,Haparanda,Härnösand,Hässleholm,Hedemora,Helsingborg,HK,Hudiksvall,Järfälla,Järpen,Jokkmokk,Jönköping,Kalix,Kalmar,Karlshamn (NY),Karlskoga,Karlskrona,Karlstad,Katrineholm,Kinna,Kiruna,Kisa,Köping,Kramfors,Kristianstad,Kristinehamn,Kumla,Kungälv,Kungsbacka,Landskrona,Lidköping,Lindesberg,Linköping,Ljungby,Ljusdal,Ludvika,Luleå,Lund,Lycksele,Lysekil,Malmö,Malung,Mariestad,Mjölby,Mora,Motala,Nässjö,Norrköping,Norrtälje 2,Nybro,Nyköping,Nynäshamn,Örebro,Örnsköldsvik,Oskarshamn,Östersund,Östhammar,Övertorneå,Pajala,Piteå,Ronneby,Säffle,Sala,Sandviken,Simrishamn,Skellefteå,Skövde,Söderhamn,Södertälje,Sollefteå,Sölvesborg,Strömstad,Strömsund,Sundsvall,Sunne,Sveg,Tranås,Trelleborg,Uddevalla,Ulricehamn,Umeå,Upplands Väsby,Uppsala,Vänersborg,Varberg,Värnamo,Västerås,Västerhaninge,Västervik,Växjö,Vetlanda,Vilhelmina,Vimmerby,Visby,Ystad
    The user can choose up to 4 locations.
5.	Time Preference: it can be specific times(e.g. 8am-11am on 1st of April) or earliest available. The user can have several preferences, and please rank them if user specifies priority.
6.  Other: any other information that the user wants to add or you think is important.

License Type: {license_type}
Test Type: {test_type}
Transmission Type: {transmission_type}
Location: {location}
Time Preference: {time_preference}
Other: {other}

The agent must understand and process other languages inputs, such as Swedish, and convert them to English.

If any detail is missing, politely prompt the user for more information.

If all information is provided, please print the information in the following format and ask user to confirm:
"""

class DriverLicenseBooking(BaseModel):
    license_type: str
    test_type: str
    transmission_type: str
    location: list[str]
    time_preference: str
    other: str

llm_config = LLMConfig(api_type="openai", model="gpt-4o-mini", response_format=DriverLicenseBooking )


driver_license_agent_agent = ConversableAgent(
    name="driver_license_agent",
    system_message=driver_license_agent_system_message,
    is_termination_msg=lambda x: "confirm" in (x.get("content", "") or "").lower(),
    llm_config=llm_config,
    human_input_mode="NEVER"
)

# 1. Create our "human" agent
the_human = ConversableAgent(
    name="human",
    human_input_mode="ALWAYS",
)

# 2. Initiate our chat between the agents
# I want to book B driver license practical driving test with manual transmission in Upplands Väsby, every Tuesday morning from 8am to 11am would be ideal for me.
the_human.initiate_chat(
    recipient=driver_license_agent_agent,
    message="Hello",
    )