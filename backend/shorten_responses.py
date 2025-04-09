import requests
import re
from bs4 import BeautifulSoup

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
    links = re.findall(r'\[.*?\]\((https?://.*?)\)', text)
    if links:
        return links[-1]
    else:
        return None

def get_contact_info(link):
    
    # Main page link, return contact info based on keywords
    keywords_mapping = {
        ("digital_scholarship", "a"):
"""
# Contact Digital Scholarhip
[Kate Boyd](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/boyd_kate.php)  
Director of Digital Research Services  
803-777-2249  
[boydkf@mailbox.sc.edu](mailto:boydkf@mailbox.sc.edu)  

[Amie Freeman](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/freeman_amie.php)  
Assistant Head, Acquisitions & Scholarly Communication  
803-777-8280  
[dillarda@mailbox.sc.edu](mailto:dillarda@mailbox.sc.edu)  
""",
        ("ai_data_science_support", "b"):
"""
# Contact AI and Data Science
[Vandana Srivastava](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/srivastava_vandana.php)  
AI/Data Science Specialist  
803-777-5699  
[vandana@sc.edu](mailto:vandana@sc.edu)

### Make an Appointment
[Make an Appointment](https://libcal.library.sc.edu/appointments/vandanasrivastava) to discuss how we might be able to assist with your AI and data science needs.
""",
        ("research_data_management", "c"):
"""
# Contact Research Data Management
[Stacy Winchester](https://sc.edu/about/offices_and_divisions/university_libraries/about/contact/faculty-staff/winchester_stacy.php)  
Research Data Librarian  
803-777-1968  
[winches2@mailbox.sc.edu](mailto:winches2@mailbox.sc.edu)

### Make an Appointment
[Book an appointment](https://libcal.library.sc.edu/appointment/31854) with Stacy Winchester to dicuss your needs.
""",
        ("data_visualization_gis", "d"):
"""
# Contact Data Visualization
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
    
    # Not a main page link, scrape the page to find out what department to contact for help    
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

    # Split on punctuation not inside links
    raw_sentences = re.split(r'(?<=[.!?])\s+', protected_text)

    # Restore links back
    restored_sentences = []
    for sentence in raw_sentences:
        for i, link in enumerate(links):
            sentence = sentence.replace(f"__LINK{i}__", link)
        restored_sentences.append(sentence.strip())

    # Stop collecting if we find a heading
    selected = []
    for sentence in restored_sentences:
        if sentence.startswith('#'):
            break
        selected.append(sentence)
        if len(selected) >= max_sentences:
            break

    return "\n".join(selected)

def summarize(response: str):
    learn_more_link = get_learn_more_link(response)
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
    if(not first_paragraph.endswith(learn_more_link_formatted)):
        summarized_text = learn_more_link_formatted
    summarized_text += "\n" + contact_info
    summarized_text = heading + "\n" + first_paragraph + "\n" + summarized_text
    return summarized_text
    
def main():
    rasa_endpoint = "http://localhost:5005/webhooks/rest/webhook"
    response = chat_with_rasa("Do I need to share my research data?", rasa_endpoint)
    print(f"RESPONSE---------------------------------------------\n{response}\nSUMMARIZED----------------------------------------{summarize(response)}")

if __name__ == "__main__":
    main()