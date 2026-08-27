[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$uploadTaskName = 'Tiny Tales - Daily Private Upload'
$summaryTaskName = 'Tiny Tales - Daily Upload Summary Email'
$uploadScript = Join-Path $PSScriptRoot 'Run-UploadCycle.ps1'
$summaryScript = Join-Path $PSScriptRoot 'Send-DailyUploadSummary.ps1'
$expectedUploadFragment = "-File `"$uploadScript`""

$uploadTask = Get-ScheduledTask -TaskName $uploadTaskName -ErrorAction Stop
if ($uploadTask.Actions.Count -ne 1 -or $uploadTask.Actions[0].Arguments -notlike "*$expectedUploadFragment*" -or $uploadTask.Actions[0].Arguments -like '*-RetryOnly*') {
    throw "Refusing to change email behavior for an unexpected upload task action: $($uploadTask.Actions[0].Arguments)"
}
if (-not (Test-Path -LiteralPath $summaryScript)) {
    throw "Daily summary script is missing: $summaryScript"
}

$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$action = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$summaryScript`""
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours(6))
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
$description = 'At 06:00 Australia/Sydney, sends one Outlook email with the count and list of successful Tiny Tales uploads from the previous Sydney calendar day.'

$existing = Get-ScheduledTask -TaskName $summaryTaskName -ErrorAction SilentlyContinue
if ($existing) {
    if ($existing.Actions.Count -ne 1 -or $existing.Actions[0].Arguments -notlike "*-File `"$summaryScript`"*") {
        throw "Refusing to overwrite an unexpected daily summary task action: $($existing.Actions[0].Arguments)"
    }
    Set-ScheduledTask -TaskName $summaryTaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
}
else {
    Register-ScheduledTask -TaskName $summaryTaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $description | Out-Null
}
Enable-ScheduledTask -TaskName $summaryTaskName | Out-Null

$task = Get-ScheduledTask -TaskName $summaryTaskName
$info = Get-ScheduledTaskInfo -TaskName $summaryTaskName
[pscustomobject]@{
    TaskName = $task.TaskName
    State = $task.State
    NextRunTime = $info.NextRunTime
    Action = $task.Actions[0].Arguments
    TriggerStart = $task.Triggers[0].StartBoundary
    UploadTaskActionVerified = $true
}
