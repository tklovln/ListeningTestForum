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
    # Check if participant info is available
    if 'participant' not in session:
        return redirect(url_for('participant.index'))
    
    forum_config = current_app.config.get('FORUM', {})
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
    # Check if participant info is available
    if 'participant' not in session:
        return redirect(url_for('participant.index'))
    
    # Randomize questions if not already done
    if 'randomized_questions' not in session:
        forum_config = current_app.config.get('FORUM', {})
        questions = forum_config.get('questions', [])
        
        # Store original question order in session
        session['randomized_questions'] = [q.get('id') for q in questions]
    
    # Redirect to the first question
    return redirect(url_for('questions.show', index=0))