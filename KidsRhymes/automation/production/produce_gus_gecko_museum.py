"""Produce Gus Gecko's Upside-Down Museum as a synchronized musical story."""

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
ITEM_ID = "gus-gecko-upside-down-museum-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
REVIEWED_MASTER_SHA256 = "1ef800d545d0ddefa3ee1730d2a64e745f6e8670cffb9d0d9d5382ccd82b68a3"
REVIEWED_THUMBNAIL_SHA256 = "daef61ab0efd82d6226f790233fbf4b651993d4b577fafa256da889a21191319"
BPM = 96
BEAT = 60 / BPM
EIGHTH = BEAT / 2
SCENE_SECONDS = BEAT * 16
END_SECONDS = 4.0
LINE_OFFSETS = (EIGHTH, EIGHTH * 11, EIGHTH * 21)

ASSETS = (
    "gus-gecko-opening-v1.png",
    "gus-gecko-placement-clues-v1.png",
    "gus-gecko-above-v1.png",
    "gus-gecko-below-v1.png",
    "gus-gecko-beside-v1.png",
    "gus-gecko-between-v1.png",
    "gus-gecko-front-behind-v1.png",
    "gus-gecko-gallery-audit-v1.png",
    "gus-gecko-gallery-finale-v1.png",
)

VOICE_PROFILES = {
    "natasha-moonlit": {**core.select_voice_profile("natasha-au"), "rate": "-12%", "pitch": "+3Hz"},
    "natasha-curious": {**core.select_voice_profile("natasha-au"), "rate": "-9%", "pitch": "+6Hz"},
    "natasha-precise": {**core.select_voice_profile("natasha-au"), "rate": "-10%", "pitch": "+4Hz"},
    "natasha-wonder": {**core.select_voice_profile("natasha-au"), "rate": "-11%", "pitch": "+8Hz"},
    "natasha-bright": {**core.select_voice_profile("natasha-au"), "rate": "-7%", "pitch": "+9Hz"},
    "natasha-finale": {**core.select_voice_profile("natasha-au"), "rate": "-6%", "pitch": "+10Hz"},
    "ana-gus": {**core.select_voice_profile("ana-us"), "rate": "-9%", "pitch": "+9Hz"},
    "ana-gus-care": {**core.select_voice_profile("ana-us"), "rate": "-12%", "pitch": "+5Hz"},
    "ana-gus-bright": {**core.select_voice_profile("ana-us"), "rate": "-7%", "pitch": "+12Hz"},
    "ryan-mara": {**core.select_voice_profile("ryan-uk"), "rate": "-11%", "pitch": "+1Hz"},
    "ryan-mara-warm": {**core.select_voice_profile("ryan-uk"), "rate": "-10%", "pitch": "+4Hz"},
    "ryan-mara-bright": {**core.select_voice_profile("ryan-uk"), "rate": "-7%", "pitch": "+7Hz"},
}

SCENE_PROFILES = (
    ("natasha-moonlit", "ryan-mara", "ana-gus-bright"),
    ("ryan-mara-warm", "natasha-curious", "natasha-precise"),
    ("natasha-wonder", "ryan-mara", "ana-gus"),
    ("natasha-precise", "ryan-mara-warm", "ana-gus-care"),
    ("natasha-curious", "ryan-mara", "ana-gus"),
    ("natasha-wonder", "ryan-mara-warm", "ana-gus-care"),
    ("natasha-precise", "ana-gus", "ryan-mara-warm"),
    ("natasha-bright", "ryan-mara-bright", "ana-gus-bright"),
    ("natasha-finale", "ana-gus-bright", "ryan-mara-bright"),
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
            raw = WORK / f"voice-raw-gus-v2-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.mp3"
            target = WORK / f"voice-grid-gus-v2-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
                ).save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, 2.7, words * 60.0 / 135.0)


