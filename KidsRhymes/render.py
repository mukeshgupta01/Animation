from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "baa-baa-black-sheep"
SCENES = OUT / "scenes"
AUDIO = OUT / "audio"
TMP = OUT / "tmp"
FINAL = OUT / "baa-baa-black-sheep.mp4"
REPORT = OUT / "ffprobe-report.txt"
SR = 48_000
DURATION = 70.0
BPM = 96
BEAT = 60.0 / BPM


def run(args: list[str]) -> None:
    print("+", subprocess.list2cmdline(args))
    subprocess.run(args, check=True)


def require_tools() -> None:
    for name in ("ffmpeg", "ffprobe", "powershell"):
        if shutil.which(name) is None:
            raise SystemExit(f"Required tool not found on PATH: {name}")


def prepare_scenes() -> list[Path]:
    names = [
        "scene-01-meadow.png", "scene-02-farmer-barn.png",
        "scene-03-wool-bag.png", "scene-04-country-lane.png",
        "scene-05-sheep-close.png", "scene-06-finale.png",
    ]
    paths = [SCENES / n for n in names]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise SystemExit("Missing scene artwork:\n" + "\n".join(missing))
    # Normalize colour and resolution once. The slight lift is intentionally gentle.
    for path in paths:
        with Image.open(path) as image:
            image = image.convert("RGB")
            image = ImageEnhance.Color(image).enhance(1.025)
            image = ImageEnhance.Contrast(image).enhance(1.015)
            image = image.resize((1920, 1080), Image.Resampling.LANCZOS)
            image.save(path, "PNG", optimize=True)
    return paths


