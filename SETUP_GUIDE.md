# Quick Setup Guide - Google Drive Integration

## Your Setup Answers:
- ✅ Files will be **moved to "processed" subfolder** after transcription
- ✅ Same filename = **overwrite** (though unlikely to happen)
- ✅ You have a Google Cloud project already

## Important: You Only Need ONE Google Cloud Project!

You can use the **same Google Cloud project and same credentials** for both accounts. You just need to:
1. Add both email addresses as "test users"
2. Authenticate with each account separately (browser will prompt)

## Step-by-Step Setup

### 1. Enable Google Drive API

1. Go to your [Google Cloud Console](https://console.cloud.google.com/)
2. Select your existing project
3. Navigate to: **APIs & Services** → **Library**
4. Search for: **"Google Drive API"**
5. Click **"Enable"**

### 2. Configure OAuth Consent Screen

1. Go to: **APIs & Services** → **OAuth consent screen**
2. If not configured yet:
   - **User Type**: External
   - **App name**: "Speech-to-Text Sync" (or any name)
   - **User support email**: Your email
   - **Developer contact email**: Your email
3. Click **Save and Continue**
4. **Scopes**: Skip (we'll add programmatically)
5. **Test users** - ADD BOTH EMAILS:
   - Click "+ ADD USERS"
   - Add email for Account 1 (source)
   - Add email for Account 2 (destination)
   - Click **Save and Continue**

### 3. Create OAuth Credentials

1. Go to: **APIs & Services** → **Credentials**
2. Click: **+ CREATE CREDENTIALS** → **OAuth client ID**
3. **Application type**: Desktop app
4. **Name**: "Drive Sync Desktop"
5. Click **CREATE**
6. Click **DOWNLOAD JSON**
7. Save the downloaded file as: **`credentials_account1.json`** in your project folder

**Important**: We'll use the same credentials file for both accounts! Just copy it:

```bash
cp credentials_account1.json credentials_account2.json
```

### 4. Get Folder IDs

#### Source Folder (Account 1):
1. Sign in to Google Drive with **Account 1**
2. Create or navigate to a folder (e.g., "Audio to Transcribe")
3. Create a subfolder called "processed" inside it
4. Click on the main folder, look at URL:
   ```
   https://drive.google.com/drive/folders/1abc...xyz
                                           ^^^^^^^^^^^
   ```
5. Copy the folder ID (the part after `/folders/`)

#### Destination Folder (Account 2):
1. Sign in to Google Drive with **Account 2**
2. Create or navigate to a folder (e.g., "Transcriptions")
3. Look at the URL and copy the folder ID

### 5. Update .env File

Edit `.env` and add the folder IDs:

```bash
GROQ_API_KEY=your_groq_api_key_here

# Add these:
SOURCE_FOLDER_ID=paste_your_source_folder_id_here
DEST_FOLDER_ID=paste_your_destination_folder_id_here
```

### 6. Install Dependencies

```bash
pip install -r requirements.txt
```

### 7. First Run - Authentication

```bash
python gdrive_sync.py
```

**What will happen:**

1. **Browser opens for Account 1**:
   - Sign in with Account 1 (source)
   - You'll see a warning "Google hasn't verified this app" - this is normal
   - Click "Advanced" → "Go to Speech-to-Text Sync (unsafe)"
   - Click "Allow" to grant Drive access

2. **Browser opens for Account 2**:
   - Sign in with Account 2 (destination)
   - Same warning - click Advanced → Continue
   - Click "Allow"

3. **Script runs**:
   - Checks for audio files
   - Processes them
   - Moves originals to "processed" subfolder

**You're done!** Tokens are saved locally - no need to authenticate again.

## Usage

### Manual Run (Recommended)
```bash
python gdrive_sync.py
```

### Scheduled Run (Every 2+ Hours)
Edit `gdrive_scheduler.py` to change interval:
```python
SYNC_INTERVAL_HOURS = 2  # Change to 3, 4, 6, etc.
```

Run scheduler:
```bash
python gdrive_scheduler.py
```

Press Ctrl+C to stop.

## How It Works

```
[Account 1 Folder]               [Account 2 Folder]
    ├── audio1.mp3     -->          ├── audio1.txt
    ├── audio2.mp3     -->          ├── audio2.txt
    └── processed/                  └── audio3.txt
        ├── audio1.mp3 (moved)
        └── audio2.mp3 (moved)
```

1. Script checks source folder for MP3 files
2. Downloads each file
3. Transcribes with Groq
4. Uploads .txt to destination folder
5. **Moves** original MP3 to "processed" subfolder in Account 1
6. Cleans up temporary files

## Troubleshooting

### "credentials_account1.json not found"
- Make sure you downloaded the JSON and renamed it correctly
- It should be in the same folder as `gdrive_sync.py`

### "Please set SOURCE_FOLDER_ID and DEST_FOLDER_ID"
- Check your `.env` file
- Make sure there are no quotes or extra spaces
- Folder IDs should be long random strings

### "Access denied" when running
- Make sure **both email addresses** are added as test users in OAuth consent screen
- Delete `token_account1.pickle` and `token_account2.pickle` and try again

### "Cannot find folder"
- Verify folder IDs are correct (copy again from URL)
- Make sure the authenticated account owns or has access to the folders

### Script hangs on "Authenticating..."
- Check if browser window opened in background
- Make sure you have a web browser installed and set as default

## Security Notes

🔒 **Keep these files private**:
- `.env` (contains API key)
- `credentials_account*.json` (OAuth credentials)
- `token_account*.pickle` (access tokens)

These are already in `.gitignore` and won't be committed to git.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python gdrive_sync.py` | Run once manually |
| `python gdrive_scheduler.py` | Run every N hours |
| Delete `.pickle` files | Force re-authentication |
| Edit `SYNC_INTERVAL_HOURS` | Change schedule interval |
