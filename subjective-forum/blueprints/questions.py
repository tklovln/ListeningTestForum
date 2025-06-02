"""
Blueprint for the questions pages of the listening test forum.
"""
import random
from flask import Blueprint, render_template, redirect, url_for, session, current_app, abort, jsonify, flash
# from utils.loader import randomize_questions # This function is replaced
# No specific import needed from loader for this blueprint anymore, as session setup is in rules_bp

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
    forum_config = current_app.config.get('FORUM', {})
    debug_mode = forum_config.get('debug', False)

    # Check if participant info is available or if in debug mode
    if not debug_mode and 'participant' not in session:
        return redirect(url_for('participant.index'))
    elif debug_mode and 'participant' not in session:
        current_app.logger.warning("Debug mode on, but no participant in session for questions. Redirecting to participant page to auto-fill.")
        return redirect(url_for('participant.index')) # This will trigger the GET debug bypass in participant.py
    
    branding = forum_config.get('branding', {})
    
    # Retrieve the list of fully resolved and randomized question instances for the session
    session_questions = session.get('session_questions', [])

    if not session_questions:
        current_app.logger.error("No 'session_questions' found in session. Redirecting to rules to regenerate.")
        flash("Your session seems to have expired or an error occurred. Please start from the rules page again.", "warning")
        return redirect(url_for('rules.index')) # rules.index will redirect to rules.begin if needed

    # Validate index
    if not 0 <= index < len(session_questions):
        current_app.logger.warning(f"Invalid question index {index} for {len(session_questions)} session questions. Redirecting to first question.")
        return redirect(url_for('questions.show', index=0))

    # Get the specific question instance for this index
    question_to_render = session_questions[index]
    print("question_to_render", question_to_render)
    
    # 'question_to_render' already contains:
    # original_question_id, title, audioSubfolder, promptId (selected), models (shuffled), metrics

    current_app.logger.info(f"Showing question index {index}: original_id='{question_to_render.get('original_question_id')}', promptId='{question_to_render.get('promptId')}', subfolder='{question_to_render.get('audioSubfolder')}'")
    current_app.logger.info(f"Models for this instance: {question_to_render.get('models')}")

    is_last = index == len(session_questions) - 1
    debug_mode = forum_config.get('debug', False) # Still useful for client-side debug flags

    return render_template(
        'questions.html',
        title=question_to_render.get('title', 'Listening Question'), # Title from the resolved question
        accent_color=branding.get('accentColor', '#888888'),
        question=question_to_render, # Pass the fully resolved question object
        question_index=index,
        total_questions=len(session_questions),
        is_last=is_last,
        next_url=url_for('questions.show', index=index+1) if not is_last else url_for('thankyou.show'), # Changed to thankyou.show
        prev_url=url_for('questions.show', index=index-1) if index > 0 else url_for('rules.index'),
        audio_root=forum_config.get('audioRoot', 'static/audio'),
        debug_mode=debug_mode
    )