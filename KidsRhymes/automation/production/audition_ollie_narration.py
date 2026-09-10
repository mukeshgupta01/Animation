"""Create equal-text, line-separated Edge TTS auditions for the Ollie rhyme."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import subprocess
import wave

import edge_tts


PROJECT = Path(__file__).resolve().parents[2]
WORK = PROJECT / "automation" / "production-work" / "ollie-otter-floating-picnic-01-narration-revision"
AUDITIONS = WORK / "auditions"

LINES = (
    "Left and right, then find the middle,",
    "Slow and steady, just a little.",
    "Sit down low and help it glide,",
    "Balance, balance, side to side!",
    "Fern sees ducks and waves hello.",
    "One side dips—so soft and slow.",
)

VOICES = {
    "ana-us": {"voice": "en-US-AnaNeural", "rate": "-7%", "pitch": "+4Hz"},
    "maisie-uk": {"voice": "en-GB-MaisieNeural", "rate": "-7%", "pitch": "+2Hz"},
    "natasha-au": {"voice": "en-AU-NatashaNeural", "rate": "-7%", "pitch": "+2Hz"},
    "ryan-uk": {"voice": "en-GB-RyanNeural", "rate": "-7%", "pitch": "+1Hz"},
}


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def join_wavs(parts: list[Path], target: Path) -> None:
    silence_after = (0.42, 0.42, 0.42, 0.72, 0.42, 0.0)
    with wave.open(str(target), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(48000)
        for part, pause in zip(parts, silence_after):
            with wave.open(str(part), "rb") as source:
                if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (2, 2, 48000):
                    raise RuntimeError(f"Unexpected WAV format: {part}")
                output.writeframes(source.readframes(source.getnframes()))
            output.writeframes(b"\x00" * round(pause * 48000) * 4)


async def make() -> None:
    AUDITIONS.mkdir(parents=True, exist_ok=True)
    report = {"representative_text": list(LINES), "voices": {}}
    for key, profile in VOICES.items():
        parts: list[Path] = []
        for index, line in enumerate(LINES, 1):
            raw = AUDITIONS / f"{key}-line-{index:02d}.mp3"
            wav = AUDITIONS / f"{key}-line-{index:02d}.wav"
            if not raw.exists():
                await edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"],
                    pitch=profile["pitch"], volume="-1%",
                ).save(str(raw))
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                "-af", "highpass=f=90,lowpass=f=10500",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav),
            ], check=True)
            parts.append(wav)
        combined = AUDITIONS / f"ollie-audition-{key}.wav"
        join_wavs(parts, combined)
        report["voices"][key] = {
            **profile,
            "duration_seconds": duration(combined),
            "file": str(combined.relative_to(PROJECT).as_posix()),
            "segmentation": "six individual rhyme lines",
        }
    (AUDITIONS / "audition-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(make())
