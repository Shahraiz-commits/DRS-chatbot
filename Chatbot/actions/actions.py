# revised g0

from typing import Any, Text, Dict, List, Union, Optional

import rasa.core.tracker_store
from rasa.shared.core.trackers import DialogueStateTracker
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
# from rasa_sdk.forms import FormAction
from datetime import datetime, timezone, timedelta
#import panda as pd
from nrclex import NRCLex
import yaml
import os
import sys
import nltk
nltk.download('punkt_tab')
nltk.download('punkt')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
# firebase_utils for PROD and .firebase_utils for LOCAL
from firebase_utils import add_question_to_intent, add_unassigned_question

class ActionSaveConversation(Action):

    def name(self) -> Text:
        return "action_save_conversation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        conversation_id = str(tracker.sender_id)
        conversation = tracker.events
         
        count_u = 0
        count_b = 0

        import os
        if not os.path.isfile('chats.csv'):
            with open('chats.csv','w') as file:
                file.write("input_time|conversation_id|count|intent|user_input| entity_name|entity_value|action|bot_reply|\n")
        chat_data=''
        for i in conversation:
            now = datetime.now()
            input_time = now.astimezone(timezone(timedelta(hours=-4))).strftime('%Y-%m-%d %H:%M:%S.%f')
            if i['event'] == 'user':
               str_count_u = 'U'+str(count_u)
               chat_data+= input_time+'|' + conversation_id + '|' + str_count_u+'|' +i['parse_data']['intent']['name']+'|' + i['text'] +'|' + '\n'
               count_u = count_u+ 1
               print('user: {}'.format(i['text']))
               if len(i['parse_data']['entities']) > 0:
                    chat_data += i['parse_data']['entities'][0]['entity']+'|'+i['parse_data']['entities'][0]['value']+'|'
                    print('extra data:', i['parse_data']['entities'][0]['entity'], '=',
                          i['parse_data']['entities'][0]['value'])
               else:
                    chat_data+=""
            elif i['event'] == 'bot':
                str_count_b = 'B'+str(count_b)
                print('Bot: {}'.format(i['text']))
                try:
                    chat_data+=input_time+'|' + conversation_id + '|' + str_count_b+'|' +'|'+'|' + '|' +'|' + i['metadata']['utter_action']+'|'+ i['text'] + '\n'
                    count_b = count_b+ 1
                except KeyError:
                    pass
        else:
            with open('chats.csv','a') as file:
                file.write(chat_data)

        #dispatcher.utter_message(text="")
        

        return []

class ActionSessionId(Action):
    def name(self) -> Text:
        return "action_session_id"

    async def run(
    self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        conversation_id=tracker.sender_id
        #dispatcher.utter_message("The conversation id is {}".format(conversation_id))
        return []

class ActionEmotion(Action):

    def name(self) -> Text:
        return "action_emotion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        text = str(tracker.latest_message["text"])
        emotion = NRCLex(text)
        #dispatcher.utter_message(text="The affect frequencies are: {}".format(emotion.affect_frequencies))
        #dispatcher.utter_message(text="Top emotions detected are: {}".format(emotion.top_emotions))

        return []
    
class ActionProcessChoice(Action):
    def name(self) -> Text:
        return "action_process_choice"
    
    def run(self, dispatcher, tracker : Tracker, domain):
        user_question_event = tracker.get_last_event_for("user", skip=1)
        question = user_question_event.get("text")
        intent_ranking = user_question_event["parse_data"].get("intent_ranking", [])
        intents = []
        for i in range(1, 4):
            intents.append(intent_ranking[i]["name"])
            #dispatcher.utter_message(intents[i-1])

        number = int(next(tracker.get_latest_entity_values("number"), None))        
        if(number in [1,2,3]):
            #bot_responses = [event for event in tracker.events if event.get("event") == "bot"]
            #picked_answer = bot_responses[number-5].get("text")
            add_question_to_intent(intents[number-1], question)
            #dispatcher.utter_message(f"You picked answer: {picked_answer} \nAnd intent: {intents[number-1]}")
        else:
            #dispatcher.utter_message(f"Question: {question} unassigned")
            add_unassigned_question(question)
                
class ActionProcessFallback(Action):
    def name(self) -> Text:
        return "action_process_fallback"
    
    def run(self, dispatcher, tracker : Tracker, domain):
        intents = tracker.latest_message["intent_ranking"]
        first_text = ""
        second_text = ""
        third_text = ""
        name1 = intents[1]['name']
        confidence1 = intents[1]['confidence']
        name2 = intents[2]['name']
        name3 = intents[3]['name']
        
        if(confidence1 <= 0.24):
            dispatcher.utter_message(f"out of scope")
            return

        # Search for first two intents text
        # NOTE: "../Chatbot/domain.yml" for LOCAL "domain.yml" for PROD
        with open("domain.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            for response_key, response_list in data["responses"].items():
                if response_key == "utter_"+name1:
                    first_text = response_list[0]["text"] 
                elif response_key == "utter_"+name2:
                    second_text = response_list[0]["text"]
                elif response_key == "utter_"+name3:
                    third_text = response_list[0]["text"]
        dispatcher.utter_message(f"Sorry, I am a bit unsure with my response. Is this what you were looking for? [1]\n\n---\n{first_text}\n\n---\n\nI also found this information that may be relevant [2]\n\n---\n{second_text}\n\n---\n\nHere's one more, that may be less relevant [3]\n\n---\n{third_text}\n\n---\n\nDid any of these responses answer your question? If so, please enter 1, 2, or 3 for the response that answered your question.\nEnter 0 if none of these responses answer your question.")

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

        resp += (f"\n\nFor the most up to date hours please visit [library hours](https://sc.edu/about/offices_and_divisions/university_libraries/about/hours/index.php)")
        dispatcher.utter_message(resp)
        return []