# Tiny Tales YouTube API setup

Target channel: `Tiny Tales`  
Immutable channel ID: `UCEn9N-ITQHshjgt6fy7fxnw`

The uploader only scans `automation/pending-uploads`. Existing project output folders are deliberately excluded.

## One-time Google Cloud setup

1. Open Google Cloud Console and select or create a project dedicated to this laptop/channel automation.
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen. If its publishing status is **Testing**, add the Google account that owns/manages Tiny Tales as a test user.
4. Create **OAuth client ID** credentials with application type **Desktop app**.
5. Download the JSON and save it exactly as:

   `automation/secrets/youtube-client-secret.json`

6. Run:

   `powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\Start-YouTubeOAuth.ps1`

Choose the Google or Brand Account identity that owns Tiny Tales. The program requests only YouTube upload and read-only verification scopes, then calls `channels.list(mine=true)` before saving credentials. It saves a laptop-local token and creates the immutable channel lock only when the returned channel ID exactly matches `UCEn9N-ITQHshjgt6fy7fxnw`.

If the wrong channel is returned, the program stops without replacing the token or lock. Repeat authorization and select the correct identity; never edit the lock to bypass the mismatch.

No upload is performed by OAuth setup or verification.
