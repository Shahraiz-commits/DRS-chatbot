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

load_dotenv(".env")
API = os.getenv("LLM_API_KEY")

system_prompt = """
You will be given a text response along with existing training examples. Your task is to generate 10-15 diverse training examples for this intent that can be answered by the given text. Ensure the new examples are distinct from the provided ones. Include casual, formal, slang, and short direct questions. Use typos to make the chatbot more robust. Output only the new examples in valid JSON format inside "questions".

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

def chat_with_model(token, system_prompt,input_prompt):
    url = 'http://login-theia.rc.sc.edu:3000/api/chat/completions'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "stream": False,
        #"num_ctx": 8000,
        "model": "llama3.1:405b",
        "temperature": 0,
        "messages":
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt}
        ],
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        data = response.json()
        llm_response = data['choices'][0]['message']['content']
        return llm_response
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
page_count = 0
questions_count = 0
with open("../Chatbot/domain.yml", "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)

for key, value in data["responses"].items():
    questions_count+=1
    #if(questions_count < 405):
    #    continue
    intent = key.replace("utter_", "")
    input_prompt = value[0]["text"]
    
    # Keep trying until valid json is recieved
    while True:
        llm_response = chat_with_model(API, system_prompt, input_prompt)
        try:
            examples = json.loads(llm_response)
            examples = examples["questions"]
            break
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON for intent {intent}, retrying...")

    configure_nlu(intent, examples)
    print(f"\n-------------CONFIGURED QUESTIONS FOR INTENT # {questions_count} : {intent}---------------------\n{examples}")

