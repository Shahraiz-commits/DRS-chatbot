# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import datetime

class ActionLibraryOpen(Action):
    def name(self) -> Text:
        return "action_library_open"
    
    def run(self, dispatcher, tracker, domain):
        #currentDate = datetime.date.today()
        currentDay = datetime.datetime.now().strftime("%A")
        currentTime = datetime.datetime.now().time()
        
        # Hours for students/faculty not visitors
        library_hours = {
            "Sunday": (datetime.time(10, 0), datetime.time(2, 0)),  # 10:00 AM - 2:00 AM
            "Monday": (datetime.time(7, 30), datetime.time(2, 0)),  # 7:30 AM - 2:00 AM
            "Tuesday": (datetime.time(7, 30), datetime.time(2, 0)), # 7:30 AM - 2:00 AM
            "Wednesday": (datetime.time(7, 30), datetime.time(2, 0)), # 7:30 AM - 2:00 AM
            "Thursday": (datetime.time(7, 30), datetime.time(2, 0)), # 7:30 AM - 2:00 AM
            "Friday": (datetime.time(7, 30), datetime.time(19, 0)),  # 7:30 AM - 7:00 PM
            "Saturday": (datetime.time(10, 0), datetime.time(19, 0))  # 10:00 AM - 7:00 PM
        }

        # Check if the library is open based on the day
        open_time, close_time = library_hours.get(currentDay, (None, None))
        is_open = open_time <= currentTime <= close_time
        response = f"The library is open until {close_time}." if is_open else f"The library is currently closed. It will open at {open_time}"
        dispatcher.utter_message(response)
        return []