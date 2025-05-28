"""
Blueprint for the rules page of the listening test forum.
"""
import markdown2
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, session, current_app, flash
from utils.loader import select_and_randomize_questions_for_session # Import the new function

rules_bp = Blueprint('rules', __name__, url_prefix='/rules')


@rules_bp.route('/')
def index():
    """
    Render the rules page.
    
    Returns:
        Rendered rules.html template
    """
    forum_config = current_app.config.get('FORUM', {})
    debug_mode = forum_config.get('debug', False)

    # Check if participant info is available or if in debug mode (where participant might be auto-filled)
    if not debug_mode and 'participant' not in session:
        return redirect(url_for('participant.index'))
    elif debug_mode and 'participant' not in session:
        # This case should ideally be handled by participant.py auto-filling in debug mode.
        # If we reach here, it means participant.py didn't redirect, so we might force it.
        current_app.logger.warning("Debug mode on, but no participant in session for rules. Redirecting to participant page to auto-fill.")
        return redirect(url_for('participant.index')) # This will trigger the GET debug bypass in participant.py
    
    branding = forum_config.get('branding', {})
    
    # Get rules markdown file path
    rules_md_file = forum_config.get('rulesMarkdown', 'rules.md')
    rules_html = ""
    
    # Extract all unique metric definitions
    metric_definitions = {}
    all_questions = forum_config.get('questions', [])
    for question_config in all_questions:
        metrics_in_question = question_config.get('metrics', [])
        for metric_obj in metrics_in_question:
            if isinstance(metric_obj, dict) and 'name' in metric_obj and 'description' in metric_obj:
                if metric_obj['name'] not in metric_definitions:
                    metric_definitions[metric_obj['name']] = metric_obj['description']
    
    try:
        # Try to load and convert markdown to HTML
        rules_path = Path('config') / rules_md_file
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules_content = f.read()
                rules_html = markdown2.markdown(rules_content)
        else:
            rules_html = "<p>Rules content not found.</p>"
    except Exception as e:
        current_app.logger.error(f"Error loading rules markdown: {e}")
        rules_html = "<p>Error loading rules content.</p>"
    
    return render_template(
        'rules.html',
        title=branding.get('title', 'Listening Survey'),
        accent_color=branding.get('accentColor', '#888888'),
        rules_html=rules_html,
        metric_definitions=metric_definitions
    )


@rules_bp.route('/begin')
def begin():
    """
    Begin the test by redirecting to the first question.
    
    Returns:
        Redirect to the first question
    """
    forum_config = current_app.config.get('FORUM', {}) # Get config to check debug mode
    debug_mode = forum_config.get('debug', False)

    # Check if participant info is available or if in debug mode
    if not debug_mode and 'participant' not in session:
        return redirect(url_for('participant.index'))
    elif debug_mode and 'participant' not in session:
        current_app.logger.warning("Debug mode on, but no participant in session for rules/begin. Redirecting to participant page to auto-fill.")
        return redirect(url_for('participant.index'))
    
    # Generate and store the full, randomized question instances for the session
    if 'session_questions' not in session:
        question_templates = forum_config.get('questions', [])
        # n_questions_to_present = forum_config.get('n_questions', 0) # Global n_questions removed
        scanned_audio_data = current_app.config.get('AUDIO_MODELS', {}) # This is populated at app start

        resolved_session_questions = select_and_randomize_questions_for_session(
            question_templates,
            scanned_audio_data
            # n_questions_to_present # This argument is removed from the function
        )

        if not resolved_session_questions:
            current_app.logger.error("Failed to generate any questions for the session. Check config and audio files.")
            # Flash a message to the user and redirect them, perhaps to the cover page or an error page.
            flash("Sorry, there was an error setting up the survey. Not enough unique audio prompts may be available for the configured questions. Please contact the administrator.", "error")
            return redirect(url_for('cover.index'))
            # Or, if you have an error page: return render_template('error.html', message="...")

        session['session_questions'] = resolved_session_questions
        current_app.logger.info(f"Generated {len(resolved_session_questions)} questions for session.")
        
        # Clear any old 'answers' if starting a new set of questions
        if 'answers' in session:
            session.pop('answers')
            current_app.logger.info("Cleared previous answers for new question set.")
            
    # Redirect to the first question
    # Ensure there are questions to show
    if not session.get('session_questions'):
        current_app.logger.error("No session questions available to show, redirecting to cover.")
        flash("An unexpected error occurred. Please try starting the survey again.", "error")
        return redirect(url_for('cover.index'))

    return redirect(url_for('questions.show', index=0))