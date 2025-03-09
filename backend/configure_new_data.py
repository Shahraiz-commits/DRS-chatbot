#import yaml
from ruamel.yaml import YAML
import json

def configure_nlu(intent: str, questions: list):
    yaml = YAML()
    with open("test_nlu.yml", "r", encoding="utf-8") as file:
        data = yaml.load(file)
    
    for index, item in enumerate(data["nlu"]):
        if(item["intent"] == intent):
            questions = "\n- ".join(questions)
            questions = "- " + questions
            item["examples"] += questions + "\n"
            break

    with open("test_nlu.yml", "w", encoding="utf-8") as file:
        yaml.dump(data, file)
    
def main():
    with open("feedback_examples.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        for intent, questions in data.items():
            configure_nlu(intent, list(questions))

if __name__ == "__main__":
    main()
    

#"interlibrary_loan_access_it": [
#"do u guys have loans for books?"
#]
