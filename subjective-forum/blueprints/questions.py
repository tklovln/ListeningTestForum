"""
Blueprint for the questions pages of the listening test forum.
"""
from flask import Blueprint, render_template, redirect, url_for, session, current_app, abort, jsonify

questions_bp = Blueprint('questions', __name__, url_prefix='/questions')


@questions_bp.route('/<int:index>')
def show(index):
    """
    Show a specific question by index.
    
    Args:
        index: Zero-based index of the question to show
        
    Returns:
        Rendered questions.html template
    """
    # Check if participant info is available
    if 'participant' not in session:
        return redirect(url_for('participant.index'))
    
    forum_config = current_app.config.get('FORUM', {})
    branding = forum_config.get('branding', {})
    questions = forum_config.get('questions', [])
    
    # Ensure randomized questions are in session
    if 'randomized_questions' not in session:
        session['randomized_questions'] = [q.get('id') for q in questions]
    
    randomized_ids = session.get('randomized_questions', [])
    
    # Validate index
    if index < 0 or index >= len(randomized_ids):
        abort(404)
    
    # Get the question ID for this index
    question_id = randomized_ids[index]
    
    # Find the question configuration
    question = None
    for q in questions:
        if q.get('id') == question_id:
            question = q
            break
    
    if not question:
        abort(404)
    
    # Get audio models for this prompt
    audio_models = current_app.config.get('AUDIO_MODELS', {})
    prompt_id = question.get('promptId')
    
    # Log information about the models
    current_app.logger.info(f"Question models from config: {question.get('models', [])}")
    current_app.logger.info(f"Available audio models from scan: {audio_models.get(prompt_id, [])}")
    
    # Use the models directly from the question config
    # This ensures we show all models defined in the config
    
    # Check if this is the last question
    is_last = index == len(randomized_ids) - 1
    
    return render_template(
        'questions.html',
        title=branding.get('title', 'Listening Survey'),
        accent_color=branding.get('accentColor', '#888888'),
        question=question,
        question_index=index,
        total_questions=len(randomized_ids),
        is_last=is_last,
        next_url=url_for('questions.show', index=index+1) if not is_last else url_for('api.finish'),
        prev_url=url_for('questions.show', index=index-1) if index > 0 else url_for('rules.index'),
        audio_root=forum_config.get('audioRoot', 'static/audio')
    )