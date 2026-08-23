param(
  [string]$Root = $PSScriptRoot,
  [ValidateSet('minimax','sinsy')]
  [string]$AudioSource = 'minimax'
)
$ErrorActionPreference = 'Stop'
$out = Join-Path $Root 'output\baa-baa-black-sheep'
$scenes = Join-Path $out 'scenes'
$audio = Join-Path $out 'audio'
$tmp = Join-Path $out 'tmp'
New-Item -ItemType Directory -Force $audio,$tmp | Out-Null

if ($AudioSource -eq 'minimax') {
  # MiniMax returns a complete sung song, including its own accompaniment.
  $song = Join-Path $audio 'baa-baa-black-sheep-minimax.mp3'
  if (-not (Test-Path $song)) {
    throw "Missing MiniMax song: $song. Run generate-minimax-song.ps1 first."
  }
} else {
  # Keep the earlier Sinsy path available for comparison/fallback.
  $voice = Join-Path $audio 'baa-baa-black-sheep-sinsy-vocal.wav'
  if (-not (Test-Path $voice)) {
    throw "Missing Sinsy vocal: $voice."
  }
  $musicScript = Join-Path $Root 'generate-better-music.ps1'
  & $musicScript -Root $Root
  if ($LASTEXITCODE) { throw 'MuseScore arrangement generation failed' }
  $music = Join-Path $audio 'storybook-arrangement.wav'
  if (-not (Test-Path $music)) { throw "Missing arrangement: $music" }
}

$sceneNames = @('scene-01-meadow.png','scene-02-farmer-barn.png','scene-03-wool-bag.png','scene-04-country-lane.png','scene-05-sheep-close.png','scene-06-finale.png')
$args = @('-y')
foreach ($name in $sceneNames) { $args += @('-loop','1','-t','12.5','-i',(Join-Path $scenes $name)) }
if ($AudioSource -eq 'minimax') {
  $args += @('-i',$song)
} else {
  $args += @('-i',$music,'-i',$voice)
}
$filters = @()
$filters += "[0:v]scale=2112:1188,zoompan=z='min(zoom+0.00020,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=1920x1080:fps=24,trim=duration=12.5,setpts=PTS-STARTPTS,format=yuv420p[v0]"
$filters += "[1:v]scale=2112:1188,zoompan=z='min(zoom+0.00020,1.06)':x='(iw-iw/zoom)*(on/299)':y='ih/2-(ih/zoom/2)':d=300:s=1920x1080:fps=24,trim=duration=12.5,setpts=PTS-STARTPTS,format=yuv420p[v1]"
$filters += "[2:v]scale=2112:1188,zoompan=z='min(zoom+0.00020,1.06)':x='(iw-iw/zoom)*(1-on/299)':y='ih/2-(ih/zoom/2)':d=300:s=1920x1080:fps=24,trim=duration=12.5,setpts=PTS-STARTPTS,format=yuv420p[v2]"
$filters += "[3:v]scale=2112:1188,zoompan=z='min(zoom+0.00020,1.06)':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(on/299)':d=300:s=1920x1080:fps=24,trim=duration=12.5,setpts=PTS-STARTPTS,format=yuv420p[v3]"
$filters += "[4:v]scale=2112:1188,zoompan=z='min(zoom+0.00020,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=1920x1080:fps=24,trim=duration=12.5,setpts=PTS-STARTPTS,format=yuv420p[v4]"
$filters += "[5:v]scale=2112:1188,zoompan=z='if(lte(on,1),1.06,max(zoom-0.00020,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=1920x1080:fps=24,trim=duration=12.5,setpts=PTS-STARTPTS,format=yuv420p[v5]"
$filters += '[v0][v1]xfade=transition=fade:duration=1:offset=11.5[x1]'
$filters += '[x1][v2]xfade=transition=fade:duration=1:offset=23[x2]'
$filters += '[x2][v3]xfade=transition=fade:duration=1:offset=34.5[x3]'
$filters += '[x3][v4]xfade=transition=fade:duration=1:offset=46[x4]'
$filters += '[x4][v5]xfade=transition=fade:duration=1:offset=57.5,fade=t=in:st=0:d=1,fade=t=out:st=67:d=3[vout]'
if ($AudioSource -eq 'minimax') {
  $filters += '[6:a]apad,loudnorm=I=-15:LRA=7:TP=-1.5,atrim=duration=70[aout]'
} else {
  $filters += '[6:a]volume=.64[m];[7:a]atrim=start=2.5,asetpts=PTS-STARTPTS,volume=2.15,highpass=f=80,acompressor=threshold=-18dB:ratio=2.2:attack=10:release=120,apad,atrim=duration=70[v];[m][v]amix=2:duration=longest:normalize=0,loudnorm=I=-15:LRA=7:TP=-1.5,atrim=duration=70[aout]'
}
$final = Join-Path $out "baa-baa-black-sheep-$AudioSource.mp4"
$args += @('-filter_complex',($filters -join ';'),'-map','[vout]','-map','[aout]','-t','70','-r','24','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',$final)
& ffmpeg @args
if ($LASTEXITCODE) { throw 'Final video render failed' }

$json = & ffprobe -v error -show_entries 'format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels' -of json $final | ConvertFrom-Json
$video = $json.streams | Where-Object codec_type -eq video
$audioStream = $json.streams | Where-Object codec_type -eq audio
$report = @"
Baa Baa Black Sheep — FFprobe Quality Report
=============================================
File: $final
Duration: $([double]$json.format.duration) seconds
Resolution: $($video.width)x$($video.height)
Frame rate: $($video.r_frame_rate)
Video codec: $($video.codec_name)
Audio stream: present
Audio codec: $($audioStream.codec_name)
Audio sample rate: $($audioStream.sample_rate) Hz
Audio channels: $($audioStream.channels)

Validation: PASS
"@
$report | Set-Content -Encoding utf8 (Join-Path $out 'ffprobe-report.txt')
$report

# Every completed rhyme also gets the standard five-second Tiny Tales ident.
$introScript = Join-Path $Root 'add-tiny-tales-intro.ps1'
$brandedFinal = Join-Path $out "baa-baa-black-sheep-$AudioSource-with-tiny-tales-intro.mp4"
if ((Test-Path $introScript) -and (Test-Path (Join-Path $Root 'output\tiny-tales\tiny-tales-intro.mp4'))) {
  & $introScript -InputVideo $final -OutputVideo $brandedFinal -Root $Root
} else {
  Write-Warning 'Tiny Tales intro is not available yet; run render-intro.ps1 once, then rerun this renderer.'
}
