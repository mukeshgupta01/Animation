"""Create the reusable original Parenting Rewind instrumental bed locally."""

from __future__ import annotations

from array import array
import math
from pathlib import Path
import wave


PROJECT = Path(__file__).resolve().parents[1]
TARGET = PROJECT / "production-work" / "pilot-02-screen-time-v1" / "original-dynamic-emotional-score.wav"
SAMPLE_RATE = 48_000
DURATION = 72.0


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def oscillator(frequency: float, t: float) -> float:
    return math.sin(2 * math.pi * frequency * t) + 0.16 * math.sin(4 * math.pi * frequency * t)


def main() -> None:
    if TARGET.exists():
        print(f"Preserved existing score: {TARGET}")
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    progression = [
        (196.00, 246.94, 293.66),
        (220.00, 261.63, 329.63),
        (174.61, 220.00, 261.63),
        (261.63, 329.63, 392.00),
    ]
    pcm = array("h")
    samples = int(DURATION * SAMPLE_RATE)
    for index in range(samples):
        t = index / SAMPLE_RATE
        chord_index = int(t / 6.0) % len(progression)
        chord = progression[chord_index]
        body = sum(oscillator(frequency, t) for frequency in chord) / len(chord)
        beat_position = (t * 72.0 / 60.0) % 1.0
        pulse = math.exp(-8.0 * beat_position) * oscillator(chord[0] / 2, t)
        shimmer = 0.85 + 0.15 * math.sin(2 * math.pi * 0.11 * t)
        fade = smoothstep(t / 1.5) * smoothstep((DURATION - t) / 2.5)
        left = (0.045 * body * shimmer + 0.016 * pulse) * fade
        right = (0.043 * body * (2.0 - shimmer) + 0.014 * pulse) * fade
        pcm.extend((round(max(-0.9, min(0.9, left)) * 32767), round(max(-0.9, min(0.9, right)) * 32767)))
    with wave.open(str(TARGET), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())
    print(f"Created original score: {TARGET}")


if __name__ == "__main__":
    main()
