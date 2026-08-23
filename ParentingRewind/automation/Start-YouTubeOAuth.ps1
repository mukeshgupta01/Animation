[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$automationRoot = $PSScriptRoot
$python = Join-Path $automationRoot '.venv\Scripts\python.exe'
$clientSecret = Join-Path $automationRoot 'secrets\youtube-client-secret.json'
$authScript = Join-Path $automationRoot 'youtube_auth.py'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Run Setup-YouTubeApi.ps1 first. Python environment not found: $python"
}
if (-not (Test-Path -LiteralPath $clientSecret)) {
    throw @"
OAuth Desktop app JSON was not found.

Download a new Desktop app OAuth JSON for Parenting Rewind and save it as:
  $clientSecret

No credentials from Birthday Songs or Tiny Tales may be copied here.
"@
}

& $python -B $authScript setup
if ($LASTEXITCODE -ne 0) {
    throw 'Parenting Rewind OAuth verification failed. No upload was performed.'
}
