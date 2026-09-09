"""Create the clear V6 sung arrangement for Dance With Dad.

Complete lyric lines are voiced once, fitted to the four-second phrase grid,
then resynthesized with a musical F0 contour via WORLD.  This preserves the
continuous consonant/spectral envelope that was destroyed by V4's word cuts.
"""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import subprocess

import edge_tts
import numpy as np
import pyworld
import soundfile as sf

import generate_dance_with_dad_chant_song as arrangement


PROJECT = Path(__file__).resolve().parents[2]
ITEM_ID = "dance-with-dad-animal-parade-01"
WORK = PROJECT / "automation" / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
OUTPUT = WORK / "dance-with-dad-clear-song-v6.wav"
RATE = 48000
TOTAL = 100.0
SCENE = 12.0
LINE_STARTS = (0.5, 6.0)
LINE_DURATION = 4.35
MELODIES = (
    (0, 2, 4, 5, 4, 2, 0, 2),
    (4, 4, 2, 0, 2, 4, 2, 0),
    (0, 2, 4, 5, 7, 5, 4, 2),
    (2, 4, 5, 7, 5, 4, 2, 0),
    (0, 4, 7, 4, 7, 5, 4, 2),
    (0, 3, 5, 7, 5, 3, 2, 0),
    (0, 2, 4, 5, 7, 5, 4, 2),
    (0, 2, 4, 5, 4, 5, 7, 7),
)


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


async def make_raw(line: str, path: Path, voice: str) -> None:
    await edge_tts.Communicate(line, voice, rate="-12%", pitch="+0Hz", volume="+4%").save(str(path))


def melodic_resynthesis(source: Path, destination: Path, base_hz: float, melody: tuple[int, ...]) -> None:
    source_duration = duration(source)
    tempo = max(0.5, min(2.0, source_duration / LINE_DURATION))
    fitted = destination.with_name(destination.stem + "-fitted.wav")
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
        "-af", (
            "silenceremove=start_periods=1:start_silence=0.015:start_threshold=-48dB,"
            f"rubberband=tempo={tempo:.8f}:transients=smooth:detector=soft:smoothing=on,"
            f"apad=pad_dur={LINE_DURATION},atrim=0:{LINE_DURATION},highpass=f=90,lowpass=f=10500"
        ),
        "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_f32le", str(fitted),
    ])
    samples, sample_rate = sf.read(fitted, dtype="float64")
    f0, spectral, aperiodicity = pyworld.wav2world(samples, sample_rate, frame_period=5.0)
    frame_times = np.arange(len(f0)) * 0.005
    note_index = np.minimum(len(melody) - 1, (frame_times / (LINE_DURATION / len(melody))).astype(int))
    target = base_hz * np.power(2.0, np.asarray(melody, dtype=np.float64)[note_index] / 12.0)
    # Smooth note boundaries over about 50 ms while consonants remain unvoiced.
    kernel = np.ones(11, dtype=np.float64) / 11.0
    target = np.convolve(np.pad(target, (5, 5), mode="edge"), kernel, mode="valid")
    sung_f0 = np.where(f0 > 0.0, target, 0.0)
    sung = pyworld.synthesize(sung_f0, spectral, aperiodicity, sample_rate, frame_period=5.0)
    sung = sung[: round(LINE_DURATION * sample_rate)]
    sung *= min(1.0, 0.82 / max(1e-9, float(np.max(np.abs(sung)))))
    spoken = samples[: len(sung)].copy()
    spoken *= min(1.0, 0.82 / max(1e-9, float(np.max(np.abs(spoken)))))
    sung = sung * 0.86 + spoken * 0.14
    fade = min(480, len(sung) // 4)
    sung[:fade] *= np.linspace(0.0, 1.0, fade)
    sung[-fade:] *= np.linspace(1.0, 0.0, fade)
    sf.write(destination, sung.astype(np.float32), sample_rate, subtype="FLOAT")


async def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    tasks = []
    entries = []
    for scene_index, scene in enumerate(plan["scenes"]):
        for line_index, line in enumerate(scene["lyrics"]):
            is_child = line_index == 0 or (scene_index == 7 and line_index == 1)
            voice = ("en-US-AnaNeural" if scene_index % 2 == 0 else "en-GB-MaisieNeural") if is_child else "en-GB-RyanNeural"
            raw = WORK / f"clear-v6-raw-{scene_index + 1:02d}-{line_index + 1:02d}.mp3"
            sung = WORK / f"clear-v6-line-{scene_index + 1:02d}-{line_index + 1:02d}.wav"
            tasks.append(make_raw(line, raw, voice))
            entries.append((scene_index, line_index, raw, sung, is_child))
    await asyncio.gather(*tasks)

    for scene_index, line_index, raw, sung, is_child in entries:
        base_hz = 261.63 if is_child else 130.81
        melodic_resynthesis(raw, sung, base_hz, MELODIES[scene_index])

    music_path = arrangement.music()
    music, sample_rate = sf.read(music_path, always_2d=True, dtype="float32")
    mix = music[: round(TOTAL * RATE)] * 0.43
    for scene_index, line_index, _raw, sung_path, _is_child in entries:
        vocal, vocal_rate = sf.read(sung_path, always_2d=True, dtype="float32")
        if vocal_rate != RATE:
            raise RuntimeError("Unexpected vocal sample rate")
        start = round((scene_index * SCENE + LINE_STARTS[line_index]) * RATE)
        end = min(len(mix), start + len(vocal))
        mix[start:end] += vocal[: end - start] * 0.98
    peak = float(np.max(np.abs(mix)))
    if not np.isfinite(mix).all() or peak < 1e-5:
        raise RuntimeError("V6 mix is invalid or silent")
    mix *= min(1.0, 0.89 / peak)
    sf.write(OUTPUT, mix, RATE, subtype="FLOAT")
    print(OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