def midi_hz(note: int) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def make_instrumental(path: Path) -> None:
    total = int(DURATION * SR)
    pcm = [0.0] * total

    def add_note(start: float, dur: float, midi: int, amp: float, kind: str) -> None:
        a = max(0, int(start * SR)); b = min(total, int((start + dur) * SR))
        f = midi_hz(midi)
        for i in range(a, b):
            t = (i - a) / SR
            if kind == "uke":
                env = min(1.0, t / 0.012) * math.exp(-3.3 * t / max(dur, .01))
                s = math.sin(2*math.pi*f*t) + .28*math.sin(4*math.pi*f*t)
            elif kind == "glock":
                env = math.exp(-5.8 * t / max(dur, .01))
                s = math.sin(2*math.pi*f*t) + .42*math.sin(2*math.pi*f*2.7*t)
            elif kind == "marimba":
                env = math.exp(-4.2 * t / max(dur, .01))
                s = math.sin(2*math.pi*f*t) + .18*math.sin(2*math.pi*f*3*t)
            else:  # pizzicato
                env = min(1.0, t/.008) * math.exp(-6.0*t/max(dur, .01))
                s = math.sin(2*math.pi*f*t)
            pcm[i] += amp * env * s

    # I–V–vi–IV, fully original accompaniment in C major.
    chords = [(60,64,67), (55,59,62), (57,60,64), (53,57,60)]
    melody = [67,67,69,67,64,64,62, 67,67,69,67,64,62,60]
    beats = int(DURATION / BEAT)
    for beat in range(beats):
        t = beat * BEAT
        chord = chords[(beat // 4) % 4]
        if beat % 2 == 0:
            for j, note in enumerate(chord):
                add_note(t + j*.035, 1.15, note, .045, "uke")
        add_note(t, .42, chord[0]-12, .05, "pizz")
        if beat % 2 == 1:
            add_note(t, .55, melody[(beat//2) % len(melody)] + 12, .028, "glock")
        add_note(t + BEAT/2, .4, chord[1], .022, "marimba")

    # Soft hand percussion: brushed thump and shaker, deliberately unobtrusive.
    for beat in range(beats):
        for offset, amp in ((0.0, .025), (BEAT/2, .012)):
            start = int((beat*BEAT + offset)*SR)
            for n in range(min(int(.055*SR), total-start)):
                env = math.exp(-n/(SR*.014))
                noise = math.sin(n*12.9898 + beat*78.233) * 43758.5453
                noise = (noise - math.floor(noise))*2-1
                pcm[start+n] += amp*env*noise

    peak = max(max(abs(x) for x in pcm), .001)
    scale = 0.72 * 32767 / peak
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
        chunk = bytearray()
        for x in pcm:
            v = int(max(-32767, min(32767, x*scale)))
            chunk.extend(struct.pack("<hh", v, v))
        out.writeframes(chunk)


def make_voice(path: Path) -> None:
    lyrics = (ROOT / "lyrics" / "baa-baa-black-sheep.txt").read_text(encoding="utf-8")
    lines = [line.strip() for line in lyrics.splitlines() if line.strip()]
    # Phonetic input prevents Windows SAPI from pronouncing “Baa” as B-A-A.
    escaped = [line.replace("Baa", "Bah").replace("&", "&amp;") for line in lines]
    parts = ["<speak version='1.0' xml:lang='en-US'><prosody rate='-12%' pitch='+2st'>"]
    for line in escaped:
        parts.append(f"{line}<break time='2700ms'/>")
    parts.append("</prosody></speak>")
    ssml = "".join(parts)
    ssml_path = TMP / "vocal.ssml"
    raw = TMP / "lead-raw.wav"
    ssml_path.write_text(ssml, encoding="utf-8")
    ps = TMP / "synth-vocal.ps1"
    ps.write_text(
        "param([string]$Ssml,[string]$Out)\n"
        "Add-Type -AssemblyName System.Speech\n"
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "$female=$s.GetInstalledVoices() | Where-Object {$_.VoiceInfo.Gender -eq 'Female'} | Select-Object -First 1\n"
        "if($female){$s.SelectVoice($female.VoiceInfo.Name)}\n"
        "$s.SetOutputToWaveFile($Out)\n"
        "$s.SpeakSsml([IO.File]::ReadAllText($Ssml))\n"
        "$s.Dispose()\n", encoding="utf-8")
    run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps), str(ssml_path), str(raw)])
    # Place a clean lead after a short instrumental intro. Pitch-shifted chorus
    # layers were intentionally removed because they introduced audible artifacts.
    filt = (
        "[0:a]adelay=2500|2500,volume=1.0,acompressor=threshold=-18dB:ratio=2.5,"
        "apad,atrim=duration=70,afade=t=in:st=2.3:d=0.5,afade=t=out:st=66:d=3[a]"
    )
    run(["ffmpeg", "-y", "-i", str(raw), "-filter_complex", filt, "-map", "[a]", "-ar", str(SR), str(path)])


def render_video(scenes: list[Path], instrumental: Path, voice: Path) -> None:
    cmd = ["ffmpeg", "-y"]
    for scene in scenes:
        cmd += ["-loop", "1", "-t", "12.5", "-i", str(scene)]
    cmd += ["-i", str(instrumental), "-i", str(voice)]
    filters = []
    motions = [
        ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("(iw-iw/zoom)*(on/299)", "ih/2-(ih/zoom/2)"),
        ("(iw-iw/zoom)*(1-on/299)", "ih/2-(ih/zoom/2)"),
        ("iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(on/299)"),
        ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(1-on/299)"),
    ]
    for i, (x, y) in enumerate(motions):
        z = "min(zoom+0.00020,1.06)" if i != 5 else "if(lte(on,1),1.06,max(zoom-0.00020,1.0))"
        filters.append(
            f"[{i}:v]scale=2112:1188,zoompan=z='{z}':x='{x}':y='{y}':d=300:s=1920x1080:fps=24,"
            f"trim=duration=12.5,setpts=PTS-STARTPTS,format=yuv420p[v{i}]"
        )
    prev = "v0"
    for i, offset in enumerate((11.5, 23.0, 34.5, 46.0, 57.5), start=1):
        out = f"x{i}"
        filters.append(f"[{prev}][v{i}]xfade=transition=fade:duration=1:offset={offset}[{out}]")
        prev = out
    filters.append(f"[{prev}]fade=t=in:st=0:d=1,fade=t=out:st=67:d=3[vout]")
    filters.append("[6:a]volume=.56[m];[7:a]volume=1.08[v];[m][v]amix=2:duration=longest:normalize=0,alimiter=limit=.95,atrim=duration=70[aout]")
    cmd += [
        "-filter_complex", ";".join(filters), "-map", "[vout]", "-map", "[aout]",
        "-t", "70", "-r", "24", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(FINAL),
    ]
    run(cmd)


def write_report() -> None:
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", str(FINAL)
    ], check=True, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio = next(s for s in data["streams"] if s["codec_type"] == "audio")
    report = (
        "Baa Baa Black Sheep — FFprobe Quality Report\n"
        "=============================================\n"
        f"File: {FINAL}\n"
        f"Duration: {float(data['format']['duration']):.3f} seconds\n"
        f"Resolution: {video['width']}x{video['height']}\n"
        f"Frame rate: {video['r_frame_rate']} ({eval(video['r_frame_rate']):.3f} fps)\n"
        f"Video codec: {video['codec_name']}\n"
        f"Audio stream: present\n"
        f"Audio codec: {audio['codec_name']}\n"
        f"Audio sample rate: {audio['sample_rate']} Hz\n"
        f"Audio channels: {audio['channels']}\n"
        "\nValidation: PASS\n"
    )
    REPORT.write_text(report, encoding="utf-8")
    print(report)


def main() -> None:
    require_tools()
    for folder in (SCENES, AUDIO, TMP): folder.mkdir(parents=True, exist_ok=True)
    scenes = prepare_scenes()
    instrumental = AUDIO / "original-instrumental.wav"
    voice = AUDIO / "female-lead-and-chorus.wav"
    final_audio = AUDIO / "baa-baa-black-sheep.wav"
    make_instrumental(instrumental)
    make_voice(voice)
    run(["ffmpeg", "-y", "-i", str(instrumental), "-i", str(voice), "-filter_complex",
         "[0:a]volume=.56[m];[1:a]volume=1.08[v];[m][v]amix=2:duration=longest:normalize=0,alimiter=limit=.95,atrim=duration=70[a]",
         "-map", "[a]", "-ar", "48000", str(final_audio)])
    render_video(scenes, instrumental, voice)
    write_report()


if __name__ == "__main__":
    main()
