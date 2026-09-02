"""Create the fail-safe Dance With Dad rhythmic vocal song.

This uses the project's established Tiny Tales voice pipeline and an original
120 BPM arrangement.  It is intentionally a clear call-and-response chant-song
rather than accepting invalid samples from the experimental music model.
"""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import random
import subprocess
import wave

import edge_tts


PROJECT = Path(__file__).resolve().parents[2]
ITEM_ID = "dance-with-dad-animal-parade-01"
WORK = PROJECT / "automation" / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
OUTPUT = WORK / "dance-with-dad-original-song.wav"
TOTAL = 100.0
SCENE = 12.0
RATE = 48000
BEAT = 0.5


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


async def voices(plan: dict) -> list[tuple[Path, float]]:
    # Bright child lead and warm dad response, alternating as a readable duet.
    profiles = (
        ("en-GB-MaisieNeural", "+15Hz"),
        ("en-GB-RyanNeural", "+5Hz"),
    )
    starts = (0.5, 6.0)
    pitch_steps = (1.0, 1.059463, 1.122462, 1.189207, 1.259921)
    placed: list[tuple[Path, float]] = []
    for si, scene in enumerate(plan["scenes"]):
        for li, line in enumerate(scene["lyrics"]):
            voice, pitch = profiles[li % 2]
            raw = WORK / f"chant-raw-{si+1:02d}-{li+1:02d}.mp3"
            fitted = WORK / f"chant-grid-{si+1:02d}-{li+1:02d}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                await edge_tts.Communicate(line, voice, rate="-3%", pitch=pitch, volume="+4%").save(str(raw))
            if not fitted.exists() or fitted.stat().st_size < 2000 or duration(fitted) < 2.94:
                length = duration(raw)
                target = min(4.35, max(2.95, length))
                ratio = length / target
                note = pitch_steps[(si + li * 2) % len(pitch_steps)]
                run([
                    "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-af", f"atempo={ratio:.7f},rubberband=pitch={note:.7f},vibrato=f=5.2:d=0.035,highpass=f=100,lowpass=f=10500,afade=t=in:d=0.05,afade=t=out:st={target-.12:.3f}:d=0.12",
                    "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s16le", str(fitted),
                ])
            placed.append((fitted, si * SCENE + starts[li]))
    return placed


def music() -> Path:
    path = WORK / "dance-with-dad-instrumental.wav"
    rng = random.Random(260902)
    # D-major family-song palette, with a clear four-beat pulse and a brighter
    # lift in the parade/finale.
    chords = (
        (146.83, 185.00, 220.00), (196.00, 246.94, 293.66),
        (220.00, 277.18, 329.63), (164.81, 207.65, 246.94),
    )
    melody = (293.66, 329.63, 369.99, 440.00, 369.99, 329.63, 293.66, 246.94)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(RATE)
        buf = bytearray()
        for n in range(round(TOTAL * RATE)):
            t = n / RATE
            beat_phase = t % BEAT
            bar = int(t / (BEAT * 4))
            chord = chords[bar % 4]
            note = melody[int(t / BEAT) % len(melody)]
            # Rounded marimba/ukulele-like plucks, bass, kick, clap and shaker.
            pluck = (math.sin(math.tau * note * t) + .28 * math.sin(math.tau * note * 2 * t)) * math.exp(-7.0 * beat_phase) * .026
            harmony = sum(math.sin(math.tau * f * t) for f in chord) * .0048
            bass_phase = t % (BEAT * 2)
            bass = math.sin(math.tau * chord[0] / 2 * t) * math.exp(-3.8 * bass_phase) * .022
            kick = math.sin(math.tau * (74 - 28 * min(.12, beat_phase)) * beat_phase) * math.exp(-30 * beat_phase) * .055
            half = t % (BEAT / 2)
            shaker = rng.uniform(-1, 1) * math.exp(-62 * half) * .008
            clap_age = (t - BEAT) % (BEAT * 2)
            clap = rng.uniform(-1, 1) * math.exp(-38 * clap_age) * .018 if clap_age < .16 else 0.0
            lift = 1.14 if t >= 72 else 1.0
            fade = min(1.0, t / .25, (TOTAL - t) / .65)
            value = (pluck + harmony + bass + kick + shaker + clap) * lift * max(0.0, fade)
            sample = int(max(-1, min(1, value)) * 30000)
            buf.extend(sample.to_bytes(2, "little", signed=True) * 2)
            if len(buf) >= RATE * 4:
                out.writeframesraw(buf); buf.clear()
        if buf: out.writeframesraw(buf)
    return path


async def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    vocal_parts = await voices(plan)
    instrumental = music()
    args = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(instrumental)]
    for path, _ in vocal_parts:
        args += ["-i", str(path)]
    chains = ["[0:a]volume=.82[m]"]
    labels = ["[m]"]
    for i, (_, start) in enumerate(vocal_parts, 1):
        delay = round(start * 1000)
        label = f"v{i}"
        chains.append(f"[{i}:a]adelay={delay}|{delay},volume=1.22[{label}]")
        labels.append(f"[{label}]")
    chains.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0,atrim=0:{TOTAL},lowpass=f=10800:p=2,loudnorm=I=-16:TP=-1.5:LRA=8[out]")
    args += ["-filter_complex", ";".join(chains), "-map", "[out]", "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s16le", str(OUTPUT)]
    run(args)
    print(OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
