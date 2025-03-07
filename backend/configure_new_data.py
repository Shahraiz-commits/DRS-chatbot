import yaml
import json

# NOTE: yaml doesnt have a newline after last entry (last intent) but does between intents
def configure_nlu(intent: str, questions: list):
    last_item = False # Track if we're at the last item in the nlu file
    #try:
    with open("test_nlu.yml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
        
    for index, item in enumerate(data["nlu"]):
        if(index == len(data["nlu"]) -1):
            last_item = True
        if(item["intent"] == intent):
            if(last_item):
                item["examples"] += "\n"
            item["examples"] = item["examples"].splitlines()    
            item["examples"].extend(questions)
            #print(item["examples"])
            break
    with open("test_nlu.yml", "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, default_flow_style=False, allow_unicode=True)
        #print(f"Added examples:\n{yaml_str}\n\nTo intent: {intent}\n-------------------------------\n")
    #except Exception as e:
        #print("Could not add examples to intent: " + str(e))
        #return

def main():
    with open("feedback_examples.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        for intent, questions in data.items():
            configure_nlu(intent, questions)

if __name__ == "__main__":
    main()
    

#"interlibrary_loan_access_it": [
#"do u guys have loans for books?"
#]
