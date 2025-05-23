"""
Blueprint for the participant information page.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash

participant_bp = Blueprint('participant', __name__, url_prefix='/participant')


@participant_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Handle participant information form.
    
    GET: Render the participant form
    POST: Process form submission and store in session
    
    Returns:
        Rendered participant.html template or redirect to rules page
    """
    forum_config = current_app.config.get('FORUM', {})
    participant_fields = forum_config.get('participantFields', [])
    branding = forum_config.get('branding', {})
    debug_mode = forum_config.get('debug', False)

    if request.method == 'GET' and debug_mode:
        # In debug mode, bypass form with dummy data
        dummy_participant_data = {field.get('key'): f"debug_{field.get('key')}" for field in participant_fields if field.get('key')}
        dummy_participant_data['debug_mode_skip'] = True # Mark as debug skip
        session['participant'] = dummy_participant_data
        current_app.logger.info("Debug mode: Bypassing participant form with dummy data.")
        # Initialize answers if not already present
        if 'answers' not in session:
            session['answers'] = {}
        return redirect(url_for('rules.index'))

    if request.method == 'POST':
        # Process form submission
        participant_data = {}
        form_valid = True
        
        # Validate and collect form data
        for field in participant_fields:
            field_key = field.get('key')
            field_required = field.get('required', False)
            
            if not field_key:
                continue
                
            field_value = request.form.get(field_key, '').strip()
            
            # Check required fields
            if field_required and not field_value:
                flash(f"Field '{field.get('label', field_key)}' is required", 'error')
                form_valid = False
                continue
                
            participant_data[field_key] = field_value
        
        # If form is valid, store in session and redirect to rules
        if form_valid:
            session['participant'] = participant_data
            
            # Initialize answers if not already present
            if 'answers' not in session:
                session['answers'] = {}
                
            return redirect(url_for('rules.index'))
    
    # For GET requests or invalid form submissions, render the form
    return render_template(
        'participant.html',
        title=branding.get('title', 'Listening Survey'),
        accent_color=branding.get('accentColor', '#888888'),
        participant_fields=participant_fields,
        participant_data=session.get('participant', {})
    )