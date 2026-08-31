"""Produce Pogo Penguin's Wobbly Ice Bridge as a synchronized musical story."""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import struct
import wave

import produce_basil_beaver_workshop as base


BASIL_QUALITY = base.quality
engine = base.engine
core = base.core
Image = base.Image
ImageDraw = base.ImageDraw
ImageEnhance = base.ImageEnhance
ImageFont = base.ImageFont
AUTOMATION = base.AUTOMATION
PROJECT = base.PROJECT
ITEM_ID = "pogo-penguin-wobbly-ice-bridge-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
REVIEWED_MASTER_SHA256 = "fffdfa340df9deeaede724e9019ab8a6ee93c64d41e0ee114abc34ea91e229c9"
REVIEWED_THUMBNAIL_SHA256 = "587777ec361a0e013b49193072c7dba8bbb108a366cbfeb63ad23c8ac50ffb96"
BPM = 104
BEAT = 60 / BPM
EIGHTH = BEAT / 2
SCENE_SECONDS = BEAT * 17
END_SECONDS = 4.0
LINE_OFFSETS = (EIGHTH, EIGHTH * 12, EIGHTH * 23)

ASSETS = (
    "pogo-penguin-opening-v1.png", "pogo-penguin-narrow-wobble-v1.png",
    "pogo-penguin-wide-stable-test-v1.png", "pogo-penguin-three-supports-v1.png",
    "pogo-penguin-two-rails-v1.png", "pogo-penguin-weight-test-v1.png",
    "pogo-penguin-cross-brace-v1.png", "pogo-penguin-first-crossing-v1.png",
    "pogo-penguin-theatre-finale-v1.png",
)

VOICE_PROFILES = {
    "ryan-bright": {**core.select_voice_profile("ryan-uk"), "rate": "-10%", "pitch": "+4Hz"},
    "ryan-test": {**core.select_voice_profile("ryan-uk"), "rate": "-13%", "pitch": "+2Hz"},
    "ryan-count": {**core.select_voice_profile("ryan-uk"), "rate": "-9%", "pitch": "+6Hz"},
    "ryan-relief": {**core.select_voice_profile("ryan-uk"), "rate": "-8%", "pitch": "+8Hz"},
    "ryan-finale": {**core.select_voice_profile("ryan-uk"), "rate": "-5%", "pitch": "+10Hz"},
    "ana-pogo": {**core.select_voice_profile("ana-us"), "rate": "-11%", "pitch": "+9Hz"},
    "ana-brave": {**core.select_voice_profile("ana-us"), "rate": "-8%", "pitch": "+12Hz"},
    "ana-finale": {**core.select_voice_profile("ana-us"), "rate": "-5%", "pitch": "+14Hz"},
    "natasha-mina": {**core.select_voice_profile("natasha-au"), "rate": "-12%", "pitch": "+5Hz"},
    "natasha-steady": {**core.select_voice_profile("natasha-au"), "rate": "-9%", "pitch": "+8Hz"},
    "natasha-finale": {**core.select_voice_profile("natasha-au"), "rate": "-6%", "pitch": "+11Hz"},
}

SCENE_PROFILES = (
    ("ryan-bright", "natasha-mina", "ana-pogo"),
    ("ryan-test", "ana-pogo", "natasha-mina"),
    ("ryan-test", "natasha-steady", "ana-brave"),
    ("ryan-count", "natasha-mina", "ana-pogo"),
    ("ryan-count", "natasha-steady", "ana-pogo"),
    ("ryan-test", "natasha-steady", "ana-brave"),
    ("ryan-test", "ana-pogo", "natasha-mina"),
    ("ryan-relief", "ana-brave", "natasha-steady"),
    ("ryan-finale", "ana-finale", "natasha-finale"),
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
            raw = WORK / f"voice-raw-pogo-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.mp3"
            target = WORK / f"voice-grid-pogo-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%").save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, 2.55, words * 60.0 / 130.0)


