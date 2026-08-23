$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = Resolve-Path (Join-Path $Root '..')
$RepoRoot = Resolve-Path (Join-Path $Project '..\..')
$Assets = Join-Path $Root 'assets'
$Output = Join-Path $Root 'output'
$ProjectAudio = Join-Path $Project 'output\audio'
$Work = Join-Path $RepoRoot '.render-work'
New-Item -ItemType Directory -Force $Output | Out-Null

$Background = Join-Path $Assets 'orchard-background.png'
$Neutral = Join-Path $Assets 'pip-neutral.png'
$Speaking = Join-Path $Assets 'pip-speaking.png'
$Blink = Join-Path $Assets 'pip-blink.png'
$Bunny = Join-Path $Assets 'bunny-neutral.png'
$Basket = Join-Path $Assets 'picnic-basket-source.png'
$Music = Join-Path $ProjectAudio 'apple-music.wav'
$Voice = Join-Path $Work 'missing-basket-voice.wav'
$Filter = Join-Path $Root 'animation-filter.txt'
$Final = Join-Path $Output 'pip-and-the-missing-picnic-basket.mp4'
$FinalWork = Join-Path $Work 'pip-and-the-missing-picnic-basket.mp4'
$Report = Join-Path $Output 'missing-basket-ffprobe-report.json'
$ReportWork = Join-Path $Work 'missing-basket-ffprobe-report.json'

if (-not (Test-Path $Music)) {
    & (Join-Path $Project '..\..\.venv\Scripts\python.exe') (Join-Path $Project 'make_audio.py')
    if ($LASTEXITCODE -ne 0) { throw 'Music generation failed.' }
}
& (Join-Path $Project 'make_voice.ps1') -OutputPath $Voice
if ($LASTEXITCODE -ne 0) { throw 'Voice generation failed.' }

foreach ($path in $Background,$Neutral,$Speaking,$Blink,$Bunny,$Basket,$Music,$Voice,$Filter) {
    if (-not (Test-Path $path)) { throw "Missing required asset: $path" }
}
$Graph = Get-Content -Raw $Filter

& ffmpeg -y `
    -loop 1 -t 52 -i $Background `
    -loop 1 -t 52 -i $Neutral `
    -loop 1 -t 52 -i $Speaking `
    -loop 1 -t 52 -i $Blink `
    -loop 1 -t 52 -i $Bunny `
    -loop 1 -t 52 -i $Basket `
    -i $Music -i $Voice `
    -filter_complex $Graph -map '[vout]' -map '[aout]' `
    -t 52 -r 24 -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p `
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart $FinalWork
if ($LASTEXITCODE -ne 0) { throw "FFmpeg animation failed with exit code $LASTEXITCODE" }

& ffprobe -v error -show_entries 'format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels' -of json $FinalWork |
    Set-Content -Encoding utf8 $ReportWork
foreach ($copy in @(@($FinalWork, $Final), @($ReportWork, $Report))) {
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Copy-Item -LiteralPath $copy[0] -Destination $copy[1] -Force
            break
        }
        catch {
            if ($attempt -eq 5) { throw }
            Start-Sleep -Milliseconds 400
        }
    }
}
Write-Output "Created $Final"
