[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$automationRoot = $PSScriptRoot
$python = Join-Path $automationRoot '.venv\Scripts\python.exe'
$uploader = Join-Path $automationRoot 'private_uploader.py'
$mailer = Join-Path $automationRoot 'Send-OutlookUploadReport.ps1'
$report = Join-Path $automationRoot 'runtime\latest-upload-report.json'
$log = Join-Path $automationRoot 'logs\upload-task.log'
New-Item -ItemType Directory -Force -Path (Split-Path $report), (Split-Path $log) | Out-Null

$createdNew = $false
$mutex = New-Object System.Threading.Mutex($false, 'Global\ParentingRewindPrivateUploader', [ref]$createdNew)
if (-not $mutex.WaitOne(0)) {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) skipped: another upload cycle is active"
    exit 0
}

try {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload check started"
    & $python -B $uploader run --confirm-private-upload *>> $log
    $uploadExit = $LASTEXITCODE
    if (Test-Path -LiteralPath $report) {
        $result = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        if ([int]$result.successful -gt 0) {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $mailer -ReportPath $report *>> $log
        }
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) upload check finished with exit code $uploadExit"
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
