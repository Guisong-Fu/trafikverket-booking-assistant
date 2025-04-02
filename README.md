https://github.com/gauravdhiman/browser-use-fastapi-docker-server



I want to build an application that help users automatically driver license exam. And the the first thing to do will be get all the information from user about what kind of tests they want to take, B license, BE license, practical driving test or theory, and their preferred time and etc. 

So I would need to build a chatbot that talks to the users, asks for users to provide information, keeps asking if the information is not enough, asks user to confirm if that is that is indeed what they are looking for, if user confirms, then the chatbot shall send the extracted information in a JSON format and send it to another backend service. 


Please help me build a chatbot(using the latest version of LangChain) that gathers the user’s preferences (license type, test type, time preferences, etc.) and sends these details, upon user confirmation, to a backend service in JSON format.


Here is the user story:
1. As a user, I want to easily provide details about the driving exam I need to schedule (e.g., license type, test type, preferred time/date), so that the scheduling process is quick and convenient.
2. As the system, I want to validate that the user has provided all the required information, so that I can ensure the request to the backend service is complete and accurate.
3.	As the chatbot, I want to confirm the user’s input before final submission, so that users can correct any mistakes and be confident in the accuracy of the data sent to the backend.


Key Requirements
1.Chatbot Interaction: the first message will be sent from user with information what kind of test he wants to book.
2.Iterative Questioning: If any required field is missing (e.g., license type), the chatbot must continue to prompt until that information is provided. Provide helpful prompts or clarifications if the user’s answer is unclear or inconsistent.
3.Confirmation: Review Summary, Once the chatbot has gathered all information, it should display a concise summary (e.g., “You want a B license test, practical, on weekday mornings, in May. Is that correct?”). User Correction: Allow the user to correct any mistakes in the summary before finalizing. User Confirmation: The user explicitly confirms the information is correct.
4.Data Packaging & Transfer. Upon user confirmation, the chatbot assembles the data into a well-defined JSON structure. The system sends this JSON payload to a specified backend endpoint (e.g., via an HTTP POST request).The chatbot reports success or failure based on the backend’s response.



Data Structure Example

Below is a sample JSON that the chatbot would send to the backend once the user confirms:


{
    "license_type": "B",
    "test_type": "practical driving test",
    "transmission_type": "manual",
    "location": ["Alingsås", "Farsta"],
    "time_preference": "earliest available",
    "other": "morning is more preferable"
}


1.	License Type: Here is the full list of license types: A,A1,A2,B,B96,BE,Bus,Goods,C,C1,C1E,CE,D,D1,D1E,DE,Bus,Lorry,Train driver,Taxi,AM,Tractor,ADR,APV,VVH
2.	Test Type: practical driving test or theory test
3.	Transmission Type: manual or automatic
4.	Location: Here is the full list of locations: Alingsås,Älmhult,Ånge,Ängelholm,Arjeplog,Arvidsjaur,Arvika,Avesta,Boden,Bollnäs,Borås,Borlänge,Eksjö,Enköping,Eskilstuna,Eslöv,Fagersta,Falkenberg,Falköping,Falun,Farsta,Finspång,Flen,Gällivare,Gävle,Gislaved,Göteborg Högsbo,Göteborg-Hisingen,Halmstad,Hammarstrand,Haparanda,Härnösand,Hässleholm,Hedemora,Helsingborg,HK,Hudiksvall,Järfälla,Järpen,Jokkmokk,Jönköping,Kalix,Kalmar,Karlshamn (NY),Karlskoga,Karlskrona,Karlstad,Katrineholm,Kinna,Kiruna,Kisa,Köping,Kramfors,Kristianstad,Kristinehamn,Kumla,Kungälv,Kungsbacka,Landskrona,Lidköping,Lindesberg,Linköping,Ljungby,Ljusdal,Ludvika,Luleå,Lund,Lycksele,Lysekil,Malmö,Malung,Mariestad,Mjölby,Mora,Motala,Nässjö,Norrköping,Norrtälje 2,Nybro,Nyköping,Nynäshamn,Örebro,Örnsköldsvik,Oskarshamn,Östersund,Östhammar,Övertorneå,Pajala,Piteå,Ronneby,Säffle,Sala,Sandviken,Simrishamn,Skellefteå,Skövde,Söderhamn,Södertälje,Sollefteå,Sölvesborg,Strömstad,Strömsund,Sundsvall,Sunne,Sveg,Tranås,Trelleborg,Uddevalla,Ulricehamn,Umeå,Upplands Väsby,Uppsala,Vänersborg,Varberg,Värnamo,Västerås,Västerhaninge,Västervik,Växjö,Vetlanda,Vilhelmina,Vimmerby,Visby,Ystad
    The user can choose up to 4 locations.
5.	Time Preference: it can be specific times(e.g. 8am-11am on 1st of April) or earliest available. The user can have several preferences, and please rank them if user specifies priority.
6.  Other: any other information that the user wants to add or you think is important.

Attached are 3 sample snippets using langchain, please take it for reference.

Please make sure to use latest version of LangChain, and the code shall be as clear as possible. Please keep in mind that, in a later stage we will expose this as API using FastAPI and further integrate with Streamlit and later with a self build front-end website.

