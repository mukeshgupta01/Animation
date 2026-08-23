param(
  [Parameter(Mandatory = $true)][string]$InputVideo,
  [string]$OutputVideo,
  [string]$Root = 'C:\KidsRhymes'
)

$ErrorActionPreference = 'Stop'
$intro = Join-Path $Root 'output\tiny-tales\tiny-tales-intro.mp4'

if (-not (Test-Path -LiteralPath $intro)) {
  throw "Tiny Tales intro not found: $intro. Run render-intro.ps1 first."
}
if (-not (Test-Path -LiteralPath $InputVideo)) {
  throw "Input video not found: $InputVideo"
}

$inputItem = Get-Item -LiteralPath $InputVideo
if (-not $OutputVideo) {
  $OutputVideo = Join-Path $inputItem.DirectoryName ($inputItem.BaseName + '-with-tiny-tales-intro.mp4')
}
if ([IO.Path]::GetFullPath($InputVideo) -eq [IO.Path]::GetFullPath($OutputVideo)) {
  throw 'Input and output paths must be different.'
}

$outputDirectory = Split-Path -Parent $OutputVideo
New-Item -ItemType Directory -Force $outputDirectory | Out-Null

& ffmpeg -y -i $intro -i $InputVideo `
  -filter_complex '[0:v]fps=24,scale=1920:1080,setsar=1[v0];[1:v]fps=24,scale=1920:1080,setsar=1[v1];[v0][v1]concat=n=2:v=1:a=0[v];[0:a]aresample=48000[a0];[1:a]aresample=48000[a1];[a0][a1]concat=n=2:v=0:a=1[a]' `
  -map '[v]' -map '[a]' -r 24 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p `
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart $OutputVideo

if ($LASTEXITCODE) { throw 'Failed to prepend the Tiny Tales intro.' }

& ffprobe -v error -show_entries 'format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate' -of json $OutputVideo |
  Set-Content -Encoding utf8 ($OutputVideo + '.ffprobe.json')

Write-Output "Branded video: $OutputVideo"