def effect_windows(scene: int) -> list[dict]:
    names = (
        ("measure_rope_pull", "ice_piece_sort", "theatre_music_call"),
        ("narrow_ice_flex", "planted_penguin_step", "spotter_rope_tension"),
        ("narrow_wobble_marker", "wide_deck_press", "stable_support_tone"),
        ("support_one_touch", "support_two_touch", "support_three_slide"),
        ("left_rail_knot", "right_rail_pull", "clear_path_brush"),
        ("two_snow_sacks_settle", "plumb_bead_straight", "level_load_chime"),
        ("gentle_wind_flags", "cross_strap_tighten", "plumb_bead_settle"),
        ("single_penguin_footsteps", "drum_carry_rustle", "waiting_wave"),
        ("pogo_drum_finale", "mina_xylophone_finale", "chime_cymbal_applause"),
    )[scene]
    starts = (0.72, 4.12, 7.48)
    return [{"effect": name, "local_start": start, "local_end": min(SCENE_SECONDS - 0.18, start + 1.45)} for name, start in zip(names, starts)]


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 8 if event["phase"] == "end" else event["scene"] - 1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]; rng = random.Random(10400 + index)
    for j in range(24 if index == 8 else 12):
        x = (rng.randint(70, 1850) + int(math.sin(local * 0.8 + j) * 8)) % 1920
        y = rng.randint(70, 940) + int(math.cos(local * 0.65 + j) * 6)
        radius = 1 + (j % 2)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(205, 241, 255, 28 if index < 8 else 42))
    if event["phase"] == "end":
        draw.rectangle((0, 0, 1920, 1080), fill=(19, 36, 66, 70))
        draw.rounded_rectangle((470, 54, 1450, 220), 42, fill=(22, 58, 82, 232), outline=(255, 207, 122, 250), width=7)
        core.base.centered(draw, (960, 108), "WIDE • LEVEL • STEADY", core.base.F48, (222, 249, 255, 255), 3)
        core.base.centered(draw, (960, 176), "TEAMWORK BRIDGES EVERY BEAT", core.base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return frame.convert("RGB")


def make_music(total: float):
    path = WORK / "original-steady-bridge-march.wav"; rate = 48000; rng = random.Random(1040901)
    chords = ((174.61,220.00,261.63),(174.61,207.65,261.63),(196.00,246.94,293.66),(220.00,261.63,329.63),(196.00,246.94,311.13),(220.00,277.18,329.63),(196.00,246.94,293.66),(233.08,293.66,349.23),(261.63,329.63,392.00))
    energy = (0.58,0.46,0.66,0.72,0.76,0.62,0.74,0.86,1.0)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); chunk = bytearray()
        for n in range(round(total * rate)):
            t=n/rate; scene=min(8,int(t//SCENE_SECONDS)); local=t-scene*SCENE_SECONDS; chord=chords[scene]
            phase=local%BEAT; eighth=local%(BEAT/2); step=int(local/(BEAT/2))%8; note=chord[(0,1,2,1,0,2,1,2)[step]]
            marimba=math.sin(math.tau*note*t)*math.exp(-7.2*eighth)*0.019*energy[scene]
            pluck=(math.sin(math.tau*note*2*t)+0.2*math.sin(math.tau*note*3*t))*math.exp(-9*eighth)*0.0065*energy[scene]
            bass=math.sin(math.tau*(chord[0]/2)*t)*0.006*energy[scene]
            snow=rng.uniform(-1,1)*math.exp(-30*(local%(BEAT/4)))*0.0025*energy[scene]
            drum=math.sin(math.tau*82*phase)*math.exp(-25*phase)*(0.0025+0.006*(scene==8))
            xyl=math.sin(math.tau*note*3.01*t)*math.exp(-10*phase)*(0.001+0.004*(scene==8))
            value=marimba+pluck+bass+snow+drum+xyl
            if t>=9*SCENE_SECONDS: value*=min(1,(total-t)/0.8)
            sample=int(max(-1,min(1,value))*30000); chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source=Image.open(ASSET_DIR/ASSETS[8]).convert("RGB"); width=round(source.height*16/9); left=max(0,(source.width-width)//2)
    canvas=source.crop((left,0,left+width,source.height)).resize((1280,720),Image.Resampling.LANCZOS)
    canvas=ImageEnhance.Color(canvas).enhance(1.08).convert("RGBA"); draw=ImageDraw.Draw(canvas,"RGBA")
    draw.rounded_rectangle((18,18,650,130),28,fill=(18,52,77,238),outline=(255,207,119,255),width=5)
    font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",56); text="BUILD IT STEADY!"; box=draw.textbbox((0,0),text,font=font,stroke_width=3)
    draw.text((334-(box[2]-box[0])//2,44),text,font=font,fill=(231,251,255),stroke_width=4,stroke_fill=(10,35,58))
    THUMBNAIL.parent.mkdir(parents=True,exist_ok=True); canvas.convert("RGB").save(THUMBNAIL,quality=89,optimize=True)


def quality(events,total,assets):
    report=BASIL_QUALITY(events,total,assets); report["format"]="balance-and-bridge engineering adventure"; report["bpm"]=BPM
    report["visual_method"]="nine reviewed tactile Antarctic engineering tableaux with exact shallow-site, width, support, rail, brace, crossing and theatre continuity"
    report["audio_method"]="original 104 BPM pizzicato, marimba, snow-percussion and theatre-band march with three rotated voices and 27 synchronized real effects"
    (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); return report


def write_metadata(total,report):
    master_hash=hashlib.sha256(OUTPUT.read_bytes()).hexdigest(); thumbnail_hash=hashlib.sha256(THUMBNAIL.read_bytes()).hexdigest(); reviewed=master_hash==REVIEWED_MASTER_SHA256 and thumbnail_hash==REVIEWED_THUMBNAIL_SHA256
    doc={
        "id":ITEM_ID,"title":"Pogo Penguin's Wobbly Ice Bridge | Building Story for Kids",
        "description":"Pogo and Mina test narrow and wide ice pieces, count three supports, add two rails and a cross brace, then carry their instruments one at a time to the snow theatre.\n\nAn original Tiny Tales musical engineering story about balance, stability, counting, testing and teamwork for children ages 3 to 7.",
        "tags":["engineering for kids","penguin story","building a bridge","balance for kids","counting to three","musical story for kids","Tiny Tales"],
        "category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":True,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":"ryan-uk",
        "character_voice_profiles":{"pogo":"ana-us","mina":"natasha-au"},"delivery":"emotion-mapped melodic Antarctic engineering story-song","bpm":BPM,"format_family":"balance-and-bridge engineering adventure",
        "quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"quality_report":f"automation/production-work/{ITEM_ID}/quality-report.json","transition_audit":f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "lyric_visual_emotion_audit":f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json","narration_visual_sync_audit":f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json","narration_pacing_audit":f"automation/production-work/{ITEM_ID}/narration-pacing-audit.json",
        "quality_contact_sheet":f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png","transition_contact_sheet":f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png","musical_story_waveform":f"automation/production-work/{ITEM_ID}/musical-story-waveform.png","musical_story_spectrum":f"automation/production-work/{ITEM_ID}/musical-story-spectrum.png",
        "prepared_thumbnail":f"automation/thumbnails/{ITEM_ID}.jpg","thumbnail_hook":"BUILD IT STEADY!","thumbnail_reviewed":reviewed,"manual_visual_review_passed":reviewed,"transition_contact_sheet_reviewed":reviewed,"quality_contact_sheet_reviewed":reviewed,"reviewed_sha256":master_hash,
        "manual_review_notes":"Review remains valid only for the exact hash-locked master and thumbnail. General sheet, every transition, shallow-site safety, narrow-to-wide test, three supports, opposite rails, X brace, Pogo-only first crossing, scene-9-only band, final-only end card, waveform and thumbnail require review.",
        "integrated_loudness_lufs":report["integrated_loudness_lufs"],"true_peak_dbfs":report["true_peak_dbfs"],"true_rigged_3d_animation":False,"paid_generation_used":False,"new_image_generation_calls":12,"spoken_sound_effect_words_removed":True,"upload_queue_released":False,
        "narration_pacing_policy":"three short phrases per scene; target at most 140 WPM, hard line ceiling 145 WPM and at least 0.4 seconds between phrases"}
    META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def configure_engine()->None:
    base.ITEM_ID=ITEM_ID; base.WORK=WORK; base.OUTPUT=OUTPUT; base.PLAN=PLAN; base.META=META; base.THUMBNAIL=THUMBNAIL; base.REVIEWED_MASTER_SHA256=REVIEWED_MASTER_SHA256; base.REVIEWED_THUMBNAIL_SHA256=REVIEWED_THUMBNAIL_SHA256
    base.BPM=BPM; base.BEAT=BEAT; base.EIGHTH=EIGHTH; base.SCENE_SECONDS=SCENE_SECONDS; base.END_SECONDS=END_SECONDS; base.LINE_OFFSETS=LINE_OFFSETS; base.ASSETS=ASSETS; base.VOICE_PROFILES=VOICE_PROFILES; base.SCENE_PROFILES=SCENE_PROFILES
    base.load_plan=load_plan; base.make_voices=make_voices; base.effect_windows=effect_windows; base.frame_for=frame_for; base.make_music=make_music; base.make_thumbnail=make_thumbnail; base.quality=quality; base.write_metadata=write_metadata; base.configure_engine(); engine.PACING_VERSION="pogo-v1"


def main()->None:
    configure_engine(); engine.main()


if __name__=="__main__": main()
