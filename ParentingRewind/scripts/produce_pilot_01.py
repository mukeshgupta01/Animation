"""Create the first Parenting Rewind vertical pilot video.

The pilot is intentionally local-only. It does not know about YouTube, OAuth,
the Tiny Tales uploader, or any scheduled task.
"""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import subprocess

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


PROJECT = Path(__file__).resolve().parents[1]
ASSET = PROJECT / "production-assets" / "pilot-01-shoe-storyboard.png"
WORK = PROJECT / "production-work" / "pilot-01-shoes"
OUTPUT = PROJECT / "output" / "parenting-rewind-pilot-01-shoes.mp4"

W, H = 1080, 1920
ART_FPS, VIDEO_FPS = 6, 30
VOICE = "en-AU-NatashaNeural"
VOICE_RATE = "-3%"
VOICE_PITCH = "+0Hz"

FONT_REGULAR = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_SEMIBOLD = Path("C:/Windows/Fonts/seguisb.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")

SEGMENTS = [
    {
        "key": "hook",
        "panel": 0,
        "kind": "hook",
        "headline": "THE SHOES BATTLE",
        "caption": "Your child refuses their shoes—\nand you are already late.",
        "voice": (
            "Your child refuses to put on their shoes, and you are already late. "
            "What happens next can turn into a power struggle, or keep the boundary calm."
        ),
        "minimum": 7.0,
    },
    {
        "key": "wrong",
        "panel": 1,
        "kind": "wrong",
        "headline": "THE FIRST REACTION",
        "caption": "“Why do you never listen?\nPut your shoes on now!”",
        "voice": (
            "It is easy to say, Why do you never listen? Put your shoes on now! "
            "The instruction is there, but criticism adds another problem."
        ),
        "minimum": 7.5,
    },
    {
        "key": "pause",
        "panel": 2,
        "kind": "pause",
        "headline": "PAUSE",
        "caption": "The boundary is not the problem.\nIt is still time to leave.",
        "voice": (
            "Pause. The boundary is not the problem. It is still time to leave. "
            "We only need to change how we deliver it."
        ),
        "minimum": 6.5,
    },
    {
        "key": "rewind",
        "panel": 2,
        "kind": "rewind",
        "headline": "LET’S REWIND",
        "caption": "Fewer words.\nTwo acceptable choices.",
        "voice": "Let us rewind and try fewer words, with two choices the parent can accept.",
        "minimum": 5.0,
    },
    {
        "key": "better",
        "panel": 3,
        "kind": "better",
        "headline": "SAY THIS INSTEAD",
        "caption": "“It’s time to leave.\nRed shoes or blue shoes?”",
        "voice": "It is time to leave. Would you like the red shoes, or the blue shoes?",
        "minimum": 5.5,
    },
    {
        "key": "choice",
        "panel": 4,
        "kind": "better",
        "headline": "ONE SMALL DECISION",
        "caption": "Both choices keep\nthe same boundary.",
        "voice": (
            "Both choices work for the parent, while the child gets one small decision. "
            "If they do not choose, calmly choose this time and help them get ready."
        ),
        "minimum": 8.0,
    },
    {
        "key": "takeaway",
        "panel": 5,
        "kind": "takeaway",
        "headline": "THE TAKEAWAY",
        "caption": "KEEP THE BOUNDARY.\nSHARE A LITTLE CONTROL.",
        "voice": (
            "Keep the boundary. Share a little control. Save this sentence for your next busy morning."
        ),
        "minimum": 7.0,
    },
]


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
        if target.exists():
            continue
        communicate = edge_tts.Communicate(
            segment["voice"],
            VOICE,
            rate=VOICE_RATE,
            pitch=VOICE_PITCH,
            volume="-1%",
        )
        await communicate.save(str(target))


def make_timeline() -> tuple[list[dict], float]:
    cursor = 0.35
    events: list[dict] = []
    for segment in SEGMENTS:
        voice = WORK / f"voice-{segment['key']}.mp3"
        length = max(segment["minimum"], media_duration(voice) + 0.95)
        event = dict(segment)
        event["start"] = cursor
        event["voice_start"] = cursor + 0.32
        event["end"] = cursor + length
        events.append(event)
        cursor = event["end"]
    return events, math.ceil((cursor + 0.45) * ART_FPS) / ART_FPS


