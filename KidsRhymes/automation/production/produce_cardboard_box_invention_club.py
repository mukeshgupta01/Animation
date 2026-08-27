"""Produce The Cardboard Box Invention Club from an exact narration-to-shot plan."""

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
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

import produce_snack_video as base
import produce_star_friends_twinkle_playground as render_engine
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "cardboard-box-invention-club-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
VOICE = select_voice_profile("maisie-uk")
ART_FPS = 10


SHOTS = [
    ("01_opening_build", "cardboard-box-opening-v1.png", "In a sunny craft club, Amara, Ben, and Kai found one big cardboard box. They drew, decorated, and opened every flap together."),
    ("02_bus_adventure", "cardboard-box-bus-v1.png", "First, their box became a bus! Turn your pretend wheel, point to the next stop, then ring the paper bell. Ding, ding!"),
    ("03_cave_exploration", "cardboard-box-cave-v1.png", "Next, wide flaps made a cozy cave. A paper lantern glowed, painted spirals appeared, and a soft waterfall lifted. Wiggle your explorer fingers."),
    ("04_puppet_show", "cardboard-box-theatre-v1.png", "Then the cave became a puppet theatre. A smiling sun rose, a friendly frog hopped, and Kai opened the curtain. Can your hands hop, shine, and clap for the show?"),
    ("05_reading_nook", "cardboard-box-reading-nook-v1.png", "At blue-hour, the theatre grew quiet. Cushions, a little roof, and picture books made a reading nook. Turn one pretend page, then make a gentle welcome wave."),
    ("06_finale", "cardboard-box-finale-v1.png", "One box became four wonderful worlds: a bus, a cave, a theatre, and a reading nook. The friends bowed, waved, and cheered, because imagination grows when we build together!"),
]


def voice_path(index: int, shot_id: str) -> Path:
    return WORK / f"voice-{index:02d}-{shot_id}.mp3"


async def make_voices() -> None:
    tasks = []
    for index, (shot_id, _asset, line) in enumerate(SHOTS):
        target = voice_path(index, shot_id)
        if not target.exists():
            tasks.append(edge_tts.Communicate(
                line, VOICE["voice"], rate=VOICE["rate"], pitch=VOICE["pitch"], volume="-1%"
            ).save(str(target)))
    if tasks:
        await asyncio.gather(*tasks)


def media_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def build_timeline() -> tuple[list[dict], list[tuple[Path, float]], float]:
    events = [{"phase": "title", "start": 0.0, "end": 4.2, "asset": SHOTS[0][1]}]
    voices: list[tuple[Path, float]] = []
    cursor = events[-1]["end"]
    for index, (shot_id, asset, line) in enumerate(SHOTS):
        voice = voice_path(index, shot_id)
        voice_length = media_duration(voice)
        if voice_length > 13.8:
            raise RuntimeError(f"Narration is too long for the 14-second shot gate: {shot_id} {voice_length:.2f}s")
        reaction = min(1.0, max(0.18, 13.98 - voice_length))
        shot_length = max(9.2, voice_length + reaction)
        event = {
            "phase": shot_id,
            "start": cursor,
            "end": cursor + shot_length,
            "voice_end": cursor + voice_length,
            "asset": asset,
            "line": line,
        }
        events.append(event)
        voices.append((voice, cursor))
        cursor = event["end"]
    events.append({"phase": "end", "start": cursor, "end": cursor + 5.2, "asset": SHOTS[-1][1]})
    return events, voices, events[-1]["end"]


def fit_image(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = max((base.W + 180) / image.width, (base.H + 110) / image.height)
    return image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)


def load_assets() -> dict[str, Image.Image]:
    paths = {asset: ASSET_DIR / asset for _shot, asset, _line in SHOTS}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Cardboard Box artwork: {missing}")
    return {name: fit_image(path) for name, path in paths.items()}


def moving_crop(image: Image.Image, event: dict, t: float, index: int) -> Image.Image:
    span = max(0.001, event["end"] - event["start"])
    progress = max(0.0, min(1.0, (t - event["start"]) / span))
    if index % 2 == 0:
        zoom = 1.00 + 0.055 * progress
        x_factor = 0.18 + 0.46 * progress
    else:
        zoom = 1.055 - 0.040 * progress
        x_factor = 0.72 - 0.40 * progress
    resized = image.resize((round((base.W + 150) * zoom), round((base.H + 90) * zoom)), Image.Resampling.BICUBIC)
    available_x = max(0, resized.width - base.W)
    available_y = max(0, resized.height - base.H)
    x = int(available_x * x_factor)
    y = int(available_y * (0.46 + 0.05 * math.sin(progress * math.pi)))
    return resized.crop((x, y, x + base.W, y + base.H))


