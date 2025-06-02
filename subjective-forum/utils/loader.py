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


def select_and_randomize_questions_for_session(
    question_templates: List[Dict[str, Any]],
    scanned_audio_data: Dict[str, Dict[str, List[str]]]
    # n_questions_to_present: int # This global parameter is removed
) -> List[Dict[str, Any]]:
    """
    Selects prompt IDs for each question template based on its 'n_to_present' value,
    shuffles models, and prepares a list of fully resolved question instances.

    Args:
        question_templates: List of question configurations (templates) from forum.json.
                            Each template should have an 'n_to_present' key.
        scanned_audio_data: Nested dictionary from scan_audio_directory:
                            {"subfolderName": {"promptId": ["model_tag1", ...]}}

    Returns:
        A list of resolved question instance dictionaries for the session.
        Each dictionary contains: 'original_question_id', 'title', 'audioSubfolder',
        'promptId' (selected), 'models' (shuffled), 'metrics'.
        Returns an empty list if errors occur or no questions can be generated.
    """
    all_session_questions: List[Dict[str, Any]] = []
    
    for q_template in question_templates:
        template_id = q_template.get("id", "UnknownTemplate")
        subfolder = q_template.get("audioSubfolder")
        n_to_present_for_template = q_template.get("n_to_present", 0)
        models_defined_in_template = q_template.get("models", [])

        if n_to_present_for_template <= 0:
            continue # Skip this template if it's not configured to present any questions

        if not subfolder or subfolder not in scanned_audio_data:
            # print(f"Warning: Audio subfolder '{subfolder}' for template '{template_id}' not found or empty. Skipping this template.")
            continue
            
        prompts_in_subfolder_dict = scanned_audio_data[subfolder]
        
        # Filter prompts to only include those that have all required models
        valid_prompt_ids = []
        for prompt_id, available_model_tags in prompts_in_subfolder_dict.items():
            # Check if this prompt has all required models (including 'prompt')
            required_models = ["prompt"] + models_defined_in_template
            has_all_models = all(model in available_model_tags for model in required_models)
            
            if has_all_models:
                valid_prompt_ids.append(prompt_id)
            else:
                missing_models = [model for model in required_models if model not in available_model_tags]
                # print(f"Skipping prompt '{prompt_id}' in subfolder '{subfolder}' for template '{template_id}': missing models {missing_models}")

        # print how many valid prompts are available in the subfolder
        # print(f"Valid prompts in subfolder '{subfolder}' for template '{template_id}': {valid_prompt_ids}")
        
        if not valid_prompt_ids:
            print(f"Warning: No valid prompts found in subfolder '{subfolder}' for template '{template_id}'. All prompts are missing required audio files. Skipping.")
            continue

        random.shuffle(valid_prompt_ids) # Shuffle available valid prompts for this subfolder
        
        # Determine how many prompts to actually select for this template
        num_to_select_for_this_template = min(n_to_present_for_template, len(valid_prompt_ids))
        
        if num_to_select_for_this_template < n_to_present_for_template:
            # print(f"Warning: Template '{template_id}' requested {n_to_present_for_template} questions, but only {len(valid_prompt_ids)} valid prompts are available in '{subfolder}'. Selecting {num_to_select_for_this_template}.")
            pass

        selected_prompt_ids_for_template = valid_prompt_ids[:num_to_select_for_this_template]
        
        for p_id in selected_prompt_ids_for_template:
            models_to_shuffle = list(models_defined_in_template)
            random.shuffle(models_to_shuffle)
            
            session_question_instance = {
                "original_question_id": template_id,
                "title": q_template.get("title"),
                "audioSubfolder": subfolder,
                "promptId": p_id,
                "models": models_to_shuffle,
                "metrics": q_template.get("metrics", [])
            }
            all_session_questions.append(session_question_instance)

    # Final shuffle of the order of all collected question instances from all templates
    random.shuffle(all_session_questions)
    
    return all_session_questions


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
    
    # 'questions' are now question templates from config
    for q_template in questions:
        template_id = q_template.get('id', 'UnknownTemplate')
        audio_subfolder = q_template.get("audioSubfolder")
        models_defined_in_template = q_template.get("models", [])

        if not audio_subfolder:
            errors.append(f"Question template '{template_id}' is missing 'audioSubfolder'.")
            continue # Cannot validate further without subfolder

        if audio_subfolder not in scanned_audio_data:
            errors.append(f"Audio subfolder '{audio_subfolder}' (for template '{template_id}') not found in scanned audio data or is empty.")
            continue # Cannot validate if subfolder data isn't present
            
        prompts_in_subfolder = scanned_audio_data[audio_subfolder]
        if not prompts_in_subfolder:
            errors.append(f"No prompt IDs found in scanned audio data for subfolder '{audio_subfolder}' (template '{template_id}'). This subfolder might be empty or lack validly named audio files.")
            continue # No prompts to validate against in this subfolder

        # For this template, check all its potential audio sources (all prompts in its designated subfolder)
        for p_id, available_model_tags_for_this_prompt in prompts_in_subfolder.items():
            # Check for the main "prompt" audio file (e.g., "001_prompt.mp3")
            if "prompt" not in available_model_tags_for_this_prompt:
                errors.append(f"Template '{template_id}': Missing 'prompt' audio file (e.g., {p_id}_prompt.mp3) for promptId '{p_id}' in subfolder '{audio_subfolder}'.")

            # Check for all comparison model audio files defined in the template
            # (e.g., "001_gt.mp3", "001_methodA.mp3")
            for model_tag_from_template in models_defined_in_template:
                if model_tag_from_template not in available_model_tags_for_this_prompt:
                    errors.append(f"Template '{template_id}': Missing audio file for model '{model_tag_from_template}' (e.g., {p_id}_{model_tag_from_template}.mp3) for promptId '{p_id}' in subfolder '{audio_subfolder}'.")
    
    return errors