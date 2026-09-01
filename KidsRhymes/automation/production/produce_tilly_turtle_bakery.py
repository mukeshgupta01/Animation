"""Produce Tilly Turtle's Travelling Bakery as a synchronized musical story."""

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
ITEM_ID = "tilly-turtle-travelling-bakery-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
REVIEWED_MASTER_SHA256 = "4c8d6e863f0fc0d9e9ae9d038421f095ee4f6657bf7d016e8f6cf657966dedd5"
REVIEWED_THUMBNAIL_SHA256 = "1960baf108c53cfb3c5d03e722232b753379a17b26db0d934dd0d15eb93e3d2b"
BPM = 98
BEAT = 60 / BPM
EIGHTH = BEAT / 2
SCENE_SECONDS = BEAT * 16
END_SECONDS = 4.0
LINE_OFFSETS = (EIGHTH, EIGHTH * 11, EIGHTH * 21)

ASSETS = (
    "tilly-turtle-opening-v1.png",
    "tilly-turtle-warm-cool-route-v1.png",
    "tilly-turtle-pier-choice-v1.png",
    "tilly-turtle-soft-crunchy-v1.png",
    "tilly-turtle-whole-half-mixup-v1.png",
    "tilly-turtle-two-halves-v1.png",
    "tilly-turtle-picnic-procession-v1.png",
    "tilly-turtle-opposites-picnic-v1.png",
    "tilly-turtle-sunset-finale-v1.png",
)

VOICE_PROFILES = {
    "ana-dawn": {**core.select_voice_profile("ana-us"), "rate": "-12%", "pitch": "+7Hz"},
    "ana-roll": {**core.select_voice_profile("ana-us"), "rate": "-8%", "pitch": "+11Hz"},
    "ana-curious": {**core.select_voice_profile("ana-us"), "rate": "-11%", "pitch": "+9Hz"},
    "ana-pause": {**core.select_voice_profile("ana-us"), "rate": "-14%", "pitch": "+3Hz"},
    "ana-finale": {**core.select_voice_profile("ana-us"), "rate": "-5%", "pitch": "+14Hz"},
    "maisie-tilly": {**core.select_voice_profile("maisie-uk"), "rate": "-11%", "pitch": "+6Hz"},
    "maisie-bright": {**core.select_voice_profile("maisie-uk"), "rate": "-8%", "pitch": "+10Hz"},
    "maisie-finale": {**core.select_voice_profile("maisie-uk"), "rate": "-5%", "pitch": "+13Hz"},
    "ryan-pip": {**core.select_voice_profile("ryan-uk"), "rate": "-10%", "pitch": "+4Hz"},
    "ryan-puffin": {**core.select_voice_profile("ryan-uk"), "rate": "-12%", "pitch": "+8Hz"},
    "natasha-seal": {**core.select_voice_profile("natasha-au"), "rate": "-12%", "pitch": "+8Hz"},
    "natasha-goat": {**core.select_voice_profile("natasha-au"), "rate": "-9%", "pitch": "+11Hz"},
    "natasha-group": {**core.select_voice_profile("natasha-au"), "rate": "-6%", "pitch": "+13Hz"},
}

SCENE_PROFILES = (
    ("ana-dawn", "maisie-tilly", "ryan-pip"),
    ("ana-roll", "maisie-bright", "ryan-pip"),
    ("ana-curious", "maisie-tilly", "natasha-seal"),
    ("ana-curious", "maisie-bright", "natasha-goat"),
    ("ana-pause", "ryan-pip", "maisie-tilly"),
    ("ana-roll", "maisie-tilly", "ryan-puffin"),
    ("ana-roll", "maisie-bright", "ryan-pip"),
    ("ana-curious", "maisie-tilly", "natasha-group"),
    ("ana-finale", "maisie-finale", "ryan-pip"),
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
            raw = WORK / f"voice-raw-tilly-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.mp3"
            target = WORK / f"voice-grid-tilly-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
                ).save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, 2.55, words * 60.0 / 130.0)


