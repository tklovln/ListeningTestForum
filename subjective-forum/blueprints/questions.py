"""
Blueprint for the questions pages of the listening test forum.
"""
import random # Add this import
from flask import Blueprint, render_template, redirect, url_for, session, current_app, abort, jsonify
from utils.loader import randomize_questions # Import the updated function

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
    all_questions_config = forum_config.get('questions', [])
    n_questions_to_show = forum_config.get('n_questions', 0) # Get n_questions from config
    
    # Ensure randomized questions for the session are generated if not present
    if 'session_question_ids' not in session:
        session['session_question_ids'] = randomize_questions(all_questions_config, n_questions_to_show)
        # Clear any previously stored answers when starting a new set of questions
        if 'answers' in session:
            session.pop('answers')
            current_app.logger.info("Cleared previous answers for new question set.")
    
    session_question_ids = session.get('session_question_ids', [])
    
    # Validate index against the selected questions for the session
    if not session_question_ids:
        current_app.logger.error("session_question_ids is empty, redirecting to cover.")
        return redirect(url_for('cover.index'))

    if index < 0 or index >= len(session_question_ids):
        current_app.logger.warning(f"Invalid question index {index} for {len(session_question_ids)} questions. Redirecting to first question.")
        return redirect(url_for('questions.show', index=0))

    # Get the question ID for this index from the session's list
    question_id = session_question_ids[index]
    
    # Find the question configuration from the full list
    question_config = None
    for q_conf in all_questions_config:
        if q_conf.get('id') == question_id:
            question_config = q_conf
            break
    
    if not question_config:
        current_app.logger.error(f"Question config not found for ID: {question_id}. Redirecting to cover.")
        return redirect(url_for('cover.index')) # Or abort(404)
    
    # Get audio models for this prompt
    audio_models = current_app.config.get('AUDIO_MODELS', {}) # This should be populated at app start
    prompt_id = question_config.get('promptId')
    
    # Get models for the current question
    original_models_for_question = question_config.get('models', [])
    current_app.logger.info(f"Question ID: {question_id} - Original models from config: {original_models_for_question}")

    # Shuffle them for this user's view
    shuffled_models_for_question = original_models_for_question.copy() # Use .copy() to avoid modifying the original config
    random.shuffle(shuffled_models_for_question)
    current_app.logger.info(f"Question ID: {question_id} - Shuffled models for this view: {shuffled_models_for_question}")
    
    # Update the question_config for the template with the shuffled models
    # This is a shallow copy, so other parts of question_config are references
    question_to_render = question_config.copy()
    question_to_render['models'] = shuffled_models_for_question

    # Log information about the models being passed to the template
    current_app.logger.info(f"Question ID: {question_id} - Models being passed to template: {question_to_render['models']}")
    current_app.logger.info(f"Available audio models from scan for prompt {prompt_id}: {audio_models.get(prompt_id, [])}")
    
    # Check if this is the last question in the session's list
    is_last = index == len(session_question_ids) - 1
    
    debug_mode = forum_config.get('debug', False)

    return render_template(
        'questions.html',
        title=question_to_render.get('title', 'Listening Question'),
        accent_color=branding.get('accentColor', '#888888'),
        question=question_to_render, # Use the version with shuffled models
        question_index=index,
        total_questions=len(session_question_ids),
        is_last=is_last,
        next_url=url_for('questions.show', index=index+1) if not is_last else url_for('api.finish'),
        prev_url=url_for('questions.show', index=index-1) if index > 0 else url_for('rules.index'),
        audio_root=forum_config.get('audioRoot', 'static/audio'),
        debug_mode=debug_mode
    )