import os
import shutil
import yaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString, LiteralScalarString
# Configuration
IGNORE_INTENTS = {"choose_number", "ask_library_open"}  # Intents to keep as-is
DOMAIN_FILE = "../Chatbot/domain.yml"
RULES_FILE = "../Chatbot/data/rules.yml"
NLU_FILE = "../Chatbot/data/nlu.yml"
BACKUP_DIR = "backup"

# Create backup before modifying files
def backup_files():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for file in [DOMAIN_FILE, RULES_FILE, NLU_FILE]:
        shutil.copy(file, os.path.join(BACKUP_DIR, os.path.basename(file)))

# Modify domain.yml
def modify_domain():
    #yaml = YAML()
    with open(DOMAIN_FILE, "r") as f:
        domain = yaml.safe_load(f)

    # Backup responses and actions from ignored intents
    responses = {}
    actions = []

    for intent in list(domain.get("intents", [])):
        if intent in IGNORE_INTENTS:
            continue

        # Create utterances for the new FAQ format
        response_name = f"utter_faq/{intent}"
        responses[response_name] = [{"text": f"{{{{ utter_{intent} }}}}" }]
        actions.append(response_name)

    # Replace intents with faq and add ResponseSelector
    domain["intents"] = list(IGNORE_INTENTS) + ["faq"]
    domain["responses"] = {**domain.get("responses", {}), **responses}
    domain["actions"] = list(set(domain.get("actions", []) + actions))

    with open(DOMAIN_FILE, "w") as f:
        yaml.dump(domain, f, default_flow_style=False)

# Modify rules.yml
def modify_rules():
    with open(RULES_FILE, "r") as f:
        rules = yaml.safe_load(f)

    new_rules = []

    for rule in rules.get("rules", []):
        intent = rule["steps"][0]["intent"]
        if intent in IGNORE_INTENTS:
            new_rules.append(rule)
        else:
            # Use ResponseSelector for FAQ intents
            new_rule = {
                "rule": f"Respond to {intent} using ResponseSelector",
                "steps": [
                    {"intent": "faq"},
                    {"action": f"utter_faq/{intent}"}
                ]
            }
            new_rules.append(new_rule)

    with open(RULES_FILE, "w") as f:
        yaml.dump({"rules": new_rules}, f, default_flow_style=False)
"""
# Modify nlu.yml
def modify_nlu():
    yaml = YAML()
    with open(NLU_FILE, "r") as f:
        data = yaml.load(f)

    examples_list = []

    new_nlu = []
    for item in data["nlu"]:
        if item["intent"] in IGNORE_INTENTS:
            new_nlu.append(item)
        else:
            intent = item["intent"]
            examples = [line.strip()[2:] for line in item["examples"].splitlines() if line.strip().startswith("-")]
            examples = "\n- ".join(examples)
            examples = "- " + examples
            examples_list.append(f"\n# {intent}\n{examples}")
    faq_examples = LiteralScalarString(("\n".join(examples_list)).strip())
    faq_intent = {
        "intent": "faq",
        "examples": faq_examples
    }
    new_nlu.append(faq_intent)

    with open(NLU_FILE, "w") as f:
        yaml.dump({"nlu": new_nlu}, f)
"""

# Modify nlu.yml
def modify_nlu():
    yaml = YAML()
    with open(NLU_FILE, "r") as f:
        data = yaml.load(f)

    examples_list = []

    new_nlu = []
    for item in data["nlu"]:
        if item["intent"] in IGNORE_INTENTS:
            new_nlu.append(item)
        else:
            intent = item["intent"]
            examples = [line.strip()[2:] for line in item["examples"].splitlines() if line.strip().startswith("-")]
            examples = "\n- ".join(examples)
            examples = "- " + examples
            #examples_list.append(f"\n# {intent}\n{examples}") # TODO: Recreate file with comment showing intent. Intent should not be indented like the examples list
            examples_list.append(examples)
    faq_examples = LiteralScalarString(("\n".join(examples_list)).strip())
    faq_intent = {
        "intent": "faq",
        "examples": faq_examples
    }
    new_nlu.append(faq_intent)

    with open(NLU_FILE, "w") as f:
        yaml.dump({"nlu": new_nlu}, f)
    
# Run the conversion
def main():
    #print("Backing up files...")
    #backup_files()

    #print("Modifying domain.yml...")
    #modify_domain()

    #print("Modifying rules.yml...")
    #modify_rules()

    print("Modifying nlu.yml...")
    modify_nlu()

    print("Conversion to ResponseSelector complete")
    #print(f"Original files backed up in '{BACKUP_DIR}'.")

if __name__ == "__main__":
    main()