def effect_windows(scene: int) -> list[dict]:
    names = (
        ("warm_bun_steam", "cool_bowl_chime", "cart_bell_invite"),
        ("wheel_roll_cobbles", "warm_breeze", "cool_pier_mist"),
        ("soft_bun_press", "cool_berry_bowl", "seal_choice_chirp"),
        ("soft_roll_spring", "breadstick_crunch_tap", "goat_happy_step"),
        ("whole_loaf_setdown", "two_half_tokens", "thoughtful_bell_pause"),
        ("two_halves_setdown", "matching_plate_touch", "puffin_relief_flutter"),
        ("rolling_procession", "customer_footsteps", "downhill_cart_bell"),
        ("warm_cool_pair", "soft_crunchy_pair", "two_halves_nearly_join"),
        ("wheel_brush_rhythm", "breadstick_taps_and_claps", "brass_bell_finale"),
    )[scene]
    starts = (0.72, 3.95, 7.18)
    return [
        {"effect": name, "local_start": start, "local_end": min(SCENE_SECONDS - 0.18, start + 1.45)}
        for name, start in zip(names, starts)
    ]


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 8 if event["phase"] == "end" else event["scene"] - 1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]
    rng = random.Random(9800 + index)
    particle_count = 22 if index == 8 else (7 if index == 4 else 12)
    for j in range(particle_count):
        x = (rng.randint(90, 1830) + int(math.sin(local * 0.72 + j) * 7)) % 1920
        y = rng.randint(80, 930) + int(math.cos(local * 0.53 + j) * 5)
        radius = 1 + (j % 2)
        colour = (255, 220, 154, 34) if index >= 6 else (255, 244, 216, 22)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=colour)
    if event["phase"] == "end":
        draw.rectangle((0, 0, 1920, 1080), fill=(38, 25, 45, 66))
        draw.rounded_rectangle((430, 54, 1490, 220), 42, fill=(39, 72, 82, 232), outline=(255, 211, 153, 250), width=7)
        core.base.centered(draw, (960, 108), "WARM OR COOL • SOFT OR CRUNCHY", core.base.F48, (255, 239, 205, 255), 3)
        core.base.centered(draw, (960, 176), "OPPOSITES SHARE THE TREAT", core.base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return semantic.apply(frame, event, t, "tilly", ASSET_DIR)


def make_music(total: float):
    path = WORK / "original-travelling-bakery-song.wav"
    rate = 48000
    rng = random.Random(980901)
    chords = (
        (196.00, 246.94, 293.66), (220.00, 261.63, 329.63), (196.00, 246.94, 311.13),
        (233.08, 293.66, 349.23), (174.61, 220.00, 261.63), (196.00, 246.94, 293.66),
        (220.00, 277.18, 329.63), (233.08, 293.66, 369.99), (261.63, 329.63, 392.00),
    )
    energy = (0.58, 0.66, 0.68, 0.74, 0.38, 0.64, 0.82, 0.88, 1.0)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate)
        chunk = bytearray()
        for n in range(round(total * rate)):
            t = n / rate
            scene = min(8, int(t // SCENE_SECONDS))
            local = t - scene * SCENE_SECONDS
            chord = chords[scene]
            phase = local % BEAT
            half_phase = local % (BEAT / 2)
            step = int(local / (BEAT / 2)) % 8
            note = chord[(0, 1, 2, 1, 0, 2, 1, 2)[step]]
            marimba = math.sin(math.tau * note * t) * math.exp(-7.5 * half_phase) * 0.020 * energy[scene]
            pluck = (math.sin(math.tau * note * 2 * t) + 0.25 * math.sin(math.tau * note * 3 * t)) * math.exp(-10 * half_phase) * 0.007 * energy[scene]
            strings = sum(math.sin(math.tau * f * t) for f in chord) * 0.0034 * energy[scene]
            wheel = rng.uniform(-1, 1) * math.exp(-31 * (local % (BEAT / 4))) * 0.0028 * energy[scene]
            bell = math.sin(math.tau * 1320 * t) * math.exp(-9 * phase) * (0.0015 + 0.0025 * (scene in (0, 6, 8)))
            drum = math.sin(math.tau * 78 * phase) * math.exp(-25 * phase) * (0.0025 + 0.0045 * (scene == 8))
            value = marimba + pluck + strings + wheel + bell + drum
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
    draw.rounded_rectangle((18, 18, 675, 130), 28, fill=(24, 63, 72, 238), outline=(255, 213, 148, 255), width=5)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 56)
    text = "WARM OR COOL?"
    box = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    draw.text((346 - (box[2] - box[0]) // 2, 44), text, font=font, fill=(255, 244, 216), stroke_width=4, stroke_fill=(18, 47, 58))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(THUMBNAIL, quality=89, optimize=True)


def quality(events, total, assets):
    report = BASIL_QUALITY(events, total, assets)
    semantic.write_evidence(WORK, events[:-1], frame_for, assets, "tilly")
    report["format"] = "seaside delivery and food-texture musical"
    report["bpm"] = BPM
    report["visual_method"] = "independently animated identity-locked foreground cast with visible cart, food-shape and opposite-state actions over defocused coastal bakery environments"
    report["audio_method"] = "original 98 BPM pizzicato, marimba and tactile bakery-percussion song with four rotated voices and 27 synchronized real effects"
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def write_metadata(total, report):
    master_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    thumbnail_hash = hashlib.sha256(THUMBNAIL.read_bytes()).hexdigest()
    reviewed = master_hash == REVIEWED_MASTER_SHA256 and thumbnail_hash == REVIEWED_THUMBNAIL_SHA256
    doc = {
        "id": ITEM_ID,
        "title": "Tilly Turtle's Travelling Bakery | Opposites Story for Kids",
        "description": "Tilly Turtle rolls her travelling bakery from the warm harbour to the cool pier, comparing soft and crunchy treats and fixing one whole-loaf mix-up before a shared sunset picnic.\n\nAn original Tiny Tales musical story about opposites, polite choices, halves, problem-solving and sharing for children ages 3 to 7.",
        "tags": ["opposites for kids", "turtle story", "warm and cool", "soft and crunchy", "whole and half", "musical story for kids", "Tiny Tales"],
        "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": True,
        "output": str(OUTPUT), "duration_seconds": total, "voice_profile": "ana-us",
        "character_voice_profiles": {"tilly": "maisie-uk", "pip": "ryan-uk", "customers": "natasha-au"},
        "delivery": "emotion-mapped melodic seaside bakery story-song", "bpm": BPM,
        "format_family": "seaside delivery and food-texture musical",
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
        "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "WARM OR COOL?",
        "thumbnail_reviewed": reviewed, "manual_visual_review_passed": reviewed,
        "transition_contact_sheet_reviewed": reviewed, "quality_contact_sheet_reviewed": reviewed,
        "reviewed_sha256": master_hash,
        "manual_review_notes": "Review remains valid only for the exact hash-locked master and thumbnail. General sheet, every transition, cart/customer continuity, warm-cool and soft-crunchy truth, whole-to-two-halves correction, scene-9-only full ensemble, final-only end card, waveform and thumbnail require review.",
        "integrated_loudness_lufs": report["integrated_loudness_lufs"], "true_peak_dbfs": report["true_peak_dbfs"],
        "true_rigged_3d_animation": False, "paid_generation_used": False, "new_image_generation_calls": 13,
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
    engine.PACING_VERSION = "tilly-v1"


def main() -> None:
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