def effect_windows(scene: int) -> list[dict]:
    names = (
        ("trolley_wheel_stop", "four_cases_settle", "gecko_toe_touch"),
        ("brass_keys_turn", "display_bays_open", "velvet_route_slide"),
        ("ladder_toe_steps", "moth_bracket_click", "moonstone_chime"),
        ("shelf_toe_grip", "fern_tile_slide", "low_slot_click"),
        ("brass_rail_steps", "amber_case_set", "shell_beside_chime"),
        ("rope_lower", "moon_seed_settle", "two_birds_chime"),
        ("glass_globe_ring", "compass_set", "depth_chime"),
        ("ceiling_rail_steps", "gallery_check_chimes", "double_doors_open"),
        ("museum_glockenspiel", "glass_handbell", "visitor_steps"),
    )[scene]
    starts = (0.7, 3.9, 7.45)
    return [
        {"effect": name, "local_start": start, "local_end": min(SCENE_SECONDS - 0.18, start + 1.55)}
        for name, start in zip(names, starts)
    ]


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 8 if event["phase"] == "end" else event["scene"] - 1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]
    rng = random.Random(9600 + index)
    mote_count = 18 if index == 8 else 9
    for j in range(mote_count):
        x = (rng.randint(80, 1840) + int(math.sin(local * 0.42 + j) * 5)) % 1920
        y = rng.randint(80, 880) + int(math.cos(local * 0.36 + j) * 4)
        radius = 1 + int((math.sin(local * 1.3 + j) + 1) * 0.45)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(255, 218, 140, 24 if index < 8 else 40))
    if event["phase"] == "end":
        draw.rectangle((0, 0, 1920, 1080), fill=(13, 20, 45, 76))
        draw.rounded_rectangle((430, 54, 1490, 220), 42, fill=(22, 31, 68, 232), outline=(236, 190, 95, 250), width=7)
        core.base.centered(draw, (960, 108), "EVERY TREASURE", core.base.F48, (255, 221, 135, 255), 3)
        core.base.centered(draw, (960, 176), "IN ITS PLACE", core.base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return semantic.apply(frame, event, t, "gus", ASSET_DIR)


def make_music(total: float):
    path = WORK / "original-upside-down-museum-caper.wav"
    rate = 48000
    rng = random.Random(963108)
    chords = (
        (174.61, 220.00, 261.63), (196.00, 246.94, 293.66), (220.00, 277.18, 329.63),
        (164.81, 207.65, 246.94), (196.00, 246.94, 311.13), (174.61, 220.00, 277.18),
        (146.83, 196.00, 246.94), (220.00, 277.18, 329.63), (246.94, 311.13, 369.99),
    )
    energy = (0.48, 0.58, 0.68, 0.62, 0.72, 0.66, 0.58, 0.84, 1.0)
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
            note = chord[(0, 2, 1, 2, 0, 1, 2, 1)[step]]
            pizz = (math.sin(math.tau * note * t) + 0.22 * math.sin(math.tau * note * 2 * t)) * math.exp(-6.2 * phase) * 0.020 * energy[scene]
            glass = math.sin(math.tau * note * 2.01 * t) * math.exp(-4.0 * phase) * 0.008 * energy[scene]
            bass = math.sin(math.tau * (chord[0] / 2) * t) * math.exp(-3.4 * (local % (BEAT * 2))) * 0.011 * energy[scene]
            chamber = sum(math.sin(math.tau * f * t) for f in chord) * 0.0038 * energy[scene]
            brush = rng.uniform(-1, 1) * math.exp(-35 * (local % (BEAT / 2))) * 0.0035 * energy[scene]
            snare = rng.uniform(-1, 1) * math.exp(-45 * phase) * (0.002 + 0.005 * (scene >= 7))
            value = pizz + glass + bass + chamber + brush + snare
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
    canvas = ImageEnhance.Color(canvas).enhance(1.09).convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((20, 20, 620, 130), 28, fill=(20, 30, 67, 238), outline=(242, 196, 102, 255), width=5)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 56)
    text = "CLIMB INTO PLACE!"
    box = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    draw.text((320 - (box[2] - box[0]) // 2, 45), text, font=font, fill=(255, 224, 135), stroke_width=4, stroke_fill=(8, 18, 45))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(THUMBNAIL, quality=89, optimize=True)


def quality(events, total, assets):
    report = BASIL_QUALITY(events, total, assets)
    semantic.write_evidence(WORK, events[:-1], frame_for, assets, "gus")
    report["format"] = "spatial-language museum caper"
    report["bpm"] = BPM
    report["visual_method"] = "independently animated identity-locked foreground cast with visible physical position changes over defocused museum environments"
    report["audio_method"] = "original 96 BPM emotion-mapped pizzicato, glass and chamber percussion with three character voices and 27 synchronized real effects"
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def write_metadata(total, report):
    master_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    thumbnail_hash = hashlib.sha256(THUMBNAIL.read_bytes()).hexdigest()
    reviewed = master_hash == REVIEWED_MASTER_SHA256 and thumbnail_hash == REVIEWED_THUMBNAIL_SHA256
    doc = {
        "id": ITEM_ID,
        "title": "Gus Gecko's Upside-Down Museum | Position Words for Kids",
        "description": "Gus Gecko climbs through a moonlit museum to return treasures above, below, beside, between, in front and behind while Mara Owl keeps every clue steady.\n\nAn original Tiny Tales musical story about position words, careful observation and helping for children ages 3 to 7.",
        "tags": ["position words for kids", "gecko story", "above and below", "beside and between", "museum for kids", "musical story for kids", "Tiny Tales"],
        "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": True,
        "output": str(OUTPUT), "duration_seconds": total, "voice_profile": "natasha-au",
        "character_voice_profiles": {"gus": "ana-us", "mara": "ryan-uk"},
        "delivery": "emotion-mapped melodic spatial-language caper", "bpm": BPM,
        "format_family": "spatial-language museum caper",
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
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "CLIMB INTO PLACE!",
        "thumbnail_reviewed": reviewed, "manual_visual_review_passed": reviewed,
        "transition_contact_sheet_reviewed": reviewed, "quality_contact_sheet_reviewed": reviewed,
        "reviewed_sha256": master_hash,
        "manual_review_notes": "Review remains valid only for the exact hash-locked master and thumbnail. General sheet, every transition, all six physical position relationships, stable horizons, scene-9-only visitors/music, Gus's landed final pose, final-only end card, waveform and thumbnail require review.",
        "integrated_loudness_lufs": report["integrated_loudness_lufs"], "true_peak_dbfs": report["true_peak_dbfs"],
        "true_rigged_3d_animation": False, "paid_generation_used": False, "new_image_generation_calls": 10,
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
    engine.PACING_VERSION = "gus-v2"


def main() -> None:
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
