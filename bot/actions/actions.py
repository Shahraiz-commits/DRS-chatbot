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

class ActionLibraryOpen(Action):
    def name(self) -> Text:
        return "action_library_open"
    
    def run(self, dispatcher, tracker, domain):
        import datetime
        import pytz
        
        def format_delta(delta):
            # Returns Xh Ym
            minutes = int(delta.total_seconds() // 60)
            h, m = divmod(minutes, 60)
            if h and m:
                return f"{h}h {m}m"
            elif h:
                return f"{h}h"
            else:
                return f"{m}m"
        
        # for testing now
        tz = pytz.timezone("America/New_York")
        now = datetime.datetime.now(tz)
        currentDay = now.strftime("%A")
        currentTime = now.time()

        # TODO: Make the hours dynamic. Account for holidays and emergency closures.
        # Hours for students/faculty not visitors
        library_hours = {
            "Monday":    (datetime.time(7, 30), datetime.time(2, 0)),
            "Tuesday":   (datetime.time(7, 30), datetime.time(2, 0)),
            "Wednesday": (datetime.time(7, 30), datetime.time(2, 0)),
            "Thursday":  (datetime.time(7, 30), datetime.time(2, 0)),
            "Friday":    (datetime.time(7, 30), datetime.time(19, 0)),
            "Saturday":  (datetime.time(10, 0), datetime.time(19, 0)),
            "Sunday":    (datetime.time(10, 0), datetime.time(2, 0)),
        }

        # If, for some reason, there's no entry for today's day:
        if currentDay not in library_hours:
            dispatcher.utter_message("I'm not sure of today's library hours.")
            return []

        open_time, close_time = library_hours[currentDay]

        # Build datetimes for now, open, and close
        dt_now = datetime.datetime.combine(now.date(), currentTime)
        dt_open = datetime.datetime.combine(now.date(), open_time)
        if open_time <= close_time:
            dt_close = datetime.datetime.combine(now.date(), close_time)
        else:
            dt_close = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), close_time)

        # Determine if library is open right now
        is_open = dt_open <= dt_now < dt_close

        if is_open:
            time_until_close = dt_close - dt_now
            resp = (f"The library is currently OPEN and will close at "
                    f"{close_time.strftime('%I:%M %p')} "
                    f"(in {format_delta(time_until_close)}).")
        else:
            # It's closed right now.
            # - If it's still before today's open_time, "It will open at open_time today."
            # - Otherwise, it opens next day.
            
            if dt_now < dt_open:
                time_until_open = dt_open - dt_now
                resp = (f"The library is currently CLOSED. It will open at "
                        f"{open_time.strftime('%I:%M %p')} today "
                        f"(in {format_delta(time_until_open)}).")
            else:
                days_of_week = list(library_hours.keys())
                i = days_of_week.index(currentDay)
                next_day = days_of_week[(i + 1) % 7]
                next_open, next_close = library_hours[next_day]
                dt_next_day = now.date() + datetime.timedelta(days=1)
                dt_next_open = datetime.datetime.combine(dt_next_day, next_open)
                # For cross-midnight next day
                if next_open <= next_close:
                    dt_next_close = datetime.datetime.combine(dt_next_day, next_close)
                else:
                    dt_next_close = datetime.datetime.combine(dt_next_day + datetime.timedelta(days=1), next_close)
                
                time_until_open = dt_next_open - dt_now
                resp = (f"The library is currently CLOSED. It will open next on "
                        f"{next_day} at {next_open.strftime('%I:%M %p')} "
                        f"(in {format_delta(time_until_open)}). It will stay open until "
                        f"{next_close.strftime('%I:%M %p')}.")

        resp += (f"\n\nFor the most up to date hours please visit:"
                 "https://sc.edu/about/offices_and_divisions/"
                 "university_libraries/about/hours/index.php")
        dispatcher.utter_message(resp)
        return []