def action_overlay(frame: Image.Image, event: dict, t: float, index: int) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    local = t - event["start"]
    rng = random.Random(20260827 + index)
    if index == 0:
        colors = [(255, 92, 116, 125), (64, 205, 190, 125), (255, 210, 67, 125), (153, 104, 232, 125)]
        for item in range(12):
            x = (rng.randint(50, 1870) + int(local * (10 + item))) % base.W
            y = 80 + rng.randint(0, 760)
            draw.rounded_rectangle((x, y, x + 12, y + 8), 3, fill=colors[item % len(colors)])
    elif index == 1:
        bounce = int(7 * math.sin(local * math.pi * 2.0))
        for x in range(80, base.W, 170):
            draw.rounded_rectangle((x, 986 + bounce, x + 90, 998 + bounce), 6, fill=(255, 244, 176, 135))
        bell = 13 + int(5 * (0.5 + 0.5 * math.sin(local * 7)))
        draw.ellipse((1334 - bell, 257 - bell, 1334 + bell, 257 + bell), outline=(255, 228, 97, 150), width=4)
    elif index == 2:
        for item in range(20):
            x = rng.randint(60, base.W - 60)
            y = rng.randint(50, base.H - 80)
            radius = 2 + int(4 * (0.5 + 0.5 * math.sin(local * 1.8 + item)))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(130, 232, 255, 90))
    elif index == 3:
        for item in range(12):
            angle = local * 1.2 + item * math.pi / 6
            x = 960 + int(math.cos(angle) * (560 + 20 * math.sin(local)))
            y = 480 + int(math.sin(angle) * 300)
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 218, 90, 115))
    elif index == 4:
        for item in range(9):
            x = 420 + item * 138
            y = 148 + int(5 * math.sin(local * 1.2 + item))
            radius = 3 + int(4 * (0.5 + 0.5 * math.sin(local * 1.5 + item)))
            draw.line((x - radius, y, x + radius, y), fill=(255, 244, 166, 115), width=2)
            draw.line((x, y - radius, x, y + radius), fill=(255, 244, 166, 115), width=2)
    else:
        colors = [(255, 87, 136, 175), (255, 207, 66, 175), (71, 211, 197, 175), (155, 103, 234, 175)]
        for item in range(24):
            x = (rng.randint(20, 1900) + int(local * (22 + item % 5 * 4))) % base.W
            y = (rng.randint(20, 1050) + int(local * (38 + item % 4 * 5))) % base.H
            draw.rectangle((x, y, x + 9, y + 6), fill=colors[item % len(colors)])


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    if event["phase"] == "title":
        frame = moving_crop(assets[event["asset"]], event, t, 0).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, 0, base.W, base.H), fill=(35, 21, 60, 55))
        base.panel(draw, (220, 105, 1700, 385), radius=54, fill=(48, 33, 88, 224), outline=(255, 218, 91, 245), width=7)
        base.centered(draw, (960, 195), "THE CARDBOARD BOX", base.F62, (255, 241, 142, 255), 3)
        base.centered(draw, (960, 298), "INVENTION CLUB", base.F62, (255, 255, 255, 255), 3)
        return frame.convert("RGB")
    if event["phase"] == "end":
        frame = moving_crop(assets[event["asset"]], event, t, 5).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, 0, base.W, base.H), fill=(27, 17, 57, 88))
        base.panel(draw, (310, 745, 1610, 980), radius=48, fill=(46, 30, 86, 228), outline=(255, 218, 91, 245), width=7)
        base.centered(draw, (960, 830), "ONE BOX • FOUR WORLDS", base.F48, (255, 241, 142, 255), 2)
        base.centered(draw, (960, 915), "IMAGINATION GROWS TOGETHER!", base.F48, (255, 255, 255, 255), 2)
        return frame.convert("RGB")
    index = next(i for i, item in enumerate(SHOTS) if item[0] == event["phase"])
    frame = moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    action_overlay(frame, event, t, index)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "original-cardboard-club-music.wav"
    rate = 48000
    notes = [261.63, 329.63, 392.0, 440.0, 392.0, 329.63, 293.66, 349.23]
    rng = random.Random(8272026)
    with wave.open(str(target), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(rate)
        chunk = bytearray()
        for sample_index in range(int(total * rate)):
            t = sample_index / rate
            note = notes[int(t / 1.0) % len(notes)]
            pluck_phase = t % 1.0
            pluck = math.sin(2 * math.pi * note * t) * math.exp(-3.8 * pluck_phase) * 0.045
            warm_pad = sum(math.sin(2 * math.pi * frequency * t) for frequency in (130.81, 164.81, 196.0)) * 0.010
            tap = 0.0
            beat_phase = t % 0.5
            if beat_phase < 0.025:
                tap = math.sin(2 * math.pi * 96 * t) * 0.030 * (1 - beat_phase / 0.025)
            value = pluck + warm_pad + tap + rng.uniform(-1, 1) * 0.0012
            sample = max(-32767, min(32767, int(value * 32767)))
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                output.writeframesraw(chunk)
                chunk.clear()
        if chunk:
            output.writeframesraw(chunk)
    return target


def make_thumbnail() -> None:
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    source = Image.open(ASSET_DIR / "cardboard-box-finale-v1.png").convert("RGB")
    target_ratio = 16 / 9
    crop_width = round(source.height * target_ratio)
    left = max(0, (source.width - crop_width) // 2)
    canvas = source.crop((left, 0, left + crop_width, source.height)).resize((1280, 720), Image.Resampling.LANCZOS).convert("RGBA")
    canvas = ImageEnhance.Color(canvas).enhance(1.08)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((62, 36, 1218, 168), 38, fill=(77, 42, 139, 225), outline=(255, 255, 255, 240), width=6)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 66)
    text = "ONE BOX, FOUR WORLDS!"
    box = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    x = (1280 - (box[2] - box[0])) // 2
    draw.text((x, 66), text, font=font, fill=(255, 244, 129), stroke_width=4, stroke_fill=(35, 20, 67))
    badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    draw.rounded_rectangle((66, 650, 258, 700), 22, fill=(24, 24, 54, 230), outline=(255, 255, 255, 225), width=3)
    draw.text((88, 662), "TINY TALES", font=badge, fill="white")
    canvas.convert("RGB").save(THUMBNAIL, quality=90, optimize=True, progressive=True)
    if THUMBNAIL.stat().st_size > 2_000_000:
        canvas.convert("RGB").save(THUMBNAIL, quality=84, optimize=True, progressive=True)
    if THUMBNAIL.stat().st_size > 2_000_000:
        raise RuntimeError("Prepared thumbnail exceeds YouTube's 2 MB limit")


def quality(events: list[dict], total: float, assets: dict[str, Image.Image]) -> None:
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
        "-of", "json", str(OUTPUT),
    ], text=True))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], capture_output=True, text=True)
    transitions = [{"from_phase": a["phase"], "to_phase": b["phase"], "gap_seconds": b["start"] - a["end"]} for a, b in zip(events, events[1:])]
    story_events = events[1:-1]
    sync_rows = [{
        "shot_id": event["phase"], "asset": event["asset"], "visual_start": event["start"],
        "visual_end": event["end"], "narration_start": event["start"], "narration_end": event["voice_end"],
        "narration_contained_by_visual": event["start"] <= event["voice_end"] <= event["end"], "line": event["line"],
    } for event in story_events]
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(transitions, indent=2) + "\n", encoding="utf-8")
    (WORK / "narration-visual-sync-audit.json").write_text(json.dumps(sync_rows, indent=2) + "\n", encoding="utf-8")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    planned = {item["id"]: item for item in plan["shots"]}
    checks = {
        "size": OUTPUT.stat().st_size > 2_000_000,
        "duration": 60 <= float(probe["format"]["duration"]) <= 120 and abs(float(probe["format"]["duration"]) - total) < 0.3,
        "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H,
        "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "full_decode": decode.returncode == 0,
        "continuous_visual_timeline": all(abs(item["gap_seconds"]) < 0.000001 for item in transitions),
        "end_card_is_final_event_only": events[-1]["phase"] == "end" and all(event["phase"] != "end" for event in events[:-1]),
        "one_unique_artwork_per_voiced_beat": len({event["asset"] for event in story_events}) == len(story_events) == 6,
        "narration_contained_by_matching_visual": all(item["narration_contained_by_visual"] for item in sync_rows),
        "narration_lines_match_approved_plan": all(planned[event["phase"]]["line"] == event["line"] for event in story_events),
        "no_story_shot_over_14_seconds": all(event["end"] - event["start"] <= 14 for event in story_events),
        "six_original_story_shots": len(assets) == 6,
        "voice_rotation": VOICE["name"] == "maisie-uk",
        "thumbnail_technical": THUMBNAIL.is_file() and THUMBNAIL.stat().st_size <= 2_000_000,
    }
    report = {
        "format": "collaborative-imagination-transformation-story",
        "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]),
        "voice_profile": VOICE["name"], "story_shots": len(story_events), "new_image_generation_calls": 6,
        "true_rigged_3d_animation": False,
        "visual_method": "six unique built-in-generated premium 3D-style story compositions with continuous camera travel and scene-specific action overlays",
        "checks": checks, "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    general = Image.new("RGB", (960, math.ceil(len(events) / 4) * 135), "white")
    for index, event in enumerate(events):
        sample = event["start"] + min(1.8, (event["end"] - event["start"]) / 2)
        image = frame_for(event, sample, assets).resize((240, 135), Image.Resampling.LANCZOS)
        general.paste(image, ((index % 4) * 240, (index // 4) * 135))
    general.save(WORK / "quality-contact-sheet.png")
    boundary = []
    for current, following in zip(events, events[1:]):
        boundary.extend([(current, max(current["start"], current["end"] - 0.12)), (following, min(following["end"] - 0.01, following["start"] + 0.12))])
    sheet = Image.new("RGB", (1200, math.ceil(len(boundary) / 5) * 135), "white")
    for index, (event, sample) in enumerate(boundary):
        image = frame_for(event, sample, assets).resize((240, 135), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 190, 19), fill="black")
        draw.text((3, 2), f"{sample:.1f}s {event['phase']}", font=base.font(12, True), fill="white")
        sheet.paste(image, ((index % 5) * 240, (index // 5) * 135))
    sheet.save(WORK / "transition-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(f"Cardboard Box quality gate failed: {report}")


def write_metadata(total: float) -> None:
    document = {
        "id": ITEM_ID,
        "title": "The Cardboard Box Invention Club | Imagination Story for Kids",
        "description": "Join Amara, Ben, and Kai as one cardboard box becomes a pretend bus, a cozy cave, a puppet theatre, and a calm reading nook. Children can steer, point, ring, explore, make hand puppets, clap, turn a pretend page, and celebrate building together.\n\nAn original Tiny Tales imagination story supporting collaborative play, creativity, listening, movement, sequencing, and calm transitions for children ages 3 to 7.",
        "tags": ["imagination story for kids", "cardboard box ideas", "pretend play", "creative play for kids", "friendship story", "preschool story", "Tiny Tales"],
        "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": False,
        "output": str(OUTPUT), "duration_seconds": total, "voice_profile": VOICE["name"],
        "format_family": "collaborative-imagination-transformation-story",
        "visual_system": "six-unique-3d-style-craft-clubhouse-box-transformations-with-continuous-motion",
        "interaction_style": "pretend-driving-exploring-puppetry-clapping-and-calm-page-turning",
        "quality_gate_passed": True, "full_decode_passed": True, "transition_audit_passed": True,
        "transition_contact_sheet_reviewed": False,
        "quality_report": f"automation/production-work/{ITEM_ID}/quality-report.json",
        "transition_audit": f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json",
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "ONE BOX, FOUR WORLDS!",
        "thumbnail_reviewed": False, "quality_contact_sheet": f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png",
        "transition_contact_sheet": f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png",
        "new_image_generation_calls": 6, "true_rigged_3d_animation": False,
    }
    META.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(make_voices())
    events, voices, total = build_timeline()
    assets = load_assets()
    make_thumbnail()
    render_engine.WORK = WORK
    render_engine.OUTPUT = OUTPUT
    render_engine.frame_for = frame_for
    render_engine.make_music = make_music
    render_engine.render(events, voices, total, assets)
    quality(events, total, assets)
    write_metadata(total)
    print(json.dumps({"output": str(OUTPUT), "duration_seconds": total, "events": len(events)}, indent=2))


if __name__ == "__main__":
    main()
