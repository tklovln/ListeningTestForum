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
import pandas as pd
import seaborn as sns

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

def extract_metrics_by_template(results):
    """
    Extract metrics from results grouped by original_template_id.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Dictionary mapping template_id to metrics data
    """
    template_metrics_data = {}
    
    for result in results:
        participant = result.get('participant', {})
        answers = result.get('answers', {})
        
        for question_id, answer in answers.items():
            # Get template ID and metrics
            template_id = answer.get('original_template_id', 'unknown')
            metrics_rated = answer.get('metrics_rated', {})
            prompt_id = answer.get('prompt_id_selected', 'unknown')
            
            if template_id not in template_metrics_data:
                template_metrics_data[template_id] = {}
            
            for model_name, model_ratings in metrics_rated.items():
                if model_name not in template_metrics_data[template_id]:
                    template_metrics_data[template_id][model_name] = {
                        'participants': [],
                        'metrics': {},
                        'prompts': []
                    }
                
                # Store participant info and prompt
                template_metrics_data[template_id][model_name]['participants'].append({
                    'participant': participant,
                    'question_id': question_id,
                    'prompt_id': prompt_id
                })
                template_metrics_data[template_id][model_name]['prompts'].append(prompt_id)
                
                # Store ratings for each metric (translate to English)
                for metric_name, rating in model_ratings.items():
                    english_metric = translate_metric_name(metric_name)
                    if english_metric not in template_metrics_data[template_id][model_name]['metrics']:
                        template_metrics_data[template_id][model_name]['metrics'][english_metric] = []
                    
                    template_metrics_data[template_id][model_name]['metrics'][english_metric].append(rating)
    
    return template_metrics_data

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

