import bs4
import requests
import json
import re # regex


# NOTE: <li> class_ = "next" for navigating sidebar

QUEUE_FILE = "queue.csv"

# Starting point 
URL = "https://sc.edu/about/offices_and_divisions/university_libraries/find_services/digital_research_services/digital_scholarship/index.php"

# The https/http prefix to only include website links
#PREFIX =(
  #"https",
  #"http",
#)

# Template to use for usc related websites search so we dont get info outside of usc
TEMP = "sc.edu"

# Extra keywords that must be present in the url so we dont follow links outside of the library
KEYWORD = (
  "library",
  "libraries"
)

# Links we dont want to search inside. Give the user these links to explore the page on their own
IGNORE_LINKS = (
  "appointments/",
  "appointment/",
  "/workshops",
  "auth/",
  "/calendar"
)

# The list of the texts and their associated links
text_list = []
text_links = []
# Links we've been to
checked_links = set()
added_text = set()


num_to_run = int(input("Give the number of links you want to complete"))

# Saving the queue of links that haven't been searched
def save_queue(q_links):
  with open("queue.csv", "w") as f:
    f.write(", ".join(q_links))
    print("Queue file is written!")

def save_text(text_arr, links_arr):
  
  for i in range(len(text_arr)):
    text_arr[i] = re.sub(r'[“”"]', '', text_arr[i]) # Remove unnecessary double quotes/curly quotes from answer. Messes with yaml syntax
    text_arr[i] = re.sub(r'[ \t]+', ' ', text_arr[i])  # Remove extra spaces/tabs
    text_arr[i] = re.sub(r'[\u00A0\u2000-\u200B\u202F\u205F\u3000]', ' ', text_arr[i]) # Remove non-breaking spaces and other unicode spaces that break yaml
    text_arr[i] = re.sub(r'\n{3,}', '\n', text_arr[i]) # Replace 2 or more new lines with a single new line
    text_arr[i] += '\n\n' + "[Learn more here](" + links_arr[i] + ")"
  
  #print(text_arr[4])
  with open("search_output.json", "a") as f:
    json.dump(text_arr, f)

# Format text to keep headers, hyperlinks etc. intact
def format_text(page_text):
  #print(page_text)
  # Tags we want to keep to process later into markdown
  allowed_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "li", "a", "p", "br"}


  # Remove all tags that are not allowed
  for tag in page_text.find_all():
    if tag.name not in allowed_tags:
      if tag.find_all(allowed_tags):  
        # If the tag contains allowed tags, unwrap it
        tag.unwrap()
      else:
        # If not, remove it along with its content
          tag.decompose()

  # Unwrap <p> tags but keep their content
  for p_tag in page_text.find_all("p"):
    p_tag.unwrap()
  
  # Format headers correctly for markdown
  for h_tag in page_text.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
    header_text = h_tag.get_text(strip=True)
    
    if header_text:  # Process only non-empty headers
        tag_number = h_tag.name[-1]  # Header level (h3 -> "3")
        formatted_header = f"{'#' * int(tag_number)} {header_text}"
        h_tag.replace_with(formatted_header)
    else:
        h_tag.decompose()  # Removes empty headers tag and content
  
  # Replace <a> tags with markdown links
  for a_tag in page_text.find_all('a'):
    link_text = a_tag.get_text()
    link_href = a_tag.get('href')
    markdown_link = f"[{link_text}]({link_href})"
        
    # Replace the <a> tag with the Markdown formatted link text
    a_tag.replace_with(markdown_link)

  
  # Format lists for markdown
  for listItem in page_text.find_all('li'):
    formattedListItem = f"\n- {listItem.get_text(strip=True)}"
    listItem.replace_with(formattedListItem) 
  
  # Replace <br> tags with new lines
  for breakTag in page_text.find_all('br'):
    breakTag.replace_with("\n\n")
  
  # Convert soup object to string so we can apply regex on it
  html_string = "".join(str(tag) for tag in page_text)
  return html_string

# Returns page text and any links found in this page
def find_page_info(page_url):
  # Dont search for info on certain pages
  if any(link in page_url for link in IGNORE_LINKS):
    print(f"Returning. {page_url} link to be ignored")
    return [], []
  
  try:
    resp = requests.get(page_url)
  except:
    return [], []
  try:
    txt = resp.content
    soup = bs4.BeautifulSoup(txt,  "html.parser")
    main_content = soup.find('div', {"id" : "mainContent"}) or soup.find('div', class_ = "s-lg-tab-content") #"row" | soup.find('div', {"id" : "main"}) or 
    links = main_content.find_all('a')
    clean_links = []
  except Exception as e:
    print(f"error getting page info for {page_url}. Main content is: {main_content}: {e}")
    return [], []
  
  # Next page link if there is one
  try:
    next_link = soup.find('li', class_ = "next")
    clean_links.append(next_link.find('a').get('href'))
  except:
    pass
  # Finding all the links in the page
  for link in links:
    clean_links.append(link.get('href'))
  formattedText = format_text(main_content)
  return clean_links, formattedText

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
  
  # Save new links found on the page to queue
  for link in links:
    if (link != None and (not link in checked_links) and (not link in queue_links) and (TEMP in link) and any(kword in link for kword in KEYWORD) and (link.startswith("https") or link.startswith("http"))):
      queue_links.append(link)
      
  #for item in page_txt:
    #if (not item in added_text):
  if(page_txt not in added_text):
    added_text.add(page_txt)
    text_list.append(page_txt)
    text_links.append(link_to_check)
  counter += 1

  # Save every hundred links just in case
  if (counter % 100 ==0):
    save_text(text_list, text_links)
    save_queue(queue_links)
    queue_links = get_queue()
    text_list = []
    text_links = []
    print(f"Saved up to {counter}th iteration")

  # Completed given number of links. Break.
  if (counter == num_to_run):
    save_text(text_list, text_links)
    save_queue(queue_links)
    break
    
  print(counter, len(queue_links), link_to_check)