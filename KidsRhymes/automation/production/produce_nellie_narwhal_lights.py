"""Produce Nellie Narwhal and the Northern Lights as a synchronized musical story."""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import struct
import wave

import produce_basil_beaver_workshop as base
import semantic_motion as semantic


BASIL_QUALITY = base.quality
engine = base.engine
core = base.core
Image = base.Image
ImageDraw = base.ImageDraw
ImageEnhance = base.ImageEnhance
ImageFont = base.ImageFont
AUTOMATION = base.AUTOMATION
PROJECT = base.PROJECT
ITEM_ID = "nellie-narwhal-northern-lights-rescue-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
REVIEWED_MASTER_SHA256 = "9e7ea66829d737741b39074ab13b85dadbed0e85b833df2bf2f39551ca13bbfe"
REVIEWED_THUMBNAIL_SHA256 = "86a1ca78161f90d15736e192e93a5b7a3521f8268519f5620abae25fb5182891"
BPM = 86
BEAT = 60 / BPM
EIGHTH = BEAT / 2
SCENE_SECONDS = BEAT * 16
END_SECONDS = 4.0
LINE_OFFSETS = (EIGHTH, EIGHTH * 11, EIGHTH * 21)

ASSETS = (
    "nellie-narwhal-opening-v1.png",
    "nellie-narwhal-three-colour-route-v1.png",
    "nellie-narwhal-green-signal-v1.png",
    "nellie-narwhal-blue-jelly-v1.png",
    "nellie-narwhal-violet-window-v1.png",
    "nellie-narwhal-mist-pause-v1.png",
    "nellie-narwhal-joined-route-v1.png",
    "nellie-narwhal-safe-swim-v1.png",
    "nellie-narwhal-reunion-finale-v1.png",
)

VOICE_PROFILES = {
    "maisie-hush": {**core.select_voice_profile("maisie-uk"), "rate": "-13%", "pitch": "+5Hz"},
    "maisie-tender": {**core.select_voice_profile("maisie-uk"), "rate": "-12%", "pitch": "+7Hz"},
    "maisie-colour": {**core.select_voice_profile("maisie-uk"), "rate": "-9%", "pitch": "+10Hz"},
    "maisie-wonder": {**core.select_voice_profile("maisie-uk"), "rate": "-11%", "pitch": "+12Hz"},
    "maisie-bright": {**core.select_voice_profile("maisie-uk"), "rate": "-7%", "pitch": "+13Hz"},
    "maisie-finale": {**core.select_voice_profile("maisie-uk"), "rate": "-6%", "pitch": "+14Hz"},
    "natasha-nellie": {**core.select_voice_profile("natasha-au"), "rate": "-11%", "pitch": "+4Hz"},
    "natasha-calm": {**core.select_voice_profile("natasha-au"), "rate": "-13%", "pitch": "+2Hz"},
    "natasha-hope": {**core.select_voice_profile("natasha-au"), "rate": "-9%", "pitch": "+8Hz"},
    "natasha-finale": {**core.select_voice_profile("natasha-au"), "rate": "-7%", "pitch": "+10Hz"},
    "ana-kiko": {**core.select_voice_profile("ana-us"), "rate": "-12%", "pitch": "+10Hz"},
    "ana-kiko-brave": {**core.select_voice_profile("ana-us"), "rate": "-8%", "pitch": "+13Hz"},
}

SCENE_PROFILES = (
    ("maisie-hush", "ana-kiko", "natasha-nellie"),
    ("maisie-colour", "natasha-calm", "natasha-nellie"),
    ("maisie-wonder", "natasha-hope", "ana-kiko"),
    ("maisie-colour", "natasha-calm", "natasha-nellie"),
    ("maisie-wonder", "natasha-hope", "natasha-nellie"),
    ("maisie-tender", "ana-kiko", "natasha-calm"),
    ("maisie-bright", "natasha-hope", "ana-kiko-brave"),
    ("ana-kiko-brave", "natasha-hope", "maisie-bright"),
    ("maisie-finale", "natasha-finale", "ana-kiko-brave"),
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
            raw = WORK / f"voice-raw-nellie-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.mp3"
            target = WORK / f"voice-grid-nellie-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
                ).save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, 2.95, words * 60.0 / 132.0)


