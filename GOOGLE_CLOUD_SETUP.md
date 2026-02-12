# Google Cloud Configuration Guide

This guide explains how to configure Google Cloud to enable the Google Drive transcription workflow.

## Overview

Your script needs to:
1. ✅ Access Google Drive Account 1 (source) - to download audio files
2. ✅ Access Google Drive Account 2 (destination) - to upload transcriptions
3. ✅ Check which files haven't been transcribed in the last X days
4. ✅ Download, transcribe, and upload transcriptions

## Step 1: Create/Select Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Either:
   - **Use existing project**: Select from dropdown
   - **Create new project**: Click "New Project" → Name it (e.g., "Speech-to-Text Sync") → Create

## Step 2: Enable Google Drive API

1. In your Google Cloud project, go to: **APIs & Services** → **Library**
2. Search for: **"Google Drive API"**
3. Click on it and press **"Enable"**
4. Wait for it to enable (usually takes a few seconds)

## Step 3: Configure OAuth Consent Screen

This allows your script to access Google Drive on behalf of users.

1. Go to: **APIs & Services** → **OAuth consent screen**
2. Configure the following:

   **App Information:**
   - **User Type**: External (unless you have a Google Workspace)
   - **App name**: "Speech-to-Text Sync" (or any name)
   - **User support email**: Your email
   - **Developer contact email**: Your email
   - Click **Save and Continue**

   **Scopes:**
   - Click **"Add or Remove Scopes"**
   - Search for: `https://www.googleapis.com/auth/drive`
   - Check the box for **".../auth/drive"** (full access)
   - Click **Update** → **Save and Continue**

   **Test Users** (CRITICAL):
   - Click **"+ ADD USERS"**
   - Add **Account 1 email** (source account)
   - Add **Account 2 email** (destination account)
   - Click **Save and Continue**

   **Summary:**
   - Review and click **Back to Dashboard**

## Step 4: Create OAuth Credentials

1. Go to: **APIs & Services** → **Credentials**
2. Click: **+ CREATE CREDENTIALS** → **OAuth client ID**
3. **Application type**: Select **"Desktop app"** ⚠️ **IMPORTANT: Must be Desktop app**
   - ❌ Do NOT select "Web application"
   - ❌ Do NOT select "iOS" or "Android"
   - ✅ Select **"Desktop app"** (or "Desktop client")
4. Fill in:
   - **Name**: "Drive Sync Desktop" (or any name you prefer)
5. Click **CREATE**
6. A popup will appear with your credentials
7. Click **DOWNLOAD JSON**
8. Save the file as: **`credentials_account1.json`** in your project folder

**Why Desktop app?** The script uses `InstalledAppFlow` which is specifically designed for desktop applications that run locally on your computer. This allows the browser-based authentication flow that opens automatically when you run the script.

**Important**: The credentials JSON file identifies your APPLICATION, not the user. You can use the same file for both accounts because each account will authenticate separately via the browser. Copy it:

```bash
cp credentials_account1.json credentials_account2.json
```

**Why this works:** The credentials file contains your app's Client ID and Secret. When you run the script, each Google account signs in separately through the browser and gets its own access token (stored in `token_account1.pickle` and `token_account2.pickle`). See [OAUTH_EXPLAINED.md](OAUTH_EXPLAINED.md) for more details.

## Step 5: Get Folder IDs

### Source Folder (Account 1 - where audio files are):

1. Sign in to Google Drive with **Account 1**
2. Navigate to or create the folder containing your audio files
3. Open the folder
4. Look at the URL:
   ```
   https://drive.google.com/drive/folders/1abcDEFghijkLMNOPqrstuvwxyz123456
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   ```
5. Copy the folder ID (the long string after `/folders/`)

### Destination Folder (Account 2 - where transcriptions go):

1. Sign in to Google Drive with **Account 2**
2. Navigate to or create the folder where you want transcriptions
3. Open the folder
4. Copy the folder ID from the URL (same way as above)

