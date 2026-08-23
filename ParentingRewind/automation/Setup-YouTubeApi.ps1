[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$automationRoot = $PSScriptRoot
$venvRoot = Join-Path $automationRoot '.venv'
$python = Join-Path $venvRoot 'Scripts\python.exe'
$requirements = Join-Path $automationRoot 'requirements.txt'
$workspacePython = 'C:\DocSphere\kid-explainer-studio\.venv\Scripts\python.exe'
$temporaryRoot = Join-Path $automationRoot '.tmp'
New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
$env:TEMP = $temporaryRoot
$env:TMP = $temporaryRoot

if (-not (Test-Path -LiteralPath $python)) {
    if (Test-Path -LiteralPath $workspacePython) {
        & $workspacePython -m venv $venvRoot
    }
    elseif (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv $venvRoot
    }
    else {
        throw 'No usable Python installation was found to create the isolated API environment.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create the isolated API environment.' }
}

if (-not (Test-Path -LiteralPath (Join-Path $venvRoot 'Lib\site-packages\pip'))) {
    & $python -m ensurepip --upgrade --default-pip
    if ($LASTEXITCODE -ne 0) { throw 'Unable to bootstrap pip in the isolated API environment.' }
}

& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Unable to update pip.' }
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Unable to install YouTube API packages.' }

Write-Host 'YouTube API dependencies are ready.'
Write-Host 'Next, save the OAuth Desktop app JSON under automation\secrets and run Start-YouTubeOAuth.ps1.'
