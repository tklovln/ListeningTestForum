#!/bin/bash
# Script to set up and run the Subjective Listening Test Forum

# Exit on error
set -e

# Print commands
set -x

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories if they don't exist
mkdir -p static/audio
mkdir -p results

# Check if there are audio files
AUDIO_COUNT=$(find static/audio -name "*.mp3" | wc -l)
if [ "$AUDIO_COUNT" -eq 0 ]; then
    echo "Warning: No audio files found in static/audio directory."
    echo "Please add audio files following the naming convention:"
    echo "  {promptId}_prompt.mp3 for reference audio"
    echo "  {promptId}_{model}.mp3 for comparison samples"
fi

# Run the application
export FLASK_APP=app.py
export FLASK_ENV=development

# Check if port is specified
if [ -z "$1" ]; then
    PORT=5000
else
    PORT=$1
fi

# Run Flask
flask run --host=0.0.0.0 --port=$PORT