"""
Blueprint for API endpoints of the listening test forum.
"""
import os
from flask import Blueprint, jsonify, request, session, current_app, redirect, url_for, send_from_directory
from utils.saver import save

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/save', methods=['POST'])
def save_answer():
    """
    Save a question answer to the session.
    
    Expected JSON payload:
    {
        "originalQuestionId": "q1", // Template ID
        "questionIndex": 0,         // Presentation index
        "answers": {
            "metric1": 3,
            "metric2": 4,
            ...
        },
        "timeSpent": 45.2
    }
    
    Returns:
        JSON response with success status
    """
    # Check if participant info is available
    if 'participant' not in session:
        return jsonify({
            'success': False,
            'error': 'No participant session found'
        }), 401
    
    # Get JSON data
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    original_question_id = data.get('originalQuestionId') # Template ID like "q1"
    question_index = data.get('questionIndex')           # 0-based presentation index
    metric_answers = data.get('answers', {})             # Renamed for clarity
    time_spent = data.get('timeSpent')

    # Get debug mode from config
    forum_config = current_app.config.get('FORUM', {})
    debug_mode = forum_config.get('debug', False)

    # Validate required fields
    if question_index is None: # question_index can be 0, so check for None
        return jsonify({'success': False, 'error': 'Missing required field: questionIndex'}), 400
    
    if not original_question_id: # original_question_id is still useful for context/logging if needed
         return jsonify({'success': False, 'error': 'Missing required field: originalQuestionId'}), 400

    if not debug_mode and not metric_answers: # In non-debug, answers are expected
        return jsonify({'success': False, 'error': 'Missing required field: answers'}), 400
    
    # Initialize session answers dict if not present
    if 'answers' not in session:
        session['answers'] = {}
    
    # Key answers by question_index (as string, since JSON keys are strings)
    session_key_for_answer = str(question_index)

    # Store the answer along with its original template ID for context if needed later
    # The full randomization details will be merged at the /finish step
    session['answers'][session_key_for_answer] = {
        'original_template_id': original_question_id, # Store for reference
        'metrics': metric_answers,
        'timeSpent': time_spent
    }
    
    return jsonify({
        'success': True
    })


@api_bp.route('/finish', methods=['GET', 'POST'])
def finish():
    """
    Finish the test and save results.
    
    Returns:
        JSON response with success status or redirect to cover page
    """
    # Check if participant info is available
    if 'participant' not in session:
        if request.method == 'POST':
            return jsonify({
                'success': False,
                'error': 'No participant session found'
            }), 401
        else:
            return redirect(url_for('participant.index'))
    
    # Get participant, answers, and resolved question instances from session
    participant = session.get('participant', {})
    # session_answers are keyed by presentation index (e.g., "0", "1")
    # and contain {'original_template_id': ..., 'metrics': ..., 'timeSpent': ...}
    session_answers = session.get('answers', {})
    
    # session_question_instances contains the full details of each presented question,
    # including the selected promptId, subfolder, and shuffled models.
    # This list is ordered by presentation.
    session_question_instances = session.get('session_questions', [])
    
    # Combine answers with their corresponding randomization details
    final_answers_to_save = {}
    for i, q_instance_details in enumerate(session_question_instances):
        answer_key = str(i) # Answers in session are keyed by stringified index
        answer_data = session_answers.get(answer_key)
        
        if answer_data:
            final_answers_to_save[answer_key] = {
                "original_template_id": q_instance_details.get("original_question_id"),
                "audio_subfolder": q_instance_details.get("audioSubfolder"),
                "prompt_id_selected": q_instance_details.get("promptId"),
                "models_shuffled_order": q_instance_details.get("models"),
                "metrics_rated": answer_data.get("metrics"), # The actual ratings
                "time_spent_on_question": answer_data.get("timeSpent")
            }
        else:
            # This case might happen if a user somehow skips saving an answer,
            # or if there's a mismatch. Log it.
            current_app.logger.warning(f"No answer data found in session for question index {i} when finalizing results.")
            final_answers_to_save[answer_key] = {
                "original_template_id": q_instance_details.get("original_question_id"),
                "audio_subfolder": q_instance_details.get("audioSubfolder"),
                "prompt_id_selected": q_instance_details.get("promptId"),
                "models_shuffled_order": q_instance_details.get("models"),
                "metrics_rated": None, # Indicate no answer recorded
                "time_spent_on_question": None
            }

    # Save results
    try:
        results_dir = current_app.config.get('RESULTS_DIR', 'results')
        # The 'answers' argument to save() is now final_answers_to_save,
        # which already includes all details. No separate randomization_details needed.
        result_file = save(participant, final_answers_to_save, results_dir)
        
        # Clear session data
        session.pop('participant', None)
        session.pop('answers', None)
        session.pop('session_questions', None)
        
        if request.method == 'POST':
            return jsonify({
                'success': True,
                'resultFile': os.path.basename(result_file)
            })
        else:
            return redirect(url_for('cover.index'))
            
    except Exception as e:
        current_app.logger.error(f"Error saving results: {e}")
        
        if request.method == 'POST':
            return jsonify({
                'success': False,
                'error': 'Failed to save results'
            }), 500
        else:
            return redirect(url_for('questions.show', index=0))


@api_bp.route('/audio/<path:filename>')
def serve_audio(filename):
    """
    Serve audio files with appropriate cache headers.
    
    Args:
        filename: Path to the audio file relative to the audio root
        
    Returns:
        Audio file response
    """
    forum_config = current_app.config.get('FORUM', {})
    audio_root = forum_config.get('audioRoot', 'static/audio')
    
    # Log the request
    current_app.logger.info(f"Audio request received for: {filename}")
    current_app.logger.info(f"Audio root from config: {audio_root}")
    
    # Handle the path correctly
    if audio_root.startswith('static/'):
        # If audio_root starts with 'static/', we need to strip it for send_from_directory
        directory = 'static'
        # Remove 'static/' prefix from audio_root and prepend to filename
        subpath = audio_root[7:]
        if subpath:
            filename = f"{subpath}/{filename}"
    else:
        # If audio_root doesn't start with 'static/', prepend it to the directory
        directory = f"static/{audio_root}"
    
    # Check if the file exists
    import os
    full_path = os.path.join(current_app.root_path, directory, filename)
    current_app.logger.info(f"Full audio path: {full_path}")
    current_app.logger.info(f"File exists: {os.path.exists(full_path)}")
    
    current_app.logger.info(f"Serving audio from directory: {directory}, file: {filename}")
    
    return send_from_directory(
        directory,
        filename,
        mimetype='audio/mpeg',
        max_age=3600  # Cache for 1 hour
    )


@api_bp.route('/heartbeat', methods=['GET'])
def heartbeat():
    """
    Simple heartbeat endpoint to keep session alive.
    
    Returns:
        JSON response with timestamp
    """
    import time
    return jsonify({
        'timestamp': int(time.time())
    })