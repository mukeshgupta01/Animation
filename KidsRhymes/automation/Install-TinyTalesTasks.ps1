[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$generationTaskName = 'Tiny Tales - Continuous Generation'
$uploadTaskName = 'Tiny Tales - Daily Private Upload'
$uploadRetryTaskName = 'Tiny Tales - Hourly Upload Retry'
foreach ($name in @($generationTaskName, $uploadTaskName, $uploadRetryTaskName)) {
    if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
        throw "Scheduled task already exists and was not overwritten: $name"
    }
}

$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$generationScript = Join-Path $PSScriptRoot 'Run-GenerationCycle.ps1'
$uploadScript = Join-Path $PSScriptRoot 'Run-UploadCycle.ps1'
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$generationAction = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$generationScript`""
$uploadAction = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$uploadScript`""
$uploadRetryAction = New-ScheduledTaskAction -Execute $powerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$uploadScript`" -RetryOnly"
$generationTriggers = @(0, 5, 10, 15, 20 | ForEach-Object { New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes(5)) })
$uploadAnchor = (Get-Date).AddMinutes(1)
$uploadStart = $uploadAnchor.Date.AddHours($uploadAnchor.Hour).AddMinutes([math]::Ceiling($uploadAnchor.Minute / 10.0) * 10)
$uploadTriggers = @(
    New-ScheduledTaskTrigger -Once -At $uploadStart -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
)
$uploadRetryTriggers = @(1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17, 19, 20, 22, 23 | ForEach-Object { New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes(20)) })
$generationSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 4 -Minutes 50)
$uploadSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 45)

Register-ScheduledTask -TaskName $generationTaskName -Action $generationAction -Trigger $generationTriggers -Principal $principal -Settings $generationSettings -Description 'Starts a fresh, non-overlapping Tiny Tales generation process roughly every five hours.' | Out-Null
try {
    Register-ScheduledTask -TaskName $uploadTaskName -Action $uploadAction -Trigger $uploadTriggers -Principal $principal -Settings $uploadSettings -Description 'Every ten minutes, uploads at most one eligible Tiny Tales video with configured visibility, archives it after success, and sends an Outlook report. A retry-safe failure is retried before any newer queue item.' | Out-Null
    Register-ScheduledTask -TaskName $uploadRetryTaskName -Action $uploadRetryAction -Trigger $uploadRetryTriggers -Principal $principal -Settings $uploadSettings -Description 'At intervening hourly slots, retries only the same Tiny Tales upload after a duplicate-safe failure; otherwise exits without uploading.' | Out-Null
    Disable-ScheduledTask -TaskName $uploadRetryTaskName | Out-Null
}
catch {
    Unregister-ScheduledTask -TaskName $generationTaskName -Confirm:$false
    Unregister-ScheduledTask -TaskName $uploadTaskName -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $uploadRetryTaskName -Confirm:$false -ErrorAction SilentlyContinue
    throw
}

Get-ScheduledTask -TaskName $generationTaskName, $uploadTaskName, $uploadRetryTaskName | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName
    [pscustomobject]@{ TaskName = $_.TaskName; State = $_.State; NextRunTime = $info.NextRunTime }
}
