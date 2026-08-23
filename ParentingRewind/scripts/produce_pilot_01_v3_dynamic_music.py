"""Render pilot 01 with a locally composed, narration-aware musical arc.

V3 reuses the V2 narration and original storyboard. It does not call an image
or speech generation service. The score is synthesized locally with Python.
"""

from array import array
import math
from pathlib import Path
import shutil
import wave

import produce_pilot_01_v2 as conversational


base = conversational.base
V2_WORK = base.PROJECT / "production-work" / "pilot-01-shoes-v2-conversational"
base.WORK = base.PROJECT / "production-work" / "pilot-01-shoes-v3-dynamic-music"
base.OUTPUT = base.PROJECT / "output" / "parenting-rewind-pilot-01-shoes-v3-dynamic-music.mp4"

SAMPLE_RATE = 48_000


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def envelope(local_time: float, duration: float, attack: float = 0.55, release: float = 0.75) -> float:
    return smoothstep(local_time / attack) * smoothstep((duration - local_time) / release)


def tone(frequency: float, time_value: float, warmth: float = 0.18) -> float:
    fundamental = math.sin(2.0 * math.pi * frequency * time_value)
    harmonic = math.sin(2.0 * math.pi * frequency * 2.0 * time_value)
    return fundamental + warmth * harmonic


def chord(frequencies: tuple[float, ...], time_value: float, local_time: float, duration: float) -> float:
    shimmer = 0.84 + 0.16 * math.sin(2.0 * math.pi * 0.13 * time_value)
    body = sum(tone(frequency, time_value) for frequency in frequencies) / len(frequencies)
    return body * shimmer * envelope(local_time, duration)


def pulse(time_value: float, bpm: float) -> float:
    beat = (time_value * bpm / 60.0) % 1.0
    return math.exp(-7.0 * beat)


def arpeggio(
    frequencies: tuple[float, ...],
    time_value: float,
    local_time: float,
    duration: float,
    bpm: float,
) -> tuple[float, float]:
    beat_position = time_value * bpm / 60.0
    note_index = int(beat_position) % len(frequencies)
    note_phase = beat_position % 1.0
    note_envelope = math.sin(math.pi * note_phase) ** 2
    note = tone(frequencies[note_index], time_value, warmth=0.10) * note_envelope
    pan = -0.22 if note_index % 2 == 0 else 0.22
    master = note * envelope(local_time, duration, attack=0.35, release=0.75)
    return master * (1.0 - pan), master * (1.0 + pan)


