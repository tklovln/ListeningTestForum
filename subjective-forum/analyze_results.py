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

def translate_metric_name(chinese_name):
    """
    Extract English metric names from Chinese names with English in parentheses.
    
    Args:
        chinese_name: Metric name in format "中文（English）"
        
    Returns:
        English metric name
    """
    # Check if the name contains parentheses with English translation
    if '（' in chinese_name and '）' in chinese_name:
        # Extract the English part from parentheses
        start = chinese_name.find('（') + 1
        end = chinese_name.find('）')
        return chinese_name[start:end]
    else:
        raise NotImplementedError(f"Metric name {chinese_name} not implemented")
    
    # # Fallback to original translation dictionary for other cases
    # translations = {
    #     '效果評價（整體）': 'Overall Effect',
    #     '音質評價（清晰度）': 'Audio Quality (Clarity)',
    #     '自然度評價（流暢度）': 'Naturalness (Fluency)',
    #     '情感表達評價': 'Emotional Expression'
    # }
    
    # return translations.get(chinese_name, chinese_name)

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
        Dictionary mapping models to metrics data
    """
    metrics_data = {}
    
    for result in results:
        participant = result.get('participant', {})
        answers = result.get('answers', {})
        
        for question_id, answer in answers.items():
            # Get the metrics_rated data instead of metrics
            metrics_rated = answer.get('metrics_rated', {})
            prompt_id = answer.get('prompt_id_selected', 'unknown')
            
            for model_name, model_ratings in metrics_rated.items():
                if model_name not in metrics_data:
                    metrics_data[model_name] = {
                        'participants': [],
                        'metrics': {},
                        'prompts': []
                    }
                
                # Store participant info and prompt
                metrics_data[model_name]['participants'].append({
                    'participant': participant,
                    'question_id': question_id,
                    'prompt_id': prompt_id
                })
                metrics_data[model_name]['prompts'].append(prompt_id)
                
                # Store ratings for each metric (translate to English)
                for metric_name, rating in model_ratings.items():
                    english_metric = translate_metric_name(metric_name)
                    if english_metric not in metrics_data[model_name]['metrics']:
                        metrics_data[model_name]['metrics'][english_metric] = []
                    
                    metrics_data[model_name]['metrics'][english_metric].append(rating)
    
    return metrics_data

def calculate_statistics(metrics_data):
    """
    Calculate statistics for each model and metric.
    
    Args:
        metrics_data: Dictionary mapping models to metrics data
        
    Returns:
        Dictionary mapping models to metric statistics
    """
    stats = {}
    
    for model_name, data in metrics_data.items():
        stats[model_name] = {
            'participant_count': len(data['participants']),
            'unique_prompts': len(set(data['prompts'])),
            'metrics': {}
        }
        
        for metric_name, ratings in data['metrics'].items():
            ratings_array = np.array(ratings)
            stats[model_name]['metrics'][metric_name] = {
                'mean': np.mean(ratings_array),
                'median': np.median(ratings_array),
                'std': np.std(ratings_array),
                'min': np.min(ratings_array),
                'max': np.max(ratings_array),
                'count': len(ratings_array)
            }
    
    return stats

def plot_metrics(stats, metrics_data, output_dir):
    """
    Create plots for metrics statistics.
    
    Args:
        stats: Dictionary mapping models to metric statistics
        metrics_data: Raw metrics data
        output_dir: Directory to save plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all unique metrics
    all_metrics = set()
    for model_data in stats.values():
        all_metrics.update(model_data['metrics'].keys())
    all_metrics = sorted(list(all_metrics))
    
    # Plot mean ratings by model and metric
    plt.figure(figsize=(15, 8))
    
    models = list(stats.keys())
    x = np.arange(len(all_metrics))
    width = 0.25
    
    for i, model in enumerate(models):
        means = []
        stds = []
        for metric in all_metrics:
            if metric in stats[model]['metrics']:
                means.append(stats[model]['metrics'][metric]['mean'])
                stds.append(stats[model]['metrics'][metric]['std'])
            else:
                means.append(0)
                stds.append(0)
        
        plt.bar(x + i * width, means, width, yerr=stds, 
                label=model, capsize=5, alpha=0.8)
    
    plt.xlabel('Metrics')
    plt.ylabel('Mean Rating')
    plt.title('Mean Ratings by Model and Metric')
    plt.xticks(x + width, all_metrics, rotation=45, ha='right')
    plt.ylim(0, 5.5)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(os.path.join(output_dir, 'mean_ratings_by_model.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Plot rating distributions for each metric
    for metric in all_metrics:
        plt.figure(figsize=(12, 8))
        
        for i, model in enumerate(models):
            if metric in metrics_data[model]['metrics']:
                ratings = np.array(metrics_data[model]['metrics'][metric])
                counts = [np.sum(ratings == rating) for rating in range(1, 6)]
                
                x_pos = np.arange(5) + i * 0.25
                plt.bar(x_pos, counts, width=0.2, label=model, alpha=0.8)
        
        plt.xlabel('Rating')
        plt.ylabel('Count')
        plt.title(f'Rating Distribution for {metric}')
        plt.xticks(np.arange(5) + 0.25, ['1', '2', '3', '4', '5'])
        plt.legend()
        plt.tight_layout()
        
        # Clean filename for saving
        safe_metric_name = metric.replace(' ', '_').replace('(', '').replace(')', '')
        plt.savefig(os.path.join(output_dir, f'distribution_{safe_metric_name}.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()

def print_statistics(stats):
    """
    Print statistics to console.
    
    Args:
        stats: Dictionary mapping models to metric statistics
    """
    print("\n=== Listening Test Results by Model ===\n")
    
    for model_name, data in stats.items():
        print(f"Model: {model_name}")
        print(f"  Total Ratings: {data['participant_count']}")
        print(f"  Unique Prompts: {data['unique_prompts']}")
        print("-" * 50)
        
        for metric_name, metric_stats in data['metrics'].items():
            print(f"  {metric_name}:")
            print(f"    Mean: {metric_stats['mean']:.2f}")
            print(f"    Median: {metric_stats['median']:.2f}")
            print(f"    Std Dev: {metric_stats['std']:.2f}")
            print(f"    Range: {metric_stats['min']:.0f} - {metric_stats['max']:.0f}")
            print(f"    Count: {metric_stats['count']}")
            print()
        
        print()

def export_csv(stats, output_file):
    """
    Export statistics to CSV file.
    
    Args:
        stats: Dictionary mapping models to metric statistics
        output_file: Path to output CSV file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("model,metric,mean,median,std_dev,min,max,count\n")
        
        # Write data
        for model_name, data in stats.items():
            for metric_name, metric_stats in data['metrics'].items():
                f.write(f"{model_name},{metric_name},{metric_stats['mean']:.2f},"
                        f"{metric_stats['median']:.2f},{metric_stats['std']:.2f},"
                        f"{metric_stats['min']:.0f},{metric_stats['max']:.0f},"
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
    metrics_data = extract_metrics(results)
    
    # Calculate statistics
    stats = calculate_statistics(metrics_data)
    
    # Print statistics
    print_statistics(stats)
    
    # Export to CSV
    export_csv(stats, args.csv)
    print(f"Exported statistics to {args.csv}")
    
    # Create plots
    plot_metrics(stats, metrics_data, args.output_dir)
    print(f"Saved plots to {args.output_dir}")

if __name__ == '__main__':
    main()