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
        "questionId": "q1",
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
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    question_id = data.get('questionId')
    answers = data.get('answers', {}) # Default to empty dict if not provided
    time_spent = data.get('timeSpent')

    # Get debug mode from config
    forum_config = current_app.config.get('FORUM', {})
    debug_mode = forum_config.get('debug', False)

    if not debug_mode: # Only do strict validation if not in debug mode
        if not question_id or not answers: # 'answers' could be an empty dict in debug mode
            return jsonify({
                'success': False,
                'error': 'Missing required fields (questionId or answers)'
            }), 400
        # Potentially add more validation here for non-debug mode,
        # e.g., check if all expected metrics are present in answers.
    elif not question_id: # In debug mode, only question_id is strictly required
         return jsonify({
            'success': False,
            'error': 'Missing required field: questionId'
        }), 400
    
    # Initialize answers dict if not present
    if 'answers' not in session:
        session['answers'] = {}
    
    # Save to session
    session['answers'][question_id] = {
        'metrics': answers,
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
    
    # Get participant and answers from session
    participant = session.get('participant', {})
    answers = session.get('answers', {})
    
    # Save results
    try:
        results_dir = current_app.config.get('RESULTS_DIR', 'results')
        result_file = save(participant, answers, results_dir)
        
        # Clear session data
        session.pop('participant', None)
        session.pop('answers', None)
        session.pop('randomized_questions', None)
        
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