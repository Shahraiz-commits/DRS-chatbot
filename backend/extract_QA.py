import json
import requests
import os
import csv
import time
from dotenv import load_dotenv
# File that holds the newly created auestion-answer pairs
#RESPONSE_JSON = "QApairs.json"
# File that pairs are saved into as csv
OUTPUT_CSV = "QAChat.csv"

load_dotenv()
API = os.getenv("LLM_API_KEY")

system_prompt = """
You are a question-answer pair generator for the development of training data for a library chatbot. I will provide some text, which you will then use to create appropriate question-answer pairs with.
Please limit the creation of questions so that each question covers as much relevant information as possible, with minimal overlap with the answers of other questions you may generate.
The questions should be sufficient in relaying all information presented within the text. I.e. the answers altogether should contain ALL of the given text. Do not change the markdown formatting present in the text and ensure all the given text is present in the answers in its entirety. Include any markdown headings and lists etc. Do not omit or change information in the text to shorten the answer in the JSON file.
Limit the number of question-answer pairs as low as appropriate, not exceeding 10. Give preference to longer answers over creating a new seperate question.

Make sure each answer contains [Learn more here](link) at the end of each response on a seperate line where the "link" to use will be given at the end of each text in the format [Learn more here](link).

Please create questions and answers and output them in JSON format. Do not output anything other than the complete JSON file.

EXAMPLE INPUT: 
## Consultations (online / in-person)\nAI Model Development and Training: Assisting in the development, training, and validation of machine learning models for research projects such as:\n- Natural Language Processing (NLP)\n- Supporting text analysis and NLP projects, including sentiment analysis, topic modeling, and classification.TIme-Series data analysis and forecasting.Software and tools: Provide guidance on the different AI softwares and tools and their applications.\n## Research Project CollaborationCollaborating on interdisciplinary research projects that require AI or data science expertise.Assist in using other library digital services such as data management and visualization.

EXAMPLE JSON OUTPUT:
[
    {
        "question": "Are there AI consultations for me?",
        "answer": "## Consultations (online / in-person)\nAI Model Development and Training: Assisting in the development, training, and validation of machine learning models for research projects such as:\n- Natural Language Processing (NLP)\n- Supporting text analysis and NLP projects, including sentiment analysis, topic modeling, and classification. TIme-Series data analysis and forecasting. Software and tools: Provide guidance on the different AI softwares and tools and their applications."
    },
    {
        "question": "Can I work with someone on my research project?",
        "answer": "\n## Research Project Collaboration: Collaborating on interdisciplinary research projects that require AI or data science expertise. Assist in using other library digital services such as data management and visualization."
    }
]

I will begin giving you text to process in the next inputs.

"""

def makeNewChat():
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
            "models": ["llama3.1:70b"],
            "messages": [
                {
                    "role": "user",
                    "content": system_prompt,
                    "models": ["llama3.1:70b"],
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

def chatCompletion():
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
        "stream": False,
        "model": "llama3.1:70b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt}
        ],
        "params": {},
        "features": {"image_generation": False, "web_search": False},
        "session_id": "hIrdD0mQs4RLYUedAAEk",
        "chat_id": chatId,
        "background_tasks": {"title_generation": True, "tags_generation": True},
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        print("Chat Completion Good")
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")

data = makeNewChat()
chatId = data["id"]
page_count = 0
questions_count = 0

# Convert JSON response to csv QApairs.json
with open("search_output.json", 'r') as all_text:
    texts_to_process = json.load(all_text)

for current_text in texts_to_process:
    input_prompt = current_text
    recieved = chatCompletion()
    LLMresponse = recieved['choices'][page_count]['message']['content']
    print(LLMresponse)
    
    # NOTE: Loading LLMresponse as json doesnt work because the scraped text has a lot of literal newline characters '\n' for formatting's sake
    # and the LLM makes that into an actual new line in its response, breaking the json format. Giving it explicit instruction not to do so doesnt work either
    # Just review the responses by printing the response for now

    """"
    data = json.loads(LLMresponse) 

    # Writing to CSV file QAChat.csv
    with open(OUTPUT_CSV, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["question", "answer"])
        
        # Write header only if the file is empty
        if file.tell() == 0:
            writer.writeheader()
        
        for item in data:
            writer.writerow(item)
            questions_count += 1
    page_count += 1
print(f"Completed {questions_count} QA pairs for page {page_count}")
    """
