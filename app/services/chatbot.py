from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
import json
import requests
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the data model for exam requests
class ExamRequest(BaseModel):
    license_type: str = Field(None, description="Type of license (e.g., A, A1, B, BE)")
    test_type: str = Field(
        None, description="Type of test (practical driving test or theory test)"
    )
    transmission_type: str = Field(
        None, description="Transmission type (manual or automatic)"
    )
    location: List[str] = Field(
        default_factory=list, description="Preferred test locations (up to 4)"
    )
    time_preference: List[Dict[str, Any]] = Field(
        default_factory=list, description="Time preferences with priorities"
    )


# Define valid options
VALID_LICENSE_TYPES = [
    "A",
    "A1",
    "A2",
    "B",
    "B96",
    "BE",
    "Bus",
    "Goods",
    "C",
    "C1",
    "C1E",
    "CE",
    "D",
    "D1",
    "D1E",
    "DE",
    "Bus",
    "Lorry",
    "Train driver",
    "Taxi",
    "AM",
    "Tractor",
    "ADR",
    "APV",
    "VVH",
]

VALID_TEST_TYPES = ["practical driving test", "theory test"]
VALID_TRANSMISSION_TYPES = ["manual", "automatic"]

# List of valid locations (truncated for brevity, but should include all locations)
VALID_LOCATIONS = [
    "Alingsås",
    "Älmhult",
    "Ånge",
    "Ängelholm",
    "Arjeplog",
    "Arvidsjaur",
    "Arvika",
    "Avesta",
    "Boden",
    "Bollnäs",
    "Borås",
    "Borlänge",
    "Eksjö",
    "Enköping",
    "Eskilstuna",
    "Eslöv",
    "Fagersta",
    "Falkenberg",
    "Falköping",
    "Falun",
    "Farsta",
    "Finspång",
    "Flen",
    "Gällivare",
    "Gävle",
    "Gislaved",
    "Göteborg Högsbo",
    "Göteborg-Hisingen",
    "Halmstad",
    "Hammarstrand",
    "Haparanda",
    "Härnösand",
    "Hässleholm",
    "Hedemora",
    "Helsingborg",
    "HK",
    "Hudiksvall",
    "Järfälla",
    "Järpen",
    "Jokkmokk",
    "Jönköping",
    "Kalix",
    "Kalmar",
    "Karlshamn (NY)",
    "Karlskoga",
    "Karlskrona",
    "Karlstad",
    "Katrineholm",
    "Kinna",
    "Kiruna",
    "Kisa",
    "Köping",
    "Kramfors",
    "Kristianstad",
    "Kristinehamn",
    "Kumla",
    "Kungälv",
    "Kungsbacka",
    "Landskrona",
    "Lidköping",
    "Lindesberg",
    "Linköping",
    "Ljungby",
    "Ljusdal",
    "Ludvika",
    "Luleå",
    "Lund",
    "Lycksele",
    "Lysekil",
    "Malmö",
    "Malung",
    "Mariestad",
    "Mjölby",
    "Mora",
    "Motala",
    "Nässjö",
    "Norrköping",
    "Norrtälje 2",
    "Nybro",
    "Nyköping",
    "Nynäshamn",
    "Örebro",
    "Örnsköldsvik",
    "Oskarshamn",
    "Östersund",
    "Östhammar",
    "Övertorneå",
    "Pajala",
    "Piteå",
    "Ronneby",
    "Säffle",
    "Sala",
    "Sandviken",
    "Simrishamn",
    "Skellefteå",
    "Skövde",
    "Söderhamn",
    "Södertälje",
    "Sollefteå",
    "Sölvesborg",
    "Strömstad",
    "Strömsund",
    "Sundsvall",
    "Sunne",
    "Sveg",
    "Tranås",
    "Trelleborg",
    "Uddevalla",
    "Ulricehamn",
    "Umeå",
    "Upplands Väsby",
    "Uppsala",
    "Vänersborg",
    "Varberg",
    "Värnamo",
    "Västerås",
    "Västerhaninge",
    "Västervik",
    "Växjö",
    "Vetlanda",
    "Vilhelmina",
    "Vimmerby",
    "Visby",
    "Ystad",
]


