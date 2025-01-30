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
        
        # TODO: Make the hours dynamic. Account for holidays and emergency closures.
        # Hours for students/faculty not visitors
        library_hours = {
            "Monday": (datetime.time(7, 30), datetime.time(2, 0)),  # 7:30 AM - 2:00 AM
            "Tuesday": (datetime.time(7, 30), datetime.time(2, 0)), # 7:30 AM - 2:00 AM
            "Wednesday": (datetime.time(7, 30), datetime.time(2, 0)), # 7:30 AM - 2:00 AM
            "Thursday": (datetime.time(7, 30), datetime.time(2, 0)), # 7:30 AM - 2:00 AM
            "Friday": (datetime.time(7, 30), datetime.time(19, 0)),  # 7:30 AM - 7:00 PM
            "Saturday": (datetime.time(10, 0), datetime.time(19, 0)),  # 10:00 AM - 7:00 PM
            "Sunday": (datetime.time(10, 0), datetime.time(2, 0)),  # 10:00 AM - 2:00 AM
        }

        open_time, close_time = library_hours.get(currentDay)
        
        # Get times for +1/-1 days for checking past-midnight hours
        days = list(library_hours.keys())
        prev_day = days[(days.index(currentDay) - 1) % len(days)]
        next_day = days[(days.index(currentDay) + 1) % len(days)]
        prev_open, prev_close = library_hours[prev_day]
        next_open, next_close = library_hours[next_day]


        if open_time < close_time:
            # Normal case: opens and closes within the same day
            is_open = open_time <= currentTime < close_time
        else:
            # Special case: closes after midnight
            is_open = (currentTime >= open_time) or (currentTime < prev_close)
        
        response = f"The library is currently open and will close at {close_time.strftime('%I:%M %p')}." if is_open else f"The library is currently closed. It will open at {next_open.strftime('%I:%M %p')} on {next_day} and stay open until {next_close.strftime('%I:%M %p')}."
        dispatcher.utter_message(response)
        return []