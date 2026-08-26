[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskName = 'Parenting Rewind - Public Upload Every Five Hours'
$oldTaskName = 'Parenting Rewind - Private Upload Cadence'

$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$runner = Join-Path $PSScriptRoot 'Run-UploadCycle.ps1'
$start = (Get-Date).AddHours(5)
$triggers = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Hours 5)
$action = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 50)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Uploads one Parenting Rewind video publicly every five hours after channel, audience, file, metadata and duplicate checks, then sends an Outlook email.' -Force | Out-Null
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
    IntervalHours = 5
    StartsAt = $start
    OldPrivateTaskDisabled = [bool](Get-ScheduledTask -TaskName $oldTaskName -ErrorAction SilentlyContinue)
}
