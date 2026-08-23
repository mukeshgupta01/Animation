[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$generationTaskName = 'Tiny Tales - Continuous Generation'
$uploadTaskName = 'Tiny Tales - Daily Private Upload'
foreach ($name in @($generationTaskName, $uploadTaskName)) {
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
$generationTriggers = @(0, 5, 10, 15, 20 | ForEach-Object { New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes(5)) })
$uploadTriggers = @(0, 4, 8, 12, 16, 20 | ForEach-Object { New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes(20)) })
$generationSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 4 -Minutes 50)
$uploadSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 45)

Register-ScheduledTask -TaskName $generationTaskName -Action $generationAction -Trigger $generationTriggers -Principal $principal -Settings $generationSettings -Description 'Starts a fresh, non-overlapping Tiny Tales generation process roughly every five hours.' | Out-Null
try {
    Register-ScheduledTask -TaskName $uploadTaskName -Action $uploadAction -Trigger $uploadTriggers -Principal $principal -Settings $uploadSettings -Description 'Every four hours, uploads the newest eligible Tiny Tales video with configured visibility, archives it after success, and sends an Outlook report.' | Out-Null
}
catch {
    Unregister-ScheduledTask -TaskName $generationTaskName -Confirm:$false
    throw
}

Get-ScheduledTask -TaskName $generationTaskName, $uploadTaskName | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName
    [pscustomobject]@{ TaskName = $_.TaskName; State = $_.State; NextRunTime = $info.NextRunTime }
}
