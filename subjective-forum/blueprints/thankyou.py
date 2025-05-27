"""
Blueprint for the thank you page.
"""
from flask import Blueprint, render_template, session, current_app

thankyou_bp = Blueprint('thankyou', __name__, url_prefix='/thankyou')

@thankyou_bp.route('/')
def show():
    """
    Render the thank you page.
    Clears the session as the survey is complete.
    """
    branding = current_app.config.get('FORUM', {}).get('branding', {})
    
    # Clear session data related to the participant and their answers
    # to ensure a fresh state if they somehow navigate back or restart.
    session.pop('participant', None)
    session.pop('answers', None)
    session.pop('randomized_questions', None)
    session.pop('current_question_index', None) # If you store this
    current_app.logger.info("Session cleared for thank you page.")

    return render_template(
        'thank_you.html',
        title=branding.get('title', 'Survey Complete'),
        accent_color=branding.get('accentColor', '#888888')
    )