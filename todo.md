Development Related:
1. chat -> a bit redudadent(ask two many questions)
2. chat -> the "ask for confirmation part" does not work, it is repeated
3. the request is not passed to the backend yet
    what if the user wants to reschedule?
4. make browser-use more reliable
    check more on browser-use
5. streamlit confirmation mode is not working
6. browser is not closed, but maybe this doesn't matter as we will run it in docker environment
7. the QR code solution seems to be working, but I haven't pressure tested it.
8. langchain prompt needs to be revised -> no need to double check with user
9. the "authentication" flow should be thought again
10. the data models need to double checked
11. chatbot needs to understand other languages
12. browser-use, how to run it locally.
13. think of some "unit tests"
14. the code needs to be cleaned
15. all the variables used in APIs should be double checked. It's a little bit too much
16. Prompt needs to be really improved!
	a. when to display the result
	b. make sure it asks for confirmation





Production Related:
1. Do we have to dockerize it? Can we simply create several browser-context?
2. If we have to use container, maybe we can look into this project https://www.nomadproject.io/



Browser-use improvement ideas:

I think the basic approach is that, instead of simply specify the tasks/steps, we can make the instruction more "explict"
it has something like 
`await page.keyboard.press('Control+G')`
`await page.keyboard.type(text, delay=0.1)`

maybe together with `controllor`, we can say for example, "if reschedule -> then use this controller(click this button and etc.), instead of letting LLM decide what to do"


There is this `ActionResult`, what is the use of this? 
`return ActionResult(extracted_content=f'Selected cell {cell_or_range}', include_in_memory=False)`



look more into the config `BrowserConfig` and `BrowserContextConfig` -> at least headless
```
	config=BrowserConfig(
		headless=False,  # This is True in production
		disable_security=True,
		new_context_config=BrowserContextConfig(
			disable_security=True,
			minimum_wait_page_load_time=1,  # 3 on prod
			maximum_wait_page_load_time=10,  # 20 on prod
			# no_viewport=True,
			browser_window_size={
				'width': 1280,
				'height': 1100,
			},
			# trace_path='./tmp/web_voyager_agent',
		),
	)
```


















haven't test the refresh, how frequent should I refresh to keep the session alive


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

