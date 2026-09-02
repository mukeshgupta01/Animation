"""Create the natural-voice V3 Dance With Dad performance.

The previous take pitch-shifted and vibrated speech, which sounded like awkward
narration. V3 keeps the voices natural, uses distinct child/dad performers and
lets a more varied original 120 BPM arrangement provide the musical character.
"""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import random
import re
import subprocess
import wave

import edge_tts


PROJECT = Path(__file__).resolve().parents[2]
ITEM_ID = "dance-with-dad-animal-parade-01"
WORK = PROJECT / "automation" / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
OUTPUT = WORK / "dance-with-dad-natural-song-v3.wav"
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


async def voices(plan: dict) -> list[tuple[Path, float, float]]:
    starts = (0.45, 6.0)
    children = ("en-US-AnaNeural", "en-GB-MaisieNeural")
    placed: list[tuple[Path, float, float]] = []
    for si, scene in enumerate(plan["scenes"]):
        for li, line in enumerate(scene["lyrics"]):
            voice = children[si % 2] if li == 0 else "en-GB-RyanNeural"
            rate = "-7%" if li == 0 else "-10%"
            slug = voice.split("-")[-1].replace("Neural", "").lower()
            raw = WORK / f"natural-v3-raw-{si+1:02d}-{li+1:02d}-{slug}.mp3"
            fitted = WORK / f"natural-v3-{si+1:02d}-{li+1:02d}-{slug}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                await edge_tts.Communicate(line, voice, rate=rate, pitch="+0Hz", volume="+2%").save(str(raw))
            if not fitted.exists() or fitted.stat().st_size < 2000:
                length = duration(raw)
                minimum = len(re.findall(r"[A-Za-z0-9']+", line)) * 60 / 135
                target = min(4.35, max(length, minimum))
                timing = f"atempo={length/target:.7f}," if abs(length-target) > .02 else ""
                run([
                    "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-af", f"{timing}highpass=f=95,lowpass=f=9800,acompressor=threshold=-18dB:ratio=2.2:attack=12:release=120,afade=t=in:d=0.04",
                    "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s16le", str(fitted),
                ])
            placed.append((fitted, si * SCENE + starts[li], 1.18 if li == 0 else 1.10))

            # The three chorus/finale scenes gain a quiet second child voice.
            # It is naturally spoken, not pitch-warped, and enters 55 ms later
            # to read as a small group rather than an electronic effect.
            if si in (0, 6, 7):
                group_voice = children[(si + 1) % 2]
                group_slug = group_voice.split("-")[-1].replace("Neural", "").lower()
                group_raw = WORK / f"natural-v3-group-raw-{si+1:02d}-{li+1:02d}-{group_slug}.mp3"
                group_wav = WORK / f"natural-v3-group-{si+1:02d}-{li+1:02d}-{group_slug}.wav"
                if not group_raw.exists() or group_raw.stat().st_size < 1000:
                    await edge_tts.Communicate(line, group_voice, rate="-8%", pitch="+0Hz", volume="-2%").save(str(group_raw))
                if not group_wav.exists() or group_wav.stat().st_size < 2000:
                    run(["ffmpeg","-y","-loglevel","error","-i",str(group_raw),"-af","highpass=f=100,lowpass=f=9500,acompressor=threshold=-20dB:ratio=2:attack=12:release=120,afade=t=in:d=0.04","-ar",str(RATE),"-ac","2","-c:a","pcm_s16le",str(group_wav)])
                placed.append((group_wav, si * SCENE + starts[li] + 0.055, .34))
    return placed


def music() -> Path:
    path = WORK / "dance-with-dad-instrumental-v3.wav"
    rng = random.Random(260903)
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
            scene = min(7, int(t // SCENE))
            local = t - scene * SCENE
            note = melody[(int(t / BEAT) + scene) % len(melody)]
            # Rounded marimba/ukulele-like plucks, bass, kick, clap and shaker.
            pluck = (math.sin(math.tau * note * t) + .22 * math.sin(math.tau * note * 2 * t)) * math.exp(-7.0 * beat_phase) * (.020 + .002*scene)
            harmony = sum(math.sin(math.tau * f * t) for f in chord) * (.0038 if scene < 6 else .0060)
            bass_phase = t % (BEAT * 2)
            bass = math.sin(math.tau * chord[0] / 2 * t) * math.exp(-3.8 * bass_phase) * .022
            kick = math.sin(math.tau * (74 - 28 * min(.12, beat_phase)) * beat_phase) * math.exp(-30 * beat_phase) * .055
            half = t % (BEAT / 2)
            shaker = rng.uniform(-1, 1) * math.exp(-72 * half) * .004
            clap_age = (t - BEAT) % (BEAT * 2)
            clap = rng.uniform(-1, 1) * math.exp(-38 * clap_age) * .018 if clap_age < .16 else 0.0
            # Each animal gets a recognizable instrumental hook.
            hook_age = local % 4.0
            hook = 0.0
            if scene == 1 and hook_age < .30:  # elephant: low stomp answer
                hook = math.sin(math.tau*98*t)*math.exp(-13*hook_age)*.035
            elif scene == 2 and hook_age < .45:  # penguin: sparkling slide
                hook = math.sin(math.tau*(660+340*hook_age)*t)*math.exp(-8*hook_age)*.017
            elif scene == 3 and hook_age < .35:  # fox: quick syncopated turn
                hook = math.sin(math.tau*523.25*t)*math.exp(-10*hook_age)*.020
            elif scene == 4 and hook_age < .34:  # kangaroo: paired bounce
                hook = (math.sin(math.tau*146.83*t)+.5*math.sin(math.tau*293.66*t))*math.exp(-11*hook_age)*.024
            elif scene == 5 and hook_age < .40:  # lion: drum-and-brass answer
                hook = (math.sin(math.tau*196*t)+.25*math.sin(math.tau*392*t))*math.exp(-8*hook_age)*.030
            elif scene >= 6 and hook_age < .40:  # full parade lift
                hook = sum(math.sin(math.tau*f*t) for f in (293.66,369.99,440.0))*math.exp(-7*hook_age)*.012
            lift = 1.18 if t >= 72 else 1.0
            fade = min(1.0, t / .25, (TOTAL - t) / .65)
            value = (pluck + harmony + bass + kick + shaker + clap + hook) * lift * max(0.0, fade)
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
    for path, _, _ in vocal_parts:
        args += ["-i", str(path)]
    chains = ["[0:a]volume=.72[m]"]
    labels = ["[m]"]
    for i, (_, start, gain) in enumerate(vocal_parts, 1):
        delay = round(start * 1000)
        label = f"v{i}"
        chains.append(f"[{i}:a]adelay={delay}|{delay},volume={gain:.3f}[{label}]")
        labels.append(f"[{label}]")
    chains.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0,atrim=0:{TOTAL},lowpass=f=10800:p=2,loudnorm=I=-16:TP=-1.5:LRA=8[out]")
    args += ["-filter_complex", ";".join(chains), "-map", "[out]", "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s16le", str(OUTPUT)]
    run(args)
    print(OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
