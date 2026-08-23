[CmdletBinding()]
param(
    [string]$TaskName = "Animation Git Sync Every Three Hours",
    [int]$Minute = 37
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $PSScriptRoot "Run-GitSync.ps1"
if (-not (Test-Path -LiteralPath $runner)) {
    throw "Git sync runner not found: $runner"
}

$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$action = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
$triggers = @(0, 3, 6, 9, 12, 15, 18, 21 | ForEach-Object {
    New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes($Minute))
})
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description "Safely fetches Animation every three hours, fast-forwards or pushes only from a clean non-diverged main branch, and never auto-commits or force-pushes." | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
$info = $task | Get-ScheduledTaskInfo
[pscustomobject]@{
    TaskName = $task.TaskName
    State = $task.State
    NextRunTime = $info.NextRunTime
    LastRunTime = $info.LastRunTime
    LastTaskResult = $info.LastTaskResult
}
