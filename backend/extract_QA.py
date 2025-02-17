from openai import OpenAI
import json
import requests
import os


user_prompt = "The library offers support with the application of AI and Machine learning ML tools for your research and projects. You can also receive guidance on the safe and responsible usage of generative AI GenAI for your research, teaching, and learning.GuidesWelcome to the world of Artificial Intelligence AI: This guide introduces AI and its subfields along with some terminology associated with it.Artificial Intelligence Basic Knowledge, Tools, and Resources:A starting point for information about AI, Generative AI, and more.Text Analysis: Find tools and information about TDM or text mining and analysis.Consultations online in-personAI Model Development and Training: Assisting in the development, training, and validation of machine learning models for research projects such as:Natural Language Processing NLP: Supporting text analysis and NLP projects, including sentiment analysis, topic modeling, and classification.TIme-Series data analysis and forecasting.Software and tools: Provide guidance on the different AI softwares and tools and their applications.WorkshopsWorkshops on AI and Data Science Tools: Conducting workshops on popular tools and platforms, such as Python, R, TensorFlow.AIMachine learning: Offering training to improve data literacy covering topics like data ethics, data management, and basic analysis techniques.AI Ethics and Responsible AI: Educating the academic community on the ethical implications of AI, including bias, fairness, and transparency.GenAI: Usage of GenAI for research and learning.Research Project CollaborationCollaborating on interdisciplinary research projects that require AI or data science expertise.Assist in using other library digital services such as data management and visualization.ContactVandana SrivastavaAIData Science Specialist Phone: 803-777-5699Email: vandana@sc.edu"
system_prompt = """
You are a question-answer pair generator for the development of training data for a library chatbot. I will provide some text, which you will then use to create appropriate question-answer pairs with.
Please limit the creation of questions so that each question covers as much relevant information as possible, with minimal overlap with the answers of other questions you may generate.
The questions should be sufficient in relaying all information presented within the text.

Please create questions and answers and output them in JSON format. 

EXAMPLE INPUT: 
Consultations (online / in-person)AI Model Development and Training: Assisting in the development, training, and validation of machine learning models for research projects such as:Natural Language Processing (NLP): Supporting text analysis and NLP projects, including sentiment analysis, topic modeling, and classification.TIme-Series data analysis and forecasting.Software and tools: Provide guidance on the different AI softwares and tools and their applications.Research Project CollaborationCollaborating on interdisciplinary research projects that require AI or data science expertise.Assist in using other library digital services such as data management and visualization.

EXAMPLE JSON OUTPUT:
[
    {
        "question": "Are there AI consultations for me?",
        "answer": "AI Model Development and Training: Assisting in the development, training, and validation of machine learning models for research projects such as: Natural Language Processing (NLP): Supporting text analysis and NLP projects, including sentiment analysis, topic modeling, and classification. TIme-Series data analysis and forecasting. Software and tools: Provide guidance on the different AI softwares and tools and their applications."
    },
    {
        "question": "Can I work with someone on my research project?",
        "answer": "Research Project Collaboration: Collaborating on interdisciplinary research projects that require AI or data science expertise. Assist in using other library digital services such as data management and visualization."
    }
]
"""

# DEEPSEEK ------------------ Api servers down
""" 
client = OpenAI(api_key=os.environ.get("deepseek-api-key"), base_url="https://api.deepseek.com")

messages = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    stream=False,
    response_format={
        'type': 'json_object'
    }
)

print(json.loads(response.choices[0].message.content))
"""
# AWANLLM -------------------- Api servers down
AWAN_API_KEY = os.environ.get("awanLLM_api_key")
MODEL_NAME = "Meta-Llama-3-8B-Instruct"
url = "https://api.awanllm.com/v1/chat/completions"

payload = json.dumps({
  "model": MODEL_NAME,
  "messages": [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}],
  "repetition_penalty": 1.1,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "max_tokens": 4000,
  "stream": False
})
headers = {
  'Content-Type': 'application/json',
  'Authorization': f"Bearer {AWAN_API_KEY}"
}

response = requests.request("POST", url, headers=headers, data=payload)
if response.status_code != 200:
    print(f"Error {response.status_code}: {response.text}")  # Print response details
else:
    print(response.json())