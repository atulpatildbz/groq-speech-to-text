#!/usr/bin/env python3
"""
Google Drive Speech-to-Text Sync
Monitors a Google Drive folder (account 1) for MP3 files,
transcribes them, and uploads transcripts to another folder (account 2)
"""

import os
import io
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import pickle

from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# If modifying these scopes, delete token files
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Configuration
TEMP_DOWNLOAD_DIR = Path("./temp_downloads")
TEMP_DOWNLOAD_DIR.mkdir(exist_ok=True)

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_drive_service(credentials_file, token_file):
    """
    Authenticate and return Google Drive service

    Args:
        credentials_file: Path to OAuth2 credentials JSON
        token_file: Path to store/load token pickle

    Returns:
        Google Drive service object
    """
    creds = None

    # Token file stores user's access and refresh tokens
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def list_audio_files(service, folder_id):
    """
    List all audio files in a Google Drive folder

    Args:
        service: Google Drive service
        folder_id: Folder ID to search

    Returns:
        List of file metadata dicts
    """
    query = f"'{folder_id}' in parents and (mimeType='audio/mpeg' or mimeType='audio/mp3' or mimeType='audio/wav' or mimeType='audio/m4a') and trashed=false"

    results = (
        service.files()
        .list(
            q=query,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, properties)",
            orderBy="createdTime desc",
        )
        .execute()
    )

    return results.get("files", [])


def find_transcription_file(service, folder_id, audio_filename):
    """
    Check if a transcription (.txt) file exists for an audio file

    Args:
        service: Google Drive service
        folder_id: Destination folder ID
        audio_filename: Name of the audio file

    Returns:
        File metadata dict if found, None otherwise
    """
    # Generate expected transcription filename
    transcript_filename = Path(audio_filename).stem + ".txt"

    query = f"'{folder_id}' in parents and name='{transcript_filename}' and mimeType='text/plain' and trashed=false"

    results = (
        service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
    )

    files = results.get("files", [])
    return files[0] if files else None


def needs_transcription(service, dest_folder_id, audio_file, days_threshold):
    """
    Check if an audio file needs transcription.

    Logic:
      1. If days_threshold > 0, skip audio files created more than N days ago.
      2. Skip audio files that already have a matching .txt transcript.

    Args:
        service: Google Drive service for destination folder
        dest_folder_id: Destination folder ID
        audio_file: Audio file metadata dict
        days_threshold: Only process audio files created in the last N days (0 = all files)

    Returns:
        bool: True if file needs transcription, False otherwise
    """
    # Filter by audio file creation date
    if days_threshold > 0:
        created_time_str = audio_file.get("createdTime", "")
        if created_time_str:
            # Handle 'Z' timezone indicator (UTC)
            if created_time_str.endswith("Z"):
                created_time_str = created_time_str[:-1] + "+00:00"

            file_created = datetime.fromisoformat(created_time_str)

            # Calculate threshold date
            if file_created.tzinfo:
                threshold_date = datetime.now(file_created.tzinfo) - timedelta(
                    days=days_threshold
                )
            else:
                threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

            # Skip files created before the threshold
            if file_created < threshold_date:
                return False

    # Check if a transcript already exists
    transcript_file = find_transcription_file(
        service, dest_folder_id, audio_file["name"]
    )

    # If transcript already exists, skip
    if transcript_file:
        return False

    # Audio file is recent enough and has no transcript
    return True


def download_file(service, file_id, destination_path):
    """
    Download a file from Google Drive

    Args:
        service: Google Drive service
        file_id: ID of file to download
        destination_path: Local path to save file
    """
    request = service.files().get_media(fileId=file_id)

    with open(destination_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"  Download progress: {int(status.progress() * 100)}%")


def upload_file(service, file_path, folder_id, filename=None):
    """
    Upload a file to Google Drive

    Args:
        service: Google Drive service
        file_path: Local file path to upload
        folder_id: Destination folder ID
        filename: Optional custom filename

    Returns:
        Uploaded file ID
    """
    if filename is None:
        filename = Path(file_path).name

    file_metadata = {"name": filename, "parents": [folder_id]}

    media = MediaFileUpload(file_path, resumable=True)

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    return file.get("id")


def get_or_create_processed_folder(service, parent_folder_id):
    """
    Get or create a 'processed' subfolder in the parent folder

    Args:
        service: Google Drive service
        parent_folder_id: Parent folder ID

    Returns:
        Processed folder ID
    """
    # Search for existing 'processed' folder
    query = f"name='processed' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"

    results = service.files().list(q=query, fields="files(id, name)").execute()

    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]

    # Create 'processed' folder if it doesn't exist
    file_metadata = {
        "name": "processed",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }

    folder = service.files().create(body=file_metadata, fields="id").execute()

    print(f"  Created 'processed' subfolder")
    return folder.get("id")


