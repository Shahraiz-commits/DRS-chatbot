import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
cred = credentials.Certificate(cert="../firebase_service_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def add_questions_to_intent(intent, new_questions):
    intent_ref = db.collection("trainingQuestions").document(intent)
    doc = intent_ref.get()

    if doc.exists:
        existing_data = doc.to_dict()
        existing_questions = existing_data.get("questions", [])

        # Make sure existing questions are a list
        if isinstance(existing_questions, str):
            existing_questions = [existing_questions]
        elif not isinstance(existing_questions, list):
            existing_questions = []
        
        # Merge new questions, no duplicates
        updated_questions = list(set(existing_questions + new_questions))
        intent_ref.update({"questions": updated_questions})
    else:
        intent_ref.set({"questions": list(new_questions)})
        print(f"Created new intent '{intent}' with questions: {new_questions}")

def add_unassigned_question(new_question):
    current_time = datetime.now().isoformat()
    doc_ref = db.collection("unassignedQuestions").document(current_time)
    doc_ref.set({"question": new_question})
    print(f"Added question: {new_question} for manual configuration")

"""For testing
def main():
    test_intent = "help_ai"
    new_questions = ["How can AI assist me?", "What are AI capabilities?", "Explain AI assistance."]
    
    add_questions_to_intent(test_intent, new_questions)

if __name__ == "__main__":
    main()
"""