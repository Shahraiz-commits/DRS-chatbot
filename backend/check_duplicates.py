from sentence_transformers import SentenceTransformer, util
import pandas as pd
import warnings
import csv
import re
import yaml
from dotenv import load_dotenv
from ruamel.yaml import YAML
import os
from configure_new_data import configure_domain, configure_nlu
warnings.filterwarnings("ignore")

def generalize_intents(domain_data, target_intents, ignore_intents):
    """
    Iterates through a list of target intents and finds the most semantically similar
    intent for each one among intents with the same [Learn more here](...) link.
    Then uses an LLM to merge the responses in contextual order.
    """
    responses = domain_data.get("responses", {})
    link_pattern = r'\[Learn more here\]\((.*?)\)'

    model = SentenceTransformer("stsb-roberta-base")

    for target_intent in target_intents:
        # Get the target response
        target_key = f"utter_{target_intent}"
        target_response = responses.get(target_key, [""])
        target_response = target_response[0]["text"]

        # Extract the "Learn more" link
        target_link_match = re.search(link_pattern, target_response)

        if not target_link_match:
            print(f"No link found in target intent: {target_intent}")
            continue

        target_link = target_link_match.group(1)
        # Find intents with the same link
        matching_intents = []
        for key, value in responses.items():
            if key == target_key:
                continue

            response = str(value[0]["text"])
            link_match = re.search(link_pattern, response)

            if link_match and link_match.group(1) == target_link:
                intent = key.replace("utter_", "")
                if intent not in ignore_intents:
                    matching_intents.append((intent, response))

        if "faq" in target_link:  # Ignore FAQs. They are meant to be short.
            continue
        if not matching_intents:
            print(f"No matching intents with the same link as '{target_intent}'")
            continue

        # Calculate semantic similarity
        target_text = re.sub(link_pattern, '', target_response).strip()
        target_embedding = model.encode(target_text, convert_to_tensor=True)

        similarities = []
        for intent, response in matching_intents:
            comparison_text = re.sub(link_pattern, '', response).strip()
            comparison_embedding = model.encode(comparison_text, convert_to_tensor=True)

            # Use util.pytorch_cos_sim for similarity calculation
            similarity = util.pytorch_cos_sim(target_embedding, comparison_embedding).item()

            similarities.append((intent, response, similarity))

        # Find the most semantically similar intent
        most_similar_intent, most_similar_response, max_similarity = max(similarities, key=lambda x: x[2])

        target_response = re.sub(r'\n?\[Learn more here\]\(.*?\)', '', target_response)
        merged_response = f"{target_response}{most_similar_response}"
        
        target_examples = get_intent_examples(target_intent)
        #configure_domain("modify", most_similar_intent, merged_response) # Overwrite the response of this intent to be the merged response
        #configure_domain("remove", target_intent) # Remove the short response from domain
        #configure_nlu("modify", most_similar_intent, target_examples) # Add to this intent's examples, the examples from short response
        #configure_nlu("remove", target_intent) # Remove the short response from nlu
        
        print(f"\nMerged {target_intent} into {most_similar_intent}:\n{merged_response}\n-------------------------------------------------------------------------------------------------------------------------------------------")
        
        #print(f"\nMost similar intent to '{target_intent}' with the same link: '{most_similar_intent}'")
        #print(f"Link: {target_link}")
        #print(f"Similarity score: {max_similarity:.4f}")
        #print(f"\nMerged Response:\n{merged_response}\n--------------------------------------------------")
        
def get_intent_examples(intent: str):
    """
    Retrieves all examples associated with a specific intent from the NLU file.
    """
    nlu_file = "../Chatbot/data/nlu.yml"
    yaml = YAML()

    with open(nlu_file, "r", encoding="utf-8") as file:
        data = yaml.load(file)

    examples = []

    for item in data.get("nlu", []):
        if item.get("intent") == intent:
            examples.extend(item.get("examples", "").split("\n- ")[1:])
                
    return examples

def main():
    #model = SentenceTransformer("stsb-roberta-base") # model suitable for semantic similarity
    IGNORE_INTENTS = {
        "greet",
        "iamabot",
        "Do not answer"
    }
    with open("../Chatbot/domain.yml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
        
    target_intents = []

    # Generalize each intent with a short response
    for key, value in data["responses"].items():
        response = re.sub(r'\n?\[Learn more here\]\(.*?\)', '', str(value)).strip()
        intent = key.replace("utter_", "")
        if(len(response) <= 300 and intent not in IGNORE_INTENTS and "Contact Us" not in response):
            target_intents.append(intent)
    generalize_intents(data, target_intents, IGNORE_INTENTS)
    
if __name__ == "__main__":
    main()
