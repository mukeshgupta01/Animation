[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskName = 'Parenting Rewind - Public Upload Cadence'
$supersededTaskName = 'Parenting Rewind - Public Upload Every Five Hours'
$oldTaskName = 'Parenting Rewind - Private Upload Cadence'

$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$runner = Join-Path $PSScriptRoot 'Run-UploadCycle.ps1'
$now = Get-Date
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask -and $existingTask.Triggers.Count -gt 0) {
    $anchor = [datetime]$existingTask.Triggers[0].StartBoundary
    $start = $now.Date.AddHours($now.Hour).AddMinutes($anchor.Minute).AddSeconds($anchor.Second)
    if ($start -le $now) {
        $start = $start.AddHours(1)
    }
}
else {
    $start = $now.AddHours(1)
}
$triggers = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Hours 1)
$action = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 50)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Uploads the oldest remaining Parenting Rewind video publicly once per hour through fail-closed cadence checks and sends an Outlook success email.' -Force | Out-Null
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
    TaskCheckIntervalHours = 1
    UploadIntervalHours = 1
    StartsAt = $start
    SupersededFiveHourTaskDisabled = [bool](Get-ScheduledTask -TaskName $supersededTaskName -ErrorAction SilentlyContinue)
    OldPrivateTaskDisabled = [bool](Get-ScheduledTask -TaskName $oldTaskName -ErrorAction SilentlyContinue)
}