SYSTEM_PROMPT_TEMPLATE = """You are a friendly and efficient assistant helping users register for driver's license exams.
        
You need to collect the following information:
1. License Type: One of {license_types}, e.g. "B"
2. Test Type: One of {test_types}, e.g. "practical driving test"
3. Transmission Type: One of {transmission_types}, e.g. "manual"
4. Location: Up to 4 locations from the provided list {locations}, user is allowed to only provide one location, e.g. "Farsta"
5. Time Preference: Flexible time ranges or "earliest available". Examples:
   - Specific times: "Every Tuesday morning 8:00-10:00"
   - Multiple options: "Tuesday morning or Wednesday afternoon"
   - Exclusions: "Not Friday afternoon, otherwise anytime"
   - Priority-based: "Morning preferred, but afternoon works too"
   - Simple: "As early as possible"

Guidelines:
1. First, thoroughly analyze the user's input to extract all available information. Only prompt for additional details if:
   - Required information is missing
   - Provided information is ambiguous or unclear
   - Information doesn't match valid options
   - User's input contains conflicting information
2. Minimize the number of questions you ask
3. Validate all provided information against the valid options
4. Be conversational but efficient
5. For time preferences, help structure them with priorities
6. Once all information is collected, provide a clear summary and ask for confirmation
7. After confirmation, return the data in the exact JSON format specified

Current collected information:
{collected_info}

Missing information:
{missing_info}

Remember to validate all inputs against the provided valid options.

IMPORTANT: Your response MUST be in valid JSON format with the following structure:
{{
  "license_type": "B",
  "test_type": "practical driving test",
  "transmission_type": "manual",
  "location": ["Uppsala"],
  "time_preference": [{{"preference": "as early as possible"}}],
  "other": null
}}

If you need to ask the user for more information, include a "message" field in your JSON response with your question.
"""


class DriverLicenseExamBot:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Initialize the chatbot with OpenAI API key and model."""
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.2)
        self.memory = ConversationBufferMemory(return_messages=True)
        self.collected_info = ExamRequest()
        self.create_agent()

    def create_agent(self):
        """Create the conversation agent with appropriate prompts."""
        try:
            # Create a simplified system prompt without JSON examples
            base_system_prompt = """You are a friendly and efficient assistant helping users register for driver's license exams.
            
You need to collect the following information:
1. License Type: One of {license_types}, e.g. "B"
2. Test Type: One of {test_types}, e.g. "practical driving test"
3. Transmission Type: One of {transmission_types}, e.g. "manual"
4. Location: Up to 4 locations from the provided list {locations}, user is allowed to only provide one location, e.g. "Farsta"
5. Time Preference: Flexible time ranges or "earliest available". Examples:
   - Specific times: "Every Tuesday morning 8:00-10:00"
   - Multiple options: "Tuesday morning or Wednesday afternoon"
   - Exclusions: "Not Friday afternoon, otherwise anytime"
   - Priority-based: "Morning preferred, but afternoon works too"
   - Simple: "As early as possible"

Guidelines:
1. First, thoroughly analyze the user's input to extract all available information. Only prompt for additional details if:
   - Required information is missing
   - Provided information is ambiguous or unclear
   - Information doesn't match valid options
   - User's input contains conflicting information
2. Minimize the number of questions you ask
3. Validate all provided information against the valid options
4. Be conversational but efficient
5. For time preferences, help structure them with priorities
6. Once all information is collected, provide a clear summary and ask for confirmation
7. After confirmation, return the data in the exact JSON format specified

Current collected information:
{collected_info}

Missing information:
{missing_info}

Remember to validate all inputs against the provided valid options.

