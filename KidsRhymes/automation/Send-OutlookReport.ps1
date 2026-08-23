[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReportPath,
    [string]$Recipient = 'mukeshmelb01@gmail.com',
    [switch]$EmailOnlyTest
)

$ErrorActionPreference = 'Stop'
$started = Get-Date
$resolvedReport = [System.IO.Path]::GetFullPath($ReportPath)
if (-not (Test-Path -LiteralPath $resolvedReport)) {
    throw "Report JSON was not found: $resolvedReport"
}
$report = Get-Content -LiteralPath $resolvedReport -Raw | ConvertFrom-Json

if ($EmailOnlyTest) {
    $subject = "Tiny Tales automation email test - $($started.ToString('yyyy-MM-dd HH:mm:ss'))"
    $body = @"
Tiny Tales automation email test

This message confirms that the local automation can send through the classic Outlook profile without storing an email password.

Computer time: $($started.ToString('yyyy-MM-dd HH:mm:ss zzz'))
Report source: $resolvedReport
"@
}
else {
    $success = [int]$report.successful
    $attempted = [int]$report.attempted
    $videoName = if ($report.video_name) { [string]$report.video_name } elseif ($report.result.source_name) { [string]$report.result.source_name } else { '(none)' }
    $url = if ($report.result.youtube_url) { [string]$report.result.youtube_url } else { '(no URL returned)' }
    $remaining = if ($null -ne $report.remaining_upload_count) { [string]$report.remaining_upload_count } else { 'unknown' }
    $visibility = if ($report.privacy_status) { [string]$report.privacy_status } else { 'configured' }
    $failureLines = @($report.failures | ForEach-Object {
        if ($_.video_name) { "- $($_.video_name): $($_.error)" } else { "- $($_.error)" }
    })
    $status = if ($success -gt 0) { 'SUCCESS' } else { 'FAILED' }
    $subject = "Tiny Tales $visibility upload $status - $videoName"
    $body = @"
Tiny Tales upload report

Status: $status
Attempted uploads: $attempted
Successful uploads: $success
Video: $videoName
YouTube URL: $url
Visibility: $visibility
Remaining upload count: $remaining
Started UTC: $($report.started_utc)
Finished UTC: $($report.finished_utc)

Failures:
$($failureLines -join [Environment]::NewLine)

The automation uploads videos with the configured visibility and marks them made for kids.
"@
}

$outlook = $null
$mail = $null
$namespace = $null
$sentFolder = $null
try {
    $outlook = New-Object -ComObject Outlook.Application
    $mail = $outlook.CreateItem(0)
    $mail.To = $Recipient
    $mail.Subject = $subject
    $mail.Body = $body
    $mail.Send()

    # Confirm through the configured profile's Sent Items rather than assuming
    # that calling Send was sufficient.
    Start-Sleep -Seconds 8
    $namespace = $outlook.GetNamespace('MAPI')
    $sentFolder = $namespace.GetDefaultFolder(5)
    $items = $sentFolder.Items
    $items.Sort('[SentOn]', $true)
    $confirmed = $false
    $sentOn = $null
    for ($index = 1; $index -le [Math]::Min(50, $items.Count); $index++) {
        $item = $items.Item($index)
        if ($item.Subject -eq $subject -and $item.SentOn -ge $started.AddMinutes(-2)) {
            $confirmed = $true
            $sentOn = $item.SentOn
            break
        }
    }
    $result = [ordered]@{
        succeeded = $confirmed
        recipient = $Recipient
        subject = $subject
        sent_on = if ($sentOn) { $sentOn.ToString('o') } else { $null }
        confirmed_in_sent_items = $confirmed
    }
    $resultPath = Join-Path $PSScriptRoot 'runtime\last-email-result.json'
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    $result | ConvertTo-Json -Depth 5
    if (-not $confirmed) {
        throw 'Outlook accepted the message, but it was not found in Sent Items during the confirmation window.'
    }
}
finally {
    foreach ($object in @($sentFolder, $namespace, $mail, $outlook)) {
        if ($null -ne $object) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($object) }
    }
}
