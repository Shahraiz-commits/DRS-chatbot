import requests
import uuid
import time
from dotenv import load_dotenv
import os

load_dotenv()
API = str(os.getenv('API_KEY'))

prompt = "explain calculus concisely"

UUID = str(uuid.uuid4())
childrenUUID = str(uuid.uuid4())
chatId = ""

models = {
    0: "yi:9b",
    1: "yi:6b",
    2: "yi:34b",
    3: "wizardlm2:latest",
    4: "wizardcoder:latest",
    5: "tinydolphin:latest",
    6: "wizard-math:latest",
    7: "starcoder:7b",
    8: "starcoder:1b",
    9: "starcoder:3b",
    10: "smollm:latest",
    11: "qwen2.5:7b",
    12: "starcoder:15b",
    13: "qwen2.5:72b",
    14: "qwen2.5:3b",
    15: "qwen2.5:32b",
    16: "qwen2.5:1.5b",
    17: "qwen2.5:14b",
    18: "qwen2.5:0.5b",
    19: "qwen2:latest",
    20: "phi3.5:latest",
    21: "qwen:latest",
    22: "phi:latest",
    23: "phi3:14b",
    24: "orca-mini:7b",
    25: "orca-mini:3b",
    26: "openchat:latest",
    27: "orca-mini:13b",
    28: "moondream:latest",
    29: "mixtral:latest",
    30: "mistral:latest",
    31: "mistral-small:latest",
    32: "llava-llama3:latest",
    33: "llava:13b",
    34: "llama3.2:3b",
    35: "llama3.2:latest",
    36: "llama3.2:1b",
    37: "llama3.1:8b",
    38: "llama3.1:70b",
    39: "llama3.1:405b"
}

model = models[39]
print("Selected model:", model)


def timeStamp():
    return int(time.time())


def timeStampMs():
    return int(time.time() * 1000)


def makeNewChat():
    timestamp = int(time.time())
    timestamp_ms = int(timestamp * 1000)

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
            "models": [model],
            "params": {},
            "history": {
                "messages": {
                    UUID: {
                        "id": UUID,
                        "parentId": None,
                        "childrenIds": [],
                        "role": "user",
                        "content": prompt,
                        "timestamp": timestamp,
                        "models": [model],
                    }
                },
                "currentId": UUID,
            },
            "messages": [
                {
                    "id": UUID,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": prompt,
                    "timestamp": timestamp,
                    "models": [model],
                }
            ],
            "tags": [],
            "timestamp": timestamp_ms,
        }
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        print("New Chat Created")
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")


def viewChat():
    timestamp = int(time.time())

    url = "http://login-theia.rc.sc.edu:3000/api/v1/chats/" + chatId
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer " + API,
        "content-type": "application/json",
        "Referer": "http://login-theia.rc.sc.edu:3000/c/" + chatId,
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    body = {
        "chat": {
            "models": [model],
            "history": {
                "messages": {
                    UUID: {
                        "id": UUID,
                        "parentId": None,
                        "childrenIds": [childrenUUID],
                        "role": "user",
                        "content": prompt,
                        "timestamp": timestamp,
                        "models": [model],
                    },
                    childrenUUID: {
                        "parentId": UUID,
                        "id": childrenUUID,
                        "childrenIds": [],
                        "role": "assistant",
                        "content": "",
                        "model": model,
                        "modelName": model,
                        "modelIdx": 0,
                        "userContext": None,
                        "timestamp": timestamp,
                    },
                },
                "currentId": childrenUUID,
            },
            "messages": [
                {
                    "id": UUID,
                    "parentId": None,
                    "childrenIds": [childrenUUID],
                    "role": "user",
                    "content": prompt,
                    "timestamp": timestamp,
                    "models": [model],
                },
                {
                    "parentId": UUID,
                    "id": childrenUUID,
                    "childrenIds": [],
                    "role": "assistant",
                    "content": "",
                    "model": model,
                    "modelName": model,
                    "modelIdx": 0,
                    "userContext": None,
                    "timestamp": timestamp,
                },
            ],
            "params": {},
            "files": [],
        }
    }

    response = requests.get(url, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        print("View Chat Good")
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
        "Referer": "http://login-theia.rc.sc.edu:3000/c/" + chatId,
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    body = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "params": {},
        "features": {"image_generation": False, "web_search": False},
        "session_id": "hIrdD0mQs4RLYUedAAEk",
        "chat_id": chatId,
        "id": childrenUUID,
        "background_tasks": {"title_generation": True, "tags_generation": True},
    }
    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        print("Chat Completion Good")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def viewPage():
    url = "http://login-theia.rc.sc.edu:3000/api/v1/chats/?page=1"
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer " + API,
        "content-type": "application/json",
        "referer": "http://login-theia.rc.sc.edu:3000/c/" + chatId,
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("View Page Good")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def completed():
    url = "http://login-theia.rc.sc.edu:3000/api/chat/completed"
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer " + API,
        "content-type": "application/json",
        "referer": "http://login-theia.rc.sc.edu:3000/c/b001bbe9-cf29-4bb6-81e2-e3cf139e25d7",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    body = {
        "model": model,
        "messages": [
            {
                "id": chatId,
                "role": "user",
                "content": prompt,
                "timestamp": 1739919955,
            },
            {
                "id": childrenUUID,
                "role": "assistant",
                "content": "",
                "timestamp": 1739919955,
            },
        ],
        "chat_id": "chatId",
        "session_id": "hIrdD0mQs4RLYUedAAEk",
        "id": "childrenId",
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        print("Completed Good")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def separator():
    print("\n-----------")


data = makeNewChat()
chatId = data["id"]
#separator()

viewChat()
#separator()

viewPage()
#separator()

chatCompletion()
#separator()

viewPage()
#separator()

#time.sleep(10)
content = viewChat()
response = content["chat"]["history"]["messages"][childrenUUID]["content"]
print("\nPrompt:", prompt)
print("\nResponse:\n", response)