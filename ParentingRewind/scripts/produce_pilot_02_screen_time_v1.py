"""Create Parenting Rewind pilot 02: ending screen time without shouting.

This producer is intentionally local-only. It creates new versioned files and
does not know about YouTube, OAuth, upload automation, or Scheduled Tasks.
"""

from __future__ import annotations

from array import array
import asyncio
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import wave

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


PROJECT = Path(__file__).resolve().parents[1]
ASSET = PROJECT / "production-assets" / "screen-time-storyboard-01.png"
WORK = PROJECT / "production-work" / "pilot-02-screen-time-v1"
OUTPUT = PROJECT / "output" / "parenting-rewind-pilot-02-screen-time-v1.mp4"

W, H = 1080, 1920
ART_FPS, VIDEO_FPS = 6, 30
SAMPLE_RATE = 48_000

VOICE = "en-US-AvaMultilingualNeural"
VOICE_RATE = "-5%"
VOICE_PITCH = "-1Hz"

FONT_REGULAR = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_SEMIBOLD = Path("C:/Windows/Fonts/seguisb.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")


SEGMENTS = [
    {
        "key": "hook",
        "panel": 0,
        "kind": "hook",
        "headline": "WHEN SCREEN TIME ENDS",
        "voice": (
            "Does ending screen time ever make everyone louder, including you? "
            "Your child asks for one more video, you say no, and suddenly a simple limit feels like a shouting match."
        ),
        "minimum": 8.5,
    },
    {
        "key": "wrong",
        "panel": 1,
        "kind": "wrong",
        "headline": "WE'VE ALL BEEN THERE",
        "voice": (
            "It is easy to snap, I said turn it off! Why can't you listen? "
            "You are holding a reasonable limit, but the volume can turn it into a fight."
        ),
        "minimum": 8.0,
    },
    {
        "key": "pause",
        "panel": 2,
        "kind": "pause",
        "headline": "TAKE ONE BREATH",
        "voice": (
            "Before you grab the device or start explaining, pause for one breath. "
            "The screen still goes off. We are changing how you help the transition."
        ),
        "minimum": 7.5,
    },
    {
        "key": "rewind",
        "panel": 3,
        "kind": "rewind",
        "headline": "OKAY—LET'S REWIND",
        "voice": (
            "Okay, rewind two minutes. Say, two minutes left. When the timer rings, "
            "the tablet goes on the counter. Then we are getting ready for dinner."
        ),
        "minimum": 8.0,
    },
    {
        "key": "better",
        "panel": 3,
        "kind": "better",
        "headline": "KEEP IT SHORT",
        "voice": (
            "When it rings, keep it short. Screen time is finished. "
            "You can switch it off, or I can help."
        ),
        "minimum": 6.5,
    },
    {
        "key": "empathy",
        "panel": 4,
        "kind": "empathy",
        "headline": "WHEN THEY ASK FOR MORE",
        "voice": (
            "If they say, one more, try this. You really want to keep watching. "
            "Stopping is hard. The answer is still no."
        ),
        "minimum": 7.0,
    },
    {
        "key": "hold",
        "panel": 4,
        "kind": "hold",
        "headline": "HOLD THE LIMIT",
        "voice": (
            "If they yell, use fewer words, not a bigger voice. "
            "I am here. I won't argue. The tablet is going away, and you can be upset. Then follow through."
        ),
        "minimum": 8.0,
    },
    {
        "key": "takeaway",
        "panel": 5,
        "kind": "takeaway",
        "headline": "THE TAKEAWAY",
        "voice": (
            "The goal is not a child who never protests. It is a predictable ending: warn, acknowledge, "
            "hold the boundary, and move to what comes next. Calm does not mean giving in."
        ),
        "minimum": 8.5,
    },
]

# Captions are intentionally verbatim, not summaries.
for _segment in SEGMENTS:
    _segment["caption"] = _segment["voice"]


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def media_duration(path: Path) -> float:
    value = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    )
    return float(value.strip())


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    path = {"regular": FONT_REGULAR, "semibold": FONT_SEMIBOLD, "bold": FONT_BOLD}[weight]
    return ImageFont.truetype(str(path), size)


