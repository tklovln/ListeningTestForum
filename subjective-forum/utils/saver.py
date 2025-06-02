"""
Utility module for saving participant results atomically.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime, timezone as dt_timezone # Renamed to avoid conflict if pytz.timezone is used
import pytz # For timezone conversion


def save(
    participant: Dict[str, Any],
    # answers now contains all details, keyed by presentation index
    answers: Dict[str, Any],
    out_dir: str = "results"
    # randomization_details parameter is removed
) -> str:
    """
    Saves participant data, including answers and their associated randomization details,
    to a JSON file atomically. The 'answers' dictionary is expected to be keyed by
    the presentation index of the question, with each value containing both the
    rated metrics and the randomization specifics for that question instance.
    
    Args:
        participant: Participant information dictionary.
        answers: Dictionary of participant answers, where keys are presentation
                 indices (e.g., "0", "1") and values are objects containing
                 metrics rated and randomization details for that question.
        out_dir: Output directory for results (default: "results").
                               
    Returns:
        Path to the saved file.
    """
    # Generate UUID for unique filename part
    uuid_hex = uuid4().hex
    
    # Get current time in UTC
    now_utc = datetime.now(dt_timezone.utc)
    
    # Define and convert to Asia/Taipei timezone
    taipei_tz = pytz.timezone('Asia/Taipei')
    now_taipei = now_utc.astimezone(taipei_tz)
    
    # Format for filename
    formatted_dt_for_filename = now_taipei.strftime('%Y%m%d_%H%M%S')
    
    filename = f"{formatted_dt_for_filename}_{uuid_hex}.json"
    
    # Keep the original Unix timestamp for storing inside the JSON data
    unix_timestamp_for_json = int(time.time())

    # Prepare output directory
    output_dir = Path(out_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Prepare data
    data = {
        "participant": participant,
        "answers": answers,
        "timestamp": unix_timestamp_for_json, # Store the precise Unix timestamp
        "uuid": uuid_hex, # Store the UUID hex
    }
    # The 'answers' dict now contains all necessary details, including randomization.
    # No separate randomization_details key at the top level of the JSON.
    
    # Write to temporary file first
    temp_file = output_dir / f".{filename}.tmp"
    with temp_file.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    
    # Atomically rename to final filename
    final_file = output_dir / filename
    temp_file.rename(final_file)
    
    return str(final_file)


def load_results(result_file: str) -> Dict[str, Any]:
    """
    Loads a saved result file.
    
    Args:
        result_file: Path to the result file
        
    Returns:
        Dictionary containing the loaded data
    """
    with open(result_file, "r", encoding="utf-8") as fp:
        return json.load(fp)