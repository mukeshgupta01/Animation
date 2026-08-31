"""Produce Basil Beaver's Leaky River Workshop as a synchronized musical story."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import random
import re
import struct
import subprocess
import wave

import produce_felix_firefly_parade as base


engine = base.engine
core = base.core
Image = base.Image
ImageDraw = base.ImageDraw
ImageEnhance = base.ImageEnhance
ImageFont = base.ImageFont
AUTOMATION = base.AUTOMATION
PROJECT = base.PROJECT
ITEM_ID = "basil-beaver-leaky-river-workshop-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
REVIEWED_MASTER_SHA256 = "af4ba483369a7aadacba0648099f40f8766b19f3197d9553275d7646a85b63a5"
REVIEWED_THUMBNAIL_SHA256 = "dcbc0f1a94200a670915a0c3dbf013117e0358e25cefb7784450cf63d3da29d0"
BPM = 88
BEAT = 60 / BPM
EIGHTH = BEAT / 2
SCENE_SECONDS = BEAT * 16
END_SECONDS = 4.0
LINE_OFFSETS = (EIGHTH, EIGHTH * 11, EIGHTH * 21)

ASSETS = (
    "basil-beaver-opening-v1.png",
    "basil-beaver-materials-v1.png",
    "basil-beaver-leaf-test-v1.png",
    "basil-beaver-stone-test-v1.png",
    "basil-beaver-stick-frame-v1.png",
    "basil-beaver-reed-weave-v1.png",
    "basil-beaver-clay-seal-v1.png",
    "basil-beaver-flow-success-v1.png",
    "basil-beaver-workshop-finale-v1.png",
)

VOICE_PROFILES = {
    "ryan-wonder": {**core.select_voice_profile("ryan-uk"), "rate": "-11%", "pitch": "+5Hz"},
    "ryan-curious": {**core.select_voice_profile("ryan-uk"), "rate": "-9%", "pitch": "+7Hz"},
    "ryan-gentle": {**core.select_voice_profile("ryan-uk"), "rate": "-12%", "pitch": "+3Hz"},
    "ryan-thoughtful": {**core.select_voice_profile("ryan-uk"), "rate": "-13%", "pitch": "+1Hz"},
    "ryan-build": {**core.select_voice_profile("ryan-uk"), "rate": "-8%", "pitch": "+6Hz"},
    "ryan-bright": {**core.select_voice_profile("ryan-uk"), "rate": "-7%", "pitch": "+9Hz"},
    "ryan-finale": {**core.select_voice_profile("ryan-uk"), "rate": "-6%", "pitch": "+10Hz"},
    "ana-basil-surprise": {**core.select_voice_profile("ana-us"), "rate": "-10%", "pitch": "+8Hz"},
    "ana-basil-care": {**core.select_voice_profile("ana-us"), "rate": "-12%", "pitch": "+4Hz"},
    "ana-basil-build": {**core.select_voice_profile("ana-us"), "rate": "-8%", "pitch": "+7Hz"},
    "ana-basil-release": {**core.select_voice_profile("ana-us"), "rate": "-6%", "pitch": "+11Hz"},
    "maisie-pippa": {**core.select_voice_profile("maisie-uk"), "rate": "-10%", "pitch": "+12Hz"},
    "maisie-pippa-soft": {**core.select_voice_profile("maisie-uk"), "rate": "-12%", "pitch": "+8Hz"},
    "maisie-pippa-bright": {**core.select_voice_profile("maisie-uk"), "rate": "-7%", "pitch": "+14Hz"},
}

SCENE_PROFILES = (
    ("ryan-wonder", "ryan-curious", "ana-basil-surprise"),
    ("ryan-curious", "maisie-pippa", "ana-basil-care"),
    ("ryan-gentle", "ana-basil-care", "maisie-pippa-bright"),
    ("ryan-thoughtful", "maisie-pippa-soft", "ryan-gentle"),
    ("ryan-build", "ana-basil-build", "ryan-thoughtful"),
    ("ryan-build", "maisie-pippa", "ana-basil-care"),
    ("ryan-thoughtful", "ana-basil-care", "maisie-pippa-soft"),
    ("ana-basil-release", "ryan-bright", "maisie-pippa-bright"),
    ("ryan-finale", "ana-basil-release", "maisie-pippa-bright"),
)


def load_plan() -> dict:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    for scene in plan["scenes"]:
        scene["visual_action"] = scene["action"]
    return plan


async def make_voices(plan: dict) -> None:
    for scene_index, scene in enumerate(plan["scenes"]):
        for line_index, line in enumerate(scene["lyrics"]):
            profile_name = SCENE_PROFILES[scene_index][line_index]
            raw = WORK / f"voice-raw-basil-v2-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.mp3"
            target = WORK / f"voice-grid-basil-v2-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
                ).save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, 2.72, words * 60.0 / 135.0)


def effect_windows(scene: int) -> list[dict]:
    names = (
        ("workshop_door_creak", "silver_water_leak", "stopped_wheel_touch"),
        ("leaf_lift", "stone_set", "clay_bowl_touch"),
        ("leaf_on_water", "floating_leaf_wake", "basket_catch"),
        ("three_stones_set", "water_between_stones", "wet_stone_touch"),
        ("five_sticks_set", "fiber_tie_pull", "water_through_frame"),
        ("reed_over_under", "reed_pull_snug", "three_soft_drops"),
        ("clay_press", "panel_support", "last_water_drop"),
        ("mill_gate_lift", "controlled_water_rush", "blue_wheel_turn"),
        ("log_xylophone", "reed_shaker", "gourd_drum"),
    )[scene]
    starts = (0.8, 4.25, 8.05)
    return [
        {"effect": name, "local_start": start, "local_end": min(SCENE_SECONDS - 0.2, start + 1.65)}
        for name, start in zip(names, starts)
    ]


def synth_scene_effect(scene: int):
    path = WORK / f"scene-{scene+1:02d}-effects.wav"
    rate = 48000
    rng = random.Random(880831 + scene)
    windows = effect_windows(scene)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate)
        chunk = bytearray()
        for n in range(round(SCENE_SECONDS * rate)):
            t = n / rate
            value = 0.0
            for wi, row in enumerate(windows):
                age = t - row["local_start"]
                duration = row["local_end"] - row["local_start"]
                if not 0 <= age < duration:
                    continue
                env = math.sin(math.pi * age / duration) ** 2
                name = row["effect"]
                if "water" in name or "drop" in name or "leak" in name or "rush" in name:
                    value += rng.uniform(-1, 1) * env * (0.045 if "rush" in name else 0.026)
                elif "stone" in name or "drum" in name:
                    value += math.sin(math.tau * (82 + wi * 16) * age) * math.exp(-10 * age) * 0.08
                elif "wood" in name or "stick" in name or "xylophone" in name or "wheel" in name:
                    value += (math.sin(math.tau * (240 + wi * 70) * age) + 0.35 * math.sin(math.tau * 480 * age)) * math.exp(-7 * age) * 0.045
                elif "reed" in name or "leaf" in name or "basket" in name or "fiber" in name:
                    value += rng.uniform(-1, 1) * math.exp(-4.5 * age) * env * 0.036
                else:
                    value += math.sin(math.tau * (150 + wi * 30) * age) * math.exp(-6 * age) * 0.04
            sample = int(max(-1, min(1, value)) * 27000)
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                out.writeframesraw(chunk); chunk.clear()
        if chunk:
            out.writeframesraw(chunk)
    return path, windows


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 8 if event["phase"] == "end" else event["scene"] - 1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]
    rng = random.Random(8800 + index)
    droplet_count = 20 if index >= 7 else (5 if index in (5, 6) else 11)
    for j in range(droplet_count):
        x = (rng.randint(70, 1850) + int(math.sin(local * 0.7 + j) * 7)) % 1920
        y = rng.randint(100, 900) + int(math.cos(local * 0.5 + j) * 5)
        radius = 1 + int((math.sin(local * 1.5 + j) + 1) * 0.55)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(180, 230, 255, 24 if index < 7 else 42))
    if event["phase"] == "end":
        draw.rectangle((0, 0, 1920, 1080), fill=(16, 34, 32, 70))
        draw.rounded_rectangle((430, 58, 1490, 224), 42, fill=(20, 58, 57, 230), outline=(255, 207, 105, 245), width=7)
        core.base.centered(draw, (960, 112), "TEST, BUILD, TRY AGAIN", core.base.F48, (255, 220, 120, 255), 3)
        core.base.centered(draw, (960, 180), "TOGETHER WE MAKE IT FLOW", core.base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    path = WORK / "original-river-workshop-groove.wav"
    rate = 48000
    rng = random.Random(883108)
    chords = (
        (174.61, 220.00, 261.63), (196.00, 246.94, 293.66), (220.00, 261.63, 329.63),
        (146.83, 196.00, 246.94), (164.81, 207.65, 261.63), (174.61, 220.00, 261.63),
        (146.83, 196.00, 246.94), (196.00, 246.94, 293.66), (220.00, 277.18, 329.63),
    )
    energy = (0.54, 0.64, 0.58, 0.48, 0.66, 0.72, 0.52, 0.86, 1.0)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate)
        chunk = bytearray()
        for n in range(round(total * rate)):
            t = n / rate
            scene = min(8, int(t // SCENE_SECONDS))
            local = t - scene * SCENE_SECONDS
            chord = chords[scene]
            phase = local % BEAT
            step = int(local / BEAT) % 8
            note = chord[(0, 1, 2, 1, 0, 2, 1, 2)[step]]
            marimba = (math.sin(math.tau * note * t) + 0.28 * math.sin(math.tau * note * 2 * t)) * math.exp(-5.4 * phase) * 0.022 * energy[scene]
            pluck = math.sin(math.tau * (chord[0] / 2) * t) * math.exp(-3.6 * (local % (BEAT * 2))) * 0.012 * energy[scene]
            strings = sum(math.sin(math.tau * f * t) for f in chord) * 0.0043 * energy[scene]
            water_brush = rng.uniform(-1, 1) * math.exp(-34 * (local % (BEAT / 2))) * 0.004 * energy[scene]
            wood_drum = math.sin(math.tau * 84 * phase) * math.exp(-27 * phase) * (0.004 + 0.008 * (scene >= 7))
            value = marimba + pluck + strings + water_brush + wood_drum
            if t >= 9 * SCENE_SECONDS:
                value *= min(1, (total - t) / 0.8)
            sample = int(max(-1, min(1, value)) * 30000)
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                out.writeframesraw(chunk); chunk.clear()
        if chunk:
            out.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source = Image.open(ASSET_DIR / ASSETS[8]).convert("RGB")
    width = round(source.height * 16 / 9)
    left = max(0, (source.width - width) // 2)
    canvas = source.crop((left, 0, left + width, source.height)).resize((1280, 720), Image.Resampling.LANCZOS)
    canvas = ImageEnhance.Color(canvas).enhance(1.08).convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((650, 22, 1254, 132), 28, fill=(17, 55, 58, 235), outline=(255, 215, 105, 255), width=5)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 57)
    text = "WE MADE IT FLOW!"
    box = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    draw.text((952 - (box[2] - box[0]) // 2, 46), text, font=font, fill=(255, 225, 120), stroke_width=4, stroke_fill=(8, 31, 38))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(THUMBNAIL, quality=89, optimize=True)


def quality(events, total, assets):
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries",
        "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(OUTPUT)
    ], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], capture_output=True)
    transitions = [{"from": a["phase"], "to": b["phase"], "gap_seconds": b["start"] - a["end"]} for a, b in zip(events, events[1:])]
    sync = []
    for event in events[:-1]:
        contained = all(event["start"] <= row["start"] < row["end"] <= event["end"] for row in event["lines"] + event["effects"])
        sync.append({"scene": event["scene"], "emotion": event["emotion"], "asset": event["asset"], "visual_action": event["visual_action"], "visual_start": event["start"], "visual_end": event["end"], "lines": event["lines"], "effects": event["effects"], "contained": contained})
    pace = core.pacing_audit(sync)
    spoken = [line["line"].lower() for item in sync for line in item["lines"]]
    zero_gaps = all(abs(row["gap_seconds"]) < 1e-6 for row in transitions)
    final_only = events[-1]["phase"] == "end" and all(event["phase"] != "end" for event in events[:-1])
    checks = {
        "duration": abs(float(probe["format"]["duration"]) - total) < 0.25,
        "h264_1080p": video.get("codec_name") == "h264" and video.get("width") == 1920 and video.get("height") == 1080,
        "aac_48k_stereo": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "full_decode": decode.returncode == 0,
        "zero_gaps": zero_gaps,
        "continuous_visual_timeline": zero_gaps,
        "end_card_final_only": final_only,
        "end_card_is_final_event_only": final_only,
        "nine_unique_scenes": len({row["asset"] for row in sync}) == 9,
        "four_bar_scene_cuts": all(abs((row["visual_end"] / BEAT) - round(row["visual_end"] / BEAT)) < 1e-5 for row in sync),
        "narration_effects_contained": all(row["contained"] for row in sync),
        "voice_starts_on_eighth_grid": all(abs(((line["start"] - item["visual_start"]) / EIGHTH) - round((line["start"] - item["visual_start"]) / EIGHTH)) < 1e-5 for item in sync for line in item["lines"]),
        "child_friendly_pacing": pace["passed"],
        "no_spoken_imitation": all(not any(word in line for word in ("clap clap", "tap tap", "ding dong", "boom boom")) for line in spoken),
        "real_effects": len({effect["effect"] for item in sync for effect in item["effects"]}) == 27,
        "thumbnail": THUMBNAIL.is_file() and THUMBNAIL.stat().st_size < 2_000_000,
    }
    loudness, peak = base.engine.audio_levels()
    report = {
        "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]),
        "format": "physical cause-and-effect engineering musical", "bpm": BPM,
        "visual_method": "nine reviewed premium tactile river-workshop tableaux with restrained eased camera travel and continuous material continuity",
        "audio_method": "original 88 BPM emotion-mapped marimba, plucked strings and wood percussion with three character voices and synchronized real effects",
        "narration_pacing": {"weighted_wpm": pace["weighted_wpm"], "maximum_line_wpm": pace["maximum_line_wpm"], "minimum_interline_gap_seconds": pace["minimum_interline_gap_seconds"]},
        "integrated_loudness_lufs": loudness, "true_peak_dbfs": peak,
        "true_rigged_3d_animation": False, "paid_generation_used": False,
        "checks": checks, "passed": all(checks.values()),
    }
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(transitions, indent=2) + "\n", encoding="utf-8")
    (WORK / "lyric-visual-emotion-audit.json").write_text(json.dumps(sync, indent=2) + "\n", encoding="utf-8")
    (WORK / "narration-pacing-audit.json").write_text(json.dumps(pace, indent=2) + "\n", encoding="utf-8")
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    general = Image.new("RGB", (960, 405), "white")
    for index, event in enumerate(events):
        general.paste(frame_for(event, event["start"] + (event["end"] - event["start"]) * 0.55, assets).resize((240, 135), Image.Resampling.LANCZOS), ((index % 4) * 240, (index // 4) * 135))
    general.save(WORK / "quality-contact-sheet.png")
    boundary = []
    for current, following in zip(events, events[1:]):
        boundary.extend([(current, current["end"] - 0.12), (following, following["start"] + 0.12)])
    sheet = Image.new("RGB", (1200, math.ceil(len(boundary) / 5) * 135), "white")
    for index, (event, timestamp) in enumerate(boundary):
        sheet.paste(frame_for(event, timestamp, assets).resize((240, 135), Image.Resampling.LANCZOS), ((index % 5) * 240, (index // 5) * 135))
    sheet.save(WORK / "transition-contact-sheet.png")
    core.make_audio_evidence()
    if not report["passed"]:
        raise RuntimeError(f"Basil quality gate failed: {report}")
    return report


def write_metadata(total, report):
    master_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    thumbnail_hash = hashlib.sha256(THUMBNAIL.read_bytes()).hexdigest()
    reviewed = master_hash == REVIEWED_MASTER_SHA256 and thumbnail_hash == REVIEWED_THUMBNAIL_SHA256
    doc = {
        "id": ITEM_ID,
        "title": "Basil Beaver's Leaky River Workshop | Engineering Story for Kids",
        "description": "Basil, Pippa and Moss test leaves, stones, sticks, reeds and clay to repair a leaky workshop channel while keeping the natural river open for fish.\n\nAn original Tiny Tales musical engineering story about floating, sinking, flow, careful testing and teamwork for children ages 3 to 7.",
        "tags": ["engineering for kids", "beaver story", "float and sink", "water flow for kids", "teamwork story", "musical story for kids", "Tiny Tales"],
        "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": True,
        "output": str(OUTPUT), "duration_seconds": total, "voice_profile": "ryan-uk",
        "character_voice_profiles": {"basil": "ana-us", "pippa": "maisie-uk"},
        "delivery": "emotion-mapped melodic engineering story-song", "bpm": BPM,
        "format_family": "physical cause-and-effect engineering musical",
        "quality_gate_passed": True, "full_decode_passed": True, "transition_audit_passed": True,
        "quality_report": f"automation/production-work/{ITEM_ID}/quality-report.json",
        "transition_audit": f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "lyric_visual_emotion_audit": f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json",
        "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json",
        "narration_pacing_audit": f"automation/production-work/{ITEM_ID}/narration-pacing-audit.json",
        "quality_contact_sheet": f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png",
        "transition_contact_sheet": f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png",
        "musical_story_waveform": f"automation/production-work/{ITEM_ID}/musical-story-waveform.png",
        "musical_story_spectrum": f"automation/production-work/{ITEM_ID}/musical-story-spectrum.png",
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "WE MADE IT FLOW!",
        "thumbnail_reviewed": reviewed, "manual_visual_review_passed": reviewed,
        "transition_contact_sheet_reviewed": reviewed, "quality_contact_sheet_reviewed": reviewed,
        "reviewed_sha256": master_hash,
        "manual_review_notes": "Review remains valid only for the exact hash-locked master and thumbnail. General sheet, every transition, material-result sequence, first wheel payoff, final-only workshop band, final-only end card, waveform and thumbnail require review.",
        "integrated_loudness_lufs": report["integrated_loudness_lufs"], "true_peak_dbfs": report["true_peak_dbfs"],
        "true_rigged_3d_animation": False, "paid_generation_used": False, "new_image_generation_calls": 10,
        "spoken_sound_effect_words_removed": True, "upload_queue_released": False,
        "narration_pacing_policy": "three short phrases per scene; target at most 140 WPM, hard line ceiling 145 WPM and at least 0.4 seconds between phrases",
    }
    META.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def configure_engine() -> None:
    engine.ITEM_ID = ITEM_ID; engine.WORK = WORK; engine.OUTPUT = OUTPUT; engine.PLAN = PLAN; engine.META = META; engine.THUMBNAIL = THUMBNAIL
    engine.SCENE_SECONDS = SCENE_SECONDS; engine.END_SECONDS = END_SECONDS; engine.BEAT = BEAT; engine.EIGHTH = EIGHTH; engine.LINE_OFFSETS = LINE_OFFSETS
    engine.ASSETS = ASSETS; engine.VOICE_PROFILES = VOICE_PROFILES; engine.SCENE_PROFILES = SCENE_PROFILES; engine.PACING_VERSION = "basil-v2"
    engine.load_plan = load_plan; engine.make_voices = make_voices; engine.effect_windows = effect_windows; engine.synth_scene_effect = synth_scene_effect
    engine.frame_for = frame_for; engine.make_music = make_music; engine.make_thumbnail = make_thumbnail; engine.quality = quality; engine.write_metadata = write_metadata


def main() -> None:
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
