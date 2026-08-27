[CmdletBinding()]
param(
    [switch]$RetryOnly
)

$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$python = Join-Path (Split-Path -Parent $project) '.venv\Scripts\python.exe'
$uploader = Join-Path $PSScriptRoot 'uploader.py'
$report = Join-Path $PSScriptRoot 'runtime\latest-upload-report.json'
$retryState = Join-Path $PSScriptRoot 'runtime\upload-retry-state.json'
$log = Join-Path $PSScriptRoot 'logs\upload-task.log'
New-Item -ItemType Directory -Force -Path (Split-Path $report), (Split-Path $log) | Out-Null

$createdNew = $false
$mutex = New-Object System.Threading.Mutex($false, 'Global\TinyTalesPrivateUploader', [ref]$createdNew)
if (-not $mutex.WaitOne(0)) {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) skipped: another upload cycle is active"
    exit 0
}

try {
    $retryVideo = $null
    if (Test-Path -LiteralPath $retryState) {
        $state = Get-Content -Raw -LiteralPath $retryState | ConvertFrom-Json
        if ($state.retry_required -eq $true) {
            $retryVideo = [string]$state.video_name
        }
    }
    if ($RetryOnly -and -not $retryVideo) {
        Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) retry check skipped: no retryable upload failure"
        exit 0
    }

    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload cycle started"
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $uploadArguments = @('-B', $uploader, 'run', '--confirm-upload', '--report-json', $report)
        if ($retryVideo) {
            $uploadArguments += @('--video-name', $retryVideo)
        }
        & $python @uploadArguments *>> $log
        $uploadExit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    $uploadReport = $null
    if (Test-Path -LiteralPath $report) {
        $uploadReport = Get-Content -Raw -LiteralPath $report | ConvertFrom-Json
    }

    if ($uploadExit -eq 0) {
        [ordered]@{
            retry_required = $false
            cleared_at = (Get-Date -Format o)
            reason = 'upload cycle succeeded or queue was empty'
        } | ConvertTo-Json | Set-Content -LiteralPath $retryState -Encoding UTF8
    }
    elseif ($uploadReport -and $uploadReport.automatic_retry_safe -eq $true -and $uploadReport.video_name) {
        [ordered]@{
            retry_required = $true
            video_name = [string]$uploadReport.video_name
            failed_at = (Get-Date -Format o)
            last_error = [string]$uploadReport.failures[0].error
        } | ConvertTo-Json | Set-Content -LiteralPath $retryState -Encoding UTF8
    }
    else {
        [ordered]@{
            retry_required = $false
            cleared_at = (Get-Date -Format o)
            reason = 'automatic retry blocked because duplicate-safe retry was not established'
        } | ConvertTo-Json | Set-Content -LiteralPath $retryState -Encoding UTF8
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload cycle finished with exit code $uploadExit"
    exit $uploadExit
}
catch {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload cycle failed: $($_.Exception.Message)"
    exit 1
}
finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
