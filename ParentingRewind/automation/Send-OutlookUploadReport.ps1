[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReportPath,
    [string]$Recipient = 'mukeshmelb01@gmail.com'
)

$ErrorActionPreference = 'Stop'
$started = Get-Date
$resolvedReport = [System.IO.Path]::GetFullPath($ReportPath)
if (-not (Test-Path -LiteralPath $resolvedReport)) { throw "Report not found: $resolvedReport" }
$report = Get-Content -LiteralPath $resolvedReport -Raw | ConvertFrom-Json
if ([int]$report.successful -lt 1 -or -not $report.result.video_id) {
    Write-Output 'No successful upload; no email required.'
    exit 0
}

$title = [string]$report.result.title
$url = [string]$report.result.youtube_url
$videoName = [string]$report.result.source_name
$remaining = [string]$report.remaining_upload_count
$nextDue = [string]$report.next_due_utc
$subject = "Parenting Rewind private upload SUCCESS - $title"
$body = @"
Parenting Rewind private upload report

Status: SUCCESS
Title: $title
Source video: $videoName
YouTube URL: $url
Visibility: Private
Audience: Not made for kids
Remaining videos in the synced folder: $remaining
Next upload due (UTC): $nextDue
Started UTC: $($report.started_utc)
Finished UTC: $($report.finished_utc)

The OneDrive source was left unchanged. Review the private video in YouTube Studio before making it public.
"@

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
    if (-not $confirmed) { throw 'Email was not confirmed in Outlook Sent Items.' }
}
finally {
    foreach ($object in @($sentFolder, $namespace, $mail, $outlook)) {
        if ($null -ne $object) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($object) }
    }
}
