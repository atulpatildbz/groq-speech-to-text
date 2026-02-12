# How OAuth Works with Multiple Accounts

## The Key Concept

**The credentials JSON file identifies the APPLICATION, not the user.**

Think of it like this:
- **Credentials JSON** = Your app's ID card (same for everyone using your app)
- **Token files (.pickle)** = Each user's personal access pass (different for each account)

## How It Works

### 1. OAuth Credentials (credentials_account1.json / credentials_account2.json)

This file contains:
- **Client ID** - Identifies your application to Google
- **Client Secret** - Proves your application is legitimate

**Important:** This is the SAME for both accounts because it identifies YOUR APPLICATION, not the users.

### 2. User Authentication (Browser Flow)

When the script runs `get_drive_service()`:

1. **First time:**
   - Browser opens
   - User signs in with **Account 1** (their own Google account)
   - User grants permission to your app
   - Google returns an access token
   - Token is saved to `token_account1.pickle`

2. **Second time (for Account 2):**
   - Browser opens again
   - User signs in with **Account 2** (different Google account)
   - User grants permission to your app
   - Google returns a different access token
   - Token is saved to `token_account2.pickle`

### 3. Token Files (.pickle)

These store the actual user-specific access tokens:
- `token_account1.pickle` - Access token for Account 1
- `token_account2.pickle` - Access token for Account 2

**These are different** because they represent different users' permissions.

## Why You Can Use the Same Credentials File

```
┌─────────────────────────────────────┐
│  credentials_account1.json          │
│  (OAuth Client ID + Secret)         │
│  ↓                                   │
│  Used to authenticate...             │
│  ↓                                   │
├─────────────────────────────────────┤
│  Account 1 → Browser → Sign in      │
│  → token_account1.pickle            │
│                                     │
│  Account 2 → Browser → Sign in      │
│  → token_account2.pickle            │
└─────────────────────────────────────┘
```

The credentials file is like a "key" that opens the authentication door. Once inside, each user gets their own personal token.

## Setup Steps

1. **Create ONE OAuth client** in Google Cloud Console
2. **Download the JSON file once** → `credentials_account1.json`
3. **Copy it** → `credentials_account2.json` (same file, different name)
4. **Add BOTH email addresses** as test users in OAuth consent screen
5. **Run the script** - it will authenticate each account separately

## What Happens During First Run

```bash
python gdrive_sync.py --days 7
```

**Step 1: Authenticate Account 1**
```
Browser opens → Sign in with account1@gmail.com
→ Click "Allow" → token_account1.pickle created
```

**Step 2: Authenticate Account 2**
```
Browser opens → Sign in with account2@gmail.com  
→ Click "Allow" → token_account2.pickle created
```

**Step 3: Script runs**
```
Uses token_account1.pickle → Access Account 1's Drive
Uses token_account2.pickle → Access Account 2's Drive
```

## Important Notes

✅ **Same credentials file works** because it's just the app identifier  
✅ **Different token files** because they represent different users  
✅ **Both accounts must be test users** in your OAuth consent screen  
✅ **After first run**, tokens are saved - no need to authenticate again  

## If You Have Issues

**"Access denied" for one account:**
- Make sure that account's email is added as a test user
- Delete the corresponding `.pickle` file and re-authenticate

**"Invalid credentials":**
- Make sure you downloaded the credentials JSON from Google Cloud Console
- Verify the file isn't corrupted

**Want separate OAuth clients?**
- You CAN create two separate OAuth clients (one per account)
- But it's not necessary - one client works for both accounts
