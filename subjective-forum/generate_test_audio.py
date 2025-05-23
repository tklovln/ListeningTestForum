#!/usr/bin/env python3
"""
Script to generate dummy audio files for testing the Subjective Listening Test Forum.
This creates simple sine wave tones with different frequencies for each model.
"""
import os
import argparse
import numpy as np
from scipy.io import wavfile
import subprocess
from pathlib import Path

def generate_sine_wave(freq, duration, sample_rate=44100):
    """
    Generate a sine wave at the specified frequency.
    
    Args:
        freq: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        Numpy array containing the sine wave
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine = 0.5 * np.sin(2 * np.pi * freq * t)
    return sine

def save_wav(filename, audio_data, sample_rate=44100):
    """
    Save audio data as a WAV file.
    
    Args:
        filename: Output filename
        audio_data: Audio data as numpy array
        sample_rate: Sample rate in Hz
    """
    # Ensure audio data is in the correct range
    audio_data = np.clip(audio_data, -1.0, 1.0)
    
    # Convert to 16-bit PCM
    audio_data_16bit = (audio_data * 32767).astype(np.int16)
    
    # Save WAV file
    wavfile.write(filename, sample_rate, audio_data_16bit)

def convert_to_mp3(wav_file, mp3_file):
    """
    Convert WAV file to MP3 using ffmpeg.
    
    Args:
        wav_file: Input WAV file
        mp3_file: Output MP3 file
    """
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', wav_file, '-codec:a', 'libmp3lame', 
            '-qscale:a', '2', mp3_file
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Created {mp3_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting {wav_file} to MP3: {e}")
    except FileNotFoundError:
        print("ffmpeg not found. Please install ffmpeg to convert to MP3.")
        print(f"WAV file saved as {wav_file}")

def generate_test_audio(output_dir, prompt_ids, models, duration=3.0):
    """
    Generate test audio files for the specified prompt IDs and models.
    
    Args:
        output_dir: Output directory
        prompt_ids: List of prompt IDs
        models: List of model names
        duration: Duration of each audio file in seconds
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Base frequencies for different prompt IDs
    base_freqs = {
        prompt_id: 220 * (1 + i * 0.2) for i, prompt_id in enumerate(prompt_ids)
    }
    
    # Model frequency multipliers
    model_multipliers = {
        'prompt': 1.0,
        'gt': 1.0,
        'methodA': 1.2,
        'methodB': 0.8
    }
    
    # Generate audio for each prompt and model
    for prompt_id in prompt_ids:
        base_freq = base_freqs[prompt_id]
        
        # Generate prompt audio
        prompt_audio = generate_sine_wave(base_freq, duration)
        wav_file = os.path.join(output_dir, f"{prompt_id}_prompt.wav")
        mp3_file = os.path.join(output_dir, f"{prompt_id}_prompt.mp3")
        save_wav(wav_file, prompt_audio)
        convert_to_mp3(wav_file, mp3_file)
        
        # Generate model audio
        for model in models:
            if model in model_multipliers:
                freq = base_freq * model_multipliers[model]
            else:
                # For custom models, use a random multiplier between 0.7 and 1.3
                freq = base_freq * (0.7 + 0.6 * np.random.random())
            
            model_audio = generate_sine_wave(freq, duration)
            wav_file = os.path.join(output_dir, f"{prompt_id}_{model}.wav")
            mp3_file = os.path.join(output_dir, f"{prompt_id}_{model}.mp3")
            save_wav(wav_file, model_audio)
            convert_to_mp3(wav_file, mp3_file)
    
    # Clean up WAV files
    for wav_file in Path(output_dir).glob("*.wav"):
        os.remove(wav_file)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate test audio files.')
    parser.add_argument('--output-dir', default='static/audio',
                        help='Output directory for audio files')
    parser.add_argument('--prompt-ids', default='001,002,003',
                        help='Comma-separated list of prompt IDs')
    parser.add_argument('--models', default='gt,methodA,methodB',
                        help='Comma-separated list of model names')
    parser.add_argument('--duration', type=float, default=3.0,
                        help='Duration of each audio file in seconds')
    
    args = parser.parse_args()
    
    prompt_ids = args.prompt_ids.split(',')
    models = args.models.split(',')
    
    print(f"Generating test audio files for prompts: {prompt_ids}")
    print(f"Models: {models}")
    print(f"Output directory: {args.output_dir}")
    
    generate_test_audio(args.output_dir, prompt_ids, models, args.duration)
    print("Done!")

if __name__ == '__main__':
    main()