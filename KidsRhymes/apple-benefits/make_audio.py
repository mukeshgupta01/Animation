from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "audio"
SAMPLE_RATE = 48_000
DURATION = 52.0
BPM = 108
BEAT = 60 / BPM


def midi_hz(note: int) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    total = int(DURATION * SAMPLE_RATE)
    samples = [0.0] * total
    random.seed(7)

    def note(start: float, duration: float, midi: int, volume: float, tone: str) -> None:
        begin = max(0, int(start * SAMPLE_RATE))
        end = min(total, int((start + duration) * SAMPLE_RATE))
        frequency = midi_hz(midi)
        for index in range(begin, end):
            t = (index - begin) / SAMPLE_RATE
            if tone == "bell":
                env = math.exp(-5.5 * t / max(duration, 0.01))
                value = math.sin(math.tau * frequency * t) + 0.28 * math.sin(math.tau * frequency * 2.6 * t)
            elif tone == "pluck":
                env = min(1.0, t / 0.008) * math.exp(-3.7 * t / max(duration, 0.01))
                value = math.sin(math.tau * frequency * t) + 0.18 * math.sin(math.tau * frequency * 2 * t)
            else:
                env = min(1.0, t / 0.02) * math.exp(-2.0 * t / max(duration, 0.01))
                value = math.sin(math.tau * frequency * t)
            samples[index] += volume * env * value

    chords = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]
    melody = [72, 74, 76, 79, 76, 74, 72, 67]
    beat_count = math.ceil(DURATION / BEAT)
    for beat in range(beat_count):
        start = beat * BEAT
        chord = chords[(beat // 4) % len(chords)]
        if beat % 2 == 0:
            for offset, pitch in enumerate(chord):
                note(start + offset * 0.025, BEAT * 1.7, pitch, 0.026, "pluck")
        note(start, BEAT * 0.7, chord[0] - 12, 0.024, "soft")
        if beat % 2:
            note(start, BEAT * 0.75, melody[(beat // 2) % len(melody)], 0.018, "bell")

        # A soft shaker gives the narration a steady, child-friendly pulse.
        shaker_start = int((start + BEAT / 2) * SAMPLE_RATE)
        for n in range(min(int(0.035 * SAMPLE_RATE), total - shaker_start)):
            env = math.exp(-n / (SAMPLE_RATE * 0.009))
            samples[shaker_start + n] += 0.008 * env * random.uniform(-1.0, 1.0)

    peak = max(max(abs(value) for value in samples), 0.001)
    scale = 0.72 * 32767 / peak
    output = OUT / "apple-music.wav"
    with wave.open(str(output), "wb") as stream:
        stream.setnchannels(2)
        stream.setsampwidth(2)
        stream.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for value in samples:
            sample = int(max(-32767, min(32767, value * scale)))
            frames.extend(struct.pack("<hh", sample, sample))
        stream.writeframes(frames)
    print(output)


if __name__ == "__main__":
    main()

