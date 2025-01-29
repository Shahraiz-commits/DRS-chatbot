import bs4
import requests
import json
import re # regex

# The file that link queues are saved to
QUEUE_FILE = "queue.csv"
# DRS starting point 
URL = "https://sc.edu/about/offices_and_divisions/university_libraries/find_services/digital_research_services/"

# The https prefix to only include website links
PREFIX ="https"

# Template to use for usc related websites search so we dont get info outside of usc
TEMP = "sc.edu"

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
  try:
    resp = requests.get(pag_url)
    # print("HERE", resp.text)
  except:
    return [], []
  try:
    txt = resp.text
    soup = bs4.BeautifulSoup(txt,  "html.parser")
    links = soup.find_all('a')
    clean_links = []
  except:
    return [], []
  # Finding all the links in the page
  for link in links:
    clean_links.append(link.get('href'))
  page_txt = []
  ps = soup.find_all('p')
  for p in ps:
    page_txt.append(p.get_text())
  return clean_links, page_txt

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
  print(link_to_check)
  checked_links.add(link_to_check) # Mark as checked
  links, page_txt = find_page_info(link_to_check)
  # Save text on the page
  for item in page_txt:
    text_list.append(item)
  # Save new links found on the page to queue
  for link in links:
    if (link != None and (not link in checked_links) and (not link in queue_links) and (TEMP in link) and link.startswith(PREFIX)):
      queue_links.append(link)
      
  for item in page_txt:
    if (not item in added_text):
      added_text.add(item)
      text_list.append(item)
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