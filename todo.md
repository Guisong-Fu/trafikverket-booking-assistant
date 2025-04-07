1. the QR code solution seems to be working, but I haven't pressure tested it.
2. langchain prompt needs to be revised -> no need to double check with user
3. the "authentication" flow should be thought again
4. the data models need to double checked
5. chatbot needs to understand other languages




1. use browser-use to do after work
    a. choose test type, location, language and etc. -> natrual language part
    b. output -> if there is such slot, do what? if no, do what?
    c. (optional): probably do screenshot as proof 
2. use an agent figure out what users want
3. Once done the operation, it should send out email for notification.
4. database


It could be reschedule -> §Mina prov§


Here is what I want to build on a very high level.
I want to use an AI tool called §browser-use§(which is offered as a python package) to automate Swedish driving license booking process, but I would need to able to extract the BankID QR code, which is used for authentication from official website, and display it on my own website. I have more or less implemented that solution in @main.py , which uses §playwright§ and extract the QR code and display it on a Flask website. However, as the next step, I want to then use §browser-user§ for the next steps, for example, clicks §boka test§ and etc. But I realized that, as per my understanding, if I call §browser-use agent§ like what I did in @main.py , the agent will start a new browser thus the authenticated session will be ignored, which is not what I want.



"""
Possible options:
1. License type: B, B96
2. Test type: Practical driving test, theory test
3. what car to rent from:  manual, automatic
4. Location: Uppsala, Stockholm, Göteborg, Malmö, etc.
5. Time Preference:

Be prepared that the user may have spelling incorrect.
"""

