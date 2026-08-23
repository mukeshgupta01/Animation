[CmdletBinding()]
param(
    [int]$MaxSeconds = 17100,
    [int]$MaxItems = 1
)

$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$python = Join-Path (Split-Path -Parent $project) '.venv\Scripts\python.exe'
$runner = Join-Path $PSScriptRoot 'generation_runner.py'
$report = Join-Path $PSScriptRoot 'runtime\latest-generation-report.json'
$log = Join-Path $PSScriptRoot 'logs\generation-task.log'
New-Item -ItemType Directory -Force -Path (Split-Path $report), (Split-Path $log) | Out-Null

$createdNew = $false
$mutex = New-Object System.Threading.Mutex($false, 'Global\TinyTalesContinuousGeneration', [ref]$createdNew)
if (-not $mutex.WaitOne(0)) {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) skipped: another generation cycle is active"
    exit 0
}

try {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) generation cycle started"
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $python -B $runner --max-seconds $MaxSeconds --max-items $MaxItems --report-json $report *>> $log
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) generation cycle finished with exit code $exitCode"
    exit $exitCode
}
catch {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) generation cycle failed: $($_.Exception.Message)"
    exit 1
}
finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
