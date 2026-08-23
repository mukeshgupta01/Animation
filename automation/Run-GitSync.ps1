[CmdletBinding()]
param(
    [string]$RepoRoot,
    [string]$Branch = "main",
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}
$runtimeDir = Join-Path $RepoRoot "runtime"
$logPath = Join-Path $runtimeDir "git-sync.log"
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

function Write-SyncLog {
    param([string]$Message)
    Add-Content -LiteralPath $logPath -Value "$(Get-Date -Format o) $Message"
}

function Invoke-Git {
    param([string[]]$Arguments)
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & git -C $RepoRoot @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return @($output)
}

try {
    $resolvedRepo = (Resolve-Path -LiteralPath $RepoRoot).Path
    $actualRoot = (Invoke-Git @("rev-parse", "--show-toplevel") | Select-Object -First 1).Trim()
    if ([System.IO.Path]::GetFullPath($actualRoot) -ne [System.IO.Path]::GetFullPath($resolvedRepo)) {
        throw "Repository identity mismatch: expected $resolvedRepo, found $actualRoot"
    }

    $currentBranch = (Invoke-Git @("branch", "--show-current") | Select-Object -First 1).Trim()
    if ($currentBranch -ne $Branch) {
        throw "Branch mismatch: expected $Branch, found $currentBranch"
    }

    Invoke-Git @("remote", "get-url", $Remote) | Out-Null
    Invoke-Git @("fetch", "--prune", $Remote, $Branch) | Out-Null

    $dirty = @(Invoke-Git @("status", "--porcelain"))
    if ($dirty.Count -gt 0) {
        Write-SyncLog "fetched-only: worktree has uncommitted changes; pull and push skipped"
        exit 0
    }

    $counts = (Invoke-Git @("rev-list", "--left-right", "--count", "HEAD...$Remote/$Branch") | Select-Object -First 1).Trim() -split "\s+"
    $ahead = [int]$counts[0]
    $behind = [int]$counts[1]

    if ($ahead -gt 0 -and $behind -gt 0) {
        Write-SyncLog "attention-required: branch diverged (ahead=$ahead behind=$behind); no merge or push attempted"
        exit 2
    }

    if ($behind -gt 0) {
        Invoke-Git @("merge", "--ff-only", "$Remote/$Branch") | Out-Null
        Write-SyncLog "pulled: fast-forwarded $behind remote commit(s)"
        exit 0
    }

    if ($ahead -gt 0) {
        Invoke-Git @("push", $Remote, "$Branch`:$Branch") | Out-Null
        Write-SyncLog "pushed: published $ahead local commit(s)"
        exit 0
    }

    Write-SyncLog "in-sync: no changes"
    exit 0
}
catch {
    Write-SyncLog "failed: $($_.Exception.Message)"
    exit 1
}
