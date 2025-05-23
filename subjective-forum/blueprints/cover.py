"""
Blueprint for the cover page of the listening test forum.
"""
from flask import Blueprint, render_template, current_app

cover_bp = Blueprint('cover', __name__)


@cover_bp.route('/')
def index():
    """
    Render the cover page.
    
    Returns:
        Rendered cover.html template
    """
    forum_config = current_app.config.get('FORUM', {})
    branding = forum_config.get('branding', {})
    
    return render_template(
        'cover.html',
        title=branding.get('title', 'Listening Survey'),
        accent_color=branding.get('accentColor', '#888888'),
        cover_animation=branding.get('coverAnimation', 'counter')
    )