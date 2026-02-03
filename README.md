# Groq Speech-to-Text

Fast and accurate speech-to-text transcription using Groq's Whisper Large V3 API with automatic audio compression for large files.

## Two Workflows Available

This project supports **two independent workflows**:

### 1. 📁 Local Workflow (Standalone)
Transcribe audio files from your local `./audio_files` directory.
- ✅ Simple and fast
- ✅ No cloud setup needed (except Groq API key)
- ✅ Great for quick transcriptions

👉 **Script**: `speech_to_text.py`

### 2. ☁️ Google Drive Workflow (Automated)
Sync between two Google Drive accounts: download from Account 1, transcribe, upload to Account 2.
- ✅ Cross-account automation
- ✅ Moves processed files to "processed" subfolder
- ✅ Can run manually or on a schedule (minimum 2-hour intervals)

👉 **Script**: `gdrive_sync.py` (see [SETUP_GUIDE.md](SETUP_GUIDE.md) for setup)

---

## Features

- 🚀 **Fast transcription** using Groq's optimized Whisper Large V3 model
- 📦 **Automatic compression** for audio files larger than 25MB
- 🎵 **Multiple format support**: MP3, WAV, M4A, OGG, FLAC, WebM
- 📝 **Batch processing** for multiple audio files
- 💾 **Auto-save** transcriptions as text files
- 🔍 **Detailed metadata** including duration and detected language
- ☁️ **Google Drive integration** for automated cross-account workflows

## Requirements

- Python 3.7+
- ffmpeg (for audio compression)
- Groq API key

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd groq-speech-to-text
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install ffmpeg (if not already installed):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Setup

1. Get your Groq API key from [Groq Console](https://console.groq.com/)

2. Create a `.env` file in the project root:
```bash
GROQ_API_KEY=your_api_key_here
```

## Usage

### Option 1: Local Workflow (Simple)

**For quick local transcriptions:**

1. Place your audio files in the `audio_files/` directory

2. Run the transcription script:
```bash
python speech_to_text.py
```

The script will:
- Find all audio files in the `audio_files/` directory
- Automatically compress large files (>25MB) to meet API limits
- Transcribe each audio file using Whisper Large V3
- Save transcriptions as `.txt` files in the same directory

### Option 2: Google Drive Workflow (Automated)

**For automated cross-account transcription:**

1. Complete the Google Drive setup (see [SETUP_GUIDE.md](SETUP_GUIDE.md))

2. Run manually:
```bash
python gdrive_sync.py
```

3. Or run on a schedule (every 2+ hours):
```bash
python gdrive_scheduler.py
```

The script will:
- Download MP3 files from Google Drive (Account 1)
- Transcribe using Groq
- Upload `.txt` files to Google Drive (Account 2)
- Move original MP3s to "processed" subfolder in Account 1

**Setup required**: OAuth credentials, folder IDs. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step instructions.

## Supported Audio Formats

- MP3 (`.mp3`)
- WAV (`.wav`)
- M4A (`.m4a`)
- OGG (`.ogg`)
- FLAC (`.flac`)
- WebM (`.webm`)

## How It Works

1. **File Detection**: Scans the `audio_files/` directory for supported audio formats
2. **Size Check**: Checks if files exceed the 25MB API limit
3. **Compression**: If needed, compresses audio to 16kHz mono, 32kbps using ffmpeg
4. **Transcription**: Sends audio to Groq's Whisper Large V3 model
5. **Output**: Saves transcription with metadata (duration, language) as text files

## Example Output

```
Found 1 audio file(s)
--------------------------------------------------
File size: 51.68 MB
File exceeds 25MB limit. Compressing...
Compressed to: 12.92 MB
Transcribing: interview.mp3

==================================================
File: interview.mp3
==================================================

Transcription:
[Your transcribed text here...]

Duration: 3386.64 seconds
Detected Language: en

Saved transcription to: audio_files/interview.txt
--------------------------------------------------
```

## Configuration

You can modify the transcription settings in `speech_to_text.py`:

- **Model**: `whisper-large-v3` (best accuracy)
- **Temperature**: `0.0` (more consistent results)
- **Response Format**: `verbose_json` (includes timestamps and metadata)
- **Language**: Auto-detected (or specify with `language="en"`)

## API Limits

- **File size**: 25MB maximum (automatically handled by compression)
- **Rate limits**: Based on your Groq plan
- **Free tier**: Uses Whisper Large V3 model

## Troubleshooting

### Local Workflow (`speech_to_text.py`)

**"ffmpeg not found" error**
- Install ffmpeg using the commands in the Installation section.

**"Request Entity Too Large" error**
- The script should automatically compress large files. If this persists, try manually compressing your audio file before processing.

**"API key not found" error**
- Ensure your `.env` file exists and contains a valid `GROQ_API_KEY`.

### Google Drive Workflow (`gdrive_sync.py`)

**"credentials_account1.json not found"**
- Download OAuth credentials from Google Cloud Console
- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions

**"Please set SOURCE_FOLDER_ID and DEST_FOLDER_ID"**
- Add folder IDs to your `.env` file
- Get folder IDs from Google Drive URLs

For more troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md)

## License

MIT License - feel free to use this project for any purpose.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Acknowledgments

- [Groq](https://groq.com/) for providing fast inference
- [OpenAI Whisper](https://github.com/openai/whisper) for the underlying model
