from sentence_transformers import SentenceTransformer, util
import pandas as pd
import warnings
import csv
warnings.filterwarnings("ignore")

# Initialize the model
model = SentenceTransformer("stsb-roberta-base") # model suitable for semantic similarity

# Load DataFrame
dataframe = pd.read_csv('test_dupes_QA.csv')
questions = dataframe['Question']
answers = dataframe['Answer']
checked_questions = set()
ignore_questions = [] # Keep track of questions that are duplicates so we dont process them for similarity with anything
# Iterate over all questions
for index in range(len(questions)):
    current_question = questions[index]
    current_answer = answers[index]
    
    if((current_question in ignore_questions) or (current_question in checked_questions)):
        continue
    similar_questions = []
    # Embed the current question
    embedding1 = model.encode(current_question, convert_to_tensor=True)

    # Compare with all other questions
    for i in range(len(questions)):
        embedding2 = model.encode(questions[i], convert_to_tensor=True)

        # Computes cosine similarity
        similarity_score = util.pytorch_cos_sim(embedding1, embedding2).item()

        if similarity_score >= 0.92:
            similar_questions.append(questions[i])

    selected_answer = ""
    selected_question = ""

    for ques in similar_questions:
        answer = answers[questions[questions == ques].index[0]]
        if len(answer) > len(selected_answer):  # Prefer longer answers
            selected_answer = answer
            selected_question = ques
    
    # Ignore all of these questions if they show again
    for ques in similar_questions:
        checked_questions.add(ques)

    
    print(f"Questions similar to '{current_question}':\n\n" +
          "\n".join(similar_questions) + "\n\n" +
          f"Selected Question: {selected_question}\n" +
          f"Answer: {selected_answer}\n-------------------------------------- QUESTION {index} ---------------------------------------\n")
    
    with open('cleaned_QA.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["question", "answer"])
        
        # Write header only if the file is empty
        if file.tell() == 0:
            writer.writeheader()
            
        writer.writerow({"question": selected_question, "answer": selected_answer})
