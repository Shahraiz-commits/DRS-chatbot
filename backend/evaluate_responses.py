
from llm_paraphraser import chat_with_model
import requests
import os
from dotenv import load_dotenv
import json
import pandas as pd
import json
import matplotlib.pyplot as plt

def chat_with_rasa(question, rasa_endpoint):
    payload = {"message": question}
    headers = {"Content-Type": "application/json"}
    response = requests.post(rasa_endpoint, json=payload, headers=headers)
    
    if response.status_code == 200:
        responses = response.json()
        if responses and isinstance(responses, list) and len(responses) > 0:
           return responses[0].get("text", "No response").replace("\n", " ")
        return "No response"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "Error"

def generate_questions(api_token):
    base_questions = [
        "I am interested in creating a web site. Does the Library have support for this?",
        "I need help organizing my data",
        "I'd like to share my research with the public. How can I do this?",
        "How do I create a map with my data?",
        "Are there workshops on data vizualization in the Libraries?",
        "How do I start with research data management?",
        "How does machine learning work?",
        "What are the applications of AI?",
        "digital scholarship services available",
        "who can help me with visualization",
    ]
    
    variations = []
    system_prompt = "Generate 5 diverse variations of the following question for AI chatbot testing. Output only a list of the variations and nothing else."
    
    for question in base_questions:
        generated_variations = chat_with_model(api_token, system_prompt, question)
        if generated_variations:
            variations.extend(generated_variations.split("\n"))
    
    return variations
def evaluate():
    load_dotenv(".env")
    api_token = os.getenv("LLM_API_KEY")
    rasa_endpoint = "http://localhost:5005/webhooks/rest/webhook"

    print("Generating test questions...")
    questions = generate_questions(api_token)
    print(f"Testing Rasa bot with {len(questions)} questions...")
    results = []

    for i, question in enumerate(questions, 1):
        response = chat_with_rasa(question, rasa_endpoint)
        results.append({"question": question, "response": response})
        print(f"{i}. {question} -> {response}")

    with open("rasa_test_results.json", "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)
        
    with open("rasa_test_results.json", "r", encoding="utf-8") as file:
        results = json.load(file)
    df = pd.DataFrame(results)
    df["status"] = "Unmarked"
    df.to_csv("rasa_responses_with_status.csv", index=False)
    
def plot():
    df = pd.read_csv("rasa_responses_with_status.csv")
    # Map status codes to full labels and colors
    status_mapping = {"g": "Correct", "r": "Incorrect", "b": "Recovered"}
    color_mapping = {"g": "green", "r": "red", "b": "blue"}

    df["status"] = df["status"].map(status_mapping)
    status_counts = df["status"].value_counts()

    plt.figure(figsize=(8, 5))
    status_counts.plot(kind="bar", color=[color_mapping.get(k) for k in status_mapping])

    plt.xlabel("Response Category")
    plt.ylabel("Number of Responses")
    plt.title("Rasa Response Accuracy")
    plt.xticks(rotation=0)
    plt.show()

def main():
    evaluate()
    plot()
    
if __name__ == "__main__":
    main()