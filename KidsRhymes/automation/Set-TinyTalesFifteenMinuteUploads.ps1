[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$uploadTaskName = 'Tiny Tales - Daily Private Upload'
$uploadScript = Join-Path $PSScriptRoot 'Run-UploadCycle.ps1'
$expectedScriptFragment = "-File `"$uploadScript`""

$uploadTask = Get-ScheduledTask -TaskName $uploadTaskName -ErrorAction Stop
if ($uploadTask.Actions.Count -ne 1 -or $uploadTask.Actions[0].Arguments -notlike "*$expectedScriptFragment*") {
    throw "Refusing to change an unexpected upload task action: $($uploadTask.Actions[0].Arguments)"
}
if ($uploadTask.Actions[0].Arguments -like '*-RetryOnly*') {
    throw 'Refusing to use the retry-only action as the regular upload task.'
}
$anchor = (Get-Date).AddMinutes(1)
$start = $anchor.Date.AddHours($anchor.Hour).AddMinutes([math]::Ceiling($anchor.Minute / 15.0) * 15)
$trigger = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = $uploadTask.Settings
$settings.DisallowStartIfOnBatteries = $false
$settings.StopIfGoingOnBatteries = $false
Set-ScheduledTask -TaskName $uploadTaskName -Trigger $trigger -Settings $settings | Out-Null
Enable-ScheduledTask -TaskName $uploadTaskName | Out-Null

$uploadTask = Get-ScheduledTask -TaskName $uploadTaskName
$uploadInfo = Get-ScheduledTaskInfo -TaskName $uploadTaskName
[pscustomobject]@{
    UploadTask = $uploadTask.TaskName
    UploadState = $uploadTask.State
    UploadNextRunTime = $uploadInfo.NextRunTime
    UploadInterval = $uploadTask.Triggers[0].Repetition.Interval
    UploadDuration = $uploadTask.Triggers[0].Repetition.Duration
    UploadAllowedOnBattery = -not $uploadTask.Settings.DisallowStartIfOnBatteries
}
