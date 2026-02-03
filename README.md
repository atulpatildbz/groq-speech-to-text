# Groq Speech-to-Text

Fast and accurate speech-to-text transcription using Groq's Whisper Large V3 API with automatic audio compression for large files.

## Features

- 🚀 **Fast transcription** using Groq's optimized Whisper Large V3 model
- 📦 **Automatic compression** for audio files larger than 25MB
- 🎵 **Multiple format support**: MP3, WAV, M4A, OGG, FLAC, WebM
- 📝 **Batch processing** for multiple audio files
- 💾 **Auto-save** transcriptions as text files
- 🔍 **Detailed metadata** including duration and detected language

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

3. Place your audio files in the `audio_files/` directory

## Usage

Run the transcription script:
```bash
python speech_to_text.py
```

The script will:
1. Find all audio files in the `audio_files/` directory
2. Automatically compress large files (>25MB) to meet API limits
3. Transcribe each audio file using Whisper Large V3
4. Save transcriptions as `.txt` files in the same directory

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

### "ffmpeg not found" error
Install ffmpeg using the commands in the Installation section.

### "Request Entity Too Large" error
The script should automatically compress large files. If this persists, try manually compressing your audio file before processing.

### "API key not found" error
Ensure your `.env` file exists and contains a valid `GROQ_API_KEY`.

## License

MIT License - feel free to use this project for any purpose.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Acknowledgments

- [Groq](https://groq.com/) for providing fast inference
- [OpenAI Whisper](https://github.com/openai/whisper) for the underlying model
