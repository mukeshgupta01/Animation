param(
  [string]$Root = $PSScriptRoot,
  [string]$Model = 'music-3.0-free'
)

$ErrorActionPreference = 'Stop'

$apiKey = $env:MINIMAX_API_KEY
if (-not $apiKey) {
  $apiKey = [Environment]::GetEnvironmentVariable('MINIMAX_API_KEY', 'User')
}
if (-not $apiKey) {
  throw @"
MINIMAX_API_KEY is not set. Create an API key at https://platform.minimax.io,
then save it locally (do not paste it into source code):

  [Environment]::SetEnvironmentVariable('MINIMAX_API_KEY', 'YOUR_KEY', 'User')

After setting it, run this script again.
"@
}

$lyrics = @'
[Intro]

[Verse]
Baa, baa, black sheep,
Have you any wool?
Yes sir, yes sir,
Three bags full.

One for the master,
One for the dame,
And one for the little child
Who lives down the lane.

[Chorus]
Baa, baa, black sheep,
Have you any wool?
Yes sir, yes sir,
Three bags full.

[Verse]
One for the master,
One for the dame,
And one for the little child
Who lives down the lane.

[Final Chorus]
Baa, baa, black sheep,
Have you any wool?
Yes sir, yes sir,
Three bags full.

[Outro]
'@

$body = @{
  model = $Model
  prompt = 'A cheerful English nursery rhyme sung clearly in tune by one warm, friendly female singer with a light children chorus only on the choruses. Simple memorable melody, playful acoustic guitar, ukulele, glockenspiel, soft hand claps, gentle bass, major key, about 105 BPM, approximately 70 seconds. Crisp intelligible words and natural phrasing. Singing from the first verse, not spoken. No narration, no animal noises, no sheep bleats, no comedy sound effects, no strange vocal effects, no long instrumental sections.'
  lyrics = $lyrics
  stream = $false
  output_format = 'url'
  lyrics_optimizer = $false
  is_instrumental = $false
  audio_setting = @{
    sample_rate = 44100
    bitrate = 256000
    format = 'mp3'
  }
} | ConvertTo-Json -Depth 5

$headers = @{
  Authorization = "Bearer $apiKey"
  'Content-Type' = 'application/json'
}

Write-Host "Generating the sung rhyme with MiniMax $Model..."
$response = Invoke-RestMethod `
  -Uri 'https://api.minimax.io/v1/music_generation' `
  -Method Post `
  -Headers $headers `
  -Body $body `
  -TimeoutSec 600

if ($response.base_resp.status_code -ne 0) {
  throw "MiniMax generation failed: $($response.base_resp.status_msg) (code $($response.base_resp.status_code))"
}
if (-not $response.data.audio) {
  throw 'MiniMax returned success but no audio data.'
}

$audioDir = Join-Path $Root 'output\baa-baa-black-sheep\audio'
New-Item -ItemType Directory -Force $audioDir | Out-Null
$output = Join-Path $audioDir 'baa-baa-black-sheep-minimax.mp3'

if ($response.data.audio -match '^https?://') {
  Invoke-WebRequest -Uri $response.data.audio -OutFile $output -TimeoutSec 600
} else {
  $hex = [string]$response.data.audio
  $bytes = New-Object byte[] ($hex.Length / 2)
  for ($i = 0; $i -lt $bytes.Length; $i++) {
    $bytes[$i] = [Convert]::ToByte($hex.Substring($i * 2, 2), 16)
  }
  [IO.File]::WriteAllBytes($output, $bytes)
}

$probe = & ffprobe -v error -show_entries 'format=duration' -of 'default=noprint_wrappers=1:nokey=1' $output
if ($LASTEXITCODE) { throw 'The generated MP3 could not be validated with ffprobe.' }

Write-Host "Saved: $output"
Write-Host "Duration: $([math]::Round([double]$probe, 2)) seconds"
