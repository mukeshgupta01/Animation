[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskName = 'Parenting Rewind - Public Upload Cadence'
$supersededTaskName = 'Parenting Rewind - Public Upload Every Five Hours'
$oldTaskName = 'Parenting Rewind - Private Upload Cadence'

$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$runner = Join-Path $PSScriptRoot 'Run-UploadCycle.ps1'
$start = (Get-Date).AddHours(2)
$triggers = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Hours 2)
$action = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 50)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Uploads the oldest remaining Parenting Rewind video publicly every two hours through 2026-08-28 10:55:10 UTC, then every four hours via fail-closed cadence checks, and sends an Outlook email.' -Force | Out-Null
if (Get-ScheduledTask -TaskName $supersededTaskName -ErrorAction SilentlyContinue) {
    Disable-ScheduledTask -TaskName $supersededTaskName | Out-Null
}
if (Get-ScheduledTask -TaskName $oldTaskName -ErrorAction SilentlyContinue) {
    Disable-ScheduledTask -TaskName $oldTaskName | Out-Null
}
$task = Get-ScheduledTask -TaskName $taskName
$info = $task | Get-ScheduledTaskInfo
[pscustomobject]@{
    TaskName = $task.TaskName
    State = $task.State
    NextRunTime = $info.NextRunTime
    User = $user
    PrivacyStatus = 'public'
    TaskCheckIntervalHours = 2
    TemporaryUploadIntervalHours = 2
    TemporaryUntilUtc = '2026-08-28T10:55:10Z'
    SteadyUploadIntervalHours = 4
    StartsAt = $start
    SupersededFiveHourTaskDisabled = [bool](Get-ScheduledTask -TaskName $supersededTaskName -ErrorAction SilentlyContinue)
    OldPrivateTaskDisabled = [bool](Get-ScheduledTask -TaskName $oldTaskName -ErrorAction SilentlyContinue)
}