def move_to_processed(
    service, file_id, file_name, source_folder_id, processed_folder_id
):
    """
    Move a file to the 'processed' subfolder

    Args:
        service: Google Drive service
        file_id: File ID to move
        file_name: File name (for display)
        source_folder_id: Current parent folder ID
        processed_folder_id: Destination 'processed' folder ID
    """
    # Remove file from source folder and add to processed folder
    service.files().update(
        fileId=file_id,
        addParents=processed_folder_id,
        removeParents=source_folder_id,
        fields="id, parents",
    ).execute()

    print(f"  Moved '{file_name}' to 'processed' subfolder")


# Groq API file size limit (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024


def compress_audio(input_path, output_path):
    """
    Compress audio file using ffmpeg to fit within Groq's 25MB limit

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
        print("  Error: ffmpeg not found. Please install ffmpeg:")
        print("    macOS: brew install ffmpeg")
        print("    Ubuntu/Debian: sudo apt-get install ffmpeg")
        return False
    except Exception as e:
        print(f"  Error compressing audio: {e}")
        return False


def transcribe_audio_file(audio_path):
    """
    Transcribe audio file using Groq API.
    Compresses large files with ffmpeg before sending.

    Args:
        audio_path: Path to audio file

    Returns:
        Transcription text
    """
    audio_path = Path(audio_path)
    file_to_transcribe = audio_path
    temp_compressed_file = None

    # Check if file exceeds Groq's 25MB limit
    file_size = audio_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        file_size_mb = file_size / (1024 * 1024)
        print(f"  File exceeds 25MB limit ({file_size_mb:.1f} MB). Compressing with ffmpeg...")
        temp_compressed_file = audio_path.parent / f"temp_compressed_{audio_path.name}"
        temp_compressed_file = temp_compressed_file.with_suffix('.mp3')

        if not compress_audio(audio_path, temp_compressed_file):
            raise Exception("Failed to compress audio file with ffmpeg")

        compressed_size = temp_compressed_file.stat().st_size
        compressed_size_mb = compressed_size / (1024 * 1024)
        print(f"  Compressed to {compressed_size_mb:.1f} MB")

        if compressed_size > MAX_FILE_SIZE:
            if temp_compressed_file.exists():
                temp_compressed_file.unlink()
            raise Exception(f"File still too large after compression ({compressed_size_mb:.1f} MB)")

        file_to_transcribe = temp_compressed_file

    print(f"  Transcribing with Groq Whisper Large V3...")

    try:
        with open(file_to_transcribe, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(file_to_transcribe.name, audio_file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
                temperature=0.0,
            )

        return transcription.text
    finally:
        # Clean up temporary compressed file
        if temp_compressed_file and temp_compressed_file.exists():
            temp_compressed_file.unlink()


def process_files(
    source_service, source_folder_id, dest_service, dest_folder_id, days_threshold=0
):
    """
    Main processing function: download, transcribe, upload, move to processed

    Args:
        source_service: Google Drive service for account 1 (source)
        source_folder_id: Source folder ID
        dest_service: Google Drive service for account 2 (destination)
        dest_folder_id: Destination folder ID
        days_threshold: Only process files not transcribed in last N days (0 = all files)
    """
    print(f"\n{'=' * 60}")
    print(f"Starting sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if days_threshold > 0:
        print(
            f"Filter: Audio files created in the last {days_threshold} day(s) that have no transcript"
        )
    else:
        print(f"Filter: All files without a transcript")
    print(f"{'=' * 60}\n")

    # Get or create 'processed' subfolder
    print("Setting up 'processed' subfolder...")
    processed_folder_id = get_or_create_processed_folder(
        source_service, source_folder_id
    )

    # List audio files in source folder (excluding processed subfolder)
    print("Fetching audio files from source folder...")
    all_files = list_audio_files(source_service, source_folder_id)

    if not all_files:
        print("No audio files found in source folder.")
        return

    print(f"Found {len(all_files)} total audio file(s)")

    # Filter files that need transcription
    print(f"Filtering files...")
    files = [
        f
        for f in all_files
        if needs_transcription(dest_service, dest_folder_id, f, days_threshold)
    ]
    skipped_count = len(all_files) - len(files)
    if skipped_count > 0:
        print(
            f"Skipped {skipped_count} file(s) (too old or already transcribed)"
        )

    if not files:
        print("No files need transcription.")
        return

    print(f"Processing {len(files)} file(s) that need transcription\n")

    processed_count = 0
    error_count = 0
    local_audio_path = None
    local_transcript_path = None

    for file in files:
        file_name = file["name"]
        file_id = file["id"]
        file_size_mb = int(file.get("size", 0)) / (1024 * 1024)

        print(f"\n{'-' * 60}")
        print(f"File: {file_name}")
        print(f"Size: {file_size_mb:.2f} MB")

        try:
            # Download file
            print("Downloading...")
            local_audio_path = TEMP_DOWNLOAD_DIR / file_name
            download_file(source_service, file_id, local_audio_path)

            # Transcribe
            print("Transcribing...")
            transcript_text = transcribe_audio_file(local_audio_path)

            # Save transcript locally
            transcript_filename = Path(file_name).stem + ".txt"
            local_transcript_path = TEMP_DOWNLOAD_DIR / transcript_filename
            local_transcript_path.write_text(transcript_text)

            print(f"Transcription complete ({len(transcript_text)} characters)")

            # Upload transcript to destination folder
            print("Uploading transcript to destination folder...")
            uploaded_file_id = upload_file(
                dest_service, local_transcript_path, dest_folder_id, transcript_filename
            )
            print(f"Uploaded successfully (ID: {uploaded_file_id})")

            # Move source file to 'processed' subfolder
            print("Moving source file to 'processed' subfolder...")
            move_to_processed(
                source_service,
                file_id,
                file_name,
                source_folder_id,
                processed_folder_id,
            )

            # Clean up local files
            local_audio_path.unlink()
            local_transcript_path.unlink()

            processed_count += 1
            print("✓ Complete")

        except Exception as e:
            print(f"✗ Error processing {file_name}: {str(e)}")
            error_count += 1

            # Clean up partial downloads
            if local_audio_path and local_audio_path.exists():
                local_audio_path.unlink()
            if local_transcript_path and local_transcript_path.exists():
                local_transcript_path.unlink()

            continue

    print(f"\n{'=' * 60}")
    print(f"Sync complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Processed: {processed_count} | Errors: {error_count}")
    print(f"{'=' * 60}\n")


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Sync audio files from Google Drive Account 1, transcribe them, and upload to Account 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gdrive_sync.py --days 7     # Process audio files created in last 7 days
  python gdrive_sync.py --days 30    # Process audio files created in last 30 days
  python gdrive_sync.py --days 0     # Process all files (no date filter)
        """,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Only process audio files created in the last N days (default: 7, use 0 for all files)",
    )
    parser.add_argument(
        "--reset-auth",
        action="store_true",
        help="Reset authentication and re-authenticate both Google Drive accounts",
    )
    args = parser.parse_args()

    if args.days < 0:
        print("Error: --days must be >= 0")
        return

    # Handle reset auth flag
    if args.reset_auth:
        print("Resetting authentication...")
        SOURCE_TOKEN = "token_account1.pickle"
        DEST_TOKEN = "token_account2.pickle"

        tokens_removed = []
        if os.path.exists(SOURCE_TOKEN):
            os.remove(SOURCE_TOKEN)
            tokens_removed.append(SOURCE_TOKEN)
        if os.path.exists(DEST_TOKEN):
            os.remove(DEST_TOKEN)
            tokens_removed.append(DEST_TOKEN)

        if tokens_removed:
            print(f"  Removed: {', '.join(tokens_removed)}")
        else:
            print("  No existing token files found")
        print("  You will be prompted to re-authenticate both accounts.\n")

    # Configuration - Update these values
    SOURCE_CREDENTIALS = "credentials_account1.json"  # OAuth2 credentials for account 1
    SOURCE_TOKEN = "token_account1.pickle"  # Token storage for account 1
    SOURCE_FOLDER_ID = os.getenv("SOURCE_FOLDER_ID")  # Folder ID in account 1

    DEST_CREDENTIALS = "credentials_account2.json"  # OAuth2 credentials for account 2
    DEST_TOKEN = "token_account2.pickle"  # Token storage for account 2
    DEST_FOLDER_ID = os.getenv("DEST_FOLDER_ID")  # Folder ID in account 2

    # Validate configuration
    if not SOURCE_FOLDER_ID or not DEST_FOLDER_ID:
        print("Error: Please set SOURCE_FOLDER_ID and DEST_FOLDER_ID in .env file")
        return

    if not os.path.exists(SOURCE_CREDENTIALS):
        print(
            f"Error: {SOURCE_CREDENTIALS} not found. Please download OAuth2 credentials."
        )
        print("See GOOGLE_CLOUD_SETUP.md for instructions.")
        return

    if not os.path.exists(DEST_CREDENTIALS):
        print(
            f"Error: {DEST_CREDENTIALS} not found. Please download OAuth2 credentials."
        )
        print("See GOOGLE_CLOUD_SETUP.md for instructions.")
        return

    # Authenticate both accounts
    print("Authenticating with Google Drive accounts...")
    source_service = get_drive_service(SOURCE_CREDENTIALS, SOURCE_TOKEN)
    print("✓ Source account (account 1) authenticated")

    dest_service = get_drive_service(DEST_CREDENTIALS, DEST_TOKEN)
    print("✓ Destination account (account 2) authenticated")

    # Process files
    process_files(
        source_service, SOURCE_FOLDER_ID, dest_service, DEST_FOLDER_ID, args.days
    )


if __name__ == "__main__":
    main()
