"""Produce an original lively 3D-look breakfast dance prototype."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import wave

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import produce_snack_video as base
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
OUTPUT = AUTOMATION / "production-output" / "nia-rainbow-breakfast-dance-01.mp4"
WORK = AUTOMATION / "production-work" / "nia-rainbow-breakfast-dance-01"
META = AUTOMATION.parent / "metadata" / "nia-rainbow-breakfast-dance-01.json"
NIA_SHEET = AUTOMATION / "production-assets" / "nia-3d-pose-sheet.png"
FRUIT_SHEET = AUTOMATION / "production-assets" / "breakfast-friends-3d-pose-sheet.png"
KITCHEN_BG = AUTOMATION / "production-assets" / "rainbow-breakfast-kitchen-3d.png"
TABLE_BG = AUTOMATION / "production-assets" / "rainbow-breakfast-table-3d.png"
FINALE_BG = AUTOMATION / "production-assets" / "rainbow-breakfast-finale-3d.png"

NIA = select_voice_profile("ana-us")
HOST = select_voice_profile("ryan-uk")
ART_FPS, VIDEO_FPS = 12, 30

SCRIPT = [
    ("hello", "nia", "Good morning! I am Nia. My breakfast friends brought a brand-new beat. Will you dance with us?"),
    ("warmup", "host", "Make a little dancing space. Clap two times, tap two times, then wiggle gently."),
    ("warmup_activity", None, "CLAP, CLAP - TAP, TAP - WIGGLE", 5.4),
    ("strawberry", "nia", "Red Strawberry rolls in first. Red, red, bounce your head!"),
    ("strawberry", "host", "Strawberries are fruit. Their tiny seeds sit on the outside."),
    ("red_activity", None, "BOUNCE TO THE RED BEAT", 5.2),
    ("banana", "nia", "Yellow Banana slides into the song. Yellow, yellow, stretch up tall!"),
    ("banana", "host", "A banana has a peel. A trusted grown-up can help little hands prepare breakfast."),
    ("yellow_activity", None, "STRETCH TO THE YELLOW BEAT", 5.2),
    ("blueberry", "nia", "Blue Blueberry spins onto the table. Blue, blue, turn around!"),
    ("blueberry", "host", "Blueberries are small fruit, so sit down to eat and follow your grown-up's safe-food instructions."),
    ("blue_activity", None, "TURN TO THE BLUE BEAT", 5.2),
    ("colour_call", "nia", "I see red, yellow, and blue. Point to the colour I call. Red! Yellow! Blue!"),
    ("colour_activity", None, "POINT: RED - YELLOW - BLUE", 5.5),
    ("together", "host", "Breakfast looks different in every family. We can notice colours, listen to our bodies, and choose from the foods a grown-up provides."),
    ("chorus", "nia", "Clap to the colours, tap to the beat. Breakfast mornings can feel so sweet. Wave to the red, the yellow, the blue. Rainbow friends are dancing with you!"),
    ("dance_activity", None, "YOUR RAINBOW BREAKFAST DANCE", 6.0),
    ("finale", "nia", "What a lively morning! Thank you for dancing with us. Bye-bye, breakfast friends!"),
]


def voice_path(index: int, phase: str) -> Path:
    return WORK / f"voice-{index:02d}-{phase}.mp3"


async def make_voices() -> None:
    tasks = []
    for index, entry in enumerate(SCRIPT):
        phase, speaker, text = entry[:3]
        if speaker is None:
            continue
        target = voice_path(index, phase)
        if target.exists():
            continue
        profile = NIA if speaker == "nia" else HOST
        tasks.append(edge_tts.Communicate(
            text, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
        ).save(str(target)))
    if tasks:
        await asyncio.gather(*tasks)


def audio_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def build_timeline() -> tuple[list[dict], list[tuple[Path, float]], float]:
    events = [{"phase": "title", "start": 0.0, "end": 5.0, "text": ""}]
    voices: list[tuple[Path, float]] = []
    cursor = 5.0
    for index, entry in enumerate(SCRIPT):
        phase, speaker, text = entry[:3]
        if speaker is None:
            duration = float(entry[3])
            events.append({"phase": phase, "start": cursor, "end": cursor + duration, "text": text, "activity": True})
            cursor += duration + 0.35
            continue
        path = voice_path(index, phase)
        duration = audio_duration(path)
        events.append({"phase": phase, "start": cursor, "end": cursor + duration + 0.35, "text": text, "speaker": speaker})
        voices.append((path, cursor))
        cursor += duration + 0.62
    events.append({"phase": "end", "start": cursor, "end": cursor + 4.5, "text": ""})
    return events, voices, cursor + 4.5


def split_sheet(path: Path) -> list[Image.Image]:
    sheet = Image.open(path).convert("RGBA")
    cell_w, cell_h = sheet.width // 3, sheet.height // 2
    result = []
    for row in range(2):
        for col in range(3):
            cell = sheet.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            bbox = cell.getchannel("A").getbbox()
            if not bbox:
                raise RuntimeError(f"Empty sprite cell {row},{col} in {path}")
            result.append(cell.crop(bbox))
    return result


def fit_background(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max((base.W + 180) / image.width, (base.H + 110) / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def load_assets() -> dict:
    required = [NIA_SHEET, FRUIT_SHEET, KITCHEN_BG, TABLE_BG, FINALE_BG]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing 3D breakfast assets: {missing}")
    return {
        "nia": split_sheet(NIA_SHEET),
        "fruit": split_sheet(FRUIT_SHEET),
        "kitchen": fit_background(KITCHEN_BG),
        "table": fit_background(TABLE_BG),
        "finale": fit_background(FINALE_BG),
    }


def camera_frame(source: Image.Image, t: float, phase: str) -> Image.Image:
    max_x = max(0, source.width - base.W)
    max_y = max(0, source.height - base.H)
    x_phase = (math.sin(t * 0.18 + len(phase)) + 1) / 2
    y_phase = (math.sin(t * 0.12 + 1.7) + 1) / 2
    x = round(max_x * x_phase)
    y = round(max_y * (0.25 + 0.35 * y_phase))
    return source.crop((x, y, x + base.W, y + base.H)).convert("RGBA")


def sprite(frame: Image.Image, image: Image.Image, center: tuple[int, int], height: int, *, bob: float = 0, tilt: float = 0, shadow: bool = True) -> None:
    ratio = height / image.height
    item = image.resize((max(1, round(image.width * ratio)), height), Image.Resampling.LANCZOS)
    if tilt:
        item = item.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=True)
    x = round(center[0] - item.width / 2)
    y = round(center[1] - item.height + bob)
    if shadow:
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer, "RGBA")
        width = max(70, round(item.width * 0.58))
        draw.ellipse((center[0] - width // 2, center[1] - 13, center[0] + width // 2, center[1] + 17), fill=(49, 31, 29, 72))
        layer = layer.filter(ImageFilter.GaussianBlur(7))
        frame.alpha_composite(layer)
    frame.alpha_composite(item, (x, y))


def activity_panel(draw: ImageDraw.ImageDraw, event: dict, t: float) -> None:
    progress = max(0.0, min(1.0, (t - event["start"]) / (event["end"] - event["start"])))
    base.panel(draw, (345, 815, 1575, 1015), radius=38, fill=(255, 250, 235, 238), outline=(255, 177, 55, 255), width=6)
    base.centered(draw, (960, 872), event["text"], base.F38, (42, 67, 86, 255))
    for index, color in enumerate(((235, 70, 75, 255), (255, 199, 45, 255), (55, 128, 205, 255), (120, 204, 170, 255), (160, 92, 200, 255))):
        x = 675 + index * 145
        active = progress >= index / 5
        radius = 29 + (8 if active and int(t * 4) % 2 == 0 else 0)
        fill = color if active else (220, 224, 224, 255)
        draw.ellipse((x - radius, 950 - radius, x + radius, 950 + radius), fill=fill, outline=(255, 255, 255, 245), width=4)


def frame_for(event: dict, t: float, assets: dict) -> Image.Image:
    phase = event["phase"]
    table_phases = {"strawberry", "red_activity", "banana", "yellow_activity", "blueberry", "blue_activity", "colour_call", "colour_activity"}
    finale_phases = {"together", "chorus", "dance_activity", "finale", "end"}
    bg_key = "table" if phase in table_phases else "finale" if phase in finale_phases else "kitchen"
    frame = camera_frame(assets[bg_key], t, phase)
    draw = ImageDraw.Draw(frame, "RGBA")
    progress = max(0.0, min(1.0, (t - event["start"]) / max(0.01, event["end"] - event["start"])))
    beat = int(t * 2.8)

    if phase == "title":
        frame.alpha_composite(Image.new("RGBA", frame.size, (38, 40, 74, 65)))
        sprite(frame, assets["nia"][1], (350, 1060), 875, bob=-18 * abs(math.sin(t * 3.0)))
        for index, fruit_index in enumerate((0, 1, 2)):
            sprite(frame, assets["fruit"][fruit_index], (1080 + index * 235, 1010), 390, bob=-18 * abs(math.sin(t * 3.4 + index)), tilt=4 * math.sin(t * 2 + index))
        base.panel(draw, (650, 125, 1770, 430), radius=48, fill=(255, 250, 232, 240), outline=(255, 179, 48, 255), width=8)
        base.centered(draw, (1210, 225), "NIA'S RAINBOW", base.F62, (48, 105, 148, 255), 2)
        base.centered(draw, (1210, 330), "BREAKFAST DANCE", base.F62, (224, 72, 82, 255), 2)
        return frame.convert("RGB")

    nia_pose = (beat % 6) if phase in {"warmup", "warmup_activity", "chorus", "dance_activity", "finale", "end"} else (0 if beat % 2 == 0 else 1)
    if phase not in table_phases:
        nia_x = round(360 + 70 * math.sin(t * 1.3)) if phase in finale_phases else round(-100 + 620 * min(1.0, progress * 2.5)) if phase == "hello" else 480
        sprite(frame, assets["nia"][nia_pose], (nia_x, 1045), 790, bob=-20 * abs(math.sin(t * 4.3)), tilt=2.3 * math.sin(t * 2.1))

    selected = None
    if phase in {"strawberry", "red_activity"}:
        selected = 0
    elif phase in {"banana", "yellow_activity"}:
        selected = 1
    elif phase in {"blueberry", "blue_activity"}:
        selected = 2

    if selected is not None:
        pose = selected + (3 if beat % 2 else 0)
        sprite(frame, assets["fruit"][pose], (960, 975), 650, bob=-34 * abs(math.sin(t * 4.8)), tilt=5 * math.sin(t * 2.6))
    elif phase in {"colour_call", "colour_activity"}:
        for index in range(3):
            pose = index + (3 if (beat + index) % 2 else 0)
            sprite(frame, assets["fruit"][pose], (520 + index * 440, 990), 470, bob=-24 * abs(math.sin(t * 4.4 + index)), tilt=4 * math.sin(t * 2.2 + index))
    elif phase in finale_phases:
        for index in range(3):
            pose = index + (3 if (beat + index) % 2 else 0)
            x = 1020 + index * 250 + round(25 * math.sin(t * 1.7 + index))
            sprite(frame, assets["fruit"][pose], (x, 1025), 360, bob=-25 * abs(math.sin(t * 4.5 + index)), tilt=5 * math.sin(t * 2.4 + index))

    for index in range(11):
        angle = t * (0.7 + index * 0.035) + index
        x = round(960 + math.cos(angle) * (650 + 20 * (index % 3)))
        y = round(500 + math.sin(angle * 1.3) * 310)
        radius = 7 + index % 4
        color = ((235, 72, 80, 155), (255, 196, 38, 150), (57, 135, 210, 150))[index % 3]
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    headings = {
        "hello": "GOOD MORNING, DANCERS!", "warmup": "MAKE A LITTLE DANCING SPACE", "warmup_activity": "WARM-UP BEAT",
        "strawberry": "RED STRAWBERRY", "red_activity": "RED BEAT", "banana": "YELLOW BANANA", "yellow_activity": "YELLOW BEAT",
        "blueberry": "BLUE BLUEBERRY", "blue_activity": "BLUE BEAT", "colour_call": "RED, YELLOW, BLUE", "colour_activity": "COLOUR CALL",
        "together": "BREAKFASTS CAN LOOK DIFFERENT", "chorus": "CLAP TO THE COLOURS", "dance_activity": "DANCE WITH THE RAINBOW FRIENDS",
        "finale": "A LIVELY MORNING", "end": "RED - YELLOW - BLUE",
    }
    base.panel(draw, (305, 42, 1615, 143), radius=31, fill=(255, 250, 234, 230), outline=(255, 179, 48, 255), width=5)
    base.centered(draw, (960, 92), headings.get(phase, "RAINBOW BREAKFAST DANCE"), base.F38, (44, 70, 92, 255))
    if event.get("activity"):
        activity_panel(draw, event, t)
    if phase == "end":
        base.panel(draw, (475, 790, 1445, 1005), radius=40, fill=(255, 250, 234, 238), outline=(255, 179, 48, 255), width=6)
        base.centered(draw, (960, 855), "CLAP - TAP - STRETCH - TURN", base.F38, (44, 70, 92, 255))
        base.centered(draw, (960, 930), "THANKS FOR DANCING!", base.F48, (224, 72, 82, 255))
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "breakfast-dance-music.wav"
    if target.exists():
        return target
    sample_rate = 48000
    count = round(total * sample_rate)
    notes = (261.63, 329.63, 392.0, 523.25)
    rng = random.Random(7319)
    with wave.open(str(target), "wb") as handle:
        handle.setnchannels(2); handle.setsampwidth(2); handle.setframerate(sample_rate)
        block = bytearray()
        for index in range(count):
            t = index / sample_rate
            beat_pos = t % 0.5
            bar = int(t / 2.0)
            root = notes[bar % len(notes)]
            kick = math.sin(2 * math.pi * (72 - 26 * min(1, beat_pos / 0.16)) * beat_pos) * math.exp(-24 * beat_pos) * 0.12
            clap_pos = (t + 0.25) % 0.5
            clap = (rng.random() * 2 - 1) * math.exp(-32 * clap_pos) * 0.022
            bass = math.sin(2 * math.pi * root / 2 * t) * 0.026
            marimba_pos = t % 0.25
            melody = math.sin(2 * math.pi * notes[(int(t / 0.25) + bar) % 4] * t) * math.exp(-10 * marimba_pos) * 0.035
            shaker = (rng.random() * 2 - 1) * (0.006 if int(t * 8) % 2 else 0.012)
            fade = min(1.0, t / 1.2, (total - t) / 1.5)
            sample = round(max(-1, min(1, (kick + clap + bass + melody + shaker) * fade)) * 32767)
            block += struct.pack("<hh", sample, sample)
            if len(block) >= 131072:
                handle.writeframes(block); block.clear()
        if block:
            handle.writeframes(block)
    return target


def render(events: list[dict], voices: list[tuple[Path, float]], total: float, assets: dict) -> None:
    silent = WORK / "silent.mp4"
    process = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{base.W}x{base.H}", "-r", str(ART_FPS), "-i", "-", "-an",
        "-vf", f"fps={VIDEO_FPS}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", str(silent),
    ], stdin=subprocess.PIPE)
    for number in range(math.ceil(total * ART_FPS)):
        t = number / ART_FPS
        event = next((item for item in events if item["start"] <= t < item["end"]), events[-1])
        process.stdin.write(frame_for(event, t, assets).tobytes())
        if number % (ART_FPS * 12) == 0:
            print(f"Rendered {t:.0f}/{total:.0f}s", flush=True)
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("3D breakfast prototype silent render failed")

    bed = make_music(total)
    inputs = ["-i", str(silent), "-i", str(bed)]
    filters = ["[1:a]volume=.76[bed]"]
    labels = ["[bed]"]
    for stream, (voice, start) in enumerate(voices, 2):
        inputs += ["-i", str(voice)]
        delay = round(start * 1000)
        filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.25[v{stream}]")
        labels.append(f"[v{stream}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
        "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUTPUT),
    ], check=True)


def quality(events: list[dict], total: float, assets: dict) -> None:
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
        "-of", "json", str(OUTPUT),
    ], text=True))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    gaps = [{"phase": event["phase"], "quiet_gap_seconds": event["end"] - event["start"]} for event in events if event.get("activity")]
    (WORK / "activity-gap-audit.json").write_text(json.dumps(gaps, indent=2) + "\n", encoding="utf-8")
    checks = {
        "size": OUTPUT.stat().st_size > 2_000_000,
        "duration": 95 <= float(probe["format"]["duration"]) <= 210 and abs(float(probe["format"]["duration"]) - total) < 0.25,
        "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H,
        "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "six_response_gaps": len(gaps) == 6 and all(item["quiet_gap_seconds"] >= 5 for item in gaps),
        "different_lead_and_host_voices": NIA["voice"] != HOST["voice"],
        "six_nia_poses_available": len(assets["nia"]) == 6,
        "six_fruit_poses_available": len(assets["fruit"]) == 6,
        "three_dimensional_environments": all(key in assets for key in ("kitchen", "table", "finale")),
    }
    report = {
        "format": "original-3d-preschool-breakfast-dance",
        "output": str(OUTPUT),
        "duration_seconds": float(probe["format"]["duration"]),
        "lead_voice_profile": NIA["name"],
        "host_voice_profile": HOST["name"],
        "new_image_generation_calls": 5,
        "true_rigged_3d_animation": False,
        "visual_method": "original 3D-rendered pose assets with pose switching, parallax, camera motion and compositing",
        "checks": checks,
        "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    wanted = {"title", "hello", "warmup_activity", "strawberry", "red_activity", "banana", "blueberry", "colour_activity", "together", "chorus", "dance_activity", "finale", "end"}
    samples = [event for event in events if event["phase"] in wanted]
    contact = Image.new("RGB", (960, math.ceil(len(samples) / 4) * 135), "white")
    for index, event in enumerate(samples):
        t = event["start"] + min(1.2, (event["end"] - event["start"]) / 2)
        image = frame_for(event, t, assets).resize((240, 135), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image); draw.rectangle((0, 0, 62, 19), fill="black"); draw.text((3, 2), f"{t:.1f}s", font=base.font(12, True), fill="white")
        contact.paste(image, ((index % 4) * 240, (index // 4) * 135))
    contact.save(WORK / "quality-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(f"3D breakfast quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc = {
        "id": "nia-rainbow-breakfast-dance-01",
        "title": "Nia's Rainbow Breakfast Dance | Colours and Movement for Kids",
        "description": "Dance through a colourful breakfast morning with Nia and three lively fruit friends. Children clap, tap, stretch, turn, identify red, yellow and blue, and hear gentle food-safety guidance for family breakfast time.\n\nAn original Tiny Tales 3D-look music-and-movement adventure for children ages 3 to 7.",
        "tags": ["breakfast song for kids", "colour song", "dance for kids", "3D animation for kids", "preschool movement", "fruit for kids", "Tiny Tales"],
        "category_id": "27",
        "made_for_kids": True,
        "privacy": "public",
        "upload_authorized": False,
        "output": str(OUTPUT),
        "duration_seconds": total,
        "voice_profile": NIA["name"],
        "character_voice_profile": HOST["name"],
        "format_family": "original-3d-preschool-breakfast-dance",
        "visual_system": "3d-rendered-pose-animation-with-parallax-kitchen",
        "interaction_style": "beat-synced-colour-call-and-movement",
        "new_image_generation_calls": 5,
        "true_rigged_3d_animation": False,
    }
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() and (WORK / "quality-report.json").exists():
        report = json.loads((WORK / "quality-report.json").read_text(encoding="utf-8"))
        if report.get("passed"):
            print(f"Completed output already exists; preserving without regeneration: {OUTPUT}")
            return
    asyncio.run(make_voices())
    events, voices, total = build_timeline()
    assets = load_assets()
    render(events, voices, total, assets)
    quality(events, total, assets)
    write_metadata(total)
    print(json.dumps({"id": "nia-rainbow-breakfast-dance-01", "duration_seconds": total, "status": "completed"}, indent=2))


if __name__ == "__main__":
    main()
