# Audio Files Directory

This directory should contain all audio files for the listening test.

## File Naming Convention

Audio files must follow this naming convention:

- `{promptId}_prompt.mp3` - Reference audio for a prompt
- `{promptId}_{model}.mp3` - Comparison audio for a specific model

For example:
- `001_prompt.mp3` - Reference audio for prompt 001
- `001_gt.mp3` - Ground truth comparison for prompt 001
- `001_methodA.mp3` - Method A comparison for prompt 001
- `001_methodB.mp3` - Method B comparison for prompt 001

## Configuration

Make sure the `promptId` values in your `config/forum.json` file match the prompt IDs in your audio filenames.

## Audio Format

- MP3 format is recommended for broad browser compatibility
- 44.1kHz, 128kbps or higher bitrate is recommended for good audio quality
- All audio files for a given prompt should have the same duration
- Keep file sizes reasonable for web delivery (under 2MB per file if possible)

## Example Structure

```
audio/
├── 001_prompt.mp3
├── 001_gt.mp3
├── 001_methodA.mp3
├── 001_methodB.mp3
├── 002_prompt.mp3
├── 002_gt.mp3
├── 002_methodA.mp3
├── 002_methodB.mp3
└── ...