import os
import json
import glob
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import seaborn as sns
from collections import defaultdict

def load_latest_stats(log_dir):
    """Load the most recent stats file from the log directory."""
    stats_files = [f for f in os.listdir(log_dir) if f.startswith("training_stats_") and f.endswith(".json")]
    
    if not stats_files:
        print("No evaluation results found in the log directory.")
        return None
    
    latest_stats = max(stats_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
    stats_path = os.path.join(log_dir, latest_stats)
    
    print(f"Loading evaluation results from {latest_stats}")
    
    with open(stats_path, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    return stats, latest_stats

def load_all_stats(log_dir):
    """Load all stats files from the log directory."""
    stats_files = [f for f in os.listdir(log_dir) if f.startswith("training_stats_") and f.endswith(".json")]
    
    if not stats_files:
        print("No evaluation results found in the log directory.")
        return []
    
    all_stats = []
    for stats_file in stats_files:
        stats_path = os.path.join(log_dir, stats_file)
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            # Extract timestamp from filename
            timestamp_str = stats_file.replace("training_stats_", "").replace(".json", "")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                stats["timestamp"] = timestamp
            except ValueError:
                stats["timestamp"] = None
            all_stats.append(stats)
    
    # Sort by timestamp if available
    all_stats.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
    
    return all_stats

def create_output_dir():
    """Create output directory for visualizations."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visualizations")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def plot_overall_metrics(stats, output_dir):
    """Plot overall metrics like correct, incorrect, and low confidence predictions."""
    metrics = {
        "Correct": stats["correct_predictions"],
        "Incorrect": stats["incorrect_predictions"],
        "Low Confidence": stats["low_confidence"],
        "Fallback": stats["fallback_count"]
    }
    
    # Calculate percentages
    total = stats["total_questions"]
    percentages = {k: v/total*100 for k, v in metrics.items()}
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Bar chart for counts
    ax1.bar(metrics.keys(), metrics.values(), color=['green', 'red', 'orange', 'blue'])
    ax1.set_title("Prediction Counts")
    ax1.set_ylabel("Count")
    for i, v in enumerate(metrics.values()):
        ax1.text(i, v + 5, str(v), ha='center')
    
    # Pie chart for percentages
    ax2.pie(percentages.values(), labels=percentages.keys(), autopct='%1.1f%%', 
            colors=['green', 'red', 'orange', 'blue'])
    ax2.set_title("Prediction Percentages")
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "overall_metrics.png"))
    plt.close()

def plot_intent_confidence(stats, output_dir):
    """Plot confidence levels for each intent."""
    intent_confidences = stats["intent_confidence"]
    
    # Calculate average confidence for each intent
    avg_confidences = {}
    for intent, confidences in intent_confidences.items():
        if confidences:
            avg_confidences[intent] = sum(confidences) / len(confidences)
    
    # Sort by average confidence
    sorted_intents = sorted(avg_confidences.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 20 intents for visualization
    top_intents = sorted_intents[:20]
    
    plt.figure(figsize=(15, 10))
    bars = plt.bar([i[0] for i in top_intents], [i[1] for i in top_intents], color='blue')
    plt.xticks(rotation=90)
    plt.title("Top 20 Most Confident Intents")
    plt.ylabel("Average Confidence")
    plt.tight_layout()
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', rotation=0)
    
    plt.savefig(os.path.join(output_dir, "intent_confidence.png"))
    plt.close()
    
    # Plot bottom 20 intents
    bottom_intents = sorted_intents[-20:] if len(sorted_intents) >= 20 else sorted_intents
    
    plt.figure(figsize=(15, 10))
    bars = plt.bar([i[0] for i in bottom_intents], [i[1] for i in bottom_intents], color='red')
    plt.xticks(rotation=90)
    plt.title("Bottom 20 Least Confident Intents")
    plt.ylabel("Average Confidence")
    plt.tight_layout()
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', rotation=0)
    
    plt.savefig(os.path.join(output_dir, "least_confident_intents.png"))
    plt.close()

def plot_confidence_distribution(stats, output_dir):
    """Plot distribution of confidence scores."""
    all_confidences = []
    for confidences in stats["intent_confidence"].values():
        all_confidences.extend(confidences)
    
    plt.figure(figsize=(10, 6))
    sns.histplot(all_confidences, bins=30, kde=True)
    plt.title("Distribution of Confidence Scores")
    plt.xlabel("Confidence Score")
    plt.ylabel("Frequency")
    plt.axvline(x=0.7, color='r', linestyle='--', label='Confidence Threshold (0.7)')
    plt.legend()
    plt.savefig(os.path.join(output_dir, "confidence_distribution.png"))
    plt.close()

def plot_correct_prediction_confidences(stats, output_dir):
    """Plot confidence levels for correct predictions."""
    correct_confidences = stats.get("correct_prediction_confidences", {})
    
    # Calculate average confidence for correct predictions by intent
    avg_correct_confidences = {}
    for intent, confidences in correct_confidences.items():
        if confidences:
            avg_correct_confidences[intent] = sum(confidences) / len(confidences)
    
    # Sort by average confidence
    sorted_intents = sorted(avg_correct_confidences.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 20 intents for visualization
    top_intents = sorted_intents[:20]
    
    plt.figure(figsize=(15, 10))
    bars = plt.bar([i[0] for i in top_intents], [i[1] for i in top_intents], color='green')
    plt.xticks(rotation=90)
    plt.title("Top 20 Intents with Highest Correct Prediction Confidence")
    plt.ylabel("Average Confidence for Correct Predictions")
    plt.tight_layout()
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', rotation=0)
    
    plt.savefig(os.path.join(output_dir, "correct_prediction_confidences.png"))
    plt.close()

def plot_confusion_matrix(stats, output_dir):
    """Plot confusion matrix for top intents."""
    confusion_matrix = stats["confusion_matrix"]
    
    # Get top 10 intents by total occurrences
    intent_counts = defaultdict(int)
    for expected, predictions in confusion_matrix.items():
        for predicted, count in predictions.items():
            intent_counts[expected] += count
            intent_counts[predicted] += count
    
    top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_intent_names = [i[0] for i in top_intents]
    
    # Create a matrix for top intents
    matrix = np.zeros((len(top_intent_names), len(top_intent_names)))
    for i, expected in enumerate(top_intent_names):
        for j, predicted in enumerate(top_intent_names):
            matrix[i, j] = confusion_matrix.get(expected, {}).get(predicted, 0)
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(matrix, annot=True, fmt='.0f', cmap='YlGnBu', 
                xticklabels=top_intent_names, yticklabels=top_intent_names)
    plt.title("Confusion Matrix for Top 10 Intents")
    plt.xlabel("Predicted Intent")
    plt.ylabel("Expected Intent")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"))
    plt.close()

def plot_improvement_over_time(all_stats, output_dir):
    """Plot improvement metrics over time if multiple stats files are available."""
    if len(all_stats) < 2:
        print("Not enough stats files to plot improvement over time.")
        return
    
    # Extract metrics over time
    timestamps = []
    correct_rates = []
    incorrect_rates = []
    low_confidence_rates = []
    
    for stats in all_stats:
        if "timestamp" in stats and stats["timestamp"]:
            timestamps.append(stats["timestamp"])
            total = stats["total_questions"]
            correct_rates.append(stats["correct_predictions"] / total * 100)
            incorrect_rates.append(stats["incorrect_predictions"] / total * 100)
            low_confidence_rates.append(stats["low_confidence"] / total * 100)
    
    if not timestamps:
        print("No timestamp data available for plotting improvement over time.")
        return
    
    # Convert timestamps to datetime objects if they're strings
    if isinstance(timestamps[0], str):
        timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps]
    
    # Sort by timestamp
    sorted_data = sorted(zip(timestamps, correct_rates, incorrect_rates, low_confidence_rates), key=lambda x: x[0])
    timestamps, correct_rates, incorrect_rates, low_confidence_rates = zip(*sorted_data)
    
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, correct_rates, 'g-', label='Correct Predictions (%)')
    plt.plot(timestamps, incorrect_rates, 'r-', label='Incorrect Predictions (%)')
    plt.plot(timestamps, low_confidence_rates, 'o-', label='Low Confidence (%)')
    plt.title("Model Performance Over Time")
    plt.xlabel("Time")
    plt.ylabel("Percentage")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "improvement_over_time.png"))
    plt.close()

def generate_html_report(stats, output_dir):
    """Generate an HTML report with all visualizations and key metrics."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rasa Model Evaluation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .metric {{ margin: 10px 0; padding: 10px; background-color: #f5f5f5; border-radius: 5px; }}
            .visualization {{ margin: 20px 0; text-align: center; }}
            .visualization img {{ max-width: 100%; border: 1px solid #ddd; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>Rasa Model Evaluation Report</h1>
        
        <h2>Overall Metrics</h2>
        <div class="metric">
            <p><strong>Total Questions:</strong> {stats["total_questions"]}</p>
            <p><strong>Correct Predictions:</strong> {stats["correct_predictions"]} ({stats["correct_predictions"]/stats["total_questions"]*100:.2f}%)</p>
            <p><strong>Incorrect Predictions:</strong> {stats["incorrect_predictions"]} ({stats["incorrect_predictions"]/stats["total_questions"]*100:.2f}%)</p>
            <p><strong>Low Confidence Predictions:</strong> {stats["low_confidence"]} ({stats["low_confidence"]/stats["total_questions"]*100:.2f}%)</p>
            <p><strong>Fallback Count:</strong> {stats["fallback_count"]} ({stats["fallback_count"]/stats["total_questions"]*100:.2f}%)</p>
        </div>
        
        <h2>Most Confident Intents</h2>
        <table>
            <tr>
                <th>Intent</th>
                <th>Average Confidence</th>
            </tr>
    """
    
    for intent, confidence in stats.get("most_confident_intents", []):
        html_content += f"""
            <tr>
                <td>{intent}</td>
                <td>{confidence:.4f}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Least Confident Intents</h2>
        <table>
            <tr>
                <th>Intent</th>
                <th>Average Confidence</th>
            </tr>
    """
    
    for intent, confidence in stats.get("least_confident_intents", []):
        html_content += f"""
            <tr>
                <td>{intent}</td>
                <td>{confidence:.4f}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Visualizations</h2>
        
        <div class="visualization">
            <h3>Overall Metrics</h3>
            <img src="overall_metrics.png" alt="Overall Metrics">
        </div>
        
        <div class="visualization">
            <h3>Intent Confidence</h3>
            <img src="intent_confidence.png" alt="Intent Confidence">
        </div>
        
        <div class="visualization">
            <h3>Least Confident Intents</h3>
            <img src="least_confident_intents.png" alt="Least Confident Intents">
        </div>
        
        <div class="visualization">
            <h3>Confidence Distribution</h3>
            <img src="confidence_distribution.png" alt="Confidence Distribution">
        </div>
        
        <div class="visualization">
            <h3>Correct Prediction Confidences</h3>
            <img src="correct_prediction_confidences.png" alt="Correct Prediction Confidences">
        </div>
        
        <div class="visualization">
            <h3>Confusion Matrix</h3>
            <img src="confusion_matrix.png" alt="Confusion Matrix">
        </div>
    """
    
    # Add improvement over time if available
    if os.path.exists(os.path.join(output_dir, "improvement_over_time.png")):
        html_content += """
        <div class="visualization">
            <h3>Improvement Over Time</h3>
            <img src="improvement_over_time.png" alt="Improvement Over Time">
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    with open(os.path.join(output_dir, "report.html"), "w") as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description="Visualize Rasa training statistics")
    parser.add_argument("--log-dir", default="log_stats", help="Directory containing log files")
    parser.add_argument("--compare", action="store_true", help="Compare multiple training runs")
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, args.log_dir)
    
    # Create output directory
    output_dir = create_output_dir()
    
    if args.compare:
        # Load all stats files for comparison
        all_stats = load_all_stats(log_dir)
        if not all_stats:
            return
        
        # Use the most recent stats for individual visualizations
        stats = all_stats[0]
        
        # Generate visualizations
        plot_overall_metrics(stats, output_dir)
        plot_intent_confidence(stats, output_dir)
        plot_confidence_distribution(stats, output_dir)
        plot_correct_prediction_confidences(stats, output_dir)
        plot_confusion_matrix(stats, output_dir)
        plot_improvement_over_time(all_stats, output_dir)
        
        # Generate HTML report
        generate_html_report(stats, output_dir)
        
        print(f"Visualization report generated in {output_dir}")
        print(f"Open {os.path.join(output_dir, 'report.html')} in a web browser to view the report")
    else:
        # Load the most recent stats file
        result = load_latest_stats(log_dir)
        if not result:
            return
        
        stats, stats_file = result
        
        # Generate visualizations
        plot_overall_metrics(stats, output_dir)
        plot_intent_confidence(stats, output_dir)
        plot_confidence_distribution(stats, output_dir)
        plot_correct_prediction_confidences(stats, output_dir)
        plot_confusion_matrix(stats, output_dir)
        
        # Generate HTML report
        generate_html_report(stats, output_dir)
        
        print(f"Visualization report generated in {output_dir}")
        print(f"Open {os.path.join(output_dir, 'report.html')} in a web browser to view the report")

if __name__ == "__main__":
    main() 