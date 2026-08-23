param(
    [ValidateSet('preview','final')][string]$Quality = 'preview',
    [switch]$SkipFrames
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $Root '..\..')
$Output = Join-Path $Root 'output'
$Audio = Join-Path $Output 'audio'
$Frames = Join-Path $Output 'frames'
New-Item -ItemType Directory -Force $Audio, $Frames | Out-Null

$Blender = Get-ChildItem (Join-Path $RepoRoot '.tools') -Filter blender.exe -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match 'blender-5\.2\.0' } |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $Blender) {
    $Blender = Get-ChildItem 'C:\Program Files\Blender Foundation' -Filter blender.exe -Recurse -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}
if (-not $Blender) { throw 'Blender was not found. Install Blender or add blender.exe to PATH.' }

$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { throw "Workspace Python was not found at $Python" }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw 'FFmpeg was not found on PATH.' }

& $Python (Join-Path $Root 'make_audio.py')
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'make_voice.ps1') -OutputPath (Join-Path $Audio 'apple-voice.wav')

if (-not $SkipFrames) {
    Get-ChildItem $Frames -Filter 'frame-*.png' -ErrorAction SilentlyContinue | Remove-Item -Force
    & $Blender --background --python (Join-Path $Root 'create_scene.py') -- --quality $Quality
    if ($LASTEXITCODE -ne 0) { throw "Blender scene creation failed with exit code $LASTEXITCODE" }
    $BlendFile = Join-Path $Output $(if ($Quality -eq 'preview') { 'pip-apple-preview.blend' } else { 'pip-apple.blend' })
    & $Blender --background $BlendFile -a
    if ($LASTEXITCODE -ne 0) { throw "Blender render failed with exit code $LASTEXITCODE" }
}

$Size = if ($Quality -eq 'preview') { '640x360' } else { '1280x720' }
$Final = Join-Path $Output $(if ($Quality -eq 'preview') { 'pip-the-apple-preview.mp4' } else { 'pip-the-apple.mp4' })
$Music = Join-Path $Audio 'apple-music.wav'
$Voice = Join-Path $Audio 'apple-voice.wav'

& ffmpeg -y -framerate 24 -i (Join-Path $Frames 'frame-%04d.png') -i $Music -i $Voice `
    -filter_complex "[1:a]volume=0.20[m];[2:a]volume=1.15,apad,atrim=duration=52[v];[m][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" `
    -map 0:v -map '[a]' -t 52 -r 24 -s $Size -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p `
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart $Final
if ($LASTEXITCODE -ne 0) { throw "FFmpeg failed with exit code $LASTEXITCODE" }

& ffprobe -v error -show_entries 'format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels' -of json $Final |
    Set-Content -Encoding utf8 (Join-Path $Output 'ffprobe-report.json')
Write-Output "Created $Final"