def effect_windows(scene: int) -> list[dict]:
    names = (
        ("under_ice_hum", "seal_floe_call", "narwhal_fin_turn"),
        ("green_ice_glow", "blue_bubbles", "violet_ice_ring"),
        ("green_water_ribbon", "single_bubble_rise", "floe_signal_touch"),
        ("blue_jelly_pulse", "char_fin_circle", "open_lane_water"),
        ("violet_window_shimmer", "tusk_near_ice", "safe_gap_wash"),
        ("soft_surface_mist", "quiet_floe_rest", "three_colour_memory"),
        ("green_blue_join", "violet_route_join", "mother_floe_call"),
        ("seal_water_entry", "side_by_side_swim", "char_lead_fin"),
        ("seal_nose_touch", "narwhal_surface", "aurora_finale_bloom"),
    )[scene]
    starts = (0.8, 4.45, 8.25)
    return [
        {"effect": name, "local_start": start, "local_end": min(SCENE_SECONDS - 0.2, start + 1.7)}
        for name, start in zip(names, starts)
    ]


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 8 if event["phase"] == "end" else event["scene"] - 1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]
    rng = random.Random(8600 + index)
    particle_count = 20 if index == 8 else (6 if index == 5 else 11)
    for j in range(particle_count):
        x = (rng.randint(80, 1840) + int(math.sin(local * 0.38 + j) * 5)) % 1920
        y = rng.randint(90, 920) + int(math.cos(local * 0.31 + j) * 4)
        radius = 1 + int((math.sin(local * 1.1 + j) + 1) * 0.5)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(185, 230, 255, 22 if index < 8 else 38))
    if event["phase"] == "end":
        draw.rectangle((0, 0, 1920, 1080), fill=(8, 23, 58, 70))
        draw.rounded_rectangle((430, 54, 1490, 220), 42, fill=(18, 42, 76, 230), outline=(158, 232, 229, 250), width=7)
        core.base.centered(draw, (960, 108), "GREEN, BLUE, VIOLET", core.base.F48, (213, 245, 245, 255), 3)
        core.base.centered(draw, (960, 176), "KIND LIGHTS GUIDE US HOME", core.base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return semantic.apply(frame, event, t, "nellie", ASSET_DIR)


def make_music(total: float):
    path = WORK / "original-northern-lights-ballad.wav"
    rate = 48000
    rng = random.Random(863108)
    chords = (
        (174.61, 220.00, 261.63), (196.00, 246.94, 293.66), (220.00, 277.18, 329.63),
        (196.00, 246.94, 311.13), (174.61, 233.08, 293.66), (146.83, 196.00, 246.94),
        (196.00, 261.63, 329.63), (220.00, 277.18, 349.23), (246.94, 311.13, 392.00),
    )
    energy = (0.44, 0.54, 0.62, 0.60, 0.66, 0.38, 0.78, 0.88, 1.0)
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
            harp = (math.sin(math.tau * note * t) + 0.25 * math.sin(math.tau * note * 2 * t)) * math.exp(-5.0 * phase) * 0.017 * energy[scene]
            glass = math.sin(math.tau * note * 2.02 * t) * math.exp(-3.8 * phase) * 0.007 * energy[scene]
            cello = math.sin(math.tau * (chord[0] / 2) * t) * 0.008 * energy[scene]
            strings = sum(math.sin(math.tau * f * t) for f in chord) * 0.0039 * energy[scene]
            water = rng.uniform(-1, 1) * math.exp(-28 * (local % (BEAT / 2))) * 0.0032 * energy[scene]
            drum = math.sin(math.tau * 72 * phase) * math.exp(-23 * phase) * (0.002 + 0.005 * (scene >= 6))
            value = harp + glass + cello + strings + water + drum
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
    draw.rounded_rectangle((18, 18, 635, 130), 28, fill=(11, 34, 70, 235), outline=(160, 235, 226, 255), width=5)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 55)
    text = "FOLLOW THE LIGHTS!"
    box = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    draw.text((326 - (box[2] - box[0]) // 2, 45), text, font=font, fill=(225, 252, 247), stroke_width=4, stroke_fill=(6, 22, 55))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(THUMBNAIL, quality=89, optimize=True)


def quality(events, total, assets):
    report = BASIL_QUALITY(events, total, assets)
    semantic.write_evidence(WORK, events[:-1], frame_for, assets, "nellie")
    report["format"] = "underwater light-and-colour rescue ballad"
    report["bpm"] = BPM
    report["visual_method"] = "independently animated identity-locked foreground cast with visible swimming and green-blue-violet route actions over defocused Arctic environments"
    report["audio_method"] = "original 86 BPM emotion-mapped glass harp, strings and soft percussion with three character voices and 27 synchronized real effects"
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def write_metadata(total, report):
    master_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    thumbnail_hash = hashlib.sha256(THUMBNAIL.read_bytes()).hexdigest()
    reviewed = master_hash == REVIEWED_MASTER_SHA256 and thumbnail_hash == REVIEWED_THUMBNAIL_SHA256
    doc = {
        "id": ITEM_ID,
        "title": "Nellie Narwhal and the Northern Lights | Colour Adventure for Kids",
        "description": "Nellie and Oona follow green, blue and violet light beneath the Arctic ice to help Kiko cross a calm lane and reunite with his mother.\n\nAn original Tiny Tales musical story about colours, courage, safe pauses, friendship and family for children ages 3 to 7.",
        "tags": ["narwhal story for kids", "northern lights for kids", "colour song", "seal family story", "Arctic animals", "musical story for kids", "Tiny Tales"],
        "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": True,
        "output": str(OUTPUT), "duration_seconds": total, "voice_profile": "maisie-uk",
        "character_voice_profiles": {"nellie": "natasha-au", "kiko": "ana-us"},
        "delivery": "emotion-mapped melodic Arctic rescue ballad", "bpm": BPM,
        "format_family": "underwater light-and-colour rescue ballad",
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
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "FOLLOW THE LIGHTS!",
        "thumbnail_reviewed": reviewed, "manual_visual_review_passed": reviewed,
        "transition_contact_sheet_reviewed": reviewed, "quality_contact_sheet_reviewed": reviewed,
        "reviewed_sha256": master_hash,
        "manual_review_notes": "Review remains valid only for the exact hash-locked master and thumbnail. General sheet, every transition, floe geography, colour order, scene-8-only swim, scene-9-only reunion/full aurora, final-only end card, waveform and thumbnail require review.",
        "integrated_loudness_lufs": report["integrated_loudness_lufs"], "true_peak_dbfs": report["true_peak_dbfs"],
        "true_rigged_3d_animation": False, "paid_generation_used": False, "new_image_generation_calls": 9,
        "spoken_sound_effect_words_removed": True, "upload_queue_released": False,
        "narration_pacing_policy": "three short phrases per scene; target at most 140 WPM, hard line ceiling 145 WPM and at least 0.4 seconds between phrases",
    }
    META.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def configure_engine() -> None:
    base.ITEM_ID = ITEM_ID; base.WORK = WORK; base.OUTPUT = OUTPUT; base.PLAN = PLAN; base.META = META; base.THUMBNAIL = THUMBNAIL
    base.REVIEWED_MASTER_SHA256 = REVIEWED_MASTER_SHA256; base.REVIEWED_THUMBNAIL_SHA256 = REVIEWED_THUMBNAIL_SHA256
    base.BPM = BPM; base.BEAT = BEAT; base.EIGHTH = EIGHTH; base.SCENE_SECONDS = SCENE_SECONDS; base.END_SECONDS = END_SECONDS; base.LINE_OFFSETS = LINE_OFFSETS
    base.ASSETS = ASSETS; base.VOICE_PROFILES = VOICE_PROFILES; base.SCENE_PROFILES = SCENE_PROFILES
    base.load_plan = load_plan; base.make_voices = make_voices; base.effect_windows = effect_windows
    base.frame_for = frame_for; base.make_music = make_music; base.make_thumbnail = make_thumbnail; base.quality = quality; base.write_metadata = write_metadata
    base.configure_engine()
    engine.PACING_VERSION = "nellie-v1"


def main() -> None:
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