def split_storyboard() -> list[Image.Image]:
    source = Image.open(ASSET).convert("RGB")
    panels: list[Image.Image] = []
    for row in range(2):
        for col in range(3):
            x1 = round(col * source.width / 3) + 7
            x2 = round((col + 1) * source.width / 3) - 7
            y1 = round(row * source.height / 2) + 7
            y2 = round((row + 1) * source.height / 2) - 7
            panels.append(source.crop((x1, y1, x2, y2)))
    return panels


def cover(image: Image.Image, progress: float, panel_index: int) -> Image.Image:
    zoom = 1.0 + 0.035 * progress
    scale = max(W / image.width, H / image.height) * zoom
    resized = image.resize(
        (math.ceil(image.width * scale), math.ceil(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    max_x = max(0, resized.width - W)
    max_y = max(0, resized.height - H)
    direction = -1 if panel_index % 2 else 1
    x = int(max_x * (0.5 + direction * 0.08 * (progress - 0.5)))
    y = int(max_y * (0.42 + 0.16 * progress))
    x = max(0, min(max_x, x))
    y = max(0, min(max_y, y))
    return resized.crop((x, y, x + W, y + H))


def add_vertical_gradient(overlay: Image.Image, top: bool, height: int, opacity: int) -> None:
    pixels = Image.new("RGBA", (W, height), (18, 24, 27, 0))
    draw = ImageDraw.Draw(pixels)
    for y in range(height):
        ratio = y / max(1, height - 1)
        alpha = int(opacity * ((1 - ratio) if top else ratio))
        draw.line((0, y, W, y), fill=(18, 24, 27, alpha))
    overlay.alpha_composite(pixels, (0, 0 if top else H - height))


def wrapped_lines(draw: ImageDraw.ImageDraw, text: str, chosen_font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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
    spacing: int = 10,
) -> int:
    lines = wrapped_lines(draw, text, chosen_font, 930)
    line_height = chosen_font.size + spacing
    for line in lines:
        box = draw.textbbox((0, 0), line, font=chosen_font)
        x = (W - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=chosen_font, fill=fill, stroke_width=2, stroke_fill=(10, 18, 20, 125))
        y += line_height
    return y


def rewind_symbol(draw: ImageDraw.ImageDraw, phase: float) -> None:
    box = (390, 690, 690, 990)
    draw.ellipse(box, fill=(22, 40, 48, 180), outline=(255, 255, 255, 220), width=7)
    start = int(35 + phase * 20)
    draw.arc((435, 735, 645, 945), start=start, end=start + 285, fill=(255, 255, 255, 255), width=18)
    draw.polygon([(451, 738), (410, 790), (479, 799)], fill=(255, 255, 255, 255))
    label = font(42, "bold")
    box2 = draw.textbbox((0, 0), "REWIND", font=label)
    draw.text(((W - (box2[2] - box2[0])) / 2, 1000), "REWIND", font=label, fill="white")


def frame_for(event: dict, absolute_time: float, panels: list[Image.Image], total: float) -> Image.Image:
    duration = event["end"] - event["start"]
    progress = max(0.0, min(1.0, (absolute_time - event["start"]) / max(0.01, duration)))
    frame = cover(panels[event["panel"]], progress, event["panel"])
    frame = ImageEnhance.Color(frame).enhance(0.96)
    if event["kind"] == "wrong":
        tint = Image.new("RGB", frame.size, (104, 28, 22))
        frame = Image.blend(frame, tint, 0.10)
    elif event["kind"] in {"better", "takeaway"}:
        tint = Image.new("RGB", frame.size, (25, 81, 65))
        frame = Image.blend(frame, tint, 0.06)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    add_vertical_gradient(overlay, top=True, height=500, opacity=225)
    add_vertical_gradient(overlay, top=False, height=690, opacity=238)
    draw = ImageDraw.Draw(overlay, "RGBA")

    accent = {
        "hook": (244, 188, 75, 255),
        "wrong": (244, 111, 96, 255),
        "pause": (244, 188, 75, 255),
        "rewind": (109, 203, 217, 255),
        "better": (112, 214, 169, 255),
        "takeaway": (255, 222, 133, 255),
    }[event["kind"]]

    draw.rounded_rectangle((54, 54, 390, 116), radius=28, fill=(19, 35, 39, 205), outline=(255, 255, 255, 85), width=2)
    draw.text((84, 68), "PARENTING REWIND", font=font(27, "bold"), fill=(255, 255, 255, 245))
    draw.rounded_rectangle((54, 151, 70, 315), radius=8, fill=accent)
    centered_text(draw, 165, event["headline"], font(55, "bold"), accent, spacing=5)

    if event["kind"] == "rewind":
        rewind_symbol(draw, progress)

    draw.rounded_rectangle((54, 1375, 1026, 1785), radius=42, fill=(14, 25, 29, 218), outline=(255, 255, 255, 70), width=2)
    centered_text(draw, 1450, event["caption"], font(48, "semibold"), (255, 255, 255, 255), spacing=14)

    if event["kind"] == "takeaway":
        source = "GENERAL PARENTING EDUCATION  •  EVERY CHILD IS DIFFERENT"
        box = draw.textbbox((0, 0), source, font=font(19, "semibold"))
        draw.text(((W - (box[2] - box[0])) / 2, 1814), source, font=font(19, "semibold"), fill=(255, 255, 255, 205))

    bar_width = int((W - 108) * absolute_time / total)
    draw.rounded_rectangle((54, 1875, 1026, 1889), radius=7, fill=(255, 255, 255, 70))
    if bar_width > 0:
        draw.rounded_rectangle((54, 1875, 54 + bar_width, 1889), radius=7, fill=accent)
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "original-ambient-bed.wav"
    if target.exists() and media_duration(target) >= total - 0.1:
        return target
    fade_out = max(0.0, total - 2.2)
    expression = (
        "0.020*sin(2*PI*220*t)+0.014*sin(2*PI*277.18*t)+"
        "0.012*sin(2*PI*329.63*t)+0.008*sin(2*PI*440*t)"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc=exprs={expression}:s=48000:d={total:.3f}",
            "-af",
            f"lowpass=f=1200,tremolo=f=0.12:d=0.12,afade=t=in:st=0:d=1.8,afade=t=out:st={fade_out:.3f}:d=2.2",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(target),
        ]
    )
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

    music = make_music(total)
    inputs = ["-i", str(silent), "-i", str(music)]
    filters = ["[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.62[bed]"]
    labels = ["[bed]"]
    for input_index, event in enumerate(events, start=2):
        voice = WORK / f"voice-{event['key']}.mp3"
        inputs.extend(["-i", str(voice)])
        delay = round(event["voice_start"] * 1000)
        filters.append(
            f"[{input_index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"adelay={delay}|{delay},volume=1.18[v{input_index}]"
        )
        labels.append(f"[v{input_index}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,"
        + "alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=9[a]"
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


def quality_check(events: list[dict], total: float, panels: list[Image.Image]) -> dict:
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
    checks = {
        "nontrivial_size": OUTPUT.stat().st_size > 1_500_000,
        "duration": abs(float(probe["format"]["duration"]) - total) < 0.30,
        "vertical_h264": video.get("codec_name") == "h264" and video.get("width") == W and video.get("height") == H,
        "aac_48khz_stereo": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
    }
    report = {
        "pilot": "parenting-rewind-shoes-01",
        "output": str(OUTPUT),
        "duration_seconds": float(probe["format"]["duration"]),
        "size_bytes": int(probe["format"]["size"]),
        "checks": checks,
        "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    contact = Image.new("RGB", (810, 960), "white")
    for index, event in enumerate(events[:6]):
        sample_time = event["start"] + (event["end"] - event["start"]) * 0.55
        sample = frame_for(event, sample_time, panels, total).resize((270, 480), Image.Resampling.LANCZOS)
        contact.paste(sample, ((index % 3) * 270, (index // 3) * 480))
    contact.save(WORK / "quality-contact-sheet.jpg", quality=92)
    if not report["passed"]:
        raise RuntimeError(f"Quality gate failed: {report}")
    return report


def main() -> None:
    if not ASSET.exists():
        raise FileNotFoundError(ASSET)
    if OUTPUT.exists():
        print(f"Completed pilot already exists; preserving without regeneration: {OUTPUT}")
        return
    WORK.mkdir(parents=True, exist_ok=True)
    asyncio.run(make_voices())
    events, total = make_timeline()
    panels = split_storyboard()
    render_video(events, total, panels)
    report = quality_check(events, total, panels)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
