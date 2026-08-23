param(
    [Parameter(Mandatory=$true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$partsDirectory = Join-Path (Split-Path -Parent $OutputPath) 'voice-parts'
New-Item -ItemType Directory -Force $partsDirectory | Out-Null
$lines = @(
    @{ Start = 3.0;  Voice = 'slt'; Text = 'Hello, friends! I packed a picnic, but my basket has vanished. Will you help me find it?' },
    @{ Start = 10.0; Voice = 'slt'; Text = 'A clue! Tiny footprints. Hop, hop, hop! They lead toward the old apple tree.' },
    @{ Start = 17.0; Voice = 'slt'; Text = 'And look, three little crumbs. Count with me: one, two, three. The trail goes this way!' },
    @{ Start = 24.0; Voice = 'slt'; Text = 'Now the trail wiggles left, then right, then disappears! Oh, where could the basket be?' },
    @{ Start = 31.0; Voice = 'slt'; Text = 'Surprise! Bunny has the basket. He was preparing a picnic for everyone.' },
    @{ Start = 38.0; Voice = 'kal'; Text = 'I should have asked first, Pip.' },
    @{ Start = 41.0; Voice = 'slt'; Text = 'That is okay. Next time, please ask.' },
    @{ Start = 45.0; Voice = 'slt'; Text = 'Friends share, friends ask, and picnics are sweeter together!' }
)

$partPaths = @()
for ($index = 0; $index -lt $lines.Count; $index++) {
    $line = $lines[$index]
    $stem = 'story-line-{0:D2}' -f ($index + 1)
    $partPath = Join-Path $partsDirectory "$stem.wav"
    $safeText = $line.Text.Replace('\', '\\').Replace(':', '\:').Replace(',', '\,').Replace("'", "\'")
    & ffmpeg -y -f lavfi -i "flite=text='$safeText':voice=$($line.Voice)" -ar 48000 $partPath
    if ($LASTEXITCODE -ne 0) { throw "Speech synthesis failed for $stem." }
    $partPaths += $partPath
}

$arguments = @('-y')
foreach ($partPath in $partPaths) { $arguments += @('-i', $partPath) }
$filters = @()
for ($index = 0; $index -lt $lines.Count; $index++) {
    $delay = [int]($lines[$index].Start * 1000)
    $filters += "[$index`:a]adelay=$delay|$delay[v$index]"
}
$mixInputs = (0..($lines.Count - 1) | ForEach-Object { "[v$_]" }) -join ''
$filters += "${mixInputs}amix=inputs=$($lines.Count):duration=longest:normalize=0,apad,atrim=duration=52[out]"
$arguments += @('-filter_complex', ($filters -join ';'), '-map', '[out]', '-ar', '48000', $OutputPath)
& ffmpeg @arguments
if ($LASTEXITCODE -ne 0) { throw "FFmpeg voice assembly failed with exit code $LASTEXITCODE" }
