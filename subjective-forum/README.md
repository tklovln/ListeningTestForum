# Subjective Listening Test Forum

A Flask-based web application for conducting subjective listening tests for research papers.

## Features

- JSON-driven configuration - customize texts, audio folders, and colors by editing a single config file
- Modular architecture with independent blueprints for each domain concept
- Aggressive audio pre-loading with graceful fallback to avoid jank on first play
- Stateless front-end with local buffering of participant answers
- Instagram "Stories"-like question navigation
- Fully responsive design for both mobile and desktop
- Atomic result saving to prevent data loss

## Folder Structure

```
subjective-forum/
├── app.py                 # Flask entry
├── config/                # All change-me files live here
│   ├── forum.json         # Main configuration file
│   └── rules.md           # Test instructions in markdown
├── blueprints/
│   ├── cover.py           # Landing page
│   ├── participant.py     # Participant information form
│   ├── rules.py           # Test instructions
│   ├── questions.py       # Question display and navigation
│   └── api.py             # AJAX endpoints (save, heartbeat, audio list)
├── static/
│   ├── css/               # CSS styles
│   ├── js/modules/        # JavaScript modules
│   └── audio/             # Audio files (not included)
├── templates/
│   ├── base.html          # Base template
│   ├── cover.html         # Landing page template
│   ├── participant.html   # Participant form template
│   ├── rules.html         # Rules page template
│   └── questions.html     # Questions page template
├── utils/
│   ├── loader.py          # Random prompt-id logic, audio scan
│   └── saver.py           # Writes result JSON atomically
└── results/               # Output directory for participant results
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Add your audio files to the `static/audio/` directory following the naming convention:
   - `{promptId}_prompt.mp3` for reference audio
   - `{promptId}_{model}.mp3` for comparison samples
   
   For example:
   - `001_prompt.mp3`
   - `001_gt.mp3`
   - `001_methodA.mp3`
   - `001_methodB.mp3`

5. Configure your test by editing `config/forum.json`

## Running the Application

```
flask run
```

Or for production:

```
gunicorn app:create_app()
```

## Configuration

Edit `config/forum.json` to customize:

- Branding (title, accent color)
- Participant information fields
- Test instructions (via `rules.md`)
- Questions and metrics
- Audio file paths

## Results

Participant results are saved as JSON files in the `results/` directory with the naming format:
`{timestamp}_{uuid}.json`

## License

MIT