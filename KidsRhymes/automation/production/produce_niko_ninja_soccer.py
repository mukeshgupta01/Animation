"""Produce Niko's Ninja Soccer Kindness Match from its locked narration-to-shot plan."""

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
ITEM_ID = "niko-ninja-soccer-kindness-match-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
PLAN_PATH = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
NARRATOR = select_voice_profile("ryan-uk")
NIKO = select_voice_profile("ana-us")
ART_FPS = 10


def plan() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def voice_path(index: int, shot_id: str, role: str) -> Path:
    return WORK / f"voice-{index:02d}-{shot_id}-{role}.mp3"


async def make_voices(shots: list[dict]) -> None:
    tasks = []
    for index, shot in enumerate(shots):
        for role, key, profile in (("narrator", "narrator_line", NARRATOR), ("niko", "character_line", NIKO)):
            line = shot.get(key)
            target = voice_path(index, shot["id"], role)
            if line and not target.exists():
                tasks.append(edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
                ).save(str(target)))
    if tasks:
        await asyncio.gather(*tasks)


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def build_timeline(shots: list[dict]) -> tuple[list[dict], list[tuple[Path, float]], float]:
    events = [{"phase": "title", "start": 0.0, "end": 4.0, "asset": shots[0]["asset"]}]
    voices: list[tuple[Path, float]] = []
    cursor = 4.0
    for index, shot in enumerate(shots):
        narrator = voice_path(index, shot["id"], "narrator")
        narrator_length = duration(narrator)
        placements = [{"role": "narrator", "start": cursor, "end": cursor + narrator_length, "line": shot["narrator_line"]}]
        voices.append((narrator, cursor))
        spoken_end = cursor + narrator_length
        if shot.get("character_line"):
            character = voice_path(index, shot["id"], "niko")
            character_start = spoken_end + 0.22
            character_end = character_start + duration(character)
            placements.append({"role": "niko", "start": character_start, "end": character_end, "line": shot["character_line"]})
            voices.append((character, character_start))
            spoken_end = character_end
        shot_length = max(8.4, spoken_end - cursor + 0.45)
        if shot_length > 14.0:
            raise RuntimeError(f"Voices exceed 14-second shot gate: {shot['id']} {shot_length:.2f}s")
        event = {
            "phase": shot["id"], "start": cursor, "end": cursor + shot_length,
            "voice_end": spoken_end, "asset": shot["asset"], "voices": placements,
        }
        events.append(event)
        cursor = event["end"]
    events.append({"phase": "end", "start": cursor, "end": cursor + 5.0, "asset": shots[-1]["asset"]})
    return events, voices, events[-1]["end"]


def fit_image(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = max((base.W + 200) / image.width, (base.H + 120) / image.height)
    return image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)


def load_assets(shots: list[dict]) -> dict[str, Image.Image]:
    paths = {shot["asset"]: ASSET_DIR / shot["asset"] for shot in shots}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Niko artwork: {missing}")
    return {name: fit_image(path) for name, path in paths.items()}


def moving_crop(image: Image.Image, event: dict, t: float, index: int) -> Image.Image:
    progress = max(0.0, min(1.0, (t - event["start"]) / max(0.001, event["end"] - event["start"])))
    zoom = 1.015 + (0.045 * progress if index % 2 == 0 else 0.045 * (1 - progress))
    resized = image.resize((round((base.W + 170) * zoom), round((base.H + 100) * zoom)), Image.Resampling.BICUBIC)
    x_room, y_room = max(0, resized.width - base.W), max(0, resized.height - base.H)
    x_factor = (0.16 + 0.56 * progress) if index % 2 == 0 else (0.76 - 0.54 * progress)
    x = int(x_room * x_factor)
    y = int(y_room * (0.48 + 0.04 * math.sin(progress * math.pi)))
    return resized.crop((x, y, x + base.W, y + base.H))


