"""
Utility module for loading and randomizing questions from the forum configuration.
"""
import os
import random
from pathlib import Path
from typing import Dict, List, Any


def scan_audio_directory(audio_root: str) -> Dict[str, List[str]]:
    """
    Scans the audio directory to build a dictionary mapping prompt IDs to available model tags.
    
    Args:
        audio_root: Path to the root audio directory
        
    Returns:
        Dictionary mapping prompt IDs to lists of model tags
    """
    prompt_models: Dict[str, List[str]] = {}
    audio_path = Path(audio_root)
    
    if not audio_path.exists():
        return prompt_models
    
    # Scan all audio files in the directory
    for file_path in audio_path.glob("*.mp3"):
        filename = file_path.stem
        parts = filename.split("_")
        
        if len(parts) != 2:
            continue
            
        prompt_id, model_tag = parts
        
        if prompt_id not in prompt_models:
            prompt_models[prompt_id] = []
            
        prompt_models[prompt_id].append(model_tag)
    
    return prompt_models


def randomize_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Randomizes the order of questions for a participant.
    
    Args:
        questions: List of question configurations from forum.json
        
    Returns:
        Randomized list of questions
    """
    # Create a copy to avoid modifying the original
    randomized = questions.copy()
    random.shuffle(randomized)
    return randomized


def validate_questions(questions: List[Dict[str, Any]], audio_models: Dict[str, List[str]]) -> List[str]:
    """
    Validates that all required audio files for questions exist.
    
    Args:
        questions: List of question configurations
        audio_models: Dictionary mapping prompt IDs to available model tags
        
    Returns:
        List of error messages, empty if all valid
    """
    errors = []
    
    for question in questions:
        prompt_id = question.get("promptId")
        models = question.get("models", [])
        
        if not prompt_id:
            errors.append(f"Question {question.get('id', 'unknown')} is missing promptId")
            continue
            
        if prompt_id not in audio_models:
            errors.append(f"No audio files found for prompt ID: {prompt_id}")
            continue
            
        # Check that prompt audio exists
        if "prompt" not in audio_models[prompt_id]:
            errors.append(f"Missing prompt audio for prompt ID: {prompt_id}")
            
        # Check that all model audios exist
        for model in models:
            if model not in audio_models[prompt_id]:
                errors.append(f"Missing audio for model '{model}' in prompt ID: {prompt_id}")
    
    return errors