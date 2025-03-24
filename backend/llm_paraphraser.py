import json
import requests
import os
import csv
import time
from dotenv import load_dotenv
import re
import yaml
from configure_new_data import configure_nlu

# File that holds the newly created auestion-answer pairs
#RESPONSE_JSON = "QApairs.json"
# File that pairs are saved into as csv
OUTPUT_CSV = "QAChat.csv"

load_dotenv()
API = os.getenv("LLM_API_KEY")

system_prompt = """
I am giving you a text that represents a response for an intent in a rasa chatbot being trained for the library. Please create anywhere from 10 - 15 diverse training examples for this intent, all of which can be answered by this text response. 
If the input text is small, limit the questions instead of generalizing too much to create new questions or creating redundant questions for the sake of increasing training examples. However, if the examples can be diverse while still sticking to the text, create upto 15 training examples.
The examples should include casual, formal, and slang language, etc. Make sure to include very short direct questions aswell insteaf of just gramatically sound ones. Try to mimic how users would ask questions. It may have some typos to better train the chatbot aswell. 
List me these training examples in a valid JSON format inside "questions" in the JSON and DO NOT OUTPUT anything other than this.

Example input:
## Library Databases
The University of South Carolina subscribes to hundreds of databases on many subjects for you to use for research and teaching. You are welcome to provide links to these resources, although in many cases, downloading and reposting is prohibited.
Copyright law and the University contractual license agreements govern the access, use, and reproduction of most of the University Libraries' electronic databases. Users of library-licensed resources must comply with the terms of these agreements by a) limiting their uses to non-commercial, educational, or personal research purposes; and b) not facilitating unauthorized access by others outside of the University community.

[Learn more here](http://guides.library.sc.edu/copyright/licensing)


Example output:
{
    "questions": [
        "How do I access USC library databases?",
        "usc library databases?",
        "Where can I find USC research resources?",
        "Does USC have online databases?",
        "are databases free",
        "Yo library research stuff where",
        "lrabry databse",
        "Can I share articles from USC library?",
        "Am I allowed to download library content?",
        "usc online resources?",
        "Can non-students use lbriary databases?",
        "databases usage rules",
        "Can I use USC databases for my job",
        "lib rules breaking penatly"
    ]
}

"""

def makeNewChat(API, system_prompt):
    url = "http://login-theia.rc.sc.edu:3000/api/v1/chats/new"
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer " + API,
        "content-type": "application/json",
        "Referer": "http://login-theia.rc.sc.edu:3000/",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    body = {
        "chat": {
            "id": "",
            "title": "New Chat",
            "models": ["llama3.1:405b"],
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                    "models": ["llama3.1:405b"],
                }
            ],
        }
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        print("New Chat Created")
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")

def chatCompletion(API, chatId, system_prompt, input_prompt):
    url = "http://login-theia.rc.sc.edu:3000/api/chat/completions"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer " + API,
        "content-type": "application/json",
        "Referer": "http://login-theia.rc.sc.edu/c/" + chatId,
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    
    body = {
        "num_ctx": 8000,
        "stream": False,
        "model": "llama3.1:405b",
        "temperature": 0,
        "messages":
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt}
        ],
        "params": {},
        "features": {"image_generation": False, "web_search": False},
        "session_id": "Ba4J-UGkZyL10GgMAAAX",
        "chat_id": chatId,
        "background_tasks": {"title_generation": True, "tags_generation": True},
    }
    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        llm_response = data['choices'][0]['message']['content']
        return llm_response
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
"""
data = makeNewChat()
chatId = data["id"]
chat_history = [{"role": "system", "content": system_prompt}]
page_count = 0
questions_count = 0
with open("../Chatbot/domain.yml", "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)

for key, value in data["responses"].items():
    questions_count+=1
    if(questions_count < 405):
        continue
    intent = key.replace("utter_", "")
    input_prompt = value[0]["text"]
    
    # Keep trying until valid json is recieved
    while True:
        llm_response = chatCompletion()
        try:
            examples = json.loads(llm_response)
            examples = examples["questions"]
            break
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON for intent {intent}, retrying...")

    configure_nlu(intent, examples)
    print(f"\n-------------CONFIGURED QUESTIONS FOR INTENT # {questions_count} : {intent}---------------------\n{examples}")
"""

