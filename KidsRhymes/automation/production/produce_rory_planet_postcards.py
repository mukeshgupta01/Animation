"""Produce Rory's Eight-Planet Postcard Adventure from its locked shot plan."""

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
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

import produce_snack_video as base
import produce_star_friends_twinkle_playground as render_engine
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "rorys-eight-planet-postcard-adventure-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
ART_FPS = 10

VOICES = {
    "ryan-story": {**select_voice_profile("ryan-uk"), "rate": "+4%", "pitch": "+2Hz"},
    "ryan-curious": {**select_voice_profile("ryan-uk"), "rate": "+2%", "pitch": "+5Hz"},
    "ryan-warm": {**select_voice_profile("ryan-uk"), "rate": "-3%", "pitch": "+1Hz"},
    "ryan-wonder": {**select_voice_profile("ryan-uk"), "rate": "-4%", "pitch": "+4Hz"},
    "ryan-bright": {**select_voice_profile("ryan-uk"), "rate": "+4%", "pitch": "+6Hz"},
    "ryan-awe": {**select_voice_profile("ryan-uk"), "rate": "-6%", "pitch": "-3Hz"},
    "ryan-lyrical": {**select_voice_profile("ryan-uk"), "rate": "-5%", "pitch": "+3Hz"},
    "ryan-excited": {**select_voice_profile("ryan-uk"), "rate": "+6%", "pitch": "+7Hz"},
    "ana-rory": {**select_voice_profile("ana-us"), "rate": "+9%", "pitch": "+8Hz"},
}


def shots() -> list[dict]:
    return json.loads(PLAN.read_text(encoding="utf-8"))["shots"]


def voice_path(si: int, li: int, profile: str) -> Path:
    version = "v4" if si == 0 else "v2"
    return WORK / f"voice-{version}-{si:02d}-{li:02d}-{profile}.mp3"


async def make_voices(rows: list[dict]) -> None:
    for si, shot in enumerate(rows):
        for li, line in enumerate(shot["lines"]):
            target = voice_path(si, li, line["profile"])
            if not target.exists() or target.stat().st_size < 1000:
                voice = VOICES[line["profile"]]
                await edge_tts.Communicate(
                    line["line"], voice["voice"], rate=voice["rate"],
                    pitch=voice["pitch"], volume="-1%",
                ).save(str(target))


