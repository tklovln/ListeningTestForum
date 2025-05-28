"""
Utility module for loading and randomizing questions from the forum configuration.
"""
import os
import random
from pathlib import Path
from typing import Dict, List, Any


def scan_audio_directory(audio_root: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Scans subdirectories within the audio_root to build a nested dictionary.
    Maps subfolder_name -> prompt_id -> list_of_model_tags.
    
    Args:
        audio_root: Path to the root audio directory (e.g., 'static/audio')
        
    Returns:
        Nested dictionary: {"subfolderName": {"promptId": ["model_tag1", "model_tag2"]}}
    """
    scanned_data: Dict[str, Dict[str, List[str]]] = {}
    root_path = Path(audio_root)

    if not root_path.is_dir():
        # print(f"Audio root path {audio_root} does not exist or is not a directory.")
        return scanned_data

    for subfolder_path in root_path.iterdir():
        if subfolder_path.is_dir():
            subfolder_name = subfolder_path.name
            prompt_models_in_subfolder: Dict[str, List[str]] = {}
            
            for file_path in subfolder_path.glob("*.mp3"):
                filename = file_path.stem
                parts = filename.split("_")
                
                if len(parts) != 2:
                    # print(f"Skipping file with unexpected format: {file_path}")
                    continue
                    
                prompt_id, model_tag = parts
                
                if prompt_id not in prompt_models_in_subfolder:
                    prompt_models_in_subfolder[prompt_id] = []
                
                if model_tag not in prompt_models_in_subfolder[prompt_id]: # Avoid duplicates if any
                    prompt_models_in_subfolder[prompt_id].append(model_tag)
            
            if prompt_models_in_subfolder: # Only add subfolder if it contains valid audio files
                scanned_data[subfolder_name] = prompt_models_in_subfolder
                
    return scanned_data


def randomize_questions(questions: List[Dict[str, Any]], n_questions: int = 0) -> List[str]:
    """
    Randomizes the order of question IDs and selects a subset.
    
    Args:
        questions: List of question configurations from forum.json
        n_questions: The number of questions to select for the participant.
                     If 0 or greater than available, all questions are used.
                     
    Returns:
        A list of selected and randomized question IDs.
    """
    question_ids = [q.get("id") for q in questions if q.get("id")]
    random.shuffle(question_ids)
    
    if n_questions <= 0 or n_questions > len(question_ids):
        return question_ids
    
    return question_ids[:n_questions]


def validate_questions(questions: List[Dict[str, Any]], scanned_audio_data: Dict[str, Dict[str, List[str]]]) -> List[str]:
    """
    Validates that all required audio files for questions exist based on their subfolder.
    
    Args:
        questions: List of question configurations from forum.json
        scanned_audio_data: Nested dictionary from scan_audio_directory:
                            {"subfolderName": {"promptId": ["model_tag1", ...]}}
        
    Returns:
        List of error messages, empty if all valid
    """
    errors = []
    
    for question_config in questions:
        question_id_str = question_config.get('id', 'unknown')
        prompt_id = question_config.get("promptId")
        audio_subfolder = question_config.get("audioSubfolder")
        models_for_question = question_config.get("models", [])
        
        if not prompt_id:
            errors.append(f"Question {question_id_str} is missing 'promptId'.")
            continue
        if not audio_subfolder:
            errors.append(f"Question {question_id_str} (promptId: {prompt_id}) is missing 'audioSubfolder'.")
            continue
            
        if audio_subfolder not in scanned_audio_data:
            errors.append(f"Audio subfolder '{audio_subfolder}' specified in question {question_id_str} (promptId: {prompt_id}) not found or empty in scanned audio data.")
            continue
            
        models_in_subfolder_for_prompt = scanned_audio_data[audio_subfolder].get(prompt_id)
        
        if not models_in_subfolder_for_prompt:
            errors.append(f"No audio files found for prompt ID '{prompt_id}' in subfolder '{audio_subfolder}' (Question {question_id_str}).")
            continue
            
        # Check that prompt audio exists (e.g., "001_prompt.mp3")
        if "prompt" not in models_in_subfolder_for_prompt:
            errors.append(f"Missing prompt audio for prompt ID '{prompt_id}' in subfolder '{audio_subfolder}' (Question {question_id_str}).")
            
        # Check that all model audios exist (e.g., "001_gt.mp3", "001_methodA.mp3")
        for model_tag in models_for_question:
            if model_tag not in models_in_subfolder_for_prompt:
                errors.append(f"Missing audio for model '{model_tag}' for prompt ID '{prompt_id}' in subfolder '{audio_subfolder}' (Question {question_id_str}).")
    
    return errors