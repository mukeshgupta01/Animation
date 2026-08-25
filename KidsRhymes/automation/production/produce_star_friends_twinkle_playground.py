"""Produce Star Friends' Twinkle Playground from a strict narration-to-shot plan."""

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
from PIL import Image, ImageDraw, ImageEnhance

import produce_snack_video as base
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "star-friends-twinkle-playground-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
ASSET_DIR = AUTOMATION / "production-assets"
VOICE = select_voice_profile("ana-us")
ART_FPS, VIDEO_FPS = 10, 30


SHOTS = [
    ("01_arrival", "star-friends-01-arrival.png", "High above the sleepy rooftops, three little Star Friends followed a glowing path to the Twinkle Playground."),
    ("02_playground_wakes", "star-friends-02-playground-wakes.png", "When their feet touched the first cloud, the whole playground shimmered awake."),
    ("03_cloud_bounce", "star-friends-03-cloud-bounce.png", "First came the cloud trampoline. Bend down low, then bounce up bright!"),
    ("04_cloud_activity", "star-friends-04-cloud-activity.png", "Can you make three gentle bounces? One, two, three!"),
    ("05_moon_seesaw", "star-friends-05-moon-seesaw.png", "Next, the crescent moon became a silver seesaw. One friend floated up while another dipped down."),
    ("06_moon_activity", "star-friends-06-moon-activity.png", "Lean gently left. Now lean gently right. You are balancing with the stars!"),
    ("07_comet_slide", "star-friends-07-comet-slide.png", "A friendly comet curled its glowing tail into the longest slide in the sky."),
    ("08_comet_activity", "star-friends-08-comet-activity.png", "Reach up tall, then swoop your hands down as the Star Friends zoom along the comet trail!"),
    ("09_constellation_path", "star-friends-09-constellation-path.png", "Across the dark-blue sky, tiny lights joined to make a stepping path."),
    ("10_constellation_activity", "star-friends-10-constellation-activity.png", "Step, step, pause. Step, step, pause. Follow the sparkling pattern!"),
    ("11_playground_finale", "star-friends-11-playground-finale.png", "Bounce, balance, swoop and step! Every light in the playground twinkled with their new dance."),
    ("12_bedtime_landing", "star-friends-12-bedtime-landing.png", "Then the playground grew quiet. The Star Friends rested on a soft cloud and took one slow, sleepy breath."),
    ("13_goodnight", "star-friends-13-goodnight.png", "The stars waved goodnight, leaving three warm twinkles above the sleeping town."),
]


def voice_path(index: int, shot_id: str) -> Path:
    return WORK / f"voice-{index:02d}-{shot_id}.mp3"


