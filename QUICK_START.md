# Quick Start Guide

## What This Script Does

1. ✅ **Checks** Google Drive Account 1 for audio files
2. ✅ **Filters** files that haven't been transcribed in the last X days (configurable)
3. ✅ **Downloads** those audio files locally
4. ✅ **Transcribes** them using Groq's Whisper Large V3
5. ✅ **Uploads** the `.txt` transcriptions to Google Drive Account 2
6. ✅ **Moves** processed audio files to a "processed" subfolder in Account 1

## Prerequisites

- Python 3.7+
- Google Cloud account (free tier works)
- Two Google Drive accounts (or one account with two folders)
- Groq API key (get from [console.groq.com](https://console.groq.com))

## Setup Steps (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Google Cloud
Follow the detailed guide: **[GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md)**

**Quick summary:**
- Enable Google Drive API
- Create OAuth credentials:
  - **Application type: Desktop app** (important!)
  - Download JSON file
- Add both email addresses as test users
- Copy credentials file: `cp credentials_account1.json credentials_account2.json`

**Why same credentials work for both accounts?** The credentials file identifies your APPLICATION, not the user. Each account authenticates separately via browser and gets its own token. See [OAUTH_EXPLAINED.md](OAUTH_EXPLAINED.md) for details.

### 3. Get Folder IDs

**Source Folder (Account 1):**
1. Open folder in Google Drive
2. Copy ID from URL: `https://drive.google.com/drive/folders/1abc...xyz`
   - The ID is the part after `/folders/`

**Destination Folder (Account 2):**
1. Open folder in Google Drive  
2. Copy ID from URL (same way)

### 4. Configure Environment

Create/edit `.env` file:
```bash
GROQ_API_KEY=your_groq_api_key_here
SOURCE_FOLDER_ID=your_source_folder_id_here
DEST_FOLDER_ID=your_destination_folder_id_here
```

### 5. First Run (Authentication)

```bash
python gdrive_sync.py --days 7
```

**What happens:**
- Browser opens → Sign in with Account 1 → Allow access
- Browser opens → Sign in with Account 2 → Allow access
- Script processes files

**Note:** After first run, tokens are saved. No need to authenticate again!

## Usage

### Process files not transcribed in last 7 days (default)
```bash
python gdrive_sync.py --days 7
```

### Process files not transcribed in last 30 days
```bash
python gdrive_sync.py --days 30
```

### Process all files (ignore date filter)
```bash
python gdrive_sync.py --days 0
```

### Scheduled runs (every 2+ hours)
```bash
python gdrive_scheduler.py
```

## How Date Filtering Works

The script checks:
1. Does a `.txt` file exist in the destination folder with the same name?
2. If yes, when was it last modified?
3. If no `.txt` exists OR it's older than X days → transcribe

**Example:**
- `audio1.mp3` → No `audio1.txt` → **Will transcribe**
- `audio2.mp3` → `audio2.txt` exists, modified 3 days ago, `--days 7` → **Skip** (transcribed recently)
- `audio3.mp3` → `audio3.txt` exists, modified 10 days ago, `--days 7` → **Will transcribe** (older than threshold)

## File Structure

```
Your Project/
├── gdrive_sync.py              # Main script
├── credentials_account1.json   # OAuth credentials (from Google Cloud)
├── credentials_account2.json   # Same file (copy)
├── token_account1.pickle       # Auto-generated (after first auth)
├── token_account2.pickle       # Auto-generated (after first auth)
├── .env                        # Your API keys and folder IDs
└── temp_downloads/             # Temporary files (auto-created)
```

## Troubleshooting

**"Access denied"**
- Make sure both emails are added as test users in Google Cloud OAuth consent screen
- Delete `.pickle` files and re-authenticate

**"Cannot find folder"**
- Verify folder IDs are correct (copy from URL again)
- Make sure authenticated account has access to folders

**"credentials_account1.json not found"**
- Download OAuth credentials from Google Cloud Console
- Make sure file is in project root directory

**Need more help?**
- See [GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md) for detailed setup
- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for original workflow details
