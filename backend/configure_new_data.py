#import yaml
from ruamel.yaml import YAML
import json

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
    with open("feedback_examples.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        for intent, questions in data.items():
            configure_nlu(intent, list(questions))

if __name__ == "__main__":
    main()
