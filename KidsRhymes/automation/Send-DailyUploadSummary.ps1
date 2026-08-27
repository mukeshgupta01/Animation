[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
    [string]$SummaryDate
)

$ErrorActionPreference = 'Stop'
$timeZone = [TimeZoneInfo]::FindSystemTimeZoneById('AUS Eastern Standard Time')
$configPath = Join-Path $PSScriptRoot 'config.json'
$ledgerPath = Join-Path $PSScriptRoot 'runtime\upload-ledger.jsonl'
$statePath = Join-Path $PSScriptRoot 'runtime\daily-summary-state.json'
$reportPath = Join-Path $PSScriptRoot 'runtime\latest-daily-upload-summary.json'
$resultPath = Join-Path $PSScriptRoot 'runtime\last-daily-summary-email-result.json'
$logPath = Join-Path $PSScriptRoot 'logs\daily-upload-summary.log'
New-Item -ItemType Directory -Force -Path (Split-Path $statePath), (Split-Path $logPath) | Out-Null

$localNow = [TimeZoneInfo]::ConvertTime([DateTimeOffset]::UtcNow, $timeZone)
if ($SummaryDate) {
    $summaryDay = [datetime]::ParseExact($SummaryDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
}
else {
    $summaryDay = $localNow.Date.AddDays(-1)
}
$summaryDay = [DateTime]::SpecifyKind($summaryDay.Date, [DateTimeKind]::Unspecified)
$nextDay = $summaryDay.AddDays(1)
$startUtc = [TimeZoneInfo]::ConvertTimeToUtc($summaryDay, $timeZone)
$endUtc = [TimeZoneInfo]::ConvertTimeToUtc($nextDay, $timeZone)
$dateKey = $summaryDay.ToString('yyyy-MM-dd')

if (-not $DryRun -and (Test-Path -LiteralPath $statePath)) {
    $priorState = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    if ([string]$priorState.last_sent_summary_date -eq $dateKey) {
        Add-Content -LiteralPath $logPath -Value "$(Get-Date -Format o) skipped duplicate summary for $dateKey"
        [ordered]@{ action = 'daily-upload-summary'; skipped = $true; reason = 'already sent'; summary_date = $dateKey } | ConvertTo-Json
        exit 0
    }
}

$rows = @()
if (Test-Path -LiteralPath $ledgerPath) {
    $lineNumber = 0
    foreach ($line in Get-Content -LiteralPath $ledgerPath) {
        $lineNumber++
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $row = $line | ConvertFrom-Json
            if ($row.video_id -and $row.uploaded_utc) {
                $uploaded = [DateTimeOffset]::Parse([string]$row.uploaded_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal)
                if ($uploaded.UtcDateTime -ge $startUtc -and $uploaded.UtcDateTime -lt $endUtc) {
                    $rows += $row
                }
            }
        }
        catch {
            throw "Corrupt upload ledger line $lineNumber prevented the daily summary: $($_.Exception.Message)"
        }
    }
}

$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$recipient = [string]$config.report_recipient
if ([string]::IsNullOrWhiteSpace($recipient)) {
    throw 'config.json does not contain report_recipient.'
}
$count = $rows.Count
$subject = "Tiny Tales daily upload summary - $dateKey - $count video$(if ($count -eq 1) { '' } else { 's' })"
$detailLines = if ($count -eq 0) {
    @('- No successful uploads were recorded.')
}
else {
    @($rows | ForEach-Object { "- $($_.source_name) - $($_.youtube_url)" })
}
$body = @"
Tiny Tales daily upload summary

Sydney date: $dateKey
Successful videos uploaded: $count

Uploads:
$($detailLines -join [Environment]::NewLine)

Count source: the local duplicate-safe Tiny Tales upload ledger.
Period UTC: $($startUtc.ToString('o')) through $($endUtc.ToString('o')) (end exclusive).
"@

$report = [ordered]@{
    action = 'daily-upload-summary'
    dry_run = [bool]$DryRun
    summary_date = $dateKey
    time_zone = $timeZone.Id
    start_utc = $startUtc.ToString('o')
    end_utc = $endUtc.ToString('o')
    successful_upload_count = $count
    uploads = @($rows | ForEach-Object { [ordered]@{ source_name = $_.source_name; video_id = $_.video_id; youtube_url = $_.youtube_url; uploaded_utc = $_.uploaded_utc } })
    subject = $subject
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8

if ($DryRun) {
    Add-Content -LiteralPath $logPath -Value "$(Get-Date -Format o) dry run counted $count upload(s) for $dateKey"
    $report | ConvertTo-Json -Depth 6
    exit 0
}

$started = Get-Date
$outlook = $null
$mail = $null
$namespace = $null
$sentFolder = $null
try {
    $outlook = New-Object -ComObject Outlook.Application
    $mail = $outlook.CreateItem(0)
    $mail.To = $recipient
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
    if (-not $confirmed) {
        throw 'Outlook accepted the daily summary, but it was not found in Sent Items during the confirmation window.'
    }
    [ordered]@{
        last_sent_summary_date = $dateKey
        sent_on = $sentOn.ToString('o')
        successful_upload_count = $count
        subject = $subject
    } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $result = [ordered]@{
        succeeded = $true
        summary_date = $dateKey
        successful_upload_count = $count
        subject = $subject
        sent_on = $sentOn.ToString('o')
        confirmed_in_sent_items = $true
    }
    $result | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Add-Content -LiteralPath $logPath -Value "$(Get-Date -Format o) sent summary for $dateKey with $count upload(s)"
    $result | ConvertTo-Json
}
catch {
    Add-Content -LiteralPath $logPath -Value "$(Get-Date -Format o) daily summary failed for ${dateKey}: $($_.Exception.Message)"
    throw
}
finally {
    foreach ($object in @($sentFolder, $namespace, $mail, $outlook)) {
        if ($null -ne $object) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($object) }
    }
}
