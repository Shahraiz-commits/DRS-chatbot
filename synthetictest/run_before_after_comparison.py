#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import argparse
import shutil
from datetime import datetime

# Add parent directory to path to import synthetic_interactive_training
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from synthetic_interactive_training import SyntheticInteractiveTraining

def run_rasa_services():
    """Start the required Rasa services in the background."""
    print("Starting Rasa services...")
    
    # Start Rasa actions server
    actions_process = subprocess.Popen(
        ["rasa", "run", "actions", "--auto-reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Start Rasa API server
    api_process = subprocess.Popen(
        ["rasa", "run", "--enable-api", "--cors", "*"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for services to start
    print("Waiting for Rasa services to start...")
    time.sleep(60)
    
    return actions_process, api_process

def stop_rasa_services(actions_process, api_process):
    """Stop the Rasa services."""
    print("Stopping Rasa services...")
    
    if actions_process:
        actions_process.terminate()
    
    if api_process:
        api_process.terminate()
    
    # Wait for processes to terminate
    time.sleep(2)

def train_rasa_model():
    """Train a new Rasa model."""
    print("Training new Rasa model...")
    
    # Run rasa train
    result = subprocess.run(
        ["rasa", "train"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        print("Error training Rasa model:")
        print(result.stderr)
        return False
    
    print("Rasa model training completed successfully")
    return True

def run_synthetic_training(evaluation_only=True, output_prefix="training"):
    """
    Run the synthetic interactive training script.
    
    Args:
        evaluation_only: If True, only evaluate without adding questions to intents
        output_prefix: Prefix for output files
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Running synthetic training (evaluation_only={evaluation_only})...")
    
    # Create a timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run the synthetic training
    trainer = SyntheticInteractiveTraining(
        rasa_url="http://localhost:5055",
        questions_file="example_questions.json",
        confidence_threshold=0.7,
        max_questions_per_intent=5,
        evaluation_only=evaluation_only
    )
    
    # Run the training
    trainer.run()
    
    # Rename the output files with the specified prefix
    log_dir = os.path.join(os.path.dirname(__file__), "log_stats")
    
    # Find the most recent log file
    log_files = [f for f in os.listdir(log_dir) if f.startswith("synthetic_training_") and f.endswith(".log")]
    if log_files:
        latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
        new_log_name = f"{output_prefix}_{timestamp}.log"
        os.rename(
            os.path.join(log_dir, latest_log),
            os.path.join(log_dir, new_log_name)
        )
        print(f"Log saved as {new_log_name}")
    
    # Find the most recent stats file
    stats_files = [f for f in os.listdir(log_dir) if f.startswith("training_stats_") and f.endswith(".json")]
    if stats_files:
        latest_stats = max(stats_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
        new_stats_name = f"{output_prefix}_{timestamp}.json"
        os.rename(
            os.path.join(log_dir, latest_stats),
            os.path.join(log_dir, new_stats_name)
        )
        print(f"Stats saved as {new_stats_name}")
    
    return True

def apply_training_changes():
    """
    Apply the training changes from the most recent evaluation.
    This function reads the most recent stats file and adds the low confidence
    questions to their respective intents.
    """
    print("Applying training changes...")
    
    # Find the most recent stats file
    log_dir = os.path.join(os.path.dirname(__file__), "log_stats")
    stats_files = [f for f in os.listdir(log_dir) if f.startswith("training_stats_") and f.endswith(".json")]
    
    if not stats_files:
        print("No stats file found. Run evaluation first.")
        return False
    
    latest_stats = max(stats_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
    stats_path = os.path.join(log_dir, latest_stats)
    
    # Import configure_nlu
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.configure_new_data import configure_nlu
    
    # Load the stats file
    import json
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
    
    # Add questions to intents
    for intent, questions in questions_by_intent.items():
        print(f"Adding {len(questions)} questions to intent '{intent}'")
        configure_nlu("modify", intent, questions)
    
    print(f"Added {sum(len(q) for q in questions_by_intent.values())} questions to {len(questions_by_intent)} intents")
    return True

def main():
    # Start Rasa services
    actions_process, api_process = run_rasa_services()
    
    try:
        # Step 1: Evaluate AND add to NLU in one go
        print("\n=== Step 1: Initial Evaluation and Adding to NLU ===")
        # This will evaluate and add to NLU since evaluation_only=False
        run_synthetic_training(evaluation_only=False, output_prefix="before_and_add")
        
        # Step 2: Train new Rasa model with updated NLU data
        print("\n=== Step 2: Training New Model ===")
        if not train_rasa_model():
            print("Failed to train Rasa model")
            return 1
        
        # Step 3: Evaluate new model only (no adding to NLU)
        print("\n=== Step 3: Final Evaluation ===")
        run_synthetic_training(evaluation_only=True, output_prefix="after")
        
        # Step 4: Compare before and after results
        print("\n=== Step 4: Comparing Results ===")
        compare_results()
        
        print("\nBefore/after comparison completed successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Stop Rasa services
        stop_rasa_services(actions_process, api_process)
    
    return 0

def compare_results():
    """Compare before and after evaluation results."""
    log_dir = os.path.join(os.path.dirname(__file__), "log_stats")
    
    # Find the relevant files
    stats_files = [f for f in os.listdir(log_dir) if f.endswith(".json")]
    before_file = next((f for f in stats_files if f.startswith("before_and_add_")), None)
    after_file = next((f for f in stats_files if f.startswith("after_")), None)
    
    if not before_file or not after_file:
        print("Could not find before and after files for comparison")
        return
    
    # Load the stats
    with open(os.path.join(log_dir, before_file), 'r') as f:
        before_stats = json.load(f)
    with open(os.path.join(log_dir, after_file), 'r') as f:
        after_stats = json.load(f)
    
    # Print comparison
    print("\n=== Performance Comparison ===")
    print(f"{'Metric':<30} {'Before':>10} {'After':>10} {'Change':>10}")
    print("-" * 62)
    
    metrics = [
        ("Total questions", "total_questions"),
        ("Correct predictions", "correct_predictions"),
        ("Incorrect predictions", "incorrect_predictions"),
        ("Low confidence", "low_confidence"),
        ("Fallback count", "fallback_count")
    ]
    
    for label, key in metrics:
        before_val = before_stats[key]
        after_val = after_stats[key]
        if before_stats["total_questions"] > 0 and after_stats["total_questions"] > 0:
            before_pct = (before_val / before_stats["total_questions"]) * 100
            after_pct = (after_val / after_stats["total_questions"]) * 100
            change = after_pct - before_pct
            print(f"{label:<30} {before_pct:>9.1f}% {after_pct:>9.1f}% {change:>+9.1f}%")
    
    print("\n=== Intent Confidence Changes ===")
    all_intents = set(before_stats["intent_confidence"].keys()) | set(after_stats["intent_confidence"].keys())
    
    for intent in sorted(all_intents):
        before_conf = before_stats["intent_confidence"].get(intent, [])
        after_conf = after_stats["intent_confidence"].get(intent, [])
        
        if before_conf and after_conf:
            before_avg = sum(before_conf) / len(before_conf)
            after_avg = sum(after_conf) / len(after_conf)
            change = after_avg - before_avg
            if abs(change) > 0.01:  # Only show significant changes
                print(f"{intent:<30} {before_avg:>9.3f} {after_avg:>9.3f} {change:>+9.3f}")

if __name__ == "__main__":
    sys.exit(main())