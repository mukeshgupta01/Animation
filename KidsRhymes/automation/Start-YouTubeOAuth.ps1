[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = 'C:\Animation\Animation\.venv\Scripts\python.exe'
$clientSecret = Join-Path $PSScriptRoot 'secrets\youtube-client-secret.json'
$uploader = Join-Path $PSScriptRoot 'uploader.py'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Project Python was not found: $python"
}
if (-not (Test-Path -LiteralPath $clientSecret)) {
    throw @"
OAuth desktop-client JSON was not found.

1. Enable YouTube Data API v3 in your Google Cloud project.
2. Configure the OAuth consent screen and add your Google account as a test user if the app is in Testing.
3. Create an OAuth client ID with application type 'Desktop app'.
4. Download its JSON file to:
   $clientSecret

Do not use or copy a token from another computer.
"@
}

Push-Location $projectRoot
try {
    & $python -B $uploader oauth --interactive
    if ($LASTEXITCODE -ne 0) {
        throw "YouTube OAuth verification failed with exit code $LASTEXITCODE. No upload was performed."
    }
}
finally {
    Pop-Location
}