def action_overlay(frame: Image.Image, event: dict, t: float, index: int) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    local = t - event["start"]
    colours = [(38, 223, 210, 125), (255, 204, 52, 130), (255, 100, 116, 120), (139, 98, 232, 120)]
    if index in (2, 3, 5):
        for item in range(5):
            x = int((220 + item * 330 + local * 85) % 1780) + 50
            y = 820 + int(18 * math.sin(local * 2 + item))
            draw.arc((x - 55, y - 22, x + 55, y + 22), 195, 345, fill=colours[item % 4], width=7)
    elif index in (0, 1, 4, 6):
        for item in range(10):
            x = 120 + item * 180
            y = 100 + int(10 * math.sin(local * 1.8 + item))
            radius = 3 + int(4 * (0.5 + 0.5 * math.sin(local * 2.2 + item)))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=colours[item % 4])
    else:
        rng = random.Random(8272608)
        for item in range(28):
            x = (rng.randint(20, 1880) + int(local * (24 + item % 4 * 5))) % base.W
            y = (rng.randint(20, 1020) + int(local * (32 + item % 5 * 4))) % base.H
            draw.rounded_rectangle((x, y, x + 11, y + 7), 2, fill=colours[item % 4])


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    shots = plan()["shots"]
    if event["phase"] == "title":
        frame = moving_crop(assets[event["asset"]], event, t, 0).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, 0, base.W, base.H), fill=(12, 37, 71, 58))
        base.panel(draw, (250, 90, 1670, 355), radius=54, fill=(15, 70, 99, 225), outline=(255, 216, 75, 245), width=7)
        base.centered(draw, (960, 178), "NIKO'S NINJA SOCCER", base.F62, (255, 241, 130, 255), 3)
        base.centered(draw, (960, 280), "KINDNESS MATCH", base.F62, (255, 255, 255, 255), 3)
        return frame.convert("RGB")
    if event["phase"] == "end":
        frame = moving_crop(assets[event["asset"]], event, t, 7).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, 0, base.W, base.H), fill=(12, 37, 71, 54))
        base.panel(draw, (310, 770, 1610, 1005), radius=48, fill=(15, 70, 99, 226), outline=(255, 216, 75, 245), width=7)
        base.centered(draw, (960, 850), "PASS • MOVE • SHARE", base.F48, (255, 241, 130, 255), 2)
        base.centered(draw, (960, 935), "KINDNESS MAKES A TEAM!", base.F48, (255, 255, 255, 255), 2)
        return frame.convert("RGB")
    index = next(i for i, shot in enumerate(shots) if shot["id"] == event["phase"])
    frame = moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    action_overlay(frame, event, t, index)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "original-kindness-match-music.wav"
    rate = 48000
    notes = [293.66, 369.99, 440.0, 493.88, 440.0, 369.99, 329.63, 392.0]
    with wave.open(str(target), "wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate)
        chunk = bytearray()
        for sample_index in range(int(total * rate)):
            t = sample_index / rate
            note = notes[int(t / 0.75) % len(notes)]
            beat = t % 0.5
            kick = math.sin(2 * math.pi * 82 * t) * max(0.0, 1 - beat / 0.075) * 0.035
            clap_phase = (t + 0.25) % 0.5
            clap = (random.Random(sample_index // 24).uniform(-1, 1) if clap_phase < 0.035 else 0.0) * max(0.0, 1 - clap_phase / 0.035) * 0.012
            mallet = math.sin(2 * math.pi * note * t) * math.exp(-4.5 * (t % 0.75)) * 0.035
            pad = math.sin(2 * math.pi * 146.83 * t) * 0.009
            sample = max(-32767, min(32767, int((kick + clap + mallet + pad) * 32767)))
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                output.writeframesraw(chunk); chunk.clear()
        if chunk:
            output.writeframesraw(chunk)
    return target


def make_thumbnail() -> None:
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    source = Image.open(ASSET_DIR / "niko-soccer-finale-v1.png").convert("RGB")
    crop_width = round(source.height * 16 / 9)
    left = max(0, (source.width - crop_width) // 2)
    canvas = source.crop((left, 0, left + crop_width, source.height)).resize((1280, 720), Image.Resampling.LANCZOS).convert("RGBA")
    canvas = ImageEnhance.Color(canvas).enhance(1.08)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((55, 36, 1005, 160), 35, fill=(12, 72, 104, 228), outline=(255, 255, 255, 242), width=6)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
    text = "PASS, MOVE, SHARE!"
    draw.text((92, 63), text, font=font, fill=(255, 239, 105), stroke_width=4, stroke_fill=(16, 45, 78))
    badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    draw.rounded_rectangle((66, 650, 258, 700), 22, fill=(24, 24, 54, 230), outline=(255, 255, 255, 225), width=3)
    draw.text((88, 662), "TINY TALES", font=badge, fill="white")
    canvas.convert("RGB").save(THUMBNAIL, quality=90, optimize=True, progressive=True)
    if THUMBNAIL.stat().st_size > 2_000_000:
        canvas.convert("RGB").save(THUMBNAIL, quality=84, optimize=True, progressive=True)
    if THUMBNAIL.stat().st_size > 2_000_000:
        raise RuntimeError("Prepared thumbnail exceeds YouTube's 2 MB limit")


def quality(events: list[dict], total: float, assets: dict[str, Image.Image], shots: list[dict]) -> None:
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(OUTPUT),
    ], text=True))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], capture_output=True, text=True)
    transitions = [{"from_phase": a["phase"], "to_phase": b["phase"], "gap_seconds": b["start"] - a["end"]} for a, b in zip(events, events[1:])]
    story_events = events[1:-1]
    sync_rows = [{
        "shot_id": event["phase"], "asset": event["asset"], "visual_start": event["start"], "visual_end": event["end"],
        "voices": event["voices"], "all_voices_contained_by_visual": all(event["start"] <= voice["start"] <= voice["end"] <= event["end"] for voice in event["voices"]),
    } for event in story_events]
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(transitions, indent=2) + "\n", encoding="utf-8")
    (WORK / "narration-visual-sync-audit.json").write_text(json.dumps(sync_rows, indent=2) + "\n", encoding="utf-8")
    checks = {
        "size": OUTPUT.stat().st_size > 2_000_000,
        "duration": 75 <= float(probe["format"]["duration"]) <= 125 and abs(float(probe["format"]["duration"]) - total) < 0.3,
        "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H,
        "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "full_decode": decode.returncode == 0,
        "continuous_visual_timeline": all(abs(item["gap_seconds"]) < 0.000001 for item in transitions),
        "end_card_is_final_event_only": events[-1]["phase"] == "end" and all(event["phase"] != "end" for event in events[:-1]),
        "one_unique_artwork_per_voiced_beat": len({event["asset"] for event in story_events}) == len(story_events) == 8,
        "all_voices_contained_by_matching_visual": all(item["all_voices_contained_by_visual"] for item in sync_rows),
        "no_story_shot_over_14_seconds": all(event["end"] - event["start"] <= 14 for event in story_events),
        "eight_original_story_shots": len(assets) == 8,
        "voice_rotation": NARRATOR["name"] == "ryan-uk" and NIKO["name"] == "ana-us",
        "thumbnail_technical": THUMBNAIL.is_file() and THUMBNAIL.stat().st_size <= 2_000_000,
    }
    report = {
        "format": "sports-teamwork-story", "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]),
        "voice_profile": NARRATOR["name"], "character_voice_profile": NIKO["name"], "story_shots": 8,
        "new_image_generation_calls": 8, "true_rigged_3d_animation": False,
        "visual_method": "eight unique built-in-generated premium 3D-style soccer compositions with paper-cut action graphics, camera travel, and scene-specific motion overlays",
        "checks": checks, "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    general = Image.new("RGB", (960, math.ceil(len(events) / 4) * 135), "white")
    for index, event in enumerate(events):
        sample = event["start"] + min(1.8, (event["end"] - event["start"]) / 2)
        general.paste(frame_for(event, sample, assets).resize((240, 135), Image.Resampling.LANCZOS), ((index % 4) * 240, (index // 4) * 135))
    general.save(WORK / "quality-contact-sheet.png")
    boundary = []
    for current, following in zip(events, events[1:]):
        boundary.extend([(current, max(current["start"], current["end"] - 0.12)), (following, min(following["end"] - 0.01, following["start"] + 0.12))])
    sheet = Image.new("RGB", (1200, math.ceil(len(boundary) / 5) * 135), "white")
    for index, (event, sample) in enumerate(boundary):
        image = frame_for(event, sample, assets).resize((240, 135), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image); draw.rectangle((0, 0, 205, 19), fill="black")
        draw.text((3, 2), f"{sample:.1f}s {event['phase']}", font=base.font(12, True), fill="white")
        sheet.paste(image, ((index % 5) * 240, (index // 5) * 135))
    sheet.save(WORK / "transition-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(f"Niko quality gate failed: {report}")


def write_metadata(total: float) -> None:
    document = {
        "id": ITEM_ID, "title": "Niko's Ninja Soccer Kindness Match | Teamwork Story for Kids",
        "description": "Join Niko and new player Lila for a colourful soccer story about calm focus, gentle passes, trying again, and making sure everyone belongs. Children can balance, follow the footwork, cheer a first touch, trace a passing triangle, and celebrate a kindness-team goal.\n\nAn original Tiny Tales sports story supporting coordination, confidence, friendship, resilience, and teamwork for children ages 3 to 7.",
        "tags": ["soccer story for kids", "teamwork for kids", "kindness story", "football skills for children", "preschool movement", "friendship story", "Tiny Tales"],
        "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": False,
        "output": str(OUTPUT), "duration_seconds": total, "voice_profile": NARRATOR["name"], "character_voice_profile": NIKO["name"],
        "format_family": "sports-teamwork-story", "visual_system": "eight-unique-3d-style-pitch-compositions-with-paper-cut-ball-arcs-and-footwork-trails",
        "interaction_style": "balance-freezes-passing-cues-first-touch-cheer-and-team-finale",
        "quality_gate_passed": True, "full_decode_passed": True, "transition_audit_passed": True,
        "transition_contact_sheet_reviewed": False,
        "quality_report": f"automation/production-work/{ITEM_ID}/quality-report.json",
        "transition_audit": f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json",
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "PASS, MOVE, SHARE!",
        "thumbnail_reviewed": False, "quality_contact_sheet": f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png",
        "transition_contact_sheet": f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png",
        "new_image_generation_calls": 8, "true_rigged_3d_animation": False,
    }
    META.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True); OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shots = plan()["shots"]
    asyncio.run(make_voices(shots))
    events, voices, total = build_timeline(shots)
    assets = load_assets(shots)
    make_thumbnail()
    render_engine.WORK = WORK; render_engine.OUTPUT = OUTPUT; render_engine.frame_for = frame_for; render_engine.make_music = make_music
    render_engine.render(events, voices, total, assets)
    quality(events, total, assets, shots)
    write_metadata(total)
    print(json.dumps({"output": str(OUTPUT), "duration_seconds": total, "events": len(events)}, indent=2))


if __name__ == "__main__":
    main()