IMPORTANT: Your response MUST be in valid JSON format. Include a "message" field if you need to ask the user for more information.
"""

            # Format the system prompt with the valid options
            system_prompt = base_system_prompt.format(
                license_types=", ".join(VALID_LICENSE_TYPES),
                test_types=", ".join(VALID_TEST_TYPES),
                locations=", ".join(VALID_LOCATIONS),
                transmission_types=", ".join(VALID_TRANSMISSION_TYPES),
                collected_info="{collected_info}",
                missing_info="{missing_info}",
            )

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{input}"),
                ]
            )

            # Create the chain
            self.chain = prompt | self.llm
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            raise

    def _validate_and_update_info(self, info: Dict[str, Any]) -> None:
        """Validate and update the collected information."""
        try:
            # Log the extracted information for debugging
            logger.info(f"Extracted info: {info}")
            
            # License Type
            if "license_type" in info and info["license_type"]:
                if info["license_type"] in VALID_LICENSE_TYPES:
                    self.collected_info.license_type = info["license_type"]
                    logger.info(f"Updated license_type: {info['license_type']}")
                else:
                    logger.warning(f"Invalid license_type: {info['license_type']}")

            # Test Type
            if "test_type" in info and info["test_type"]:
                if info["test_type"] in VALID_TEST_TYPES:
                    self.collected_info.test_type = info["test_type"]
                    logger.info(f"Updated test_type: {info['test_type']}")
                else:
                    logger.warning(f"Invalid test_type: {info['test_type']}")

            # Transmission Type
            if "transmission_type" in info and info["transmission_type"]:
                if info["transmission_type"] in VALID_TRANSMISSION_TYPES:
                    self.collected_info.transmission_type = info["transmission_type"]
                    logger.info(f"Updated transmission_type: {info['transmission_type']}")
                else:
                    logger.warning(f"Invalid transmission_type: {info['transmission_type']}")

            # Location
            if "location" in info and info["location"]:
                if isinstance(info["location"], list):
                    valid_locations = [
                        loc for loc in info["location"] if loc in VALID_LOCATIONS
                    ]
                    if valid_locations:
                        self.collected_info.location = valid_locations[:4]  # Limit to 4 locations
                        logger.info(f"Updated location: {valid_locations}")
                    else:
                        logger.warning(f"No valid locations found in: {info['location']}")
                else:
                    logger.warning(f"Location is not a list: {info['location']}")

            # Time Preference
            if "time_preference" in info and info["time_preference"]:
                # Handle different formats of time preference
                if isinstance(info["time_preference"], list):
                    # If it's already a list, use it directly
                    self.collected_info.time_preference = info["time_preference"]
                    logger.info(f"Updated time_preference: {info['time_preference']}")
                elif isinstance(info["time_preference"], str):
                    # If it's a string, convert it to a list with a single dict
                    self.collected_info.time_preference = [{"preference": info["time_preference"]}]
                    logger.info(f"Updated time_preference from string: {info['time_preference']}")
                elif isinstance(info["time_preference"], dict):
                    # If it's a dict, convert it to a list with that dict
                    self.collected_info.time_preference = [info["time_preference"]]
                    logger.info(f"Updated time_preference from dict: {info['time_preference']}")
                else:
                    # For any other type, try to convert to string
                    self.collected_info.time_preference = [{"preference": str(info["time_preference"])}]
                    logger.info(f"Updated time_preference from other type: {info['time_preference']}")

            # Other information
            if "other" in info:
                self.collected_info.other = info["other"]
                logger.info(f"Updated other: {info['other']}")
        except Exception as e:
            logger.error(f"Error validating and updating info: {str(e)}", exc_info=True)
            raise

    def _get_missing_info(self) -> List[str]:
        """Return a list of missing required information."""
        try:
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
        except Exception as e:
            logger.error(f"Error getting missing info: {str(e)}", exc_info=True)
            raise

    def _create_summary(self) -> str:
        """Create a human-readable summary of the collected information."""
        try:
            summary = "Here's a summary of your exam request:\n\n"
            
            # License Type
            if self.collected_info.license_type:
                summary += f"License Type: {self.collected_info.license_type}\n"
            else:
                summary += "License Type: Not specified\n"
                
            # Test Type
            if self.collected_info.test_type:
                summary += f"Test Type: {self.collected_info.test_type}\n"
            else:
                summary += "Test Type: Not specified\n"
                
            # Transmission Type
            if self.collected_info.transmission_type:
                summary += f"Transmission Type: {self.collected_info.transmission_type}\n"
            else:
                summary += "Transmission Type: Not specified\n"
                
            # Location
            if self.collected_info.location:
                locations_str = ", ".join(self.collected_info.location)
                summary += f"Location: {locations_str}\n"
            else:
                summary += "Location: Not specified\n"
                
            # Time Preference
            if self.collected_info.time_preference:
                time_prefs = []
                for pref in self.collected_info.time_preference:
                    if isinstance(pref, dict) and "preference" in pref:
                        time_prefs.append(pref["preference"])
                    else:
                        time_prefs.append(str(pref))
                summary += f"Time Preference: {', '.join(time_prefs)}\n"
            else:
                summary += "Time Preference: Not specified\n"
                
            # Check if any information is missing
            missing_info = self._get_missing_info()
            if missing_info:
                summary += "\nMissing information:\n"
                for info in missing_info:
                    if info == "license_type":
                        summary += "- License Type\n"
                    elif info == "test_type":
                        summary += "- Test Type\n"
                    elif info == "transmission_type":
                        summary += "- Transmission Type\n"
                    elif info == "location":
                        summary += "- Location\n"
                    elif info == "time_preference":
                        summary += "- Time Preference\n"
                
            return summary
        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}", exc_info=True)
            raise

    def chat(self, user_input: str) -> str:
        """Process a user message and return the bot's response."""
        try:
            # Add the message to memory
            self.memory.chat_memory.add_user_message(user_input)

            # Check if we've collected all required info
            missing_info = self._get_missing_info()

            print("Missing info: ", missing_info)

            try:
                # Generate response based on the conversation history
                chain_response = self.chain.invoke(
                    {
                        "history": self.memory.load_memory_variables({})["history"],
                        "input": user_input,
                        "collected_info": self.collected_info.dict(),
                        "missing_info": missing_info,
                    }
                )

                # Update collected information if any new data was provided
                try:
                    # Try to extract JSON from the response
                    response_text = chain_response.content
                    
                    # Look for JSON in the response (it might be embedded in markdown code blocks)
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|{[\s\S]*}', response_text)
                    if json_match:
                        json_str = json_match.group(1) or json_match.group(2) or json_match.group(0)
                        try:
                            extracted_info = json.loads(json_str)
                            self._validate_and_update_info(extracted_info)
                            
                            # If there's a message field, use it as the response
                            if "message" in extracted_info:
                                response_text = extracted_info["message"]
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON from match: {str(e)}")
                            # Try to parse the entire response
                            try:
                                extracted_info = json.loads(response_text)
                                self._validate_and_update_info(extracted_info)
                                
                                # If there's a message field, use it as the response
                                if "message" in extracted_info:
                                    response_text = extracted_info["message"]
                            except json.JSONDecodeError:
                                logger.warning("Failed to parse entire response as JSON")
                                # Continue with the original response text
                    else:
                        # If no JSON found, try to parse the entire response
                        try:
                            extracted_info = json.loads(response_text)
                            self._validate_and_update_info(extracted_info)
                            
                            # If there's a message field, use it as the response
                            if "message" in extracted_info:
                                response_text = extracted_info["message"]
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse response as JSON")
                            # Continue with the original response text
                except Exception as e:
                    logger.error(f"Error processing LLM response: {str(e)}", exc_info=True)
                    # Continue with the original response text

                # Check again if we've collected all required info after processing the response
                missing_info = self._get_missing_info()
                
                # If all information is collected, generate confirmation
                if not missing_info:
                    summary = self._create_summary()
                    response = f"{summary}\n\nIs this information correct? (yes/no)"
                    self.memory.chat_memory.add_ai_message(response)
                    return response

                # Save the response to memory
                self.memory.chat_memory.add_ai_message(response_text)
                return response_text
            except KeyError as e:
                # Handle KeyError specifically (missing variables in prompt)
                error_msg = str(e)
                logger.error(f"Error in prompt template: {error_msg}")
                
                # Provide a fallback response
                fallback_response = "I'm having trouble processing your request. Let me try a different approach."
                fallback_response += "\n\nCould you please provide the following information:"
                
                for info in missing_info:
                    if info == "license_type":
                        fallback_response += "\n- What type of license are you applying for? (e.g., B, A, etc.)"
                    elif info == "test_type":
                        fallback_response += "\n- Are you taking a practical driving test or a theory test?"
                    elif info == "transmission_type":
                        fallback_response += "\n- Do you prefer a manual or automatic transmission?"
                    elif info == "location":
                        fallback_response += "\n- Where would you like to take the test?"
                    elif info == "time_preference":
                        fallback_response += "\n- When would you like to take the test?"
                
                self.memory.chat_memory.add_ai_message(fallback_response)
                return fallback_response
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            raise

    def get_collected_info(self) -> Dict[str, Any]:
        """Return the collected information as a dictionary."""
        try:
            return self.collected_info.dict()
        except Exception as e:
            logger.error(f"Error getting collected info: {str(e)}", exc_info=True)
            raise

    def send_to_backend(self, backend_url: str) -> Dict[str, Any]:
        """Send the collected information to the backend service."""
        try:
            response = requests.post(backend_url, json=self.get_collected_info())
            response.raise_for_status()
            return {
                "success": True,
                "message": "Registration information received",
                "registration_id": response.json().get(
                    "registration_id", "DL-" + datetime.now().strftime("%Y%m%d-%H%M%S")
                ),
                "data": self.get_collected_info(),
            }
        except requests.RequestException as e:
            logger.error(f"Error sending to backend: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to send data to backend: {str(e)}",
                "data": self.get_collected_info(),
            }
