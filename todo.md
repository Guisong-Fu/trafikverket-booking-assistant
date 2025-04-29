1. improve prompt -> how we can make the prompt better, I had a feeling that the current prompt is a bottleneck
2. understand better about that controller -> add got to page, instead of click -> this is more or less only for testing purpose, in the real world, we may just use playwright to go to that page to save some token(it will save some token, right)?
3. try to see if there is any other controller I can use or implement -> for example, instead of selecting index, try select text
4. try with multiple agents instead of one big



Here is what we can do: 
1. print more information and see where the problem is
2. try multiple agents with tasks on its own


It has to find the exact component to click one!
It's too much of hassle to let LLM to decide which one to click on! And it's way too slow, and potentially costly    





This looks cool: -> they are all YC companies~ 
https://mem0.ai/
https://lmnr.ai/



Here are the features that we can refer to:
https://github.com/browser-use/browser-use/blob/main/examples/features/initial_actions.py





Use ReAct in the prompt, it's indeed art to write good prompt.

something like this. Maybe we do not need to write it on our own, LangChain templates may have something we can reuse


This is a very cool one, haven't seen this before
https://smith.langchain.com/hub

```
prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

average_dog_weight:
e.g. average_dog_weight: Collie
returns average weight of a dog when given the breed

Example session:

Question: How much does a Bulldog weigh?
Thought: I should look the dogs weight using average_dog_weight
Action: average_dog_weight: Bulldog
PAUSE

You will be called again with this:

Observation: A Bulldog weights 51 lbs

You then output:

Answer: A bulldog weights 51 lbs
""".strip()
```




There is this bug。  `choose m, a, n, u, a, l as transmission type` is apparently wrong
```
INFO     [agent] 🚀 Starting task: 
            1. Click "Boka prov"
            2. choose and click B type of exam
            3. choose practical driving test type of test
            4. choose Uppsala as test location
            5. choose m, a, n, u, a, l as transmission type
            6. If there is a slot available in the preferred time mentioned in the as early as possible in May, click "Välj"
            7. click that "trash-icon"(ta bort) to remove/cancel it from shopping cart
            8. Click "Logga ut"
            9. Then click "Ja, logga ut"
            10. close the browser
```

1. browser use is not reliable at all. need more work on that. Maybe use controller or something
2. Now it works like that. If the first message has all the information(no missing_info), there will be no LLM generated response and ask for confirmation. But if there is any more information that is missing and requires chat, then LLM ask for confirmation, instead of the hardcoded response.




Essential:




1. collected info shall be passed to frontend, instead of the "summary"
2. what message shall be displayed on frontend for user to confirm and clarify? -> maybe we can help multiple prompts that do specific things, instead of one big prompt?

why is there still that message



I should better organize it.
what are essential? what are for mvp? what are for production? what are for refactorization? what are must have? what are nice to have





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
17. we probably need sessions? I mean, how to make sure if there won't be any problem 
18. double check the data that is being passed from front-end or API
19. Right now, 'time preference' is set to a list. Do we need to have some kind of ranking or priority here?




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