## Step 6: Configure Environment Variables

Edit your `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here

# Google Drive Folder IDs
SOURCE_FOLDER_ID=paste_source_folder_id_here
DEST_FOLDER_ID=paste_destination_folder_id_here
```

## Step 7: First Authentication Run

Run the script once to authenticate both accounts:

```bash
python gdrive_sync.py --days 7
```

**What happens:**

1. **Browser opens for Account 1**:
   - Sign in with Account 1 (source account)
   - You'll see: "Google hasn't verified this app" (normal for test apps)
   - Click **"Advanced"** → **"Go to Speech-to-Text Sync (unsafe)"**
   - Click **"Allow"** to grant Drive access
   - A token file (`token_account1.pickle`) will be created
   - **This token is specific to Account 1**

2. **Browser opens for Account 2**:
   - Sign in with Account 2 (destination account) - **different account!**
   - Same warning → Click **"Advanced"** → **"Continue"**
   - Click **"Allow"**
   - A token file (`token_account2.pickle`) will be created
   - **This token is specific to Account 2**

3. **Script runs**:
   - Uses `token_account1.pickle` to access Account 1's Drive
   - Uses `token_account2.pickle` to access Account 2's Drive
   - Checks for audio files that need transcription
   - Downloads, transcribes, and uploads them

**Key Point**: Even though both accounts use the same `credentials_account1.json` file, they authenticate separately and get different tokens. The credentials file is just your app's ID - the tokens are what actually give access to each account's Drive.

**Note**: After first run, tokens are saved. You won't need to authenticate again unless tokens expire (rare).

## How the Script Determines "Not Transcribed"

The script checks:
1. Does a `.txt` file with the same name exist in the destination folder?
2. If yes, when was it last modified?
3. If the `.txt` file doesn't exist OR was modified more than X days ago → transcribe

## Troubleshooting

### "Access Denied" or "403 Forbidden"
- ✅ Make sure **both email addresses** are added as test users in OAuth consent screen
- ✅ Delete `token_account1.pickle` and `token_account2.pickle` and re-authenticate
- ✅ Make sure Google Drive API is enabled

### "Cannot find folder"
- ✅ Verify folder IDs are correct (copy from URL again)
- ✅ Make sure the authenticated account has access to the folders
- ✅ Check that folders aren't in trash

### "credentials_account1.json not found"
- ✅ Make sure you downloaded the JSON from Google Cloud Console
- ✅ Check the file is in the same directory as `gdrive_sync.py`
- ✅ Verify the filename is exactly `credentials_account1.json`

### "OAuth client ID not found"
- ✅ Make sure you created OAuth credentials (Step 4)
- ✅ Download the JSON file again if needed

### Browser doesn't open
- ✅ Make sure you have a default web browser set
- ✅ Check firewall/network settings
- ✅ Try running the script again

## Security Notes

🔒 **Keep these files private** (already in `.gitignore`):
- `.env` - Contains API keys
- `credentials_account*.json` - OAuth credentials
- `token_account*.pickle` - Access tokens

**Never commit these to git!**

## Quick Checklist

- [ ] Google Cloud project created/selected
- [ ] Google Drive API enabled
- [ ] OAuth consent screen configured
- [ ] Both email addresses added as test users
- [ ] OAuth credentials created and downloaded
- [ ] `credentials_account1.json` and `credentials_account2.json` in project folder
- [ ] Source folder ID copied to `.env`
- [ ] Destination folder ID copied to `.env`
- [ ] First authentication run completed successfully

## Next Steps

Once configured, you can run:
```bash
# Process files not transcribed in last 7 days
python gdrive_sync.py --days 7

# Process files not transcribed in last 30 days
python gdrive_sync.py --days 30

# Process all files (no date filter)
python gdrive_sync.py --days 0
```
