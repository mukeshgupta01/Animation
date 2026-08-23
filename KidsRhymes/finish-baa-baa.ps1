param([string]$Root = 'C:\KidsRhymes')
$ErrorActionPreference = 'Stop'
$baa = Join-Path $Root 'output\baa-baa-black-sheep'
$brand = Join-Path $Root 'output\tiny-tales'
$intro = Join-Path $brand 'tiny-tales-intro.mp4'
$baseVideo = Join-Path $baa 'baa-baa-black-sheep.mp4'
$voice = Join-Path $baa 'audio\female-lead-and-chorus.wav'
$music = Join-Path $baa 'audio\storybook-arrangement.wav'
$mark = Join-Path $brand 'tiny-tales-watermark-under-1mb.png'
$body = Join-Path $baa 'tmp\baa-baa-remixed-watermarked.mp4'
$final = Join-Path $baa 'baa-baa-black-sheep-tiny-tales-final.mp4'

foreach($f in @($intro,$baseVideo,$voice,$music,$mark)){if(-not(Test-Path $f)){throw "Missing: $f"}}

# Preserve the picture, add a discreet 130 px watermark, and replace the weak soundtrack.
$filter = "[1:v]scale=130:130,format=rgba,colorchannelmixer=aa=0.78[wm];[0:v][wm]overlay=W-w-38:H-h-32:format=auto[v];[2:a]volume=1.12[lead];[3:a]volume=0.60[music];[lead][music]amix=2:duration=first:normalize=0,loudnorm=I=-15:LRA=7:TP=-1.5[a]"
& ffmpeg -y -i $baseVideo -i $mark -i $voice -i $music -filter_complex $filter -map '[v]' -map '[a]' -t 70 -r 24 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -movflags +faststart $body
if($LASTEXITCODE){throw 'Watermarked remix render failed.'}

& ffmpeg -y -i $intro -i $body -filter_complex '[0:v][1:v]concat=n=2:v=1:a=0[v];[0:a][1:a]concat=n=2:v=0:a=1[a]' -map '[v]' -map '[a]' -r 24 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -movflags +faststart $final
if($LASTEXITCODE){throw 'Final branded render failed.'}

cmd /c "ffmpeg -hide_banner -i `"$final`" -af volumedetect -f null NUL 2> `"$baa\final-audio-level-report.txt`""
& ffprobe -v error -show_entries 'format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate' -of json $final | Set-Content -Encoding utf8 (Join-Path $baa 'final-ffprobe-report.json')
Write-Output "Final video: $final"
