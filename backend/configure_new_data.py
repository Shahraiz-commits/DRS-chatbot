#import yaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString, LiteralScalarString
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
import json

# Finds the intent and adds questions to its examples Or removes an intent along with its examples
def configure_nlu(action: str, intent: str, questions: list = []):
    OUTPUT_FILE = "../Chatbot/data/nlu.yml"
    yaml = YAML()
    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        data = yaml.load(file)
        
    if(action == "remove"):
        for index, item in enumerate(data["nlu"]):
            if(item["intent"] == intent):
                del data["nlu"][index]
                remove_rule(intent) # Remove the corresponding rule entry for this intent
                break
    elif(action == "modify"):
        for index, item in enumerate(data["nlu"]):
            if(item["intent"] == intent):
                questions = "\n- ".join(questions)
                questions = "- " + questions
                #item["examples"] += questions + "\n"
                
                # Merge the questions without adding unnecessary newlines
                new_examples = item["examples"].strip() + "\n" + questions
                # Use LiteralScalarString to enforce the `|` symbol only
                item["examples"] = LiteralScalarString(new_examples.strip())
                
                break

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        yaml.dump(data, file)

def remove_rule(target_intent):
    rules_file = "../Chatbot/data/rules.yml"
    yaml = YAML()
    with open(rules_file, "r", encoding="utf-8") as file:
        data = yaml.load(file)
    
    for index, item in enumerate(data["rules"]):
        current_intent = item["steps"][0]["intent"]
        if(current_intent == target_intent):
            del data["rules"][index]
    
    with open(rules_file, "w", encoding="utf-8") as file:
        yaml.dump(data, file)

# Remove intents from domain file or change the response of an intent in the file
def configure_domain(action: str, intent: str, new_response: str = ""):
    """
    action: remove or modify
    intent: The intent to be removed, OR The intent that will hold the new response
    new_response: The new response to store
    """
    yaml = YAML()
    domain_file = "../Chatbot/domain.yml"
    with open(domain_file, "r", encoding="utf-8") as file:
        data = yaml.load(file)

    if(action == "remove"):
        # Remove the intent
        if "intents" in data and intent in data["intents"]:
            data["intents"].remove(intent)

        # Remove the response linked to the intent
        if "responses" in data and f"utter_{intent}" in data["responses"]:
            del data["responses"][f"utter_{intent}"]

    elif(action == "modify"):
        if "responses" in data:
            main_response_key = f"utter_{intent}"
        
            # Overwrite the response with the merged one
            data["responses"][main_response_key] = [{"text": PreservedScalarString(new_response)}]
            
    with open(domain_file, "w", encoding="utf-8") as file:
        yaml.dump(data, file)   
        
    
def main():
    cred = credentials.Certificate(cert="../Chatbot/actions/firebase_service_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    ASSIGNED_QS_PATH = "assigned_questions.json"
    # Keep track of added questions locally for reference/backup
    if(os.path.getsize(ASSIGNED_QS_PATH) != 0):
        with open(ASSIGNED_QS_PATH, "r", encoding="utf-8") as file:
            json_data = json.load(file)
    else:
        json_data = {}
        
    # Configured automatically
    doc_ref = db.collection("trainingQuestions")
    for doc in doc_ref.get():
        data = doc.to_dict()
        questions = data.get("questions", [])
        if(isinstance(questions, str)):
            questions = [questions]
        
        # Update local file with new questions
        if(doc.id in json_data.items()):
            json_data[doc.id].extend(questions) # Append to existing
        else:
            json_data[doc.id] = questions # new entry
        configure_nlu("modify", doc.id, questions)
        print(f"Added questions for intent: {doc.id}\n Questions: {questions}\n--------------------------------")
        doc.reference.delete()
    
    with open(ASSIGNED_QS_PATH, "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4)

    # Configure these questions manually
    doc_ref = db.collection("unassignedQuestions")
    unassignedQs = []
    for doc in doc_ref.get():
        data = doc.to_dict()
        unassignedQs.append(data.get("question", ""))
        doc.reference.delete()

    with open("unassigned_questions.csv", "a", encoding="utf-8") as file:
        #writer = csv.writer(file)
        for q in unassignedQs:
            file.write(q)
            file.write("\n")
    print(f"Added unassigned questions:\n{unassignedQs}")
    
if __name__ == "__main__":
    main()
