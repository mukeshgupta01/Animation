param([string]$Root = 'C:\KidsRhymes')
$ErrorActionPreference = 'Stop'
$brand = Join-Path $Root 'output\tiny-tales'
$assets = Join-Path $brand 'assets'
$tmp = Join-Path $brand 'tmp'
New-Item -ItemType Directory -Force $assets,$tmp | Out-Null

$empty = Join-Path $assets 'intro-empty-meadow.png'
$plain = Join-Path $assets 'intro-bunny-open.png'
$plainBlink = Join-Path $assets 'intro-bunny-blink.png'
$rainbow = Join-Path $assets 'intro-bunny-rainbow-open.png'
$rainbowBlink = Join-Path $assets 'intro-bunny-rainbow-blink.png'
$intro = Join-Path $brand 'tiny-tales-intro.mp4'
$voiceRaw = Join-Path $tmp 'tiny-tales-voice.wav'
$audio = Join-Path $tmp 'tiny-tales-audio.wav'
$font = 'C\:/Windows/Fonts/arialbd.ttf'

foreach ($file in @($empty,$plain,$plainBlink,$rainbow,$rainbowBlink)) {
  if (-not (Test-Path $file)) { throw "Missing ident asset: $file" }
}

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$female = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Gender -eq 'Female' } | Select-Object -First 1
if ($female) { $synth.SelectVoice($female.VoiceInfo.Name) }
$synth.Rate = -1
$synth.SetOutputToWaveFile($voiceRaw)
$synth.Speak('Tiny Tales')
$synth.Dispose()

# Gentle C-major chime under the locally synthesized spoken ident.
$soundFilter = "sine=f=523.251:r=48000:d=5,volume=0.035[c];sine=f=659.255:r=48000:d=5,volume=0.025[e];sine=f=783.991:r=48000:d=5,volume=0.02[g];[3:a]adelay=2150|2150,volume=1.25[v];[c][e][g][v]amix=4:duration=longest:normalize=0,aecho=0.8:0.25:55:0.10,afade=t=in:d=0.3,afade=t=out:st=4.35:d=0.65,apad,atrim=duration=5[a]"
& ffmpeg -y -f lavfi -i 'sine=f=1:d=0.01' -f lavfi -i 'sine=f=1:d=0.01' -f lavfi -i 'sine=f=1:d=0.01' -i $voiceRaw -filter_complex $soundFilter -map '[a]' -ar 48000 $audio
if ($LASTEXITCODE) { throw 'Tiny Tales audio generation failed' }

$filter = @"
[0:v]scale=1920:1080,setsar=1,fps=24,format=yuv420p,trim=duration=5,setpts=PTS-STARTPTS[e];
[1:v]scale=1920:1080,setsar=1,fps=24,format=yuv420p,trim=duration=5,setpts=PTS-STARTPTS[p];
[2:v]scale=1920:1080,setsar=1,fps=24,format=yuv420p,trim=duration=5,setpts=PTS-STARTPTS[pb];[pb]nullsink;
[3:v]scale=1920:1080,setsar=1,fps=24,format=yuv420p,trim=duration=5,setpts=PTS-STARTPTS,split=3[rbase][r1][r2];
[4:v]scale=1920:1080,setsar=1,fps=24,format=yuv420p,trim=duration=5,setpts=PTS-STARTPTS,split=2[rb1][rb2];
[e][p]xfade=transition=fade:duration=0.35:offset=0.35[x1];
[x1][rbase]xfade=transition=smoothleft:duration=1.0:offset=1.15[x2];
[x2]trim=start=0:end=2.70,setpts=PTS-STARTPTS[s0];
[rb1]trim=duration=0.15,setpts=PTS-STARTPTS[s1];
[r1]trim=duration=0.80,setpts=PTS-STARTPTS[s2];
[rb2]trim=duration=0.15,setpts=PTS-STARTPTS[s3];
[r2]trim=duration=1.20,setpts=PTS-STARTPTS[s4];
[s0][s1][s2][s3][s4]concat=n=5:v=1:a=0,
drawtext=fontfile='$font':text='Tiny Tales':fontsize=128:fontcolor=white:borderw=7:bordercolor=0xD89A25:shadowx=5:shadowy=6:shadowcolor=0x087D84@0.75:x=(w-text_w)/2:y=95:enable='between(t,1.85,5)',
fade=t=in:d=0.25,fade=t=out:st=4.65:d=0.35[v]
"@ -replace "`r?`n",''

& ffmpeg -y -loop 1 -t 5 -i $empty -loop 1 -t 5 -i $plain -loop 1 -t 5 -i $plainBlink -loop 1 -t 5 -i $rainbow -loop 1 -t 5 -i $rainbowBlink -i $audio -filter_complex $filter -map '[v]' -map '5:a' -t 5 -r 24 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -movflags +faststart $intro
if ($LASTEXITCODE) { throw 'Tiny Tales intro render failed' }

$rhyme = Join-Path $Root 'output\baa-baa-black-sheep\baa-baa-black-sheep.mp4'
$combined = Join-Path $Root 'output\baa-baa-black-sheep\baa-baa-black-sheep-with-tiny-tales-intro.mp4'
& ffmpeg -y -i $intro -i $rhyme -filter_complex '[0:v][1:v]concat=n=2:v=1:a=0[v];[0:a][1:a]concat=n=2:v=0:a=1[a]' -map '[v]' -map '[a]' -r 24 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -movflags +faststart $combined
if ($LASTEXITCODE) { throw 'Combined Tiny Tales video render failed' }

$bannerSource = Join-Path $assets 'tiny-tales-banner-source.png'
$banner = Join-Path $brand 'tiny-tales-youtube-banner-2560x1440.png'
& ffmpeg -y -i $bannerSource -vf 'scale=2560:1440:flags=lanczos' -frames:v 1 -update 1 $banner
if ($LASTEXITCODE) { throw 'Banner sizing failed' }

& ffprobe -v error -show_entries 'format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate' -of json $intro | Set-Content -Encoding utf8 (Join-Path $brand 'intro-ffprobe-report.json')
& ffprobe -v error -show_entries 'format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate' -of json $combined | Set-Content -Encoding utf8 (Join-Path $brand 'combined-ffprobe-report.json')
Write-Output "Intro: $intro"
Write-Output "Combined: $combined"
Write-Output "Banner: $banner"
