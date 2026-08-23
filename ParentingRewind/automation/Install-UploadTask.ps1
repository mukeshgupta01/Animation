[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskName = 'Parenting Rewind - Private Upload Cadence'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw "Scheduled task already exists and was not overwritten: $taskName"
}

$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$runner = Join-Path $PSScriptRoot 'Run-UploadCycle.ps1'
$start = (Get-Date).AddHours(1)
$minute = $start.Minute
$triggers = @(0..23 | ForEach-Object {
    New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes($minute))
})
$action = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 50)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Checks hourly; uploads one Parenting Rewind video privately only when its 4h/6h/8h cadence is due, then sends an Outlook email.' | Out-Null
$task = Get-ScheduledTask -TaskName $taskName
$info = $task | Get-ScheduledTaskInfo
[pscustomobject]@{
    TaskName = $task.TaskName
    State = $task.State
    NextRunTime = $info.NextRunTime
    User = $user
    FirstSixIntervalHours = 4
    NextSixIntervalHours = 6
    RemainingIntervalHours = 8
}
