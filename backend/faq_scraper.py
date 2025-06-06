import bs4
from selenium import webdriver
from selenium.webdriver.common.by import By
#import chromedriver_binary # sets PATH for driver automatically
import time
import csv
import re

"""IMPORTANT. If selenium doesnt run RUN COMMAND: pip install chromedriver-binary-auto
This installs the correct chromedriver for you so selenium can use it (uncomment the driver import)
Need selenium to access dynamically loaded javascript content (FAQs)"""


# Return all stored faq links
def get_links():
    try:
        with open("backend/faq_links.csv", "r") as f: # read all links
            links = f.read().splitlines()
    except FileNotFoundError:
        links = []
    return links

# If link isnt already stored, save it to faq_links.csv
def save_link(link):
    existing_links = get_links()
    
    with open("backend/faq_links.csv", "a") as f:
        if link not in existing_links:
            f.write(link + '\n')
            print(f"added link {link}")
            return True
        else:
            print(f"link already exists: {link}")
            return False
            
# Save the fetched question answer pairs into the given file
def save_QA(questions, answers, filePath):
    with open(filePath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # zip pairs each question with its corresponding answer and loops through both lists (questions and answers) simultaneously
        for question, answer in zip(questions, answers):
            # Write the question and answer as a row in the CSV
            writer.writerow([question, answer])
    
# Keep hyperlinks/headers intact in answers    
def configure_text(text):
    
    # For single a tags, as in for hyperlinks at the end of the answer
    if text.name == 'a':
        # Remove all <span> tags inside the <a> tag. Removes the "Opens in new window" text
        for span in text.find_all('span'):
            span.decompose()  
        
        link_text = text.get_text(strip=True)
        link_href = text.get('href', '#')  # Default to '#' if no href
        #link_text = re.sub(r'Opens\s?in\s?new\s?window', '', link_text, flags=re.IGNORECASE).strip()
        return f"[{link_text}]({link_href})"
    
    # Replace <a> tags with markdown links
    for a_tag in text.find_all('a'):
        link_text = a_tag.get_text()
        link_href = a_tag.get('href')
        markdown_link = f"[{link_text}]({link_href})"
        
        # Replace the <a> tag with the Markdown formatted link text
        a_tag.replace_with(markdown_link)

    # Format headers correctly for markdown
    for h_tag in text.find_all('h'):
        header_text = h_tag.get_text()
        opening_tag = f"<{h_tag.name}>"
        closing_tag = f"</{h_tag.name}>"
        formatted_header = f"{opening_tag}{header_text}{closing_tag}"
        h_tag.replace_with()

    return text.get_text()

# Gets the valid question since the DRS faq pages are inconsistent
def get_valid_question(soup):
    headers = soup.find_all(['h1', 'h2'])
    
    # Iterate through headers and find the first valid question
    for header in headers:
        header_text = header.text.strip()
        if header_text.startswith("Q."):
            header_text = header_text[2:].strip()
            return header_text
        elif "FAQ" not in header_text:
            return header_text
    return None  # No question found (shouldnt happen)

# Starting point
URL = "https://libanswers.library.sc.edu/search"

# Prefix for faq links
faq_prefix = "https://libanswers.library.sc.edu/"

driver = webdriver.Chrome()
driver.get(URL)

time.sleep(3)  # Wait for JavaScript to load content
links_to_be_processed = [] # links we havent checked
page_count = 1 # The faq page we're currently on

# Iterate over each page looking for faqs
while True:

    soup = bs4.BeautifulSoup(driver.page_source, "html.parser")
    list = soup.find('ul', class_ = "list-unstyled s-srch-results") # The list containing faqs
    list_items = list.find_all("li", class_ = "s-srch-result") # Elements within this list containing a question

    complete_links = []
    for item in list_items: 
        link_suffix = item.find("a").get('href')
        complete_link = faq_prefix + link_suffix
        complete_links.append(complete_link)
        
    for link in complete_links:
        # If link hasnt been seen before, store it for processing to extract question-answer pairs
        if(save_link(link)):
            links_to_be_processed.append(link)
    
    try:   
        next_button = driver.find_element(By.XPATH, '//a[@data-page and contains(text(), ">")]')
        next_button.click()  # Click ">" to go to the next page
        time.sleep(2)  # Wait for content to load
    except:
        print(f"Went through {page_count} faq pages. No more pages left")
        break
    page_count+=1


print(f"Total number of FAQs found is {len(get_links())}")

# Extract questions and answers for each faq
faq_links = get_links()
full_answer = "" # The complete answer for a faq
all_questions = []
all_answers = []
count = 1
# use: links_to_be_processed
for link in links_to_be_processed:
    print(f"running question {count} faq: {link}")
    full_answer = ""
    driver.get(link) # The faq webpage
    time.sleep(0.5)  # Wait for JavaScript to load content
    soup = bs4.BeautifulSoup(driver.page_source, "html.parser")
    
    question = get_valid_question(soup)   
    answerDIV = soup.find('div', class_ = "s-la-faq-answer-body") or soup.find('div', class_ = "s-la-faq-answer")

    for element in answerDIV.contents:
        if(element.name):
            element = configure_text(element)
            full_answer += element + '\\n'
    
    full_answer += '\n' # Seperate links from main body of answer
    
    # Hyperlinks relevant to the answer
    try:
        answerLinksDIV = soup.find('div', class_ = "s-la-faq-links")
        answer_links = answerLinksDIV.find_all('a')
        for a in answer_links:
            a = configure_text(a)
            #print(f"hyper link: {a}")
            full_answer += a + '\n'
    except Exception as e:
        print(f"No extra links error: {e}")
         
    full_answer = re.sub(r'[“”"]', '', full_answer) # Remove unnecessary double quotes/curly quotes from answer. Messes with yaml syntax
    full_answer = re.sub(r'[ \t]+', ' ', full_answer)  # Remove extra spaces/tabs
    full_answer = re.sub(r'[\u00A0\u2000-\u200B\u202F\u205F\u3000]', ' ', full_answer) # Remove non-breaking spaces and other unicode spaces that break yaml
    full_answer = re.sub(r'\n+', '\n', full_answer)  # Replace multiple new lines with a single new line
    full_answer += '\n' + "[Learn more here](" + link + ")"
    
    
    #print(f"FAQ {count} LINK: {link}")
    #print(f"Question: {question},Answer: {full_answer}\n")
    all_questions.append(question)
    all_answers.append(full_answer)
    count +=1

# Save question answer pairs to:
botFile = "data/input/Chat.csv" # For pushing to bot
testFile = "backend/faq_QA.csv" # For testing
save_QA(all_questions, all_answers, botFile)