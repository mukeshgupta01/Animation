"""Build a note-by-note sung arrangement for Dance With Dad.

Each lyric line is divided into four musical phrases, time-shaped to the
120 BPM grid and moved through an explicit melody with formants preserved.
This is intentionally different from the rejected continuous narration takes.
"""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import re
import subprocess

import edge_tts

import generate_dance_with_dad_chant_song as arrangement


PROJECT = Path(__file__).resolve().parents[2]
ITEM_ID = "dance-with-dad-animal-parade-01"
WORK = PROJECT / "automation" / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
OUTPUT = WORK / "dance-with-dad-sung-song-v4.wav"
RATE = 48000
TOTAL = 100.0
SCENE = 12.0
LINE_STARTS = (0.5, 6.0)
CHUNK_STARTS = (0.0, 0.75, 1.55, 2.55)
CHUNK_DURATIONS = (0.72, 0.72, 0.95, 1.45)
MELODIES = (
    ((0, 4, 7, 12), (7, 5, 4, 0)),
    ((0, 2, 4, 7), (7, 4, 2, 0)),
    ((2, 5, 7, 9), (9, 7, 5, 2)),
    ((0, 4, 7, 11), (7, 4, 2, 4)),
    ((0, 4, 7, 12), (12, 9, 7, 4)),
    ((0, 3, 7, 10), (7, 5, 3, 0)),
    ((2, 5, 9, 12), (9, 7, 5, 2)),
    ((4, 7, 9, 12), (0, 4, 7, 12)),
)
VOICE_SEMAPHORE = asyncio.Semaphore(6)


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def media_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def four_chunks(line: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9']+", line)
    chunks: list[str] = []
    for index in range(4):
        start = round(index * len(words) / 4)
        end = round((index + 1) * len(words) / 4)
        chunks.append(" ".join(words[start:end]) or words[-1])
    return chunks


async def raw_chunk(text: str, path: Path, voice: str) -> None:
    if path.is_file() and path.stat().st_size > 800:
        return
    async with VOICE_SEMAPHORE:
        await edge_tts.Communicate(text, voice, rate="-12%", pitch="+0Hz", volume="+5%").save(str(path))


async def make_line(scene_index: int, line_index: int, line: str) -> Path:
    child_voice = "en-US-AnaNeural" if scene_index % 2 == 0 else "en-GB-MaisieNeural"
    voice = child_voice if line_index == 0 else "en-GB-RyanNeural"
    if scene_index == 7 and line_index == 1:
        voice = "en-GB-MaisieNeural"
    chunks = four_chunks(line)
    raws = [WORK / f"sung-v4-raw-{scene_index+1:02d}-{line_index+1:02d}-{i+1:02d}.mp3" for i in range(4)]
    await asyncio.gather(*(raw_chunk(text, path, voice) for text, path in zip(chunks, raws)))
    notes = MELODIES[scene_index][line_index]
    shaped: list[Path] = []
    for index, (raw, semitones, target) in enumerate(zip(raws, notes, CHUNK_DURATIONS)):
        part = WORK / f"sung-v4-note-{scene_index+1:02d}-{line_index+1:02d}-{index+1:02d}.wav"
        source_length = media_duration(raw)
        tempo = max(.12, min(8.0, source_length / target))
        pitch = 2 ** (semitones / 12)
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
            "-af", f"silenceremove=start_periods=1:start_silence=0.015:start_threshold=-48dB,rubberband=tempo={tempo:.7f}:pitch={pitch:.7f}:transients=smooth:detector=soft:smoothing=on:formant=preserved:pitchq=quality,apad=pad_dur={target},atrim=0:{target},afade=t=in:d=0.025,afade=t=out:st={max(.04,target-.08):.3f}:d=0.08,highpass=f=100,lowpass=f=9800",
            "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s16le", str(part),
        ])
        shaped.append(part)
    line_path = WORK / f"sung-v4-line-{scene_index+1:02d}-{line_index+1:02d}.wav"
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for part in shaped:
        args += ["-i", str(part)]
    filters=[]; labels=[]
    for i,start in enumerate(CHUNK_STARTS):
        delay=round(start*1000); filters.append(f"[{i}:a]adelay={delay}|{delay}[n{i}]"); labels.append(f"[n{i}]")
    filters.append("".join(labels)+"amix=inputs=4:duration=longest:normalize=0,atrim=0:4.05,acompressor=threshold=-18dB:ratio=2.3:attack=8:release=110[out]")
    args += ["-filter_complex",";".join(filters),"-map","[out]","-ar",str(RATE),"-ac","2","-c:a","pcm_s16le",str(line_path)]
    run(args)
    return line_path


async def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    plan=json.loads(PLAN.read_text(encoding="utf-8"))
    line_tasks=[]
    for si,scene in enumerate(plan["scenes"]):
        for li,line in enumerate(scene["lyrics"]):
            line_tasks.append((si,li,asyncio.create_task(make_line(si,li,line))))
    lines=[(si,li,await task) for si,li,task in line_tasks]
    music=arrangement.music()
    args=["ffmpeg","-y","-loglevel","error","-i",str(music)]
    for _,_,path in lines: args += ["-i",str(path)]
    filters=["[0:a]volume=.68[m]"]; labels=["[m]"]
    for input_index,(si,li,_) in enumerate(lines,1):
        start=si*SCENE+LINE_STARTS[li]; delay=round(start*1000); label=f"v{input_index}"
        filters.append(f"[{input_index}:a]adelay={delay}|{delay},volume=1.18,aecho=.8:.72:55:.045[{label}]"); labels.append(f"[{label}]")
        if si in (0,6,7):
            harmony=f"h{input_index}"
            filters.append(f"[{input_index}:a]rubberband=pitch=1.189207:formant=preserved,adelay={delay+45}|{delay+45},volume=.20[{harmony}]")
            labels.append(f"[{harmony}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:duration=first:normalize=0,atrim=0:{TOTAL},lowpass=f=10500:p=2,loudnorm=I=-16:TP=-1.5:LRA=8[out]")
    args += ["-filter_complex",";".join(filters),"-map","[out]","-ar",str(RATE),"-ac","2","-c:a","pcm_s16le",str(OUTPUT)]
    run(args)
    print(OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
