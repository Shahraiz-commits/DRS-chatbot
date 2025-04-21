import json
import os
import sys
import time
import logging
import requests
import argparse
import numpy as np
from datetime import datetime
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString
from collections import defaultdict


log_file_path = os.path.join(os.path.dirname(__file__), "log_stats", f"synthetic_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.configure_new_data import configure_nlu

completed_intents = 0
total_intents = 0

class SyntheticInteractiveTraining:
    def __init__(self, rasa_url="http://localhost:5005", questions_file="example_questions.json", 
                 confidence_threshold=0.7, max_questions_per_intent=5, evaluation_only=False):
        """
        Initialize the synthetic interactive training.
        
        Args:
            rasa_url: URL of the running Rasa server
            questions_file: Path to the JSON file containing synthetic questions
            confidence_threshold: Minimum confidence for intent prediction
            max_questions_per_intent: Maximum number of questions to add per intent
            evaluation_only: If True, only evaluate without adding questions to intents
        """
        self.rasa_url = rasa_url
        self.questions_file = questions_file
        self.confidence_threshold = confidence_threshold
        self.max_questions_per_intent = max_questions_per_intent
        self.evaluation_only = evaluation_only
        
        # Initialize stats
        self.stats = self._initialize_stats()
        
        # Load questions
        self.load_questions()
        
    def _initialize_stats(self):
        """Initialize statistics dictionary."""
        return {
            "total_questions": 0,
            "correct_predictions": 0,
            "incorrect_predictions": 0,
            "low_confidence": 0,
            "questions_added": 0,
            "intents_updated": set(),
            "incorrect_predictions_list": [],
            "fallback_count": 0,
            "expected_in_alternatives": 0,
            "expected_rank_in_alternatives": [],
            "intent_confidence": defaultdict(list),
            "confusion_matrix": defaultdict(lambda: defaultdict(int)),
            "correct_prediction_confidences": defaultdict(list),  # Track confidences for correct predictions
            "most_confident_intents": [],  # Will store top 5 most confident intents
            "least_confident_intents": []  # Will store bottom 5 least confident intents
        }
        
    def load_questions(self):
        """Load synthetic questions from the JSON file."""
        global total_intents
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                self.questions_data = json.load(f)
            total_intents = len(self.questions_data)
            logger.info(f"Loaded {total_intents} intents with questions from {self.questions_file}")
        except Exception as e:
            logger.error(f"Error loading questions file: {e}")
            sys.exit(1)
            
    def ask_rasa(self, question):
        """
        Send a question to the Rasa chatbot and get the response.
        
        Args:
            question: The question to ask
            
        Returns:
            dict: The response from Rasa
        """
        try:
            response = requests.post(
                f"{self.rasa_url}/model/parse",
                json={"text": question}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error asking Rasa: {e}")
            return None
            
    def process_question(self, question, expected_intent):
        """
        Process a single question and update training data if needed.
        
        Args:
            question: The question to process
            expected_intent: The expected intent for this question
            
        Returns:
            bool: True if the question was added to training data
        """
        global completed_intents
        self.stats["total_questions"] += 1
        
        # Ask Rasa
        rasa_response = self.ask_rasa(question)
        if not rasa_response:
            logger.warning(f"Could not get response from Rasa for question: {question}")
            return False
            
        # Get the predicted intent and confidence
        intent_ranking = rasa_response.get("intent_ranking", [])
        if not intent_ranking:
            logger.warning(f"No intent ranking in Rasa response for question: {question}")
            return False
            
        predicted_intent = intent_ranking[0].get("name", "")
        confidence = intent_ranking[0].get("confidence", 0)
        
        # Find the expected intent's confidence in the ranking
        expected_confidence = 0
        expected_rank = -1
        for i, intent_data in enumerate(intent_ranking):
            if intent_data.get("name") == expected_intent:
                expected_confidence = intent_data.get("confidence", 0)
                expected_rank = i
                break
        
        # Store confidence for this intent
        self.stats["intent_confidence"][expected_intent].append(expected_confidence)
        
        # Update confusion matrix
        self.stats["confusion_matrix"][expected_intent][predicted_intent] += 1
        
        # Log the prediction
        logger.info(f"Question: '{question}'")
        logger.info(f"Expected intent: {expected_intent}")
        logger.info(f"Predicted intent: {predicted_intent} (confidence: {confidence:.4f})")
        
        # Check if prediction is correct
        if predicted_intent == expected_intent:
            logger.info("✅ Prediction is correct!")
            self.stats["correct_predictions"] += 1
            # Store confidence for correct predictions
            self.stats["correct_prediction_confidences"][expected_intent].append(confidence)
            return False
        
        # Check if it's a fallback
        if predicted_intent == "nlu_fallback":
            self.stats["fallback_count"] += 1
            logger.info("⚠️ Question went to fallback")
            
            # Log the top 3 alternatives
            logger.info("Top 3 alternatives:")
            for i, intent_data in enumerate(intent_ranking[1:4]):  # get next 3
                intent_name = intent_data.get("name", "")
                intent_confidence = intent_data.get("confidence", 0)
                logger.info(f"  {i}. {intent_name} (confidence: {intent_confidence:.4f})")
            
            # Check if expected intent is in top 3 alternatives
            found_in_alternatives = False
            for i, intent_data in enumerate(intent_ranking[:3]):
                if intent_data.get("name") == expected_intent:
                    found_in_alternatives = True
                    self.stats["expected_in_alternatives"] += 1
                    self.stats["expected_rank_in_alternatives"].append(i)
                    logger.info(f"✅ Expected intent found in alternative #{i} with confidence {intent_data.get('confidence', 0):.4f}")
                    break
            
            if not found_in_alternatives:
                logger.info("❌ Expected intent not found in top 3 alternatives")
                self.stats["incorrect_predictions"] += 1
                
                # Track incorrect predictions
                self.stats["incorrect_predictions_list"].append({
                    "question": question,
                    "expected_intent": expected_intent,
                    "predicted_intent": predicted_intent,
                    "confidence": confidence,
                    "expected_confidence": expected_confidence,
                    "in_alternatives": False
                })
                
                # Add question to training data if not in evaluation_only mode
                if not self.evaluation_only:
                    logger.info(f"Adding question to intent '{expected_intent}'")
                    configure_nlu("modify", expected_intent, [question])
                    self.stats["questions_added"] += 1
                    self.stats["intents_updated"].add(expected_intent)
                    return True
                
                return False
                
            return False
              
        # Check confidence
        if confidence < self.confidence_threshold:
            logger.info(f"⚠️ Low confidence prediction (expected intent confidence: {expected_confidence:.4f})")
            self.stats["low_confidence"] += 1
        else:
            logger.info(f"❌ Prediction is incorrect (expected intent confidence: {expected_confidence:.4f})")
            self.stats["incorrect_predictions"] += 1
            
        # Track incorrect predictions
        self.stats["incorrect_predictions_list"].append({
            "question": question,
            "expected_intent": expected_intent,
            "predicted_intent": predicted_intent,
            "confidence": confidence,
            "expected_confidence": expected_confidence,
            "in_alternatives": False
        })
            
        # Add question to training data if not in evaluation_only mode
        if not self.evaluation_only:
            logger.info(f"Adding question to intent '{expected_intent}'")
            configure_nlu("modify", expected_intent, [question])
            self.stats["questions_added"] += 1
            self.stats["intents_updated"].add(expected_intent)
            return True
        
        return False
        
    def run_evaluation(self):
        """Run evaluation on all questions."""
        global completed_intents, total_intents
        completed_intents = 0  # Reset counter at the start of run
        
        logger.info("Starting evaluation...")
        logger.info(f"Confidence threshold: {self.confidence_threshold}")
        logger.info(f"Evaluation only mode: {self.evaluation_only}")
        
        # Process each intent and its questions
        for intent_data in self.questions_data:
            intent = intent_data.get("intent", "")
            questions = intent_data.get("questions", [])
            
            if not intent or not questions:
                logger.warning(f"Skipping invalid intent data: {intent_data}")
                continue
                
            logger.info(f"\n{'='*80}")
            logger.info(f"{completed_intents}/{total_intents} intents processed ({completed_intents/total_intents*100:.2f}% done...)")
            logger.info(f"Processing intent: {intent}")
            logger.info(f"Number of questions: {len(questions)}")
            
            # Process each question
            for question in questions:
                self.process_question(question, intent)
                    
            completed_intents += 1
                
        # Print summary
        self._print_summary()
        
    def _print_summary(self):
        """Print summary of current evaluation."""
        logger.info("\n" + "="*50)
        logger.info("Evaluation Summary:")
        logger.info(f"Total questions processed: {self.stats['total_questions']}")
        logger.info(f"Correct predictions: {self.stats['correct_predictions']} ({self.stats['correct_predictions']/self.stats['total_questions']*100:.2f}%)")
        logger.info(f"Incorrect predictions: {self.stats['incorrect_predictions']} ({self.stats['incorrect_predictions']/self.stats['total_questions']*100:.2f}%)")
        logger.info(f"Low confidence predictions: {self.stats['low_confidence']} ({self.stats['low_confidence']/self.stats['total_questions']*100:.2f}%)")
        logger.info(f"Fallback count: {self.stats['fallback_count']} ({self.stats['fallback_count']/self.stats['total_questions']*100:.2f}%)")
        logger.info(f"Expected intent in alternatives: {self.stats['expected_in_alternatives']} ({self.stats['expected_in_alternatives']/max(1, self.stats['fallback_count'])*100:.2f}% of fallbacks)")
        
        if self.stats["expected_rank_in_alternatives"]:
            avg_rank = sum(self.stats["expected_rank_in_alternatives"]) / len(self.stats["expected_rank_in_alternatives"])
            logger.info(f"Average rank of expected intent in alternatives: {avg_rank:.2f}")
        
        # Calculate and store most and least confident intents
        self._calculate_confidence_rankings()
        
        # Print intent confidence averages
        logger.info("\nIntent Confidence Averages:")
        for intent, confidences in self.stats["intent_confidence"].items():
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                logger.info(f"{intent}: {avg_confidence:.4f}")
        
        # Print most and least confident intents
        logger.info("\nMost Confident Intents:")
        for intent, avg_confidence in self.stats["most_confident_intents"]:
            logger.info(f"{intent}: {avg_confidence:.4f}")
            
        logger.info("\nLeast Confident Intents:")
        for intent, avg_confidence in self.stats["least_confident_intents"]:
            logger.info(f"{intent}: {avg_confidence:.4f}")
        
        # Print incorrect predictions
        if self.stats["incorrect_predictions_list"]:
            logger.info("\nIncorrect Predictions:")
            for i, item in enumerate(self.stats["incorrect_predictions_list"], 1):
                logger.info(f"{i}. Question: '{item['question']}'")
                logger.info(f"   Expected: {item['expected_intent']} (confidence: {item['expected_confidence']:.4f}) | Predicted: {item['predicted_intent']} (confidence: {item['confidence']:.4f})")
                if "in_alternatives" in item:
                    logger.info(f"   In alternatives: {'Yes' if item['in_alternatives'] else 'No'}")
        
    def _calculate_confidence_rankings(self):
        """Calculate the most and least confident intents."""
        intent_avg_confidences = []
        
        for intent, confidences in self.stats["intent_confidence"].items():
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                intent_avg_confidences.append((intent, avg_confidence))
        
        # Sort by average confidence (descending)
        intent_avg_confidences.sort(key=lambda x: x[1], reverse=True)
        
        # Store top 5 most confident intents
        self.stats["most_confident_intents"] = intent_avg_confidences[:5]
        
        # Store bottom 5 least confident intents
        self.stats["least_confident_intents"] = intent_avg_confidences[-5:] if len(intent_avg_confidences) >= 5 else intent_avg_confidences
        
    def _save_stats(self):
        """Save current stats to file."""
        stats_filename = f"training_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        stats_file_path = os.path.join(os.path.dirname(__file__), "log_stats", stats_filename)
        
        # Convert set to list for JSON serialization
        json_stats = self.stats.copy()
        json_stats["intents_updated"] = list(self.stats["intents_updated"])
        
        # Convert defaultdict to regular dict for JSON serialization
        json_stats["intent_confidence"] = dict(json_stats["intent_confidence"])
        json_stats["confusion_matrix"] = {k: dict(v) for k, v in json_stats["confusion_matrix"].items()}
        
        with open(stats_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_stats, f, indent=2)
        logger.info(f"Stats saved to {stats_filename}")
        
    def run(self):
        """Run the synthetic interactive training process."""
        # Run the training process
        self.run_evaluation()
        
        # Save stats
        self._save_stats()

def main():
    parser = argparse.ArgumentParser(description="Synthetic Interactive Training for Rasa")
    parser.add_argument("--rasa-url", default="http://localhost:5005", help="URL of the running Rasa server")
    parser.add_argument("--questions-file", default="example_questions.json", help="Path to the JSON file containing synthetic questions")
    parser.add_argument("--confidence-threshold", type=float, default=0.7, help="Minimum confidence for intent prediction")
    parser.add_argument("--evaluation-only", action="store_true", help="Only evaluate without adding questions to intents")
    parser.add_argument("--apply-saved", action="store_true", help="Apply changes from the most recent evaluation results")
    
    args = parser.parse_args()

    if args.apply_saved:
        log_dir = os.path.join(os.path.dirname(__file__), "log_stats")
        stats_files = [f for f in os.listdir(log_dir) if f.startswith("training_stats_") and f.endswith(".json")]
        
        if not stats_files:
            print("No evaluation results found. Run evaluation first.")
            return
        
        latest_stats = max(stats_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
        stats_path = os.path.join(log_dir, latest_stats)
        
        print(f"Loading evaluation results from {latest_stats}")
        
        # Load the stats file
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        # Get the incorrect predictions
        incorrect_predictions = stats.get("incorrect_predictions_list", [])
        
        # Group questions by intent
        questions_by_intent = {}
        for item in incorrect_predictions:
            intent = item["expected_intent"]
            question = item["question"]
            if intent not in questions_by_intent:
                questions_by_intent[intent] = []
            questions_by_intent[intent].append(question)
        
        total_questions = sum(len(questions) for questions in questions_by_intent.values())
        # Add questions to intents
        added_questions = 0
        for intent, questions in questions_by_intent.items():
            # add a print statement to show how much % of total questions have been added
            print(f"Adding {len(questions)} questions to intent '{intent}' ({(added_questions)/total_questions*100:.2f}% done)")
            configure_nlu("modify", intent, questions)
            added_questions += len(questions)
        print("100% done")
        print(f"Added {added_questions} questions to {len(questions_by_intent)} intents")
        return

    trainer = SyntheticInteractiveTraining(
        rasa_url=args.rasa_url,
        questions_file=args.questions_file,
        confidence_threshold=args.confidence_threshold,
        evaluation_only=args.evaluation_only
    )
    
    trainer.run()

if __name__ == "__main__":
    main() 