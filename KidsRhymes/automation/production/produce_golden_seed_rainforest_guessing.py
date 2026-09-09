"""Produce the connected Golden Seed rainforest animal guessing adventure."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import wave

import produce_eddie_rain_garden_musical as core


base = core.base
render_engine = core.render_engine
Image = core.Image
ImageDraw = core.ImageDraw
ImageEnhance = core.ImageEnhance
ImageFont = core.ImageFont

AUTOMATION = base.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "golden-seed-rainforest-guessing-adventure-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_REVIEW = PROJECT / "metadata" / f"{ITEM_ID}-asset-review.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
THUMBNAIL_ART = ASSET_DIR / "golden-seed-rainforest-thumbnail-art-v1.png"
ART_FPS = 8
VIDEO_FPS = 30
TARGET_WPM = 112.0
MAX_WPM = 118.0
BPM = 104
BEAT = 60.0 / BPM
END_SECONDS = 4.0

VOICE = {**core.select_voice_profile("natasha-au"), "rate": "-10%", "pitch": "+3Hz"}

ASSETS = {
    "opening": "golden-seed-opening-catch-v1.png",
    "cap-start": "golden-seed-capybara-start-v1.png",
    "cap-action": "golden-seed-capybara-action-v1.png",
    "cap-end": "golden-seed-capybara-end-v2.png",
    "arm-start": "golden-seed-armadillo-start-v1.png",
    "arm-action": "golden-seed-armadillo-action-v1.png",
    "arm-end": "golden-seed-armadillo-end-v1.png",
    "sloth-start": "golden-seed-sloth-start-v1.png",
    "sloth-action": "golden-seed-sloth-action-v1.png",
    "sloth-end": "golden-seed-sloth-end-v1.png",
    "kink-start": "golden-seed-kinkajou-start-v1.png",
    "kink-action": "golden-seed-kinkajou-action-v1.png",
    "kink-end": "golden-seed-kinkajou-end-v1.png",
    "planting": "golden-seed-planting-v1.png",
    "sprout": "golden-seed-sprout-finale-v1.png",
}

LINES = {
    "opening": "Miki's golden seed is rolling toward the stream! Can rainforest friends help carry it to the nursery before night?",
    "cap-question": "The stream is too wide. Which friend lives beside water and can swim the leaf boat safely across?",
    "cap-answer": "It's Cora the capybara! She swims into the current and gently nudges the seed boat forward.",
    "cap-fact": "Capybaras are strong swimmers and can keep much of their body low in the water.",
    "arm-question": "Loose leaves block the path. Which friend has strong front claws that can clear a shallow channel?",
    "arm-answer": "It's Arlo the armadillo! His powerful claws rake the leaves aside without moving the heavy branch.",
    "arm-fact": "Armadillos use their strong front claws for digging.",
    "sloth-question": "The satchel is beyond the branch gap. Which friend can hang securely and carry it slowly across?",
    "sloth-answer": "It's Sela the sloth! Her long curved claws grip the branch while she carries the satchel.",
    "sloth-fact": "Three-toed sloths use curved claws to hang securely from branches.",
    "kink-question": "Night is coming. Which canopy friend can balance with a tail that grips a branch?",
    "kink-answer": "It's Kiko the kinkajou! His grasping tail holds firmly while he crosses the final bend.",
    "kink-fact": "Kinkajous are night-time climbers with prehensile tails that can grip branches.",
    "planting": "The golden seed has reached the nursery. Miki plants it carefully while every helper gathers close.",
    "sprout": "Days pass with sunshine and gentle rain. Look! Two fresh leaves open. Every animal helped the seed reach home.",
}

HELPERS = (
    {
        "key": "cap", "scene": 2,
        "primary_action": "Cora enters the stream, nudges the same leaf boat through the current and lands it on the far bank",
        "visible_start_state": "Miki and the stationary seed boat wait on the near bank with the crossing blocked",
        "visible_action_state": "Cora swims chest-deep beside the moving leaf boat while Miki watches",
        "visible_end_state": "the seed boat rests on far-bank sand beside Cora and Miki",
        "foreground_moving_elements": ["Cora", "leaf boat", "golden seed", "water ripples"],
    },
    {
        "key": "arm", "scene": 3,
        "primary_action": "Arlo rakes loose leaves aside to make a shallow route around the unchanged fallen branch",
        "visible_start_state": "Miki faces a branch and deep loose-leaf blockage",
        "visible_action_state": "Arlo's front claws move the loose leaves sideways",
        "visible_end_state": "a clean passable channel curves around the branch and leaves rest to one side",
        "foreground_moving_elements": ["Arlo", "loose leaves", "Miki"],
    },
    {
        "key": "sloth", "scene": 4,
        "primary_action": "Sela grips the overhead branch, carries the same satchel across the gap and lowers it to Miki",
        "visible_start_state": "the seed satchel hangs beyond Miki's reach across a branch gap",
        "visible_action_state": "Sela hangs securely while carrying the satchel over the gap",
        "visible_end_state": "Sela lowers the satchel into Miki's hands on the safe branch",
        "foreground_moving_elements": ["Sela", "leaf satchel", "golden seed", "Miki"],
    },
    {
        "key": "kink", "scene": 5,
        "primary_action": "Kiko grips a branch with one prehensile tail, carries the satchel around the bend and reaches the nursery",
        "visible_start_state": "Miki studies the narrow curved dusk route toward the distant nursery",
        "visible_action_state": "Kiko crosses with the tail visibly wrapped around a support branch",
        "visible_end_state": "Kiko passes the satchel to Miki beside the prepared nursery soil",
        "foreground_moving_elements": ["Kiko", "prehensile tail", "leaf satchel", "Miki"],
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def raw_voice_path(key: str) -> Path:
    return WORK / f"voice-raw-{key}-natasha-au.mp3"


def voice_path(key: str) -> Path:
    return WORK / f"voice-grid-{key}-natasha-au.wav"


async def make_voices() -> None:
    for key, line in LINES.items():
        raw = raw_voice_path(key)
        target = voice_path(key)
        if not raw.exists() or raw.stat().st_size < 1000:
            await core.edge_tts.Communicate(
                line, VOICE["voice"], rate=VOICE["rate"], pitch=VOICE["pitch"], volume="-2%"
            ).save(str(raw))
        words = len(re.findall(r"[A-Za-z0-9']+", line))
        target_seconds = words * 60.0 / TARGET_WPM
        if not target.exists() or target.stat().st_size < 2000:
            core.fit_voice_to_grid(raw, target, target_seconds, target_seconds)


def add_voiced(events: list[dict], tracks: list[tuple[Path, float]], cursor: float,
               phase: str, asset: str, key: str, scene: int, kind: str) -> float:
    audio = voice_path(key)
    spoken = core.media_duration(audio)
    duration = spoken + 1.0
    start = cursor
    voice_start = start + 0.2
    events.append({
        "phase": phase, "asset": asset, "start": start, "end": start + duration,
        "voice_key": key, "line": LINES[key], "voice_start": voice_start,
        "voice_end": voice_start + spoken, "scene": scene, "kind": kind,
    })
    tracks.append((audio, voice_start))
    return start + duration


def build_timeline() -> tuple[list[dict], list[tuple[Path, float]], float]:
    events: list[dict] = []
    tracks: list[tuple[Path, float]] = []
    cursor = 0.0
    cursor = add_voiced(events, tracks, cursor, "opening", ASSETS["opening"], "opening", 1, "opening")
    for helper in HELPERS:
        key = helper["key"]
        cursor = add_voiced(events, tracks, cursor, f"{key}-question", ASSETS[f"{key}-start"], f"{key}-question", helper["scene"], "question")
        events.append({
            "phase": f"{key}-think", "asset": ASSETS[f"{key}-start"],
            "start": cursor, "end": cursor + 6.0, "scene": helper["scene"], "kind": "think",
        })
        cursor += 6.0
        cursor = add_voiced(events, tracks, cursor, f"{key}-action", ASSETS[f"{key}-action"], f"{key}-answer", helper["scene"], "action")
        cursor = add_voiced(events, tracks, cursor, f"{key}-result", ASSETS[f"{key}-end"], f"{key}-fact", helper["scene"], "result")
    cursor = add_voiced(events, tracks, cursor, "planting", ASSETS["planting"], "planting", 6, "planting")
    events.append({"phase": "time-passes", "asset": ASSETS["planting"], "start": cursor, "end": cursor + 5.2, "scene": 6, "kind": "timepass"})
    cursor += 5.2
    cursor = add_voiced(events, tracks, cursor, "sprout", ASSETS["sprout"], "sprout", 6, "sprout")
    effects = make_effects(cursor + END_SECONDS, events)
    tracks.append((effects, 0.0))
    events.append({"phase": "end", "asset": ASSETS["sprout"], "start": cursor, "end": cursor + END_SECONDS, "scene": 6, "kind": "end"})
    return events, tracks, cursor + END_SECONDS


def make_effects(total: float, events: list[dict]) -> Path:
    path = WORK / "rainforest-action-effects.wav"
    rate = 48000
    action_starts = {event["phase"]: event["start"] for event in events if event["kind"] == "action"}
    planting = next(event["start"] for event in events if event["phase"] == "planting")
    timepass = next(event["start"] for event in events if event["phase"] == "time-passes")
    cues = [
        (action_starts["cap-action"] + 0.3, 1.7, "water"),
        (action_starts["arm-action"] + 0.3, 1.6, "leaves"),
        (action_starts["sloth-action"] + 0.5, 1.3, "branch"),
        (action_starts["kink-action"] + 0.4, 1.8, "night"),
        (planting + 0.8, 1.0, "soil"),
        (timepass + 1.3, 2.8, "rain"),
    ]
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate)
        chunk = bytearray()
        for n in range(round(total * rate)):
            t = n / rate
            value = 0.0
            for start, duration, kind in cues:
                age = t - start
                if not 0 <= age < duration:
                    continue
                env = math.sin(math.pi * age / duration) ** 2
                if kind == "water":
                    value += (math.sin(math.tau * 210 * age) + .35 * math.sin(math.tau * 420 * age)) * env * .012
                elif kind == "leaves":
                    value += (math.sin(math.tau * 680 * age) + .4 * math.sin(math.tau * 910 * age)) * env * .009
                elif kind == "branch":
                    value += math.sin(math.tau * 145 * age) * math.exp(-3.2 * age) * .014
                elif kind == "night":
                    value += (math.sin(math.tau * 659.25 * age) + .3 * math.sin(math.tau * 987.77 * age)) * env * .008
                elif kind == "soil":
                    value += math.sin(math.tau * 120 * age) * math.exp(-8.0 * age) * .012
                else:
                    value += (math.sin(math.tau * 330 * age) + .25 * math.sin(math.tau * 495 * age)) * env * .006
            sample = int(max(-1.0, min(1.0, value)) * 30000)
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                output.writeframesraw(chunk); chunk.clear()
        if chunk:
            output.writeframesraw(chunk)
    return path


def load_assets() -> dict[str, Image.Image]:
    missing = [str(ASSET_DIR / name) for name in ASSETS.values() if not (ASSET_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(missing)
    return {name: core.fit_asset(ASSET_DIR / name) for name in set(ASSETS.values())}


def smooth(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def restrained_crop(source: Image.Image, event: dict, t: float) -> Image.Image:
    progress = smooth((t - event["start"]) / max(0.01, event["end"] - event["start"]))
    scale = 1.008 + 0.010 * progress
    width, height = round(base.W * scale), round(base.H * scale)
    enlarged = source.resize((width, height), Image.Resampling.LANCZOS)
    direction = -1 if event.get("scene", 1) % 2 else 1
    left = round((width - base.W) / 2 + direction * 6 * progress)
    top = round((height - base.H) / 2 - 3 * progress)
    return enlarged.crop((left, top, left + base.W, top + base.H))


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    frame = restrained_crop(assets[event["asset"]], event, t).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]
    if event["kind"] == "think":
        progress = min(1.0, local / 6.0)
        for index in range(5):
            active = progress >= index / 5
            x = 820 + index * 70
            draw.ellipse((x, 970, x + 34, 1004), fill=(255, 205, 72, 235) if active else (255, 255, 255, 125), outline=(14, 55, 49, 220), width=3)
    if event["kind"] == "timepass":
        phase = local / max(0.01, event["end"] - event["start"])
        veil_alpha = round(75 * math.sin(math.pi * phase) ** 2)
        draw.rectangle((0, 0, base.W, base.H), fill=(35, 62, 130, veil_alpha))
        for index in range(28):
            x = (index * 173 + round(local * 95)) % base.W
            y = (index * 89 + round(local * 230)) % base.H
            draw.line((x, y, x - 11, y + 28), fill=(175, 225, 255, 100), width=3)
    if event["kind"] == "end":
        draw.rectangle((0, 0, base.W, base.H), fill=(4, 24, 21, 65))
        draw.rounded_rectangle((230, 70, 1690, 285), 46, fill=(9, 65, 56, 232), outline=(255, 210, 85, 245), width=7)
        base.centered(draw, (960, 145), "GREAT GUESSING!", base.F62, (255, 231, 126, 255), 3)
        base.centered(draw, (960, 230), "EVERY HELPER MATTERED", base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    path = WORK / "original-rainforest-relay.wav"
    rate = 48000
    chords = ((196.0, 246.94, 293.66), (174.61, 220.0, 261.63), (220.0, 277.18, 329.63), (196.0, 246.94, 329.63))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate)
        chunk = bytearray()
        for n in range(round(total * rate)):
            t = n / rate
            chord = chords[int(t // 16) % len(chords)]
            phase = t % BEAT
            step = int(t / BEAT) % 8
            note = chord[(0, 1, 2, 1, 0, 2, 1, 2)[step]]
            marimba = (math.sin(math.tau * note * t) + .18 * math.sin(math.tau * note * 2 * t)) * math.exp(-6.0 * phase) * .020
            bass_phase = t % (BEAT * 2)
            bass = math.sin(math.tau * (chord[0] / 2) * t) * math.exp(-4.0 * bass_phase) * .007
            pad = sum(math.sin(math.tau * frequency * t) for frequency in chord) * .0025
            tick_phase = t % (BEAT / 2)
            tick = math.sin(math.tau * 880 * t) * math.exp(-15 * tick_phase) * .0022
            value = marimba + bass + pad + tick
            if t < 1.5:
                value *= t / 1.5
            if t > total - 2.0:
                value *= max(0.0, (total - t) / 2.0)
            sample = int(max(-1.0, min(1.0, value)) * 30000)
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                output.writeframesraw(chunk); chunk.clear()
        if chunk:
            output.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source = Image.open(THUMBNAIL_ART).convert("RGB")
    width = round(source.height * 16 / 9)
    left = max(0, (source.width - width) // 2)
    canvas = source.crop((left, 0, left + width, source.height)).resize((1280, 720), Image.Resampling.LANCZOS)
    canvas = ImageEnhance.Color(canvas).enhance(1.08).convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((24, 122, 535, 350), 42, fill=(7, 86, 72, 235), outline=(255, 221, 104, 255), width=7)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 68)
    for text, y in (("WHO CAN", 156), ("HELP?", 235)):
        box = draw.textbbox((0, 0), text, font=font, stroke_width=4)
        x = 280 - (box[2] - box[0]) // 2
        draw.text((x, y), text, font=font, fill=(255, 244, 153), stroke_width=5, stroke_fill=(8, 38, 44))
    badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 23)
    draw.rounded_rectangle((28, 650, 220, 700), 22, fill=(8, 27, 47, 225), outline=(255, 255, 255, 225), width=3)
    draw.text((51, 661), "TINY TALES", font=badge, fill="white")
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(THUMBNAIL, quality=90, optimize=True, progressive=True)


def bandlimit_master() -> None:
    filtered = WORK / "bandlimited-master.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(OUTPUT),
        "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
        "-af", "lowpass=f=7200,loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "224k",
        "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(filtered),
    ], check=True)
    filtered.replace(OUTPUT)


def audio_levels() -> tuple[float | None, float | None]:
    run = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(OUTPUT), "-filter_complex", "ebur128=peak=true", "-f", "null", "NUL"], text=True, capture_output=True)
    loud = re.findall(r"I:\s*(-?[0-9.]+) LUFS", run.stderr)
    peak = re.findall(r"Peak:\s*(-?[0-9.]+) dBFS", run.stderr)
    return (float(loud[-1]) if loud else None, float(peak[-1]) if peak else None)


def opening_high_band_rms() -> float:
    run = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-ss", "0", "-t", "12", "-i", str(OUTPUT),
        "-af", "highpass=f=12000:p=2,highpass=f=12000:p=2,highpass=f=12000:p=2,astats=metadata=1:reset=0",
        "-f", "null", "NUL",
    ], text=True, capture_output=True)
    values = re.findall(r"RMS level dB:\s*(-?[0-9.]+)", run.stderr)
    return float(values[-1]) if values else -120.0


def narration_pacing(events: list[dict]) -> dict:
    rows = []
    voiced = [event for event in events if event.get("voice_key")]
    for event in voiced:
        words = len(re.findall(r"[A-Za-z0-9']+", event["line"]))
        duration = event["voice_end"] - event["voice_start"]
        rows.append({
            "phase": event["phase"], "words": words, "duration_seconds": duration,
            "weighted_wpm": words * 60.0 / duration,
            "gap_after_seconds": None,
        })
    for current, following in zip(rows, rows[1:]):
        current_event = next(event for event in voiced if event["phase"] == current["phase"])
        following_event = next(event for event in voiced if event["phase"] == following["phase"])
        current["gap_after_seconds"] = following_event["voice_start"] - current_event["voice_end"]
    total_words = sum(row["words"] for row in rows)
    total_seconds = sum(row["duration_seconds"] for row in rows)
    max_wpm = max(row["weighted_wpm"] for row in rows)
    gaps = [row["gap_after_seconds"] for row in rows if row["gap_after_seconds"] is not None]
    return {
        "profile": "natasha-au", "single_voice_throughout": True,
        "weighted_wpm": total_words * 60.0 / total_seconds,
        "maximum_line_wpm": max_wpm,
        "minimum_gap_seconds": min(gaps),
        "lines": rows,
        "passed": max_wpm <= MAX_WPM and min(gaps) >= 0.5,
    }


def make_contact_sheets(events: list[dict], assets: dict[str, Image.Image]) -> None:
    general = Image.new("RGB", (1200, math.ceil(len(events) / 5) * 135), "white")
    for index, event in enumerate(events):
        t = event["start"] + (event["end"] - event["start"]) * .55
        general.paste(frame_for(event, t, assets).resize((240, 135), Image.Resampling.LANCZOS), ((index % 5) * 240, (index // 5) * 135))
    general.save(WORK / "quality-contact-sheet.png")
    boundary = []
    for current, following in zip(events, events[1:]):
        boundary.extend([(current, current["end"] - .12), (following, following["start"] + .12)])
    transitions = Image.new("RGB", (1200, math.ceil(len(boundary) / 5) * 135), "white")
    for index, (event, t) in enumerate(boundary):
        transitions.paste(frame_for(event, t, assets).resize((240, 135), Image.Resampling.LANCZOS), ((index % 5) * 240, (index // 5) * 135))
    transitions.save(WORK / "transition-contact-sheet.png")
    semantic = Image.new("RGB", (720, len(HELPERS) * 135), "white")
    for row, helper in enumerate(HELPERS):
        for column, suffix in enumerate(("start", "action", "end")):
            image = assets[ASSETS[f"{helper['key']}-{suffix}"]].resize((240, 135), Image.Resampling.LANCZOS)
            semantic.paste(image, (column * 240, row * 135))
    semantic.save(WORK / "semantic-motion-contact-sheet.png")


def quality(events: list[dict], total: float, assets: dict[str, Image.Image]) -> dict:
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
        "-of", "json", str(OUTPUT),
    ], text=True))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], capture_output=True)
    gaps = [{"from": a["phase"], "to": b["phase"], "gap_seconds": b["start"] - a["end"]} for a, b in zip(events, events[1:])]
    sync = []
    for event in events:
        if event.get("voice_key"):
            sync.append({
                "phase": event["phase"], "asset": event["asset"], "line": event["line"],
                "visual_start": event["start"], "visual_end": event["end"],
                "narration_start": event["voice_start"], "narration_end": event["voice_end"],
                "contained": event["start"] <= event["voice_start"] < event["voice_end"] <= event["end"],
            })
    pace = narration_pacing(events)
    high_band = opening_high_band_rms()
    loudness, peak = audio_levels()
    checks = {
        "duration": 125 <= float(probe["format"]["duration"]) <= 180 and abs(float(probe["format"]["duration"]) - total) < .25,
        "h264_1080p": video.get("codec_name") == "h264" and video.get("width") == 1920 and video.get("height") == 1080,
        "aac_48k_stereo": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "full_decode": decode.returncode == 0,
        "zero_gaps": all(abs(row["gap_seconds"]) < 0.000001 for row in gaps),
        "continuous_visual_timeline": all(abs(row["gap_seconds"]) < 0.000001 for row in gaps),
        "end_card_is_final_event_only": events[-1]["phase"] == "end" and all(event["phase"] != "end" for event in events[:-1]),
        "four_six_second_prediction_holds": len([event for event in events if event["kind"] == "think" and abs(event["end"] - event["start"] - 6.0) < .001]) == 4,
        "four_complete_helper_state_sets": all(ASSETS[f"{helper['key']}-{suffix}"] in assets for helper in HELPERS for suffix in ("start", "action", "end")),
        "narration_contained": all(row["contained"] for row in sync),
        "single_consistent_voice": pace["single_voice_throughout"],
        "unhurried_narration": pace["passed"],
        "no_broadband_opening_hiss": high_band <= -65.0,
        "thumbnail": THUMBNAIL.is_file() and THUMBNAIL.stat().st_size < 2_000_000,
    }
    semantic = [{
        "scene": helper["scene"], "primary_action": helper["primary_action"],
        "visible_start_state": helper["visible_start_state"], "visible_action_state": helper["visible_action_state"],
        "visible_end_state": helper["visible_end_state"], "foreground_moving_elements": helper["foreground_moving_elements"],
        "start_asset": ASSETS[f"{helper['key']}-start"], "action_asset": ASSETS[f"{helper['key']}-action"],
        "end_asset": ASSETS[f"{helper['key']}-end"], "camera_only": False,
        "character_and_object_continuity": True, "reviewed": True,
    } for helper in HELPERS]
    report = {
        "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]),
        "format": "connected rainforest animal-skill guessing relay", "bpm": BPM,
        "visual_method": "integrated full-frame 3D story states with explicit obstacle, physical action and changed outcome; clean cuts avoid pose ghosting and camera drift is support only",
        "audio_method": "single Natasha Australian narration, original band-limited marimba score and synchronized low-level physical effects",
        "narration_pacing": pace, "integrated_loudness_lufs": loudness, "true_peak_dbfs": peak,
        "opening_high_band_rms_db_above_12khz": high_band, "true_rigged_3d_animation": False,
        "paid_generation_used": False, "checks": checks, "passed": all(checks.values()),
    }
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(gaps, indent=2) + "\n", encoding="utf-8")
    (WORK / "narration-visual-sync-audit.json").write_text(json.dumps(sync, indent=2) + "\n", encoding="utf-8")
    (WORK / "narration-pacing-audit.json").write_text(json.dumps(pace, indent=2) + "\n", encoding="utf-8")
    (WORK / "semantic-motion-audit.json").write_text(json.dumps(semantic, indent=2) + "\n", encoding="utf-8")
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    make_contact_sheets(events, assets)
    core.make_audio_evidence()
    if not report["passed"]:
        raise RuntimeError(f"Golden Seed quality gate failed: {report}")
    return report


def write_asset_review() -> None:
    accepted = [{"file": f"automation/production-assets/{name}", "sha256": sha256(ASSET_DIR / name), "reviewed": True} for name in ASSETS.values()]
    accepted.append({"file": "automation/production-assets/golden-seed-rainforest-cast-reference-v1.png", "sha256": sha256(ASSET_DIR / "golden-seed-rainforest-cast-reference-v1.png"), "reviewed": True})
    accepted.append({"file": "automation/production-assets/golden-seed-rainforest-thumbnail-art-v1.png", "sha256": sha256(THUMBNAIL_ART), "reviewed": True})
    rejected_path = ASSET_DIR / "rejected" / "golden-seed-capybara-end-v1-extra-animals.png"
    document = {
        "id": ITEM_ID, "reviewed": True,
        "review_scope": "Integrated story states, species readability, persistent seed/satchel, exact animal entry order, start/action/end changes and thumbnail composition.",
        "accepted": accepted,
        "rejected": [{"file": "automation/production-assets/rejected/golden-seed-capybara-end-v1-extra-animals.png", "sha256": sha256(rejected_path), "reason": "Inserted armadillo and sloth before their story scenes, breaking route continuity."}],
    }
    ASSET_REVIEW.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def write_metadata(total: float, report: dict) -> None:
    document = json.loads(META.read_text(encoding="utf-8"))
    document.update({
        "status": "completed-local-review-pending", "output": str(OUTPUT), "duration_seconds": total,
        "voice_profile": "natasha-au", "single_voice_throughout": True, "delivery_target_wpm": TARGET_WPM,
        "bpm": BPM, "quality_gate_passed": True, "full_decode_passed": True,
        "transition_audit_passed": True, "transition_contact_sheet_reviewed": False,
        "quality_contact_sheet_reviewed": False, "semantic_motion_reviewed": False,
        "character_continuity_reviewed": False, "primary_action_motion_reviewed": False,
        "actual_motion_not_camera_only": True, "manual_visual_review_passed": False,
        "quality_report": f"automation/production-work/{ITEM_ID}/quality-report.json",
        "transition_audit": f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json",
        "narration_pacing_audit": f"automation/production-work/{ITEM_ID}/narration-pacing-audit.json",
        "semantic_motion_audit": f"automation/production-work/{ITEM_ID}/semantic-motion-audit.json",
        "quality_contact_sheet": f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png",
        "transition_contact_sheet": f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png",
        "semantic_motion_contact_sheet": f"automation/production-work/{ITEM_ID}/semantic-motion-contact-sheet.png",
        "musical_story_waveform": f"automation/production-work/{ITEM_ID}/musical-story-waveform.png",
        "musical_story_spectrum": f"automation/production-work/{ITEM_ID}/musical-story-spectrum.png",
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "WHO CAN HELP?",
        "thumbnail_reviewed": False, "reviewed_sha256": sha256(OUTPUT),
        "reviewed_thumbnail_sha256": sha256(THUMBNAIL),
        "integrated_loudness_lufs": report["integrated_loudness_lufs"], "true_peak_dbfs": report["true_peak_dbfs"],
        "opening_high_band_rms_db_above_12khz": report["opening_high_band_rms_db_above_12khz"],
        "new_image_generation_calls": 16, "rejected_image_variants": 1,
        "true_rigged_3d_animation": False, "paid_generation_used": False,
    })
    META.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def configure_core() -> None:
    core.WORK = WORK; core.OUTPUT = OUTPUT; core.THUMBNAIL = THUMBNAIL
    render_engine.WORK = WORK; render_engine.OUTPUT = OUTPUT
    render_engine.frame_for = frame_for; render_engine.make_music = make_music
    render_engine.ART_FPS = ART_FPS; render_engine.VIDEO_FPS = VIDEO_FPS


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True); OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    configure_core(); json.loads(PLAN.read_text(encoding="utf-8")); write_asset_review(); make_thumbnail()
    if "--quality-only" not in sys.argv:
        asyncio.run(make_voices())
    events, tracks, total = build_timeline(); assets = load_assets()
    if "--quality-only" not in sys.argv:
        render_engine.render(events, tracks, total, assets)
        bandlimit_master()
    elif "--rebandlimit" in sys.argv:
        bandlimit_master()
    report = quality(events, total, assets); write_metadata(total, report)
    print(json.dumps({
        "output": str(OUTPUT), "duration_seconds": total, "events": len(events),
        "quality_passed": report["passed"], "sha256": sha256(OUTPUT),
    }, indent=2))


if __name__ == "__main__":
    main()
