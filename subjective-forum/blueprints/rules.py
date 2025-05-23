"""
Blueprint for the rules page of the listening test forum.
"""
import markdown2
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, session, current_app

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
        rules_html=rules_html
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
    
    # Randomize questions if not already done
    if 'randomized_questions' not in session:
        forum_config = current_app.config.get('FORUM', {})
        questions = forum_config.get('questions', [])
        
        # Store original question order in session
        session['randomized_questions'] = [q.get('id') for q in questions]
    
    # Redirect to the first question
    return redirect(url_for('questions.show', index=0))