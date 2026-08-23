param([string]$Root = 'C:\KidsRhymes')
$ErrorActionPreference = 'Stop'
$baa = Join-Path $Root 'output\baa-baa-black-sheep'
$tmp = Join-Path $baa 'tmp'
$audio = Join-Path $baa 'audio'
New-Item -ItemType Directory -Force $tmp,$audio | Out-Null

# “Bah” is intentional phonetic input: Windows SAPI otherwise reads “Baa” as B-A-A.
$spokenLines = @(
  'Bah, bah, black sheep,','Have you any wool?','Yes sir, yes sir,','Three bags full.',
  'One for the master,','One for the dame,','And one for the little child','Who lives down the lane.',
  'Bah, bah, black sheep,','Have you any wool?','Yes sir, yes sir,','Three bags full.'
)
$ssml = "<speak version='1.0' xml:lang='en-US'><prosody rate='-12%' pitch='+2st'>"
foreach ($line in $spokenLines) { $ssml += "$line<break time='2700ms'/>" }
$ssml += '</prosody></speak>'

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$female = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Gender -eq 'Female' } | Select-Object -First 1
if ($female) { $synth.SelectVoice($female.VoiceInfo.Name) }
$raw = Join-Path $tmp 'lead-raw.wav'
$synth.SetOutputToWaveFile($raw)
$synth.SpeakSsml($ssml)
$synth.Dispose()

$voice = Join-Path $audio 'female-lead-and-chorus.wav'
$filter = "[0:a]adelay=2500|2500,volume=1.0[lead];[0:a]asetrate=57081,aresample=48000,atempo=0.841,adelay=2550|2550,volume=0.16[c1];[0:a]asetrate=53878,aresample=48000,atempo=0.891,adelay=2620|2620,volume=0.12[c2];[lead][c1][c2]amix=3:normalize=0,acompressor=threshold=-18dB:ratio=2.5,apad,atrim=duration=70,afade=t=in:st=2.3:d=0.5,afade=t=out:st=66:d=3[a]"
& ffmpeg -y -i $raw -filter_complex $filter -map '[a]' -ar 48000 $voice
if ($LASTEXITCODE) { throw 'Corrected vocal generation failed.' }
Write-Output "Corrected vocal: $voice"

