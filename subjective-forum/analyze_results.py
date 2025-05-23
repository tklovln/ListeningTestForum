#!/usr/bin/env python3
"""
Script to analyze listening test results.
"""
import os
import json
import glob
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def load_results(results_dir):
    """
    Load all result files from the results directory.
    
    Args:
        results_dir: Path to the results directory
        
    Returns:
        List of result dictionaries
    """
    results = []
    for file_path in glob.glob(os.path.join(results_dir, '*.json')):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                results.append(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {file_path}: {e}")
    
    return results

def extract_metrics(results):
    """
    Extract metrics from results.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Dictionary mapping question IDs to metrics data
    """
    metrics_data = {}
    
    for result in results:
        participant = result.get('participant', {})
        answers = result.get('answers', {})
        
        for question_id, answer in answers.items():
            if question_id not in metrics_data:
                metrics_data[question_id] = {
                    'participants': [],
                    'metrics': {}
                }
            
            metrics = answer.get('metrics', {})
            metrics_data[question_id]['participants'].append(participant)
            
            for metric_name, rating in metrics.items():
                if metric_name not in metrics_data[question_id]['metrics']:
                    metrics_data[question_id]['metrics'][metric_name] = []
                
                metrics_data[question_id]['metrics'][metric_name].append(rating)
    
    return metrics_data

def calculate_statistics(metrics_data):
    """
    Calculate statistics for each metric.
    
    Args:
        metrics_data: Dictionary mapping question IDs to metrics data
        
    Returns:
        Dictionary mapping question IDs to metric statistics
    """
    stats = {}
    
    for question_id, data in metrics_data.items():
        stats[question_id] = {
            'participant_count': len(data['participants']),
            'metrics': {}
        }
        
        for metric_name, ratings in data['metrics'].items():
            ratings_array = np.array(ratings)
            stats[question_id]['metrics'][metric_name] = {
                'mean': np.mean(ratings_array),
                'median': np.median(ratings_array),
                'std': np.std(ratings_array),
                'min': np.min(ratings_array),
                'max': np.max(ratings_array),
                'count': len(ratings_array)
            }
    
    return stats

def plot_metrics(stats, output_dir):
    """
    Create plots for metrics statistics.
    
    Args:
        stats: Dictionary mapping question IDs to metric statistics
        output_dir: Directory to save plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot mean ratings for each question
    plt.figure(figsize=(12, 8))
    
    for i, (question_id, data) in enumerate(stats.items()):
        metrics = data['metrics']
        metric_names = list(metrics.keys())
        means = [metrics[name]['mean'] for name in metric_names]
        stds = [metrics[name]['std'] for name in metric_names]
        
        x = np.arange(len(metric_names))
        plt.bar(x + i * 0.25, means, width=0.2, yerr=stds, 
                label=f'Question {question_id}', capsize=5)
    
    plt.xlabel('Metrics')
    plt.ylabel('Mean Rating')
    plt.title('Mean Ratings by Metric and Question')
    plt.xticks(np.arange(len(metric_names)) + 0.25, metric_names, rotation=45)
    plt.ylim(0, 5.5)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(os.path.join(output_dir, 'mean_ratings.png'))
    plt.close()
    
    # Plot distribution of ratings for each metric
    for question_id, data in stats.items():
        metrics = data['metrics']
        metric_names = list(metrics.keys())
        
        plt.figure(figsize=(12, 8))
        
        for i, metric_name in enumerate(metric_names):
            # Count occurrences of each rating (1-5)
            ratings = np.array(metrics_data[question_id]['metrics'][metric_name])
            counts = [np.sum(ratings == rating) for rating in range(1, 6)]
            
            x = np.arange(5)  # 5 possible ratings (1-5)
            plt.bar(x + i * 0.15, counts, width=0.1, label=metric_name)
        
        plt.xlabel('Rating')
        plt.ylabel('Count')
        plt.title(f'Rating Distribution for Question {question_id}')
        plt.xticks(np.arange(5) + 0.3, ['1', '2', '3', '4', '5'])
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(output_dir, f'distribution_q{question_id}.png'))
        plt.close()

def print_statistics(stats):
    """
    Print statistics to console.
    
    Args:
        stats: Dictionary mapping question IDs to metric statistics
    """
    print("\n=== Listening Test Results ===\n")
    
    for question_id, data in stats.items():
        print(f"Question {question_id} (Participants: {data['participant_count']})")
        print("-" * 40)
        
        for metric_name, metric_stats in data['metrics'].items():
            print(f"  {metric_name}:")
            print(f"    Mean: {metric_stats['mean']:.2f}")
            print(f"    Median: {metric_stats['median']:.2f}")
            print(f"    Std Dev: {metric_stats['std']:.2f}")
            print(f"    Range: {metric_stats['min']:.2f} - {metric_stats['max']:.2f}")
            print()
        
        print()

def export_csv(stats, output_file):
    """
    Export statistics to CSV file.
    
    Args:
        stats: Dictionary mapping question IDs to metric statistics
        output_file: Path to output CSV file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("question_id,metric,mean,median,std_dev,min,max,count\n")
        
        # Write data
        for question_id, data in stats.items():
            for metric_name, metric_stats in data['metrics'].items():
                f.write(f"{question_id},{metric_name},{metric_stats['mean']:.2f},"
                        f"{metric_stats['median']:.2f},{metric_stats['std']:.2f},"
                        f"{metric_stats['min']:.2f},{metric_stats['max']:.2f},"
                        f"{metric_stats['count']}\n")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Analyze listening test results.')
    parser.add_argument('--results-dir', default='results',
                        help='Directory containing result JSON files')
    parser.add_argument('--output-dir', default='analysis',
                        help='Directory to save analysis results')
    parser.add_argument('--csv', default='analysis/results.csv',
                        help='Path to output CSV file')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load results
    results = load_results(args.results_dir)
    print(f"Loaded {len(results)} result files")
    
    if not results:
        print("No results found. Exiting.")
        return
    
    # Extract metrics
    global metrics_data
    metrics_data = extract_metrics(results)
    
    # Calculate statistics
    stats = calculate_statistics(metrics_data)
    
    # Print statistics
    print_statistics(stats)
    
    # Export to CSV
    export_csv(stats, args.csv)
    print(f"Exported statistics to {args.csv}")
    
    # Create plots
    plot_metrics(stats, args.output_dir)
    print(f"Saved plots to {args.output_dir}")

if __name__ == '__main__':
    main()