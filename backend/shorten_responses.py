import requests
import re
from bs4 import BeautifulSoup
from configure_new_data import configure_domain
from ruamel.yaml import YAML
def chat_with_rasa(question, rasa_endpoint):
    payload = {"message": question}
    headers = {"Content-Type": "application/json"}
    response = requests.post(rasa_endpoint, json=payload, headers=headers)
    
    if response.status_code == 200:
        responses = response.json()
        if responses and isinstance(responses, list):
            all_texts = [r.get("text", "") for r in responses if "text" in r]
            return "\n".join(all_texts) if all_texts else "No response"
        return "No response"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "Error"

def get_learn_more_link(text):
    links = re.findall(r'\[Learn more here\]\((https?://.*?)\)', text)
    if links:
        return links[-1]
    else:
        return None

def get_contact_info(link):
    if "faq" in link.lower() or "calendar" in link.lower() or "appointment" in link.lower():
        return
    # Main page link, return contact info based on keywords
    keywords_mapping = {
        ("digital_scholarship", "digital scholarship", "text analysis", "scholar commons: using the institutional repository"):
"""
##### Contact Digital Scholarhip
[Kate Boyd](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/boyd_kate.php)  
Director of Digital Research Services  
803-777-2249  
[boydkf@mailbox.sc.edu](mailto:boydkf@mailbox.sc.edu)  

[Amie Freeman](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/freeman_amie.php)  
Assistant Head, Acquisitions & Scholarly Communication  
803-777-8280  
[dillarda@mailbox.sc.edu](mailto:dillarda@mailbox.sc.edu)  
""",
        ("ai_data_science_support", "welcome to the world of artificial intelligence (ai)! ", "ai (artificial intelligence) knowledge, tools, and resources"):
"""
##### Contact AI and Data Science
[Vandana Srivastava](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/srivastava_vandana.php)  
AI/Data Science Specialist  
803-777-5699  
[vandana@sc.edu](mailto:vandana@sc.edu)

##### Make an Appointment
[Make an Appointment](https://libcal.library.sc.edu/appointments/vandanasrivastava) to discuss how we might be able to assist with your AI and data science needs.
""",
        ("research_data_management", "data management"):
"""
##### Contact Research Data Management
[Stacy Winchester](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/winchester_stacy.php)  
Research Data Librarian  
803-777-1968  
[winches2@mailbox.sc.edu](mailto:winches2@mailbox.sc.edu)

##### Make an Appointment
[Book an appointment](https://libcal.library.sc.edu/appointment/31854) with Stacy Winchester to dicuss your needs.
""",
        ("data_visualization_gis", "data visualization services", "datalab", "data visualization basics"):
"""
##### Contact Data Visualization
[Make an appointment](https://libcal.library.sc.edu/appointments/datavis) to discuss how we might be able to assist with your data visualization needs.  
Glenn Bunton  
Data Visualization Librarian  
803-777-2903  
[buntonga@mailbox.sc.edu](mailto:buntonga@mailbox.sc.edu)
"""
    }

    for keywords, info in keywords_mapping.items():
        if any(keyword in link.lower() for keyword in keywords):
            return info
    
    # Not a main page link, scrape the page header to find out what department to contact for help    
    try:
        response = requests.get(link)
        if(response.status_code == 200):                
            soup = BeautifulSoup(response.text, 'html.parser')
            header = soup.find('h1', id = "s-lg-guide-name")
            
            for keywords, info in keywords_mapping.items():
                if any(keyword == header.text.lower() for keyword in keywords):
                    return info
    except Exception as e:
        print(f"Error fetching {link}: {e}")
        return

def split_sentences(text, max_sentences=4):
    # Find all markdown links so we can ignore their punctuation
    links = re.findall(r'\[.*?\]\(.*?\)', text)

    # Protect links by temporarily replacing them
    protected_text = text
    for i, link in enumerate(links):
        protected_text = protected_text.replace(link, f"__LINK{i}__")

    # Split on punctuation or when a new bullet point starts (- ...)
    raw_sentences = re.split(r'(?<=[.!?])(?=\s|\n|$)|(?=\n\s*-\s)', protected_text)
    #print("\n PARTED".join(raw_sentences) + "\n--------------------------------------------------------------------")

    # Restore links back
    restored_sentences = []
    for sentence in raw_sentences:
        for i, link in enumerate(links):
            sentence = sentence.replace(f"__LINK{i}__", link)
        restored_sentences.append(sentence.strip())

    # Select sentences to use
    selected = []
    for index, sentence in enumerate(restored_sentences):
        if sentence.startswith('#'): # Ignore subheadings, we want everything summarized under a single heading
            continue
            #if(restored_sentences[index+1].startswith("#")):
            #    break
        #print("new sentence " + sentence)
        selected.append(sentence)
        if len(selected) >= max_sentences:
            break

    return "\n".join(selected)