def plot_metrics_by_template(template_metrics_data, output_dir):
    """
    Create plots for each template ID showing mean ratings by model.
    
    Args:
        template_metrics_data: Dictionary mapping template_id to metrics data
        output_dir: Directory to save plots
    """
    # Set seaborn style
    sns.set_theme(style="whitegrid")
    sns.set_context("talk")  # Increase font sizes for labels

    # Define custom color palette
    custom_palette = ["#533B4D", "#F564A9", "#FAA4BD", "#FAE3C6"]

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for template_id, template_data in template_metrics_data.items():
        # Prepare data in a long-form DataFrame for seaborn
        plot_data = []
        for model, m_data in template_data.items():
            for metric, ratings in m_data['metrics'].items():
                for rating in ratings:
                    plot_data.append({'model': model, 'metric': metric, 'rating': rating})
        
        if not plot_data:
            print(f"No data to plot for template {template_id}.")
            continue

        df = pd.DataFrame(plot_data)
        all_metrics = sorted(list(df['metric'].unique()))
        
        # Plot mean ratings by model and metric for this template
        plt.figure(figsize=(15, 8))
        sns.barplot(x='metric', y='rating', hue='model', data=df, errorbar='sd', palette=custom_palette)
        
        plt.xlabel('Metrics')
        plt.ylabel('Mean Rating')
        plt.title(f'Mean Ratings by Model and Metric - Template {template_id}')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 5.5)
        plt.legend(title='Model', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        
        plt.savefig(os.path.join(output_dir, f'{template_id}_rates.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Created plot for template {template_id}: {template_id}_rates.png")

def plot_metrics(stats, metrics_data, output_dir):
    """
    Create plots for metrics statistics.
    
    Args:
        stats: Dictionary mapping models to metric statistics
        metrics_data: Raw metrics data
        output_dir: Directory to save plots
    """
    # Set seaborn style
    sns.set_theme(style="whitegrid")
    sns.set_context("talk")  # Increase font sizes for labels

    # Define custom color palette
    custom_palette = ["#533B4D", "#F564A9", "#FAA4BD", "#FAE3C6"]

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare data in a long-form DataFrame for seaborn
    plot_data = []
    for model, m_data in metrics_data.items():
        for metric, ratings in m_data['metrics'].items():
            for rating in ratings:
                plot_data.append({'model': model, 'metric': metric, 'rating': rating})
    
    if not plot_data:
        print("No data to plot.")
        return

    df = pd.DataFrame(plot_data)
    all_metrics = sorted(list(df['metric'].unique()))
    
    # Plot mean ratings by model and metric
    plt.figure(figsize=(15, 8))
    sns.barplot(x='metric', y='rating', hue='model', data=df, errorbar='sd', palette=custom_palette)
    
    plt.xlabel('Metrics')
    plt.ylabel('Mean Rating')
    plt.title('Mean Ratings by Model and Metric')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 5.5)
    plt.legend(title='Model', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    
    plt.savefig(os.path.join(output_dir, 'mean_ratings_by_model.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Plot rating distributions for each metric
    for metric in all_metrics:
        plt.figure(figsize=(12, 8))
        
        metric_df = df[df['metric'] == metric]
        
        # Use countplot for distributions
        sns.countplot(x='rating', hue='model', data=metric_df, order=range(1, 6), palette=custom_palette)

        plt.xlabel('Rating')
        plt.ylabel('Count')
        plt.title(f'Rating Distribution for {metric}')
        plt.legend(title='Model', bbox_to_anchor=(1.02, 1), loc='upper left')
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

def print_statistics_by_template(template_stats):
    """
    Print statistics to console grouped by template.
    
    Args:
        template_stats: Dictionary mapping template_id to model statistics
    """
    print("\n=== Listening Test Results by Template ID ===\n")
    
    for template_id, template_data in template_stats.items():
        print(f"Template ID: {template_id}")
        print("=" * 60)
        
        for model_name, data in template_data.items():
            print(f"  Model: {model_name}")
            print(f"    Total Ratings: {data['participant_count']}")
            print(f"    Unique Prompts: {data['unique_prompts']}")
            print("-" * 50)
            
            for metric_name, metric_stats in data['metrics'].items():
                print(f"    {metric_name}:")
                print(f"      Mean: {metric_stats['mean']:.2f}")
                print(f"      Median: {metric_stats['median']:.2f}")
                print(f"      Std Dev: {metric_stats['std']:.2f}")
                print(f"      Range: {metric_stats['min']:.0f} - {metric_stats['max']:.0f}")
                print(f"      Count: {metric_stats['count']}")
                print()
            
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
        f.write("model,metric,mean,median,std_dev,min,max,count,MOS\n")
        
        # Write data
        for model_name, data in stats.items():
            # Calculate MOS (Mean Opinion Score) as average of all metric means
            metric_means = []
            for metric_name, metric_stats in data['metrics'].items():
                metric_means.append(metric_stats['mean'])
            
            mos = sum(metric_means) / len(metric_means) if metric_means else 0.0
            
            # Write individual metric data with MOS
            for metric_name, metric_stats in data['metrics'].items():
                f.write(f"{model_name},{metric_name},{metric_stats['mean']:.2f},"
                        f"{metric_stats['median']:.2f},{metric_stats['std']:.2f},"
                        f"{metric_stats['min']:.0f},{metric_stats['max']:.0f},"
                        f"{metric_stats['count']},{mos:.2f}\n")

def export_mos_by_template(template_metrics_data, output_file):
    """
    Export MOS with std for each template-model combination to CSV file.
    
    Args:
        template_metrics_data: Dictionary mapping template_id to model metrics data
        output_file: Path to output MOS CSV file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("template_id,model,MOS,std,rating_count\n")
        
        # Write MOS for each template-model combination
        for template_id, template_data in template_metrics_data.items():
            for model_name, data in template_data.items():
                # Collect all individual ratings across all metrics
                all_ratings = []
                for metric_name, ratings in data['metrics'].items():
                    all_ratings.extend(ratings)
                
                if all_ratings:
                    # Calculate statistics from all individual ratings
                    all_ratings_array = np.array(all_ratings)
                    std_rating = np.std(all_ratings_array)
                    rating_count = len(all_ratings)
                    
                    # Calculate MOS as average of metric means
                    metric_means = []
                    for metric_name, ratings in data['metrics'].items():
                        metric_means.append(np.mean(ratings))
                    
                    mos = sum(metric_means) / len(metric_means) if metric_means else 0.0
                else:
                    std_rating = 0.0
                    rating_count = 0
                    mos = 0.0
                
                f.write(f"{template_id},{model_name},{mos:.2f},{std_rating:.2f},{rating_count}\n")

def export_csv_by_template(template_stats, output_file):
    """
    Export statistics by template to CSV file.
    
    Args:
        template_stats: Dictionary mapping template_id to model statistics
        output_file: Path to output CSV file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("template_id,model,metric,mean,median,std_dev,min,max,count,MOS\n")
        
        # Write data
        for template_id, template_data in template_stats.items():
            for model_name, data in template_data.items():
                # Calculate MOS (Mean Opinion Score) as average of all metric means
                metric_means = []
                for metric_name, metric_stats in data['metrics'].items():
                    metric_means.append(metric_stats['mean'])
                
                mos = sum(metric_means) / len(metric_means) if metric_means else 0.0
                
                # Write individual metric data with MOS
                for metric_name, metric_stats in data['metrics'].items():
                    f.write(f"{template_id},{model_name},{metric_name},{metric_stats['mean']:.2f},"
                            f"{metric_stats['median']:.2f},{metric_stats['std']:.2f},"
                            f"{metric_stats['min']:.0f},{metric_stats['max']:.0f},"
                            f"{metric_stats['count']},{mos:.2f}\n")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Analyze listening test results.')
    parser.add_argument('--results-dir', default='results_0610',
                        help='Directory containing result JSON files')
    parser.add_argument('--output-dir', default=None,
                        help='Directory to save analysis results')
    parser.add_argument('--csv', default=None,
                        help='Path to output CSV file')
    parser.add_argument('--by-template', action='store_true',
                        help='Analyze results grouped by original_template_id')
    
    args = parser.parse_args()

    if args.output_dir is None:
        args.output_dir = os.path.join(args.results_dir, 'analysis')
    
    if args.csv is None:
        args.csv = os.path.join(args.output_dir, 'results.csv')
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load results
    results = load_results(args.results_dir)
    print(f"Loaded {len(results)} result files")
    
    if not results:
        print("No results found. Exiting.")
        return
    
    if args.by_template:
        # Analyze by template ID
        template_metrics_data = extract_metrics_by_template(results)
        
        # Calculate statistics for each template
        template_stats = {}
        for template_id, template_data in template_metrics_data.items():
            template_stats[template_id] = calculate_statistics(template_data)
        
        # Print statistics
        print_statistics_by_template(template_stats)
        
        # Export to CSV
        template_csv = os.path.join(args.output_dir, 'results_by_template.csv')
        export_csv_by_template(template_stats, template_csv)
        print(f"Exported template statistics to {template_csv}")
        
        # Create plots by template
        plot_metrics_by_template(template_metrics_data, args.output_dir)
        print(f"Saved template-specific plots to {args.output_dir}")
        
        # Export MOS by template
        template_mos_csv = os.path.join(args.output_dir, 'MOS.csv')
        export_mos_by_template(template_metrics_data, template_mos_csv)
        print(f"Exported MOS statistics to {template_mos_csv}")
    
    else:
        # Original analysis (overall)
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

'''
python analyze_results.py --by-template --results-dir results_0610
'''