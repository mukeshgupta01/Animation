[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$venvRoot = Join-Path $projectRoot '.venv'
$python = Join-Path $venvRoot 'Scripts\python.exe'
$workspacePython = 'C:\DocSphere\kid-explainer-studio\.venv\Scripts\python.exe'
$temporaryRoot = Join-Path $projectRoot '.cache\python-temp'
New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
$env:TEMP = $temporaryRoot
$env:TMP = $temporaryRoot

if (-not (Test-Path -LiteralPath $python)) {
    if (-not (Test-Path -LiteralPath $workspacePython)) { throw "Bootstrap Python not found: $workspacePython" }
    & $workspacePython -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create the Parenting Rewind production environment.' }
}
if (-not (Test-Path -LiteralPath (Join-Path $venvRoot 'Lib\site-packages\pip'))) {
    & $python -m ensurepip --upgrade --default-pip
    if ($LASTEXITCODE -ne 0) { throw 'Unable to bootstrap pip.' }
}
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Unable to update pip.' }
& $python -m pip install 'Pillow>=11,<13' 'edge-tts>=7.2,<8'
if ($LASTEXITCODE -ne 0) { throw 'Unable to install production dependencies.' }
Write-Output "Production environment ready: $python"