async def make_voices() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    for segment in SEGMENTS:
        target = WORK / f"voice-{segment['key']}.mp3"
        metadata = WORK / f"voice-{segment['key']}-boundaries.jsonl"
        if target.exists() and metadata.exists():
            continue
        if target.exists() != metadata.exists():
            raise RuntimeError(
                f"Incomplete narration pair; preserve it and resolve manually: {target}, {metadata}"
            )
        communicate = edge_tts.Communicate(
            segment["voice"],
            VOICE,
            rate=VOICE_RATE,
            pitch=VOICE_PITCH,
            volume="-1%",
        )
        await communicate.save(str(target), str(metadata))


def make_timeline() -> tuple[list[dict], float]:
    cursor = 0.35
    events: list[dict] = []
    for segment in SEGMENTS:
        voice = WORK / f"voice-{segment['key']}.mp3"
        voice_length = media_duration(voice)
        length = max(segment["minimum"], voice_length + 1.10)
        event = dict(segment)
        event["start"] = cursor
        event["voice_start"] = cursor + 0.38
        event["voice_duration"] = voice_length
        event["end"] = cursor + length
        events.append(event)
        cursor = event["end"]
    total = math.ceil((cursor + 0.55) * ART_FPS) / ART_FPS
    return events, total


def split_storyboard() -> list[Image.Image]:
    source = Image.open(ASSET).convert("RGB")
    panels: list[Image.Image] = []
    margin = 5
    for row in range(2):
        for col in range(3):
            x1 = round(col * source.width / 3) + margin
            x2 = round((col + 1) * source.width / 3) - margin
            y1 = round(row * source.height / 2) + margin
            y2 = round((row + 1) * source.height / 2) - margin
            panel = source.crop((x1, y1, x2, y2))
            if panel.width < 250 or panel.height < 600:
                raise RuntimeError(f"Unexpected storyboard panel dimensions: {panel.size}")
            panels.append(panel)
    if len(panels) != 6:
        raise RuntimeError("Expected exactly six storyboard panels")
    return panels