def summarize(response: str):
    learn_more_link = get_learn_more_link(response)
    learn_more_link_formatted = ""
    contact_info = ""
    if(learn_more_link):
        learn_more_link_formatted = f"[Learn more here]({learn_more_link})"
        contact_info = get_contact_info(learn_more_link)
    
    has_heading = re.match(r'^#+', response)
    heading = ""
    if has_heading:
        parts = response.split('\n', 1)  # Split into [heading, rest_of_text]
        heading = parts[0]
        if len(parts) > 1:
            response = parts[1]
        else:
            response = ""  # only heading existed
    first_paragraph = split_sentences(response)
    summarized_text = ""
    if(learn_more_link and (not first_paragraph.endswith(learn_more_link_formatted))):
        summarized_text = learn_more_link_formatted
    if(contact_info):
        summarized_text += "\n" + contact_info.strip()
    summarized_text = heading + "\n" + first_paragraph + "\n\n" + summarized_text
    return summarized_text
    
def modify_data():
    yaml = YAML()
    with open("../Chatbot/domain.yml", "r", encoding="utf-8") as file:
        data = yaml.load(file)
    responses = data["responses"]
    
    TO_IGNORE = ["utter_greet", "utter_iamabot", "utter_Do not answer", "utter_help_digital_tool", "utter_help_ai", "utter_contact_help_research_data", "utter_get_data_visualization_help"]
    for intent, answers in responses.items():
        if intent in TO_IGNORE:
            continue
        for answer in answers:
            #print(answer["text"] + "\n" + intent.replace("utter_", ""))
            curr_intent = intent.replace("utter_", "")
            print(f"INTENT: {curr_intent}")
            new_answer = summarize(answer["text"])
            #print("NEW ANSWER---------------------------------------------------------------------\n" + new_answer)
            configure_domain("modify", intent.replace("utter_", ""), new_answer)

# Changes all headers to level 6 headers
def remove_headers():
    yaml = YAML()
    with open("../Chatbot/domain.yml", "r", encoding='utf-8') as file:
        data = yaml.load(file)
    responses = data["responses"]
    for intent, answers in responses.items():
        for answer in answers:
            response = answer['text']
            has_heading = re.match(r'^#+', response)
            if(has_heading):
                new_response = re.sub(r'^(#+)\s*(.*)', r'###### \2', response, flags=re.MULTILINE) # level 6 headers for all
                #print(f"old:\n{response}\nnew:\n{new_response}")
                configure_domain("modify", intent.replace("utter_", ""), new_response)
    
def main():
    #rasa_endpoint = "http://localhost:5005/webhooks/rest/webhook"
    #response = chat_with_rasa("ai services", rasa_endpoint)
    response ="""## Business Statistics and Data Set Resources
Below are some examples of resources that you can use to find business resources. 
## Statistics
#### International Statistics
- [Fitch Connect](https://saml.fitchconnect.com/saml/login?orgId=6iU4UH3SLU2L51lDBPe9iT)
- [Hoover's Online](https://login.pallas2.tcl.sc.edu/login?url=https://www.mergentonline.com/Hoovers)
- [IMF Data Mapper](http://www.imf.org/external/datamapper/index.php)Interactive tool for various time periods by country, regions, or analytical groupsTIP: Population and unemployment are under World Economic Outlook dataset
- [OECD iLibrary Statistics](https://www.oecd-ilibrary.org/statistics)
- [OSHA Statistics and Data](https://www.osha.gov/oshstats/)

[Learn more here](https://guides.library.sc.edu/data-and-statistics/cj)"""
    #print(f"\nSUMMARIZED----------------------------------------\n{summarize(response)}")
    #print(chr(sum(range(ord(min(str(not()))))))) # Prints among us character ඞ
    
    #modify_data()
    #remove_headers()
if __name__ == "__main__":
    main()