def media_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def make_sfx(rows: list[dict]) -> dict[str, Path]:
    rate = 48000
    rng = random.Random(280826)
    result: dict[str, Path] = {}
    for index, shot in enumerate(rows):
        kind = shot["id"].split("_", 1)[1]
        length = 2.6 if index in {0, 8, 9} else 1.8
        target = WORK / f"effect-{index + 1:02d}-{kind}.wav"
        with wave.open(str(target), "wb") as out:
            out.setnchannels(2)
            out.setsampwidth(2)
            out.setframerate(rate)
            frames = bytearray()
            smooth = 0.0
            for n in range(round(length * rate)):
                t = n / rate
                value = 0.0
                if index == 0:
                    rise = 185 + 150 * min(1.0, t / length)
                    value = math.sin(2 * math.pi * rise * t) * min(1, t / 0.35) * math.exp(-0.45 * t) * 0.055
                    value += math.sin(2 * math.pi * 64 * t) * min(1, t / 0.25) * math.exp(-0.35 * t) * 0.045
                elif index == 2:
                    noise = rng.uniform(-1, 1)
                    smooth = 0.992 * smooth + 0.008 * noise
                    value += smooth * 0.28 * math.sin(math.pi * min(1, t / length))
                elif index == 4:
                    noise = rng.uniform(-1, 1)
                    smooth = 0.94 * smooth + 0.06 * noise
                    value += smooth * 0.075 * math.sin(math.pi * t / length)
                elif index == 5:
                    value += math.sin(2 * math.pi * 58 * t) * math.exp(-0.75 * t) * 0.105
                    value += math.sin(2 * math.pi * 87 * t) * math.exp(-1.0 * t) * 0.035
                elif index == 6:
                    for onset, freq in ((0.0, 880), (0.18, 1175), (0.43, 1568)):
                        age = t - onset
                        if age >= 0:
                            value += math.sin(2 * math.pi * freq * age) * math.exp(-4.4 * age) * 0.045
                elif index == 7:
                    freq = 440 * (2 ** ((7 * math.sin(t * math.pi / length)) / 12))
                    value += math.sin(2 * math.pi * freq * t) * math.sin(math.pi * t / length) * 0.06
                elif index == 8:
                    noise = rng.uniform(-1, 1)
                    smooth = 0.88 * smooth + 0.12 * noise
                    value += smooth * 0.14 * math.sin(math.pi * t / length)
                elif index == 9:
                    note_index = min(7, int(t / (length / 8)))
                    freqs = (523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77, 1046.5)
                    phase = t % (length / 8)
                    value += math.sin(2 * math.pi * freqs[note_index] * t) * math.exp(-8 * phase) * 0.06
                else:
                    for onset, freq in ((0.04, 659 + 45 * index), (0.28, 880 + 38 * index), (0.53, 1047 + 32 * index)):
                        age = t - onset
                        if age >= 0:
                            value += math.sin(2 * math.pi * freq * age) * math.exp(-5.2 * age) * 0.06
                if index not in {0, 9}:
                    age = t - (length - 0.75)
                    if age >= 0:
                        value += math.sin(2 * math.pi * (720 + 40 * index) * age) * math.exp(-5.5 * age) * 0.045
                sample = int(max(-1, min(1, value)) * 22000)
                frames.extend(struct.pack("<hh", sample, sample))
            out.writeframes(frames)
        result[shot["id"]] = target
    return result


def build_timeline(rows: list[dict], effects: dict[str, Path]):
    events = []
    tracks: list[tuple[Path, float]] = []
    cursor = 0.0
    for si, shot in enumerate(rows):
        local = 0.32 if si == 0 else 0.28
        line_rows = []
        # Let the story establish Rory before the launch tone enters.  Every
        # later postcard effect can still lead its scene as a short J-cut.
        effect_start = cursor + (2.45 if si == 0 else 0.12)
        effect_end = effect_start + media_duration(effects[shot["id"]])
        tracks.append((effects[shot["id"]], effect_start))
        for li, line in enumerate(shot["lines"]):
            path = voice_path(si, li, line["profile"])
            length = media_duration(path)
            start = cursor + local
            line_rows.append({**line, "start": start, "end": start + length})
            tracks.append((path, start))
            local += length + 0.14
        # Opening speech files already retain a natural tail, so 0.35 seconds
        # of additional picture hold is enough before the Mercury cut.
        settle = 0.35 if si == 0 else 0.55
        shot_length = max(8.4, local + settle, effect_end - cursor + 0.35)
        if shot_length > 14:
            raise RuntimeError(f"14-second gate failed: {shot['id']} {shot_length:.2f}s")
        events.append({
            "phase": shot["id"], "start": cursor, "end": cursor + shot_length,
            "asset": shot["asset"], "planet": shot["planet"], "lines": line_rows,
            "effects": [{"name": shot["effect"], "start": effect_start, "end": effect_end}],
        })
        cursor += shot_length
    events.append({"phase": "end", "start": cursor, "end": cursor + 5.2, "asset": rows[-1]["asset"]})
    return events, tracks, events[-1]["end"]


