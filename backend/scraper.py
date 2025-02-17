import bs4
import requests
import json
import re # regex


QUEUE_FILE = "queue.csv"

# Starting point 
URL = "https://sc.edu/about/offices_and_divisions/university_libraries/find_services/digital_research_services/ai_data_science_support/index.php"

# The https prefix to only include website links
PREFIX ="https"

# Template to use for usc related websites search so we dont get info outside of usc
TEMP = "sc.edu"

# Extra keywords that must be present in the url so we dont follow links outside of the library
KEYWORD = (
  "library",
  "libraries"
)

# Links we dont want to search inside. Give the user these links to explore the page on their own
IGNORE_LINKS = (
  "https://libcal.library.sc.edu/appointments/",
  "https://libcal.library.sc.edu/calendar/workshops",
)

# The list of the texts
text_list = []
# Links we've been to
checked_links = set()
added_text = set()


num_to_run = int(input("Give the number of links you want to complete"))

# Saving the queue of links that haven't been searched
def save_queue(q_links):
  with open("queue.csv", "w") as f:
    f.write(", ".join(q_links))
    print("Queue file is written!")

def save_text(text_arr):
  clean_txt = []
  for item in text_arr:
    clean_txt.append(item)
  #print(len(clean_txt))
  for i in range(len(clean_txt)):
    # clean_text = re.sub(r'[^a-zA-Z ]', '', text)
    clean_txt[i] = re.sub(r'[^a-zA-Z@0-9?!_\-.,;:\' ]', '', clean_txt[i])
    clean_txt[i]= re.sub(r'\s+', ' ', clean_txt[i])
  with open("search_output.json", "a") as f:

    json.dump(clean_txt, f)
    # f.write(", ".join(text_arr))

# Returns page_txt, page_links
def find_page_info(pag_url):
  # Dont search for info on appointments page
  if any(link in pag_url for link in IGNORE_LINKS):
    print(f"Returning. {pag_url} link to be ignored")
    return [], []
  try:
    resp = requests.get(pag_url)
    # print("HERE", resp.text)
  except:
    return [], []
  try:
    txt = resp.content
    soup = bs4.BeautifulSoup(txt,  "html.parser")
    main_content = soup.find('div', {"id" : "main"}) or soup.find('div', class_ = "row") #"s-lg-tab-content")
    links = main_content.find_all('a')
    clean_links = []
  except Exception as e:
    print(f"error getting page info for {pag_url}. Main content is: {main_content}: {e}")
    return [], []
  # Finding all the links in the page
  for link in links:
    clean_links.append(link.get('href'))
  #page_txt = []
  #ps = soup.find_all('p')
  #for p in ps:
    #page_txt.append(p.get_text())
  return clean_links, main_content.get_text() #page_txt

def get_queue():
  with open("queue.csv", "r") as file:
    content = file.read()
    if(not content):
        return []
    else:
        splited = content.split(", ")
        return splited


queue_links = get_queue()
if (not queue_links):
  queue_links = [URL]
  print("setting base url to queue")


# Main loop
counter = 0
while(queue_links):
  link_to_check = queue_links.pop(0) # get link in front of the queue 
  checked_links.add(link_to_check) # Mark as checked
  links, page_txt = find_page_info(link_to_check)
  
  # Move on if page info returned nothing
  if(not links and not page_txt):
    continue
  
  # Save text on the page
  #for item in page_txt:
    #text_list.append(item)
  # Save new links found on the page to queue
  for link in links:
    if (link != None and (not link in checked_links) and (not link in queue_links) and (TEMP in link) and any(kword in link for kword in KEYWORD) and link.startswith(PREFIX)):
      queue_links.append(link)
      
  #for item in page_txt:
    #if (not item in added_text):
  if(page_txt not in added_text):
    added_text.add(page_txt)
    text_list.append(page_txt)
  counter += 1

  # Save every hundred links just in case
  if (counter % 100 ==0):
    save_text(text_list)
    save_queue(queue_links)
    queue_links = get_queue()
    text_list = []
    print(f"Saved up to {counter}th iteration")

  # Completed given number of links. Break.
  if (counter == num_to_run):
    save_text(text_list)
    save_queue(queue_links)
    break
  print(counter, len(queue_links), link_to_check)