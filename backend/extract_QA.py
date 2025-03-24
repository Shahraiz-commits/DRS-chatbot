import json
import requests
import os
import csv
import time
from dotenv import load_dotenv
from llm_paraphraser import makeNewChat, chatCompletion
import re
# File that holds the newly created auestion-answer pairs
#RESPONSE_JSON = "QApairs.json"
# File that pairs are saved into as csv
OUTPUT_CSV = "QAChat.csv"

load_dotenv()
API = os.getenv("LLM_API_KEY")

system_prompt = """
You are a question-answer pair generator for the development of training data for a library chatbot. I will provide some text, which you will then use to create appropriate question-answer pairs with.
Please limit the creation of questions so that each question covers as much relevant information as possible.
The questions should be sufficient in relaying all information presented within the text. I.e. the answers altogether should contain ALL of the given text.
If there is significant content that can be coupled together in an answer, create a general, vague question for it. Create specific questions aswell where appropriate with shorter answers, but DO NOT create specific questions where the answers may require additional context not present in the answer.
Do not change the markdown formatting present in the text and ensure all the given text is present in the answers in its entirety. Include any markdown headings and lists etc. Do not omit or change information in the text to shorten the answer in the JSON file.
Limit the number of question-answer pairs to as few as possible, never exceeding 15 per text. Avoid phrasing questions similary and phrase them in a way college students or staff may speak. For example they may say "library" instead of "university library" to save time. Try to make the questions general rather than too specific. Where appropriate, you may opt to create a statement as the question instead of a question with question mark.

Make sure each answer in the question-answer pairs contains [Learn more here](link) at the end of EVERY answer inside the JSON file. This should be included on a seperate line as part of each answer in the pair where the "link" to use will be given at the end of each text once in the format [Learn more here](link). Use the same link at the end of each answer. If you cannot find this learn more link, then leave it, but do not give me a warning.
If you see any escaped new line characters like '\\n', then keep them as such in your answers. Do not omit these.
Do not include "or" or "and" in any question. If you must, seperate the two queries into two questions instead.
Do not give me any added notes.
Please create questions and answers and output them in valid JSON format ONLY. Do not output anything other than the complete JSON file.

EXAMPLE INPUT: 
## Consultations (online / in-person)\\nAI Model Development and Training: Assisting in the development, training, and validation of machine learning models for research projects such as:\\n- Natural Language Processing (NLP)\\n- Supporting text analysis and NLP projects, including sentiment analysis, topic modeling, and classification.TIme-Series data analysis and forecasting.Software and tools: Provide guidance on the different AI softwares and tools and their applications.\\n## Research Project CollaborationCollaborating on interdisciplinary research projects that require AI or data science expertise.Assist in using other library digital services such as data management and visualization.

EXAMPLE OUTPUT:
[
    {
        "question": "Do you have AI consultations",
        "answer": "## Consultations (online / in-person)\\nAI Model Development and Training: Assisting in the development, training, and validation of machine learning models for research projects such as:\\n- Natural Language Processing (NLP)\\n- Supporting text analysis and NLP projects, including sentiment analysis, topic modeling, and classification. TIme-Series data analysis and forecasting. Software and tools: Provide guidance on the different AI softwares and tools and their applications."
    },
    {
        "question": "I wanna work with someone on my project",
        "answer": "\\n\\n## Research Project Collaboration: Collaborating on interdisciplinary research projects that require AI or data science expertise. Assist in using other library digital services such as data management and visualization."
    }
]

"""


data = makeNewChat(API, system_prompt)
chatId = data["id"]

chat_history = [{"role": "system", "content": system_prompt}]
page_count = 0
questions_count = 0

# Convert JSON response to csv QApairs.json
with open("search_output.json", 'r') as all_text:
    texts_to_process = json.load(all_text)
# NOTE: LLM not processing some texts for some reason. Hangs at specific ones it seems.
for current_text in texts_to_process:
    if(page_count < 0): # Start from specific index - missing 21
        page_count += 1
        continue
    input_prompt = current_text
    input_prompt = re.sub(r'\n', '\\n', input_prompt)
    LLMresponse = chatCompletion(API, chatId, system_prompt, input_prompt)
    print(f"RESPONSE --------------------------------------------------------------------------------------------------------------------------------------\
        {LLMresponse}\n")

    #LLMresponse = re.sub(r'\\n', '\n', LLMresponse)
    data = json.loads(LLMresponse) 

    # Writing to CSV file QAChat.csv
    with open(OUTPUT_CSV, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["question", "answer"])
        
        # Write header only if the file is empty
        if file.tell() == 0:
            writer.writeheader()
            
        questions_count = 0
        for item in data:
            writer.writerow(item)
            questions_count += 1
        page_count += 1
    print(f"Completed {questions_count} QA pairs for page {page_count-1}\n\n")