def cover_background(image: Image.Image, progress: float, panel_index: int) -> Image.Image:
    zoom = 1.05 + 0.035 * progress
    scale = max(W / image.width, H / image.height) * zoom
    resized = image.resize(
        (math.ceil(image.width * scale), math.ceil(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    max_x = max(0, resized.width - W)
    max_y = max(0, resized.height - H)
    direction = -1 if panel_index % 2 else 1
    x = int(max_x * (0.5 + direction * 0.06 * (progress - 0.5)))
    y = int(max_y * (0.48 + 0.05 * (progress - 0.5)))
    x = max(0, min(max_x, x))
    y = max(0, min(max_y, y))
    background = resized.crop((x, y, x + W, y + H))
    background = background.filter(ImageFilter.GaussianBlur(28))
    background = ImageEnhance.Brightness(background).enhance(0.52)
    background = ImageEnhance.Color(background).enhance(0.72)
    return background


def compose_panel(image: Image.Image, progress: float, panel_index: int) -> Image.Image:
    """Preserve the tall source panel over a cinematic blurred full-frame fill."""
    background = cover_background(image, progress, panel_index).convert("RGBA")
    zoom = 1.0 + 0.020 * progress
    scale = min((W * 0.82) / image.width, (H * 1.015) / image.height) * zoom
    foreground = image.resize(
        (math.ceil(image.width * scale), math.ceil(image.height * scale)),
        Image.Resampling.LANCZOS,
    ).convert("RGBA")
    x = (W - foreground.width) // 2
    travel = max(0, foreground.height - H)
    y = -int(travel * progress)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow, "RGBA")
    shadow_draw.rounded_rectangle(
        (x - 18, -20, x + foreground.width + 18, H + 20),
        radius=28,
        fill=(0, 0, 0, 125),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    background = Image.alpha_composite(background, shadow)
    background.alpha_composite(foreground, (x, y))
    return background.convert("RGB")


def add_vertical_gradient(overlay: Image.Image, top: bool, height: int, opacity: int) -> None:
    pixels = Image.new("RGBA", (W, height), (18, 24, 27, 0))
    draw = ImageDraw.Draw(pixels)
    for y in range(height):
        ratio = y / max(1, height - 1)
        alpha = int(opacity * ((1 - ratio) if top else ratio))
        draw.line((0, y, W, y), fill=(18, 24, 27, alpha))
    overlay.alpha_composite(pixels, (0, 0 if top else H - height))


def wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    chosen_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textbbox((0, 0), candidate, font=chosen_font)[2] <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def centered_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    chosen_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    max_width: int = 930,
    spacing: int = 10,
) -> int:
    lines = wrapped_lines(draw, text, chosen_font, max_width)
    line_height = chosen_font.size + spacing
    for line in lines:
        box = draw.textbbox((0, 0), line, font=chosen_font)
        x = (W - (box[2] - box[0])) // 2
        draw.text(
            (x, y),
            line,
            font=chosen_font,
            fill=fill,
            stroke_width=2,
            stroke_fill=(10, 18, 20, 140),
        )
        y += line_height
    return y


def caption_font_and_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    for size in (54, 52, 50, 48, 46, 44, 42, 40):
        chosen = font(size, "semibold")
        spacing = 11
        lines = wrapped_lines(draw, text, chosen, 850)
        height = len(lines) * (size + spacing)
        if height <= 280:
            return chosen, lines, spacing
    raise RuntimeError(f"Caption does not fit safely: {text}")


def draw_verbatim_caption(draw: ImageDraw.ImageDraw, text: str) -> None:
    chosen, lines, spacing = caption_font_and_lines(draw, text)
    line_height = chosen.size + spacing
    total_height = len(lines) * line_height
    y = 1370 + max(0, (265 - total_height) // 2)
    for line in lines:
        box = draw.textbbox((0, 0), line, font=chosen)
        x = (W - (box[2] - box[0])) // 2
        draw.text(
            (x, y),
            line,
            font=chosen,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(8, 15, 18, 180),
        )
        y += line_height


def rewind_symbol(draw: ImageDraw.ImageDraw, phase: float) -> None:
    draw.ellipse(
        (390, 690, 690, 990),
        fill=(22, 40, 48, 180),
        outline=(255, 255, 255, 220),
        width=7,
    )
    start = int(35 + phase * 20)
    draw.arc((435, 735, 645, 945), start=start, end=start + 285, fill="white", width=18)
    draw.polygon([(451, 738), (410, 790), (479, 799)], fill="white")
    label = font(42, "bold")
    box = draw.textbbox((0, 0), "REWIND", font=label)
    draw.text(((W - (box[2] - box[0])) / 2, 1000), "REWIND", font=label, fill="white")


def frame_for(event: dict, absolute_time: float, panels: list[Image.Image], total: float) -> Image.Image:
    duration = event["end"] - event["start"]
    progress = max(0.0, min(1.0, (absolute_time - event["start"]) / max(0.01, duration)))
    frame = compose_panel(panels[event["panel"]], progress, event["panel"])
    frame = ImageEnhance.Color(frame).enhance(0.96)
    if event["kind"] == "wrong":
        frame = Image.blend(frame, Image.new("RGB", frame.size, (104, 28, 22)), 0.10)
    elif event["kind"] in {"better", "empathy", "hold", "takeaway"}:
        frame = Image.blend(frame, Image.new("RGB", frame.size, (25, 81, 65)), 0.055)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    add_vertical_gradient(overlay, top=True, height=500, opacity=225)
    add_vertical_gradient(overlay, top=False, height=700, opacity=242)
    draw = ImageDraw.Draw(overlay, "RGBA")

    accent = {
        "hook": (244, 188, 75, 255),
        "wrong": (244, 111, 96, 255),
        "pause": (244, 188, 75, 255),
        "rewind": (109, 203, 217, 255),
        "better": (112, 214, 169, 255),
        "empathy": (112, 214, 169, 255),
        "hold": (112, 214, 169, 255),
        "takeaway": (255, 222, 133, 255),
    }[event["kind"]]

    draw.rounded_rectangle(
        (54, 54, 390, 116),
        radius=28,
        fill=(19, 35, 39, 205),
        outline=(255, 255, 255, 85),
        width=2,
    )
    draw.text((84, 68), "PARENTING REWIND", font=font(27, "bold"), fill=(255, 255, 255, 245))
    draw.rounded_rectangle((54, 151, 70, 325), radius=8, fill=accent)
    centered_text(draw, 165, event["headline"], font(52, "bold"), accent, spacing=5)

    if event["kind"] == "rewind":
        rewind_symbol(draw, progress)

    active_caption = next(
        (
            cue["text"]
            for cue in event.get("caption_cues", [])
            if cue["start"] <= absolute_time < cue["end"]
        ),
        "",
    )
    if active_caption:
        draw.rounded_rectangle(
            (54, 1295, 1026, 1745),
            radius=42,
            fill=(14, 25, 29, 224),
            outline=(255, 255, 255, 75),
            width=2,
        )
        draw_verbatim_caption(draw, active_caption)

    if event["kind"] == "takeaway":
        disclaimer = "GENERAL PARENTING EDUCATION  •  EVERY CHILD IS DIFFERENT"
        disclaimer_font = font(19, "semibold")
        box = draw.textbbox((0, 0), disclaimer, font=disclaimer_font)
        draw.text(
            ((W - (box[2] - box[0])) / 2, 1780),
            disclaimer,
            font=disclaimer_font,
            fill=(255, 255, 255, 205),
        )

    bar_width = int((W - 108) * absolute_time / total)
    draw.rounded_rectangle((54, 1875, 1026, 1889), radius=7, fill=(255, 255, 255, 70))
    if bar_width > 0:
        draw.rounded_rectangle((54, 1875, 54 + bar_width, 1889), radius=7, fill=accent)
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


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
        bed = chord((220.00, 261.63, 329.63), time_value, local_time, duration)
        beat = tone(110.00, time_value, warmth=0.08) * pulse(time_value, 92.0)
        return 0.040 * bed + 0.030 * beat, 0.039 * bed + 0.028 * beat

    if kind == "wrong":
        bed = chord((146.83, 174.61, 220.00), time_value, local_time, duration)
        beat = tone(73.42, time_value, warmth=0.12) * pulse(time_value, 112.0)
        tension = tone(233.08, time_value, warmth=0.06) * (
            0.45 + 0.55 * pulse(time_value + 0.22, 56.0)
        )
        signal = 0.046 * bed + 0.040 * beat + 0.010 * tension
        return signal * 1.02, signal * 0.98

    if kind == "pause":
        breath = 0.5 + 0.5 * math.sin(2.0 * math.pi * 0.10 * time_value - math.pi / 2.0)
        bed = chord((196.00, 261.63, 293.66), time_value, local_time, duration)
        signal = 0.030 * bed * (0.45 + 0.55 * breath)
        return signal, signal

    if kind == "rewind":
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

    if kind in {"better", "empathy"}:
        bed = chord((261.63, 329.63, 392.00), time_value, local_time, duration)
        left_note, right_note = arpeggio(
            (261.63, 329.63, 392.00, 329.63), time_value, local_time, duration, 76.0
        )
        level = 0.034 if kind == "empathy" else 0.038
        return level * bed + 0.028 * left_note, level * bed + 0.028 * right_note

    if kind == "hold":
        bed = chord((174.61, 220.00, 261.63), time_value, local_time, duration)
        grounding = tone(87.31, time_value, warmth=0.06) * pulse(time_value, 64.0)
        signal = 0.037 * bed + 0.018 * grounding
        return signal, signal

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


def make_dynamic_music(events: list[dict], total: float) -> Path:
    target = WORK / "original-dynamic-emotional-score.wav"
    if target.exists() and media_duration(target) >= total - 0.1:
        return target

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
        left, right = profile_sample(event["kind"], current_time, local_time, duration)

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

    with wave.open(str(target), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())
    return target


def render_video(events: list[dict], total: float, panels: list[Image.Image]) -> None:
    silent = WORK / "silent-vertical.mp4"
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{W}x{H}",
            "-r",
            str(ART_FPS),
            "-i",
            "-",
            "-an",
            "-vf",
            f"fps={VIDEO_FPS}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(silent),
        ],
        stdin=subprocess.PIPE,
    )
    assert process.stdin is not None
    for number in range(math.ceil(total * ART_FPS)):
        current = number / ART_FPS
        event = next((item for item in events if item["start"] <= current < item["end"]), events[-1])
        process.stdin.write(frame_for(event, current, panels, total).tobytes())
        if number % (ART_FPS * 10) == 0:
            print(f"Rendered {current:.0f}/{total:.0f} seconds", flush=True)
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("Silent video rendering failed")

    music = make_dynamic_music(events, total)
    inputs = ["-i", str(silent), "-i", str(music)]
    filters: list[str] = []
    voice_labels: list[str] = []

    for input_index, event in enumerate(events, start=2):
        voice = WORK / f"voice-{event['key']}.mp3"
        inputs.extend(["-i", str(voice)])
        delay = round(event["voice_start"] * 1000)
        filters.append(
            f"[{input_index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"adelay={delay}|{delay},volume=1.18[v{input_index}]"
        )
        voice_labels.append(f"[v{input_index}]")

    filters.append(
        "".join(voice_labels)
        + f"amix=inputs={len(voice_labels)}:normalize=0:dropout_transition=0,"
        + "alimiter=limit=.93[voice_mix]"
    )
    filters.append("[voice_mix]asplit=2[voice_sidechain][voice_final]")
    filters.append(
        "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
        "volume=3.0,alimiter=limit=.90[music_full]"
    )
    filters.append(
        "[music_full][voice_sidechain]sidechaincompress="
        "threshold=.025:ratio=3.2:attack=18:release=320[music_ducked]"
    )
    filters.append(
        "[music_ducked][voice_final]amix=inputs=2:normalize=0:dropout_transition=0,"
        "alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=9[a]"
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-t",
            f"{total:.3f}",
            "-movflags",
            "+faststart",
            str(OUTPUT),
        ]
    )


def srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def word_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def build_caption_cues(events: list[dict]) -> list[dict]:
    all_cues: list[dict] = []
    for event in events:
        metadata = WORK / f"voice-{event['key']}-boundaries.jsonl"
        boundaries = [
            json.loads(line)
            for line in metadata.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        sentences = [item for item in boundaries if item.get("type") == "SentenceBoundary"]
        words = [item for item in boundaries if item.get("type") == "WordBoundary"]

        groups: list[list[dict]] = []
        if sentences:
            # Sentence boundaries retain the exact punctuation supplied to TTS.
            groups = [[item] for item in sentences]
        elif words:
            current: list[dict] = []
            current_length = 0
            for item in words:
                text = str(item["text"]).strip()
                added_length = len(text) + (1 if current else 0)
                if current and (len(current) >= 9 or current_length + added_length > 72):
                    groups.append(current)
                    current = []
                    current_length = 0
                current.append(item)
                current_length += len(text) + (1 if len(current) > 1 else 0)
            if current:
                groups.append(current)
        else:
            raise RuntimeError(f"No speech-boundary timing was generated for {event['key']}")

        event_cues: list[dict] = []
        for index, group in enumerate(groups):
            first = group[0]
            last = group[-1]
            start = event["voice_start"] + float(first["offset"]) / 10_000_000
            natural_end = event["voice_start"] + (
                float(last["offset"]) + float(last["duration"])
            ) / 10_000_000
            if index + 1 < len(groups):
                next_start = event["voice_start"] + float(groups[index + 1][0]["offset"]) / 10_000_000
                end = max(natural_end, next_start - 0.035)
            else:
                end = min(event["end"] - 0.10, event["voice_start"] + event["voice_duration"])
            cue = {
                "start": start,
                "end": end,
                "text": " ".join(str(item["text"]).strip() for item in group),
                "event": event["key"],
            }
            event_cues.append(cue)
            all_cues.append(cue)
        event["caption_cues"] = event_cues

        spoken = word_tokens(event["voice"])
        captioned = word_tokens(" ".join(cue["text"] for cue in event_cues))
        if captioned != spoken:
            raise RuntimeError(
                f"Caption words do not match narration for {event['key']}: {captioned!r} != {spoken!r}"
            )
    return all_cues


def write_captions(cues: list[dict]) -> Path:
    target = WORK / "captions.srt"
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n{srt_timestamp(cue['start'])} --> {srt_timestamp(cue['end'])}\n{cue['text']}"
        )
    target.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return target


