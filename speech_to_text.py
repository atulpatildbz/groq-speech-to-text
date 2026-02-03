#!/usr/bin/env python3
"""
Speech-to-Text using Groq API (Whisper Large V3)
Handles large files by compressing them if needed
"""
import os
import subprocess
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Groq API file size limit (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024

def compress_audio(input_path: Path, output_path: Path) -> bool:
    """
    Compress audio file using ffmpeg

    Args:
        input_path: Path to input audio file
        output_path: Path to output compressed file

    Returns:
        bool: True if successful
    """
    try:
        # Use ffmpeg to compress audio to smaller size
        # -ar 16000: Set sample rate to 16kHz (sufficient for speech)
        # -ac 1: Convert to mono
        # -b:a 32k: Set audio bitrate to 32kbps
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-ar", "16000",
            "-ac", "1",
            "-b:a", "32k",
            "-y",  # Overwrite output file if exists
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        return False
    except Exception as e:
        print(f"Error compressing audio: {e}")
        return False

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes"""
    return file_path.stat().st_size / (1024 * 1024)

def transcribe_audio(audio_file_path: Path) -> dict:
    """
    Transcribe audio file using Groq's Whisper Large V3 model

    Args:
        audio_file_path: Path to the audio file

    Returns:
        dict: Transcription result with text and metadata
    """
    file_to_transcribe = audio_file_path
    temp_compressed_file = None

    # Check if file is too large
    file_size_mb = get_file_size_mb(audio_file_path)
    print(f"File size: {file_size_mb:.2f} MB")

    if file_size_mb > 25:
        print(f"File exceeds 25MB limit. Compressing...")
        temp_compressed_file = audio_file_path.parent / f"temp_compressed_{audio_file_path.name}"
        temp_compressed_file = temp_compressed_file.with_suffix('.mp3')

        if not compress_audio(audio_file_path, temp_compressed_file):
            raise Exception("Failed to compress audio file")

        compressed_size_mb = get_file_size_mb(temp_compressed_file)
        print(f"Compressed to: {compressed_size_mb:.2f} MB")

        if compressed_size_mb > 25:
            if temp_compressed_file.exists():
                temp_compressed_file.unlink()
            raise Exception(f"File still too large after compression ({compressed_size_mb:.2f} MB)")

        file_to_transcribe = temp_compressed_file

    print(f"Transcribing: {audio_file_path.name}")

    try:
        with open(file_to_transcribe, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(file_to_transcribe.name, audio_file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",  # Get detailed output with timestamps
                temperature=0.0  # Lower temperature for more consistent results
            )
        return transcription
    finally:
        # Clean up temporary compressed file
        if temp_compressed_file and temp_compressed_file.exists():
            temp_compressed_file.unlink()

def main():
    """Main function to process audio files"""
    audio_dir = Path("./audio_files")

    if not audio_dir.exists():
        print(f"Error: Directory {audio_dir} does not exist")
        return

    # Get all audio files (common formats)
    audio_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"]
    audio_files = [f for f in audio_dir.iterdir() if f.suffix.lower() in audio_extensions]

    if not audio_files:
        print(f"No audio files found in {audio_dir}")
        return

    print(f"Found {len(audio_files)} audio file(s)")
    print("-" * 50)

    for audio_file in audio_files:
        try:
            result = transcribe_audio(audio_file)

            print(f"\n{'='*50}")
            print(f"File: {audio_file.name}")
            print(f"{'='*50}")
            print(f"\nTranscription:\n{result.text}")

            # Optional: Print additional metadata
            if hasattr(result, 'duration'):
                print(f"\nDuration: {result.duration:.2f} seconds")
            if hasattr(result, 'language'):
                print(f"Detected Language: {result.language}")

            # Save transcription to text file
            output_file = audio_file.with_suffix('.txt')
            output_file.write_text(result.text)
            print(f"\nSaved transcription to: {output_file}")
            print("-" * 50)

        except Exception as e:
            print(f"Error processing {audio_file.name}: {str(e)}")
            continue

if __name__ == "__main__":
    main()
