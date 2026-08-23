[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$python = Join-Path (Split-Path -Parent $project) '.venv\Scripts\python.exe'
$uploader = Join-Path $PSScriptRoot 'uploader.py'
$mailer = Join-Path $PSScriptRoot 'Send-OutlookReport.ps1'
$report = Join-Path $PSScriptRoot 'runtime\latest-upload-report.json'
$log = Join-Path $PSScriptRoot 'logs\upload-task.log'
New-Item -ItemType Directory -Force -Path (Split-Path $report), (Split-Path $log) | Out-Null

$createdNew = $false
$mutex = New-Object System.Threading.Mutex($false, 'Global\TinyTalesPrivateUploader', [ref]$createdNew)
if (-not $mutex.WaitOne(0)) {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) skipped: another upload cycle is active"
    exit 0
}

try {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload cycle started"
    & $python -B $uploader run --confirm-upload --report-json $report *>> $log
    $uploadExit = $LASTEXITCODE
    if (Test-Path -LiteralPath $report) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $mailer -ReportPath $report *>> $log
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload cycle finished with exit code $uploadExit"
    exit $uploadExit
}
catch {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload/email cycle failed: $($_.Exception.Message)"
    exit 1
}
finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