def normalized_caption(text: str) -> str:
    return " ".join(text.split()).casefold()


def quality_check(
    events: list[dict],
    total: float,
    panels: list[Image.Image],
    captions: Path,
    cues: list[dict],
) -> dict:
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size",
                "-show_entries",
                "stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
                "-of",
                "json",
                str(OUTPUT),
            ],
            text=True,
        )
    )
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    caption_match = all(
        word_tokens(" ".join(cue["text"] for cue in event["caption_cues"]))
        == word_tokens(event["voice"])
        for event in events
    )
    caption_timing = all(
        cue["start"] < cue["end"]
        and (index == 0 or cues[index - 1]["end"] <= cue["start"] + 0.001)
        for index, cue in enumerate(cues)
    )
    checks = {
        "nontrivial_size": OUTPUT.stat().st_size > 1_500_000,
        "duration_matches_timeline": abs(float(probe["format"]["duration"]) - total) < 0.30,
        "vertical_h264_1080x1920": (
            video.get("codec_name") == "h264"
            and video.get("width") == W
            and video.get("height") == H
            and video.get("r_frame_rate") == "30/1"
        ),
        "aac_48khz_stereo": (
            audio.get("codec_name") == "aac"
            and audio.get("sample_rate") == "48000"
            and audio.get("channels") == 2
        ),
        "verbatim_burned_captions_match_narration": caption_match,
        "caption_cues_are_ordered_and_nonoverlapping": caption_timing,
        "caption_sidecar_exists": captions.exists() and captions.stat().st_size > 100,
        "all_scene_panels_available": len(panels) == 6,
    }
    report = {
        "episode": "parenting-rewind-screen-time-02",
        "version": "v1",
        "output": str(OUTPUT),
        "duration_seconds": float(probe["format"]["duration"]),
        "size_bytes": int(probe["format"]["size"]),
        "narration_voice": VOICE,
        "music": {
            "type": "original locally synthesized emotional score",
            "v4_style_gain_multiplier": 3.0,
            "narration_sidechain_ducking": True,
            "ambient_background_noise": False,
            "sound_effects": False,
        },
        "captions": {
            "burned_in": True,
            "verbatim_to_narration": True,
            "sidecar_srt": str(captions),
        },
        "checks": checks,
        "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    contact = Image.new("RGB", (1080, 960), "white")
    for index, event in enumerate(events):
        sample_time = event["start"] + (event["end"] - event["start"]) * 0.55
        sample = frame_for(event, sample_time, panels, total).resize((270, 480), Image.Resampling.LANCZOS)
        contact.paste(sample, ((index % 4) * 270, (index // 4) * 480))
    contact.save(WORK / "quality-contact-sheet.jpg", quality=93)

    if not report["passed"]:
        raise RuntimeError(f"Quality gate failed: {report}")
    return report


def main() -> None:
    if not ASSET.exists():
        raise FileNotFoundError(ASSET)
    if OUTPUT.exists():
        print(f"Completed episode already exists; preserving without regeneration: {OUTPUT}")
        return
    WORK.mkdir(parents=True, exist_ok=True)
    asyncio.run(make_voices())
    events, total = make_timeline()
    cues = build_caption_cues(events)
    captions = write_captions(cues)
    panels = split_storyboard()
    render_video(events, total, panels)
    report = quality_check(events, total, panels, captions, cues)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