def profile_sample(kind: str, time_value: float, local_time: float, duration: float) -> tuple[float, float]:
    if kind == "hook":
        # Light urgency: A minor pulse, present but not alarming.
        bed = chord((220.00, 261.63, 329.63), time_value, local_time, duration)
        beat = tone(110.00, time_value, warmth=0.08) * pulse(time_value, 92.0)
        return 0.040 * bed + 0.030 * beat, 0.039 * bed + 0.028 * beat

    if kind == "wrong":
        # Frustration: darker D-minor harmony and a quicker low pulse.
        bed = chord((146.83, 174.61, 220.00), time_value, local_time, duration)
        beat = tone(73.42, time_value, warmth=0.12) * pulse(time_value, 112.0)
        tension = tone(233.08, time_value, warmth=0.06) * (0.45 + 0.55 * pulse(time_value + 0.22, 56.0))
        signal = 0.046 * bed + 0.040 * beat + 0.010 * tension
        return signal * 1.02, signal * 0.98

    if kind == "pause":
        # Space to breathe: thinner suspended harmony and long gaps.
        breath = 0.5 + 0.5 * math.sin(2.0 * math.pi * 0.10 * time_value - math.pi / 2.0)
        bed = chord((196.00, 261.63, 293.66), time_value, local_time, duration)
        signal = 0.030 * bed * (0.45 + 0.55 * breath)
        return signal, signal

    if kind == "rewind":
        # A clearly musical rising transition rather than a sound effect.
        progress = max(0.0, min(1.0, local_time / max(0.01, duration)))
        start_frequency, end_frequency = 196.00, 587.33
        sweep_rate = (end_frequency - start_frequency) / max(0.01, duration)
        phase = 2.0 * math.pi * (
            start_frequency * local_time + 0.5 * sweep_rate * local_time * local_time
        )
        swell = math.sin(phase) * (0.20 + 0.80 * smoothstep(progress))
        bed = chord((196.00, 246.94, 329.63), time_value, local_time, duration)
        signal = (0.032 * bed + 0.040 * swell) * envelope(local_time, duration, 0.25, 0.50)
        return signal * 0.92, signal * 1.08

    if kind == "better":
        # Calm clarity: warm C-major bed with a soft, moving arpeggio.
        bed = chord((261.63, 329.63, 392.00), time_value, local_time, duration)
        left_note, right_note = arpeggio(
            (261.63, 329.63, 392.00, 329.63), time_value, local_time, duration, 76.0
        )
        return 0.038 * bed + 0.030 * left_note, 0.038 * bed + 0.030 * right_note

    # Resolution: an open C-major chord with a gentle high-note cadence.
    bed = chord((261.63, 329.63, 392.00, 523.25), time_value, local_time, duration)
    left_note, right_note = arpeggio(
        (261.63, 329.63, 392.00, 523.25), time_value, local_time, duration, 68.0
    )
    cadence_position = local_time % 3.2
    cadence_envelope = math.exp(-2.8 * cadence_position)
    cadence = tone(783.99, time_value, warmth=0.05) * cadence_envelope
    return (
        0.044 * bed + 0.027 * left_note + 0.012 * cadence,
        0.044 * bed + 0.027 * right_note + 0.014 * cadence,
    )


def make_dynamic_music(total: float) -> Path:
    target = base.WORK / "original-dynamic-emotional-score.wav"
    if target.exists() and base.media_duration(target) >= total - 0.1:
        return target

    events, _ = base.make_timeline()
    sample_count = math.ceil(total * SAMPLE_RATE)
    pcm = array("h")
    event_index = 0
    crossfade_seconds = 0.65

    for sample_index in range(sample_count):
        current_time = sample_index / SAMPLE_RATE
        while event_index + 1 < len(events) and current_time >= events[event_index]["end"]:
            event_index += 1
        event = events[event_index]
        local_time = max(0.0, current_time - event["start"])
        duration = event["end"] - event["start"]
        kind = event["kind"]
        left, right = profile_sample(kind, current_time, local_time, duration)

        # Crossfade the emotional palette at scene boundaries.
        if event_index > 0 and local_time < crossfade_seconds:
            previous = events[event_index - 1]
            previous_duration = previous["end"] - previous["start"]
            previous_local = previous_duration - crossfade_seconds + local_time
            previous_left, previous_right = profile_sample(
                previous["kind"], current_time, previous_local, previous_duration
            )
            blend = smoothstep(local_time / crossfade_seconds)
            left = previous_left * (1.0 - blend) + left * blend
            right = previous_right * (1.0 - blend) + right * blend

        master_fade = smoothstep(current_time / 1.25) * smoothstep((total - current_time) / 2.0)
        left = max(-0.95, min(0.95, left * master_fade))
        right = max(-0.95, min(0.95, right * master_fade))
        pcm.append(round(left * 32767))
        pcm.append(round(right * 32767))

    base.WORK.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())
    return target


def reuse_v2_narration() -> None:
    base.WORK.mkdir(parents=True, exist_ok=True)
    for segment in base.SEGMENTS:
        source = V2_WORK / f"voice-{segment['key']}.mp3"
        destination = base.WORK / source.name
        if not source.exists():
            raise FileNotFoundError(f"Render V2 first so its narration can be reused: {source}")
        if not destination.exists():
            shutil.copy2(source, destination)


base.make_music = make_dynamic_music


if __name__ == "__main__":
    reuse_v2_narration()
    base.main()