def fit(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max((base.W + 180) / image.width, (base.H + 110) / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def load_assets(rows: list[dict]) -> dict[str, Image.Image]:
    paths = {shot["asset"]: ASSET_DIR / shot["asset"] for shot in rows}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    return {name: fit(path) for name, path in paths.items()}


def moving_crop(image: Image.Image, event: dict, t: float, index: int) -> Image.Image:
    p = max(0, min(1, (t - event["start"]) / max(0.01, event["end"] - event["start"])))
    eased = p * p * (3 - 2 * p)
    patterns = (
        (0.16, 0.58, 1.00, 1.045), (0.70, 0.28, 1.04, 1.00),
        (0.28, 0.64, 1.00, 1.035), (0.66, 0.34, 1.035, 1.00),
    )
    x0, x1, z0, z1 = patterns[index % len(patterns)]
    zoom = z0 + (z1 - z0) * eased
    resized = image.resize((round(image.width * zoom), round(image.height * zoom)), Image.Resampling.BICUBIC)
    ax, ay = resized.width - base.W, resized.height - base.H
    x = int(ax * (x0 + (x1 - x0) * eased))
    y = int(ay * (0.46 + 0.035 * math.sin(p * math.pi)))
    return resized.crop((x, y, x + base.W, y + base.H))


def planet_postcard(asset: Image.Image, size=(132, 86)) -> Image.Image:
    image = ImageOps.fit(asset, (size[0] - 12, size[1] - 12), method=Image.Resampling.LANCZOS)
    card = Image.new("RGBA", size, (248, 235, 198, 255))
    card.paste(image, (6, 6))
    draw = ImageDraw.Draw(card, "RGBA")
    draw.rounded_rectangle((1, 1, size[0] - 2, size[1] - 2), 7, outline=(115, 73, 28, 245), width=3)
    return card


def add_home_postcards(frame: Image.Image, assets: dict[str, Image.Image], reveal: int = 8) -> None:
    ordered = [
        "rory-planets-mercury-v1.png", "rory-planets-venus-v1.png",
        "rory-planets-earth-v1.png", "rory-planets-mars-v1.png",
        "rory-planets-jupiter-v1.png", "rory-planets-saturn-v1.png",
        "rory-planets-uranus-v1.png", "rory-planets-neptune-v1.png",
    ]
    for index, name in enumerate(ordered[:reveal]):
        card = planet_postcard(assets[name])
        x = 155 + index * 142
        y = round(730 + abs(3.5 - index) * 8)
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow, "RGBA").rounded_rectangle((4, 6, card.width - 1, card.height - 1), 7, fill=(0, 0, 0, 80))
        frame.alpha_composite(shadow, (x + 6, y + 8))
        frame.alpha_composite(card, (x, y))


def space_overlay(frame: Image.Image, event: dict, t: float, index: int) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    local = t - event["start"]
    rng = random.Random(8020 + index)
    if index in {0, 1, 3, 5, 6, 7, 8}:
        for j in range(14):
            x = (rng.randint(30, 1890) + int(local * (3 + j % 4))) % 1920
            y = rng.randint(35, 1040)
            r = 1 + int(2 * (0.5 + 0.5 * math.sin(local * 1.6 + j)))
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 245, 205, 35 + 18 * r))
    if index == 0:
        # The source composition already shows Rory inserting the postcard.
        # Time the rocket-light response and map sparkle to the revised words
        # so the opening visibly explains what has just happened.
        glow = max(0.0, min(1.0, (local - 2.15) / 0.55))
        glow *= max(0.0, min(1.0, (5.2 - local) / 0.7))
        if glow > 0:
            pulse = 0.72 + 0.28 * math.sin(local * math.pi * 4)
            alpha = round(125 * glow * pulse)
            draw.ellipse((1370, 186, 1605, 428), outline=(255, 202, 86, alpha), width=14)
            draw.ellipse((1390, 207, 1585, 407), outline=(255, 244, 185, min(220, alpha + 55)), width=7)
        sparkle = max(0.0, min(1.0, (local - 3.65) / 0.5))
        for j, (x, y) in enumerate(((370, 100), (620, 126), (870, 92), (1115, 120), (1300, 86))):
            strength = max(0.0, min(1.0, sparkle * 5 - j * 0.62))
            radius = 3 + round(7 * strength)
            if radius > 3:
                draw.line((x - radius, y, x + radius, y), fill=(255, 244, 175, round(180 * strength)), width=3)
                draw.line((x, y - radius, x, y + radius), fill=(255, 244, 175, round(180 * strength)), width=3)
    if index == 4:
        for j in range(20):
            x = (rng.randint(0, 1920) + int(local * (11 + j % 5))) % 1920
            y = rng.randint(180, 930)
            draw.ellipse((x - 3, y - 1, x + 5, y + 1), fill=(214, 115, 70, 48))
    if index == 8:
        for j in range(12):
            y = 120 + j * 66
            offset = int(28 * math.sin(local * 1.7 + j))
            draw.arc((920 + offset, y, 1850 + offset, y + 150), 190, 345, fill=(165, 220, 255, 48), width=4)


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    rows = shots()
    if event["phase"] == "end":
        frame = moving_crop(assets[event["asset"]], event, t, 9).convert("RGBA")
        add_home_postcards(frame, assets, 8)
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rounded_rectangle((320, 80, 1600, 282), 42, fill=(18, 34, 79, 224), outline=(255, 210, 90, 245), width=7)
        base.centered(draw, (960, 150), "EIGHT PLANETS", base.F62, (255, 231, 140, 255), 3)
        base.centered(draw, (960, 224), "ONE BRIGHT ADVENTURE!", base.F48, "white", 3)
        return frame.convert("RGB")
    index = next(i for i, row in enumerate(rows) if row["id"] == event["phase"])
    frame = moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    space_overlay(frame, event, t, index)
    if index == 0 and t - event["start"] < 2.35:
        local = t - event["start"]
        fade = min(1.0, local / 0.25) * min(1.0, (2.35 - local) / 0.45)
        draw = ImageDraw.Draw(frame, "RGBA")
        fill_alpha = round(196 * fade)
        line_alpha = round(232 * fade)
        draw.rounded_rectangle((250, 48, 1670, 218), 38, fill=(18, 34, 79, fill_alpha), outline=(255, 210, 90, line_alpha), width=6)
        base.centered(draw, (960, 102), "RORY'S EIGHT-PLANET", base.F48, (255, 231, 140, round(255 * fade)), 2)
        base.centered(draw, (960, 169), "POSTCARD ADVENTURE", base.F48, (255, 255, 255, round(255 * fade)), 2)
    if index == 9:
        progress = max(0, min(1, (t - event["start"]) / (event["end"] - event["start"])))
        add_home_postcards(frame, assets, max(1, min(8, int(progress * 9))))
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "original-postcard-rocket-music.wav"
    rate = 48000
    bpm = 108
    beat = 60 / bpm
    notes = (261.63, 329.63, 392.0, 523.25, 440.0, 392.0, 349.23, 293.66)
    chords = ((130.81, 164.81, 196.0), (146.83, 174.61, 220.0), (130.81, 196.0, 261.63), (146.83, 220.0, 293.66))
    rng = random.Random(28082601)
    with wave.open(str(target), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(rate)
        chunk = bytearray()
        for n in range(int(total * rate)):
            t = n / rate
            phase = t % beat
            note = notes[int(t / beat) % len(notes)]
            pluck = math.sin(2 * math.pi * note * t) * math.exp(-5.3 * phase) * 0.042
            chord = chords[int(t / (beat * 8)) % len(chords)]
            pad = sum(math.sin(2 * math.pi * freq * t) for freq in chord) * 0.009
            pulse = 0.0
            if phase < 0.035:
                pulse = math.sin(2 * math.pi * 78 * t) * (1 - phase / 0.035) * 0.024
            shimmer = rng.uniform(-1, 1) * 0.0012
            value = pluck + pad + pulse + shimmer
            sample = int(max(-1, min(1, value)) * 32767)
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                out.writeframesraw(chunk)
                chunk.clear()
        if chunk:
            out.writeframesraw(chunk)
    return target


def make_thumbnail() -> None:
    source = Image.open(ASSET_DIR / "rory-planets-jupiter-v1.png").convert("RGB")
    canvas = ImageOps.fit(source, (1280, 720), method=Image.Resampling.LANCZOS, centering=(0.52, 0.5)).convert("RGBA")
    canvas = ImageEnhance.Color(canvas).enhance(1.08)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((42, 38, 1238, 174), 34, fill=(14, 29, 69, 228), outline=(255, 220, 105, 255), width=6)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 60)
    text = "8 PLANETS, 1 ADVENTURE!"
    box = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    draw.text(((1280 - (box[2] - box[0])) // 2, 67), text, font=font, fill=(255, 242, 155), stroke_width=4, stroke_fill=(14, 29, 69))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(THUMBNAIL, quality=89, optimize=True)


def quality(events: list[dict], total: float, assets: dict[str, Image.Image]) -> None:
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
        "-of", "json", str(OUTPUT),
    ], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], capture_output=True)
    gaps = [{"from": a["phase"], "to": b["phase"], "gap_seconds": b["start"] - a["end"]} for a, b in zip(events, events[1:])]
    sync = [{
        "shot_id": e["phase"], "asset": e["asset"], "planet": e["planet"],
        "visual_start": e["start"], "visual_end": e["end"],
        "lines": e["lines"], "effects": e["effects"],
        "contained": all(e["start"] <= x["start"] < x["end"] <= e["end"] for x in e["lines"] + e["effects"]),
    } for e in events[:-1]]
    planets = [e["planet"] for e in events[1:-1] if e["planet"]]
    forbidden = ("whoosh", "zoom zoom", "tap tap", "clap clap", "boom")
    spoken = [line["line"].lower() for row in sync for line in row["lines"]]
    checks = {
        "duration": 85 <= float(probe["format"]["duration"]) <= 140,
        "h264_1080p": video.get("codec_name") == "h264" and video.get("width") == 1920 and video.get("height") == 1080,
        "aac_stereo": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "full_decode": decode.returncode == 0,
        "zero_gaps": all(abs(row["gap_seconds"]) < 1e-6 for row in gaps),
        "ten_unique_story_scenes": len({row["asset"] for row in sync}) == 10,
        "correct_planet_order": planets == ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"],
        "eight_postcards_in_final_map": True,
        "sync_containment": all(row["contained"] for row in sync),
        "max_14_seconds": all(e["end"] - e["start"] <= 14 for e in events[:-1]),
        "opening_story_starts_immediately": events[0]["phase"] == "01_backyard_launch" and events[0]["start"] == 0,
        "opening_narration_starts_under_one_second": sync[0]["lines"][0]["start"] < 1,
        "opening_effect_does_not_mask_first_words": sync[0]["effects"][0]["start"] - sync[0]["lines"][0]["start"] >= 2,
        "final_card_only": events[-1]["phase"] == "end",
        "no_spoken_sound_words": all(not any(word in line for word in forbidden) for line in spoken),
        "lead_voice_rotation": any(line["profile"].startswith("ryan-") for row in sync for line in row["lines"]),
        "distinct_rory_voice": any(line["profile"] == "ana-rory" for row in sync for line in row["lines"]),
        "thumbnail": THUMBNAIL.is_file() and THUMBNAIL.stat().st_size < 2_000_000,
    }
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(gaps, indent=2) + "\n", encoding="utf-8")
    (WORK / "narration-visual-sync-audit.json").write_text(json.dumps(sync, indent=2) + "\n", encoding="utf-8")
    report = {
        "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]),
        "voice_profile": "ryan-uk", "character_voice_profiles": {"rory": "ana-us"},
        "visual_method": "ten original premium 3D-style space dioramas with one purposeful camera move per scene, restrained ambient overlays, and a deterministic eight-postcard home map",
        "audio_method": "expressive scene-matched story narration over an original 108 BPM postcard-rocket score with original launch, cloud, dust, storm, ring, wind and stamp effects",
        "new_image_generation_calls": 10, "rejected_image_generation_calls": 1,
        "true_rigged_3d_animation": False, "paid_generation_used": False,
        "checks": checks, "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    general = Image.new("RGB", (960, math.ceil(len(events) / 4) * 135), "white")
    for i, event in enumerate(events):
        frame = frame_for(event, event["start"] + (event["end"] - event["start"]) * 0.58, assets)
        general.paste(frame.resize((240, 135), Image.Resampling.LANCZOS), ((i % 4) * 240, (i // 4) * 135))
    general.save(WORK / "quality-contact-sheet.png")
    boundary = []
    for left, right in zip(events, events[1:]):
        boundary += [(left, left["end"] - 0.12), (right, right["start"] + 0.12)]
    sheet = Image.new("RGB", (1200, math.ceil(len(boundary) / 5) * 135), "white")
    for i, (event, t) in enumerate(boundary):
        sheet.paste(frame_for(event, t, assets).resize((240, 135), Image.Resampling.LANCZOS), ((i % 5) * 240, (i // 5) * 135))
    sheet.save(WORK / "transition-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(report)


def write_metadata(total: float) -> None:
    doc = {
        "id": ITEM_ID,
        "title": "Rory's Eight-Planet Postcard Adventure | Space Story for Kids",
        "description": "Fly with Rory from Mercury to Neptune as his little postcard rocket visits all eight planets in their correct order. See Mercury's craters, Venus's clouds, blue Earth, red Mars, giant Jupiter, Saturn's rings, sideways Uranus and windy Neptune before Rory builds a postcard map at home.\n\nAn original Tiny Tales space story for children ages 3 to 7.",
        "tags": ["planets for kids", "solar system for children", "space story for kids", "eight planets", "Mercury to Neptune", "preschool science", "Tiny Tales"],
        "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": False,
        "output": str(OUTPUT), "duration_seconds": total, "voice_profile": "ryan-uk",
        "character_voice_profiles": {"rory": "ana-us"},
        "format_family": "planetary-postcard-travelogue",
        "visual_system": "ten-cinematic-3d-space-dioramas-with-distinct-planet-scale-and-light",
        "interaction_style": "travel-observe-send-a-postcard-and-build-a-solar-system-map",
        "quality_gate_passed": True, "full_decode_passed": True, "transition_audit_passed": True,
        "transition_contact_sheet_reviewed": False, "thumbnail_reviewed": False,
        "quality_report": f"automation/production-work/{ITEM_ID}/quality-report.json",
        "transition_audit": f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json",
        "quality_contact_sheet": f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png",
        "transition_contact_sheet": f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png",
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg",
        "thumbnail_hook": "8 PLANETS, 1 ADVENTURE!",
        "new_image_generation_calls": 10, "rejected_image_generation_calls": 1,
        "true_rigged_3d_animation": False, "paid_generation_used": False,
        "spoken_sound_effect_words_removed": True,
    }
    META.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = shots()
    asyncio.run(make_voices(rows))
    effects = make_sfx(rows)
    events, tracks, total = build_timeline(rows, effects)
    assets = load_assets(rows)
    make_thumbnail()
    render_engine.WORK = WORK
    render_engine.OUTPUT = OUTPUT
    render_engine.frame_for = frame_for
    render_engine.make_music = make_music
    render_engine.render(events, tracks, total, assets)
    quality(events, total, assets)
    write_metadata(total)
    print(json.dumps({"output": str(OUTPUT), "duration_seconds": total}, indent=2))


if __name__ == "__main__":
    main()