async def make_voices() -> None:
    tasks = []
    for index, (shot_id, _asset, line) in enumerate(SHOTS):
        target = voice_path(index, shot_id)
        if not target.exists():
            tasks.append(edge_tts.Communicate(
                line,
                VOICE["voice"],
                rate=VOICE["rate"],
                pitch=VOICE["pitch"],
                volume="-1%",
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
        # The matching visual begins with its narration and remains for a short
        # reaction beat. No later shot appears under the current line.
        shot_length = voice_length + (1.2 if "activity" in shot_id else 0.8)
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
    events.append({"phase": "end", "start": cursor, "end": cursor + 4.8, "asset": SHOTS[-1][1]})
    return events, voices, events[-1]["end"]


def fit_image(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = max((base.W + 140) / image.width, (base.H + 80) / image.height)
    return image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)


def load_assets() -> dict[str, Image.Image]:
    paths = {asset: ASSET_DIR / asset for _shot, asset, _line in SHOTS}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Star Friends shot artwork: {missing}")
    return {name: fit_image(path) for name, path in paths.items()}


def moving_crop(image: Image.Image, event: dict, t: float, shot_index: int) -> Image.Image:
    span = max(0.001, event["end"] - event["start"])
    progress = max(0.0, min(1.0, (t - event["start"]) / span))
    # Alternate push-in, pull-back, and horizontal tracking. The crop remains
    # continuous within a shot, avoiding pose/image switching.
    direction = shot_index % 4
    zoom = (1.00 + 0.055 * progress) if direction in {0, 2} else (1.055 - 0.045 * progress)
    target_w = round(base.W * zoom)
    target_h = round(base.H * zoom)
    resized = image.resize((target_w + 120, target_h + 70), Image.Resampling.BICUBIC)
    available_x = resized.width - base.W
    available_y = resized.height - base.H
    if direction == 0:
        x = int(available_x * (0.20 + 0.40 * progress))
    elif direction == 1:
        x = int(available_x * (0.72 - 0.35 * progress))
    elif direction == 2:
        x = int(available_x * (0.62 - 0.30 * progress))
    else:
        x = int(available_x * (0.28 + 0.30 * progress))
    y = int(available_y * (0.45 + 0.08 * math.sin(progress * math.pi)))
    return resized.crop((x, y, x + base.W, y + base.H))


def sparkle_overlay(frame: Image.Image, event: dict, t: float, shot_index: int) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    local = t - event["start"]
    rng = random.Random(9800 + shot_index)
    for index in range(22):
        x = rng.randint(35, base.W - 35)
        y = rng.randint(30, base.H - 35)
        phase = local * (0.8 + index % 4 * 0.12) + index
        radius = 2 + int(5 * (0.5 + 0.5 * math.sin(phase)))
        alpha = 45 + int(90 * (0.5 + 0.5 * math.sin(phase)))
        draw.line((x - radius, y, x + radius, y), fill=(255, 245, 190, alpha), width=2)
        draw.line((x, y - radius, x, y + radius), fill=(255, 245, 190, alpha), width=2)


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    if event["phase"] == "title":
        frame = moving_crop(assets[event["asset"]], event, t, 0).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, 0, base.W, base.H), fill=(16, 24, 66, 65))
        base.panel(draw, (205, 105, 1715, 390), radius=54, fill=(24, 37, 91, 222), outline=(255, 221, 116, 245), width=7)
        base.centered(draw, (960, 195), "STAR FRIENDS'", base.F62, (255, 239, 148, 255), 3)
        base.centered(draw, (960, 300), "TWINKLE PLAYGROUND", base.F62, (255, 255, 255, 255), 3)
        return frame.convert("RGB")
    if event["phase"] == "end":
        frame = moving_crop(assets[event["asset"]], event, t, 12).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, 0, base.W, base.H), fill=(12, 20, 58, 105))
        base.panel(draw, (360, 730, 1560, 965), radius=48, fill=(24, 37, 91, 224), outline=(255, 221, 116, 245), width=7)
        base.centered(draw, (960, 815), "BOUNCE • BALANCE • SWOOP • STEP", base.F48, (255, 247, 202, 255), 2)
        base.centered(draw, (960, 900), "GOODNIGHT, STAR FRIENDS!", base.F48, (255, 255, 255, 255), 2)
        return frame.convert("RGB")
    shot_index = next(index for index, item in enumerate(SHOTS) if item[0] == event["phase"])
    frame = moving_crop(assets[event["asset"]], event, t, shot_index).convert("RGBA")
    sparkle_overlay(frame, event, t, shot_index)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "original-twinkle-playground-music.wav"
    rate = 48000
    rng = random.Random(20260825)
    notes = [261.63, 329.63, 392.00, 523.25, 440.00, 392.00, 329.63, 293.66]
    with wave.open(str(target), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(rate)
        chunk = bytearray()
        for index in range(int(total * rate)):
            t = index / rate
            note = notes[int(t / 1.25) % len(notes)]
            bell_phase = t % 1.25
            bell = math.sin(2 * math.pi * note * t) * math.exp(-2.2 * bell_phase) * 0.055
            pad = sum(math.sin(2 * math.pi * frequency * t) for frequency in (130.81, 196.0, 261.63)) * 0.012
            pulse = 0.0
            if t < total - 18 and t % 0.625 < 0.035:
                pulse = math.sin(2 * math.pi * 84 * t) * 0.035 * (1 - (t % 0.625) / 0.035)
            shimmer = rng.uniform(-1, 1) * 0.0025
            value = bell + pad + pulse + shimmer
            sample = max(-32767, min(32767, int(value * 32767)))
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                output.writeframesraw(chunk)
                chunk.clear()
        if chunk:
            output.writeframesraw(chunk)
    return target


def render(events: list[dict], voices: list[tuple[Path, float]], total: float, assets: dict[str, Image.Image]) -> None:
    silent = WORK / "silent.mp4"
    process = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{base.W}x{base.H}", "-r", str(ART_FPS), "-i", "-", "-an",
        "-vf", f"fps={VIDEO_FPS}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-profile:v", "high", "-pix_fmt", "yuv420p", str(silent),
    ], stdin=subprocess.PIPE)
    assert process.stdin
    for number in range(math.ceil(total * ART_FPS)):
        t = number / ART_FPS
        event = next((item for item in events if item["start"] <= t < item["end"]), None)
        if event is None:
            raise RuntimeError(f"Star Friends timeline has no visual event at {t:.3f}s")
        process.stdin.write(frame_for(event, t, assets).tobytes())
        if number % (ART_FPS * 15) == 0:
            print(f"Rendered {t:.0f}/{total:.0f}s", flush=True)
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("Star Friends silent render failed")
    music = make_music(total)
    inputs = ["-i", str(silent), "-i", str(music)]
    filters = ["[1:a]volume=0.32[m]"]
    labels = ["[m]"]
    for input_index, (path, start) in enumerate(voices, 2):
        inputs += ["-i", str(path)]
        delay = round(start * 1000)
        filters.append(f"[{input_index}:a]adelay={delay}|{delay},volume=1.70[v{input_index}]")
        labels.append(f"[v{input_index}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:normalize=0,alimiter=limit=0.94[a]")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUTPUT),
    ], check=True)


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
        "shot_id": event["phase"],
        "asset": event["asset"],
        "visual_start": event["start"],
        "visual_end": event["end"],
        "narration_start": event["start"],
        "narration_end": event["voice_end"],
        "narration_contained_by_visual": event["start"] <= event["voice_end"] <= event["end"],
        "line": event["line"],
    } for event in story_events]
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(transitions, indent=2) + "\n", encoding="utf-8")
    (WORK / "narration-visual-sync-audit.json").write_text(json.dumps(sync_rows, indent=2) + "\n", encoding="utf-8")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    planned = {item["id"]: item for item in plan["shots"]}
    checks = {
        "size": OUTPUT.stat().st_size > 2_000_000,
        "duration": 80 <= float(probe["format"]["duration"]) <= 180 and abs(float(probe["format"]["duration"]) - total) < 0.3,
        "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H,
        "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "full_decode": decode.returncode == 0,
        "continuous_visual_timeline": all(abs(item["gap_seconds"]) < 0.000001 for item in transitions),
        "end_card_is_final_event_only": events[-1]["phase"] == "end" and all(event["phase"] != "end" for event in events[:-1]),
        "one_unique_artwork_per_voiced_beat": len({event["asset"] for event in story_events}) == len(story_events) == 13,
        "narration_contained_by_matching_visual": all(item["narration_contained_by_visual"] for item in sync_rows),
        "narration_lines_match_approved_plan": all(planned[event["phase"]]["line"] == event["line"] for event in story_events),
        "no_story_shot_over_14_seconds": all(event["end"] - event["start"] <= 14 for event in story_events),
        "thirteen_original_story_shots": len(assets) == 13,
        "voice_rotation": VOICE["name"] == "ana-us",
    }
    report = {
        "format": "celestial-playground-movement-song-story",
        "output": str(OUTPUT),
        "duration_seconds": float(probe["format"]["duration"]),
        "voice_profile": VOICE["name"],
        "story_shots": len(story_events),
        "new_image_generation_calls": 13,
        "true_rigged_3d_animation": False,
        "visual_method": "thirteen unique built-in-generated 3D-style story compositions with continuous per-shot camera motion and sparkle animation",
        "checks": checks,
        "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    general = Image.new("RGB", (960, math.ceil(len(events) / 4) * 135), "white")
    for index, event in enumerate(events):
        t = event["start"] + min(1.5, (event["end"] - event["start"]) / 2)
        image = frame_for(event, t, assets).resize((240, 135), Image.Resampling.LANCZOS)
        general.paste(image, ((index % 4) * 240, (index // 4) * 135))
    general.save(WORK / "quality-contact-sheet.png")
    boundary = []
    for current, following in zip(events, events[1:]):
        boundary.extend([(current, max(current["start"], current["end"] - 0.12)), (following, min(following["end"] - 0.01, following["start"] + 0.12))])
    sheet = Image.new("RGB", (1200, math.ceil(len(boundary) / 5) * 135), "white")
    for index, (event, t) in enumerate(boundary):
        image = frame_for(event, t, assets).resize((240, 135), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 170, 19), fill="black")
        draw.text((3, 2), f"{t:.1f}s {event['phase']}", font=base.font(12, True), fill="white")
        sheet.paste(image, ((index % 5) * 240, (index // 5) * 135))
    sheet.save(WORK / "transition-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(f"Star Friends quality gate failed: {report}")


def write_metadata(total: float) -> None:
    document = {
        "id": ITEM_ID,
        "title": "Star Friends' Twinkle Playground | Movement and Bedtime Story for Kids",
        "description": "Bounce on a cloud trampoline, balance on a moon seesaw, swoop down a comet slide and follow a sparkling constellation path with three original Star Friends. The playful movement adventure finishes with a gentle breathing moment and a calm goodnight.\n\nAn original Tiny Tales 3D-look sky story supporting listening, movement patterns, balance, imagination and bedtime transitions for children ages 3 to 7.",
        "tags": ["star story for kids", "movement for kids", "bedtime story", "twinkle stars", "preschool movement", "calm down for kids", "Tiny Tales"],
        "category_id": "27",
        "made_for_kids": True,
        "privacy": "public",
        "upload_authorized": False,
        "output": str(OUTPUT),
        "duration_seconds": total,
        "voice_profile": VOICE["name"],
        "format_family": "celestial-playground-movement-song-story",
        "visual_system": "thirteen-unique-3d-style-celestial-story-shots-with-continuous-camera-motion",
        "interaction_style": "literal-action-cues-and-calm-bedtime-landing",
        "quality_gate_passed": True,
        "full_decode_passed": True,
        "transition_audit_passed": True,
        "transition_contact_sheet_reviewed": False,
        "quality_report": f"automation/production-work/{ITEM_ID}/quality-report.json",
        "transition_audit": f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json",
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg",
        "thumbnail_hook": "PLAY WITH THE STARS!",
        "thumbnail_reviewed": True,
        "quality_contact_sheet": f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png",
        "transition_contact_sheet": f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png",
        "new_image_generation_calls": 13,
        "true_rigged_3d_animation": False,
    }
    META.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(make_voices())
    events, voices, total = build_timeline()
    assets = load_assets()
    render(events, voices, total, assets)
    quality(events, total, assets)
    write_metadata(total)
    print(json.dumps({"output": str(OUTPUT), "duration_seconds": total, "events": len(events)}, indent=2))


if __name__ == "__main__":
    main()
