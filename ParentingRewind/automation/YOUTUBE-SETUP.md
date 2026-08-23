# Parenting Rewind YouTube API setup

Target channel: **Parenting Rewind**
Immutable channel ID: `UCGb-IUQX2KQa_KA24MwE_aQ`

This setup is isolated from every other YouTube project. It verifies the live OAuth identity against the immutable channel ID before saving a token or channel lock. It performs no upload.

## Google Cloud setup

1. Open Google Cloud Console and select or create a project dedicated to Parenting Rewind automation.
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen. If the app is in Testing, add the Google account that owns Parenting Rewind as a test user.
4. Create an **OAuth client ID** with application type **Desktop app**.
5. Download the JSON and save it exactly as `automation/secrets/youtube-client-secret.json`.
6. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\Setup-YouTubeApi.ps1`.
7. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\Start-YouTubeOAuth.ps1`.
8. In Google, choose the account/channel identity that owns Parenting Rewind and approve the requested YouTube access.

The setup succeeds only if Google returns `UCGb-IUQX2KQa_KA24MwE_aQ` from `channels.list(mine=true)`. A wrong-channel response is rejected without saving a token or lock.
