"""
Main Flask application for the Subjective Listening Test Forum.
"""
import json
import os
from pathlib import Path
from flask import Flask, session

# Import blueprints
from blueprints.cover import cover_bp
from blueprints.participant import participant_bp
from blueprints.rules import rules_bp
from blueprints.questions import questions_bp
from blueprints.api import api_bp
from blueprints.thankyou import thankyou_bp

# Import utilities
from utils.loader import scan_audio_directory, validate_questions


def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config: Test configuration dictionary (optional)
        
    Returns:
        Configured Flask application
    """
    # Create and configure the app
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')
    
    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        FORUM_CONFIG='config/forum.json',
        RESULTS_DIR='results',
        DEBUG=True,
    )
    
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(logging.DEBUG)
    app.logger.info("Application starting up in debug mode")
    
    # Override config with test config if provided
    if test_config is not None:
        app.config.update(test_config)
    
    # Ensure the results directory exists
    Path(app.config['RESULTS_DIR']).mkdir(exist_ok=True)
    
    # Load forum configuration
    try:
        with open(app.config['FORUM_CONFIG'], 'r', encoding='utf-8') as f:
            forum_config = json.load(f)
            app.config['FORUM'] = forum_config
            # log the forum config
            app.logger.info(f"Forum config: {forum_config}")

            # Scan audio directory
            audio_root = forum_config.get('audioRoot', 'static/audio')
            app.config['AUDIO_MODELS'] = scan_audio_directory(audio_root)
            
            # Validate questions
            errors = validate_questions(
                forum_config.get('questions', []),
                app.config['AUDIO_MODELS']
            )
            
            if errors:
                app.logger.error("Forum configuration validation errors:")
                for error in errors:
                    app.logger.error(f"- {error}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        app.logger.error(f"Error loading forum configuration: {e}")
        app.config['FORUM'] = {}
        app.config['AUDIO_MODELS'] = {}
    
    # Register blueprints
    app.register_blueprint(cover_bp)
    app.register_blueprint(participant_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(thankyou_bp)
    
    # Session configuration
    @app.before_request
    def make_session_permanent():
        session.permanent = True
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)