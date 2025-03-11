#import yaml
from ruamel.yaml import YAML
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import csv

# Finds the intent and adds questions to its examples
def configure_nlu(intent: str, questions: list):
    OUTPUT_FILE = "../Chatbot/data/nlu.yml"
    yaml = YAML()
    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        data = yaml.load(file)
    
    for index, item in enumerate(data["nlu"]):
        if(item["intent"] == intent):
            questions = "\n- ".join(questions)
            questions = "- " + questions
            item["examples"] += questions + "\n"
            break

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        yaml.dump(data, file)
    
def main():
    cred = credentials.Certificate(cert="../firebase_service_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Configured automatically
    doc_ref = db.collection("trainingQuestions")
    for doc in doc_ref.get():
        data = doc.to_dict()
        questions = data.get("questions", [])
        if(isinstance(questions, str)):
            questions = [questions]
        configure_nlu(doc.id, questions)
        print(f"Added questions for intent: {doc.id}\n Questions: {questions}\n--------------------------------")
        doc.reference.delete()

    # Configure these questions manually
    doc_ref = db.collection("unassignedQuestions")
    unassignedQs = []
    for doc in doc_ref.get():
        data = doc.to_dict()
        unassignedQs.append(data.get("question", ""))
        doc.reference.delete()

    with open("unassigned_questions.csv", "a", encoding="utf-8") as file:
        writer = csv.writer(file)
        for q in unassignedQs:
            file.write(q)
            file.write("\n")
    print(f"Added unassigned questions:\n{unassignedQs}")
if __name__ == "__main__":
    main()
