from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
import json
import requests
from datetime import datetime

# Define the data model for exam requests
class ExamRequest(BaseModel):
    license_type: str = Field(None, description="Type of license (e.g., A, A1, B, BE)")
    test_type: str = Field(None, description="Type of test (practical driving test or theory test)")
    transmission_type: str = Field(None, description="Transmission type (manual or automatic)")
    location: List[str] = Field(default_factory=list, description="Preferred test locations (up to 4)")
    time_preference: List[Dict[str, Any]] = Field(default_factory=list, description="Time preferences with priorities")
    other: Optional[str] = Field(None, description="Additional information or notes")

# Define valid options
VALID_LICENSE_TYPES = [
    "A", "A1", "A2", "B", "B96", "BE", "Bus", "Goods", "C", "C1", "C1E", "CE",
    "D", "D1", "D1E", "DE", "Bus", "Lorry", "Train driver", "Taxi", "AM", "Tractor", "ADR", "APV", "VVH"
]

VALID_TEST_TYPES = ["practical driving test", "theory test"]
VALID_TRANSMISSION_TYPES = ["manual", "automatic"]

# List of valid locations (truncated for brevity, but should include all locations)
VALID_LOCATIONS = [
    "Alingsås", "Älmhult", "Ånge", "Ängelholm", "Arjeplog", "Arvidsjaur", "Arvika",
    "Avesta", "Boden", "Bollnäs", "Borås", "Borlänge", "Eksjö", "Enköping", "Eskilstuna",
    "Eslöv", "Fagersta", "Falkenberg", "Falköping", "Falun", "Farsta", "Finspång", "Flen",
    "Gällivare", "Gävle", "Gislaved", "Göteborg Högsbo", "Göteborg-Hisingen", "Halmstad",
    "Hammarstrand", "Haparanda", "Härnösand", "Hässleholm", "Hedemora", "Helsingborg",
    "HK", "Hudiksvall", "Järfälla", "Järpen", "Jokkmokk", "Jönköping", "Kalix", "Kalmar",
    "Karlshamn (NY)", "Karlskoga", "Karlskrona", "Karlstad", "Katrineholm", "Kinna",
    "Kiruna", "Kisa", "Köping", "Kramfors", "Kristianstad", "Kristinehamn", "Kumla",
    "Kungälv", "Kungsbacka", "Landskrona", "Lidköping", "Lindesberg", "Linköping",
    "Ljungby", "Ljusdal", "Ludvika", "Luleå", "Lund", "Lycksele", "Lysekil", "Malmö",
    "Malung", "Mariestad", "Mjölby", "Mora", "Motala", "Nässjö", "Norrköping",
    "Norrtälje 2", "Nybro", "Nyköping", "Nynäshamn", "Örebro", "Örnsköldsvik",
    "Oskarshamn", "Östersund", "Östhammar", "Övertorneå", "Pajala", "Piteå", "Ronneby",
    "Säffle", "Sala", "Sandviken", "Simrishamn", "Skellefteå", "Skövde", "Söderhamn",
    "Södertälje", "Sollefteå", "Sölvesborg", "Strömstad", "Strömsund", "Sundsvall",
    "Sunne", "Sveg", "Tranås", "Trelleborg", "Uddevalla", "Ulricehamn", "Umeå",
    "Upplands Väsby", "Uppsala", "Vänersborg", "Varberg", "Värnamo", "Västerås",
    "Västerhaninge", "Västervik", "Växjö", "Vetlanda", "Vilhelmina", "Vimmerby",
    "Visby", "Ystad"
]

SYSTEM_PROMPT_TEMPLATE = """You are a friendly and efficient assistant helping users register for driver's license exams.
        
You need to collect the following information:
1. License Type: One of {license_types}
2. Test Type: One of {test_types}
3. Transmission Type: One of {transmission_types}
4. Location: Up to 4 locations from the provided list
5. Time Preference: Specific times or "earliest available"
6. Other: Any additional information

Guidelines:
1. Ask for ONE piece of missing information at a time
2. Validate all provided information against the valid options
3. If the user provides multiple pieces of information, acknowledge and save them all
4. Be conversational but efficient
5. For time preferences, help structure them with priorities
6. Once all information is collected, provide a clear summary and ask for confirmation
7. After confirmation, return the data in the exact JSON format specified

Current collected information:
{collected_info}

Missing information:
{missing_info}

Remember to validate all inputs against the provided valid options.
"""




class DriverLicenseExamBot:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Initialize the chatbot with OpenAI API key and model."""
        self.llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.2)
        self.memory = ConversationBufferMemory(return_messages=True)
        self.collected_info = ExamRequest()
        self.create_agent()
        
    def create_agent(self):
        """Create the conversation agent with appropriate prompts."""

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            license_types=', '.join(VALID_LICENSE_TYPES),
            test_types=', '.join(VALID_TEST_TYPES),
            transmission_types=', '.join(VALID_TRANSMISSION_TYPES),
            collected_info="{collected_info}",
            missing_info="{missing_info}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        
        self.chain = prompt | self.llm
        
    def _validate_and_update_info(self, info: Dict[str, Any]) -> None:
        """Validate and update the collected information."""
        if "license_type" in info and info["license_type"] in VALID_LICENSE_TYPES:
            self.collected_info.license_type = info["license_type"]
            
        if "test_type" in info and info["test_type"] in VALID_TEST_TYPES:
            self.collected_info.test_type = info["test_type"]
            
        if "transmission_type" in info and info["transmission_type"] in VALID_TRANSMISSION_TYPES:
            self.collected_info.transmission_type = info["transmission_type"]
            
        if "location" in info:
            valid_locations = [loc for loc in info["location"] if loc in VALID_LOCATIONS]
            self.collected_info.location = valid_locations[:4]  # Limit to 4 locations
            
        if "time_preference" in info:
            self.collected_info.time_preference = info["time_preference"]
            
        if "other" in info:
            self.collected_info.other = info["other"]
    
    def _get_missing_info(self) -> List[str]:
        """Return a list of missing required information."""
        missing = []
        if not self.collected_info.license_type:
            missing.append("license_type")
        if not self.collected_info.test_type:
            missing.append("test_type")
        if not self.collected_info.transmission_type:
            missing.append("transmission_type")
        if not self.collected_info.location:
            missing.append("location")
        if not self.collected_info.time_preference:
            missing.append("time_preference")
        return missing
    
    def _create_summary(self) -> str:
        """Create a human-readable summary of the collected information."""
        summary = "Here's a summary of your exam request:\n\n"
        summary += f"License Type: {self.collected_info.license_type}\n"
        summary += f"Test Type: {self.collected_info.test_type}\n"
        summary += f"Transmission Type: {self.collected_info.transmission_type}\n"
        summary += f"Preferred Locations: {', '.join(self.collected_info.location)}\n"
        summary += "Time Preferences:\n"
        for pref in self.collected_info.time_preference:
            summary += f"- {pref}\n"
        if self.collected_info.other:
            summary += f"\nAdditional Information: {self.collected_info.other}\n"
        return summary
    
    def chat(self, user_input: str) -> str:
        """Process a user message and return the bot's response."""
        # Add the message to memory
        self.memory.chat_memory.add_user_message(user_input)
        
        # Check if we've collected all required info
        missing_info = self._get_missing_info()
        if not missing_info:
            # All information collected, generate confirmation
            summary = self._create_summary()
            response = f"{summary}\n\nIs this information correct? (yes/no)"
            self.memory.chat_memory.add_ai_message(response)
            return response
        
        # Generate response based on the conversation history
        chain_response = self.chain.invoke({
            "history": self.memory.load_memory_variables({})["history"],
            "input": user_input,
            "collected_info": self.collected_info.dict(),
            "missing_info": missing_info
        })
        
        # Update collected information if any new data was provided
        try:
            extracted_info = json.loads(chain_response.content)
            self._validate_and_update_info(extracted_info)
        except json.JSONDecodeError:
            pass
            
        # Save the response to memory
        self.memory.chat_memory.add_ai_message(chain_response.content)
        return chain_response.content
    
    def get_collected_info(self) -> Dict[str, Any]:
        """Return the collected information as a dictionary."""
        return self.collected_info.dict()
    
    def send_to_backend(self, backend_url: str) -> Dict[str, Any]:
        """Send the collected information to the backend service."""
        try:
            response = requests.post(backend_url, json=self.get_collected_info())
            response.raise_for_status()
            return {
                "success": True,
                "message": "Registration information received",
                "registration_id": response.json().get("registration_id", "DL-" + datetime.now().strftime("%Y%m%d-%H%M%S")),
                "data": self.get_collected_info()
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "message": f"Failed to send data to backend: {str(e)}",
                "data": self.get_collected_info()
            }

# Example usage
if __name__ == "__main__":
    import os
    
    # Initialize the bot
    bot = DriverLicenseExamBot(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("Driver's License Exam Registration Bot")
    print("Type 'exit' to end the conversation\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
            
        response = bot.chat(user_input)
        print(f"Bot: {response}")
        
        # Check if all information has been collected and confirmed
        if not bot._get_missing_info() and "Is this information correct?" in response:
            confirmation = input("You: ")
            if confirmation.lower() == 'yes':
                backend_response = bot.send_to_backend("https://api.example.com/register")
                print(f"\nBackend Response: {json.dumps(backend_response, indent=2)}")
                break
            else:
                # Reset collected info and continue
                bot.collected_info = ExamRequest()
                print("Bot: Let's start over. What type of license are you applying for?")

