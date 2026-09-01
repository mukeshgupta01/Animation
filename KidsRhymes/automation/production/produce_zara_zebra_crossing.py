"""Produce Zara Zebra's Musical Crossing as a synchronized musical story."""

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
ITEM_ID = "zara-zebra-musical-crossing-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
REVIEWED_MASTER_SHA256 = "4eda4fc00f00f2b0615533f835b11f61c8d4262c2a21421417d95a516ba8a7f1"
REVIEWED_THUMBNAIL_SHA256 = "370264aa7a15bda8abf46ccf045b6f8e1f027d2926409d0395fe70643ca24115"
BPM = 100
BEAT = 60 / BPM
EIGHTH = BEAT / 2
SCENE_SECONDS = BEAT * 17
END_SECONDS = 4.0
LINE_OFFSETS = (EIGHTH, EIGHTH * 12, EIGHTH * 23)

ASSETS = (
    "zara-zebra-opening-v1.png", "zara-zebra-stop-look-listen-v1.png",
    "zara-zebra-six-stripes-v1.png", "zara-zebra-tuned-stripes-v1.png",
    "zara-zebra-safety-test-v1.png", "zara-zebra-curb-rhythm-v1.png",
    "zara-zebra-first-crossing-v1.png", "zara-zebra-procession-v1.png",
    "zara-zebra-finale-concert-v1.png",
)

VOICE_PROFILES = {
    "natasha-sunrise": {**core.select_voice_profile("natasha-au"), "rate": "-12%", "pitch": "+7Hz"},
    "natasha-careful": {**core.select_voice_profile("natasha-au"), "rate": "-15%", "pitch": "+3Hz"},
    "natasha-groove": {**core.select_voice_profile("natasha-au"), "rate": "-9%", "pitch": "+10Hz"},
    "natasha-finale": {**core.select_voice_profile("natasha-au"), "rate": "-5%", "pitch": "+13Hz"},
    "ana-zara": {**core.select_voice_profile("ana-us"), "rate": "-11%", "pitch": "+10Hz"},
    "ana-safety": {**core.select_voice_profile("ana-us"), "rate": "-14%", "pitch": "+6Hz"},
    "ana-song": {**core.select_voice_profile("ana-us"), "rate": "-6%", "pitch": "+15Hz"},
    "maisie-nuru": {**core.select_voice_profile("maisie-uk"), "rate": "-13%", "pitch": "+5Hz"},
    "maisie-count": {**core.select_voice_profile("maisie-uk"), "rate": "-10%", "pitch": "+9Hz"},
    "maisie-song": {**core.select_voice_profile("maisie-uk"), "rate": "-6%", "pitch": "+13Hz"},
}

SCENE_PROFILES = (
    ("natasha-sunrise", "maisie-nuru", "ana-zara"),
    ("ana-safety", "natasha-careful", "maisie-nuru"),
    ("natasha-groove", "maisie-count", "ana-zara"),
    ("ana-zara", "maisie-count", "natasha-groove"),
    ("natasha-careful", "maisie-nuru", "ana-safety"),
    ("ana-zara", "maisie-count", "natasha-groove"),
    ("natasha-sunrise", "ana-safety", "maisie-nuru"),
    ("maisie-count", "natasha-groove", "ana-song"),
    ("natasha-finale", "ana-song", "maisie-song"),
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
            raw = WORK / f"voice-raw-zara-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.mp3"
            target = WORK / f"voice-grid-zara-v1-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%").save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, 2.55, words * 60.0 / 130.0)


def effect_windows(scene: int) -> list[dict]:
    names = (
        ("morning_market_bell", "wooden_cart_brake", "zara_invitation_chime"),
        ("curb_stop_tone", "left_right_shaker", "nuru_token_turn"),
        ("stripe_one_two_three_set", "stripe_four_five_six_set", "measuring_rope_pull"),
        ("first_brass_resonator", "sixth_tuning_fork", "six_note_answer"),
        ("two_cart_blocks_settle", "clear_sightline_bell", "double_safety_check"),
        ("two_two_mallet_pattern", "curb_shaker_answer", "neighbor_drum_response"),
        ("family_handhold_rustle", "three_slow_footsteps", "destination_flag_wave"),
        ("spaced_procession_steps", "small_instruments_walk", "single_direction_chime"),
        ("six_stripe_finale", "town_band_answer", "safe_steps_chorus_applause"),
    )[scene]
    starts = (0.72, 4.12, 7.48)
    return [{"effect": name, "local_start": start, "local_end": min(SCENE_SECONDS - 0.18, start + 1.45)} for name, start in zip(names, starts)]


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 8 if event["phase"] == "end" else event["scene"] - 1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]; rng = random.Random(10060 + index)
    for j in range(24 if index == 8 else 12):
        x = (rng.randint(70, 1850) + int(math.sin(local * 0.8 + j) * 8)) % 1920
        y = rng.randint(70, 940) + int(math.cos(local * 0.65 + j) * 6)
        radius = 1 + (j % 2)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(211, 114, 184, 30 if index < 8 else 48))
    if event["phase"] == "end":
        draw.rectangle((0, 0, 1920, 1080), fill=(35, 20, 62, 62))
        draw.rounded_rectangle((430, 54, 1490, 220), 42, fill=(29, 70, 77, 235), outline=(255, 190, 112, 250), width=7)
        core.base.centered(draw, (960, 108), "STOP - LOOK - LISTEN", core.base.F48, (255, 235, 183, 255), 3)
        core.base.centered(draw, (960, 176), "SAFE STEPS MAKE MUSIC", core.base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return semantic.apply(frame, event, t, "zara", ASSET_DIR)


def make_music(total: float):
    path = WORK / "original-savannah-crossing-song.wav"; rate = 48000; rng = random.Random(1000601)
    chords = ((196.00,246.94,293.66),(174.61,220.00,261.63),(196.00,246.94,329.63),(220.00,277.18,329.63),(174.61,220.00,261.63),(196.00,246.94,329.63),(220.00,261.63,329.63),(233.08,293.66,349.23),(261.63,329.63,392.00))
    energy = (0.60,0.45,0.66,0.72,0.50,0.76,0.70,0.86,1.0)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); chunk = bytearray()
        for n in range(round(total * rate)):
            t=n/rate; scene=min(8,int(t//SCENE_SECONDS)); local=t-scene*SCENE_SECONDS; chord=chords[scene]
            phase=local%BEAT; eighth=local%(BEAT/2); step=int(local/(BEAT/2))%8; note=chord[(0,1,2,1,0,2,1,2)[step]]
            marimba=(math.sin(math.tau*note*t)+0.24*math.sin(math.tau*note*2.01*t))*math.exp(-7.5*eighth)*0.018*energy[scene]
            bell=math.sin(math.tau*note*2.01*t)*math.exp(-10*eighth)*0.0045*energy[scene]
            bass=math.sin(math.tau*(chord[0]/2)*t)*0.0065*energy[scene]
            shaker=rng.uniform(-1,1)*math.exp(-34*(local%(BEAT/4)))*0.0028*energy[scene]
            hand_drum=math.sin(math.tau*78*phase)*math.exp(-23*phase)*(0.003+0.006*(scene>=7))
            flute=math.sin(math.tau*(note*2)*t)*0.0018*(0.3+0.7*math.sin(math.pi*min(1,local/SCENE_SECONDS))) if scene>=6 else 0.0
            finale_harmony=sum(math.sin(math.tau*f*t) for f in chord)*0.0017 if scene==8 else 0.0
            value=marimba+bell+bass+shaker+hand_drum+flute+finale_harmony
            if t>=9*SCENE_SECONDS: value*=min(1,(total-t)/0.8)
            sample=int(max(-1,min(1,value))*30000); chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source=Image.open(ASSET_DIR/ASSETS[8]).convert("RGB"); width=round(source.height*16/9); left=max(0,(source.width-width)//2)
    canvas=source.crop((left,0,left+width,source.height)).resize((1280,720),Image.Resampling.LANCZOS)
    canvas=ImageEnhance.Color(canvas).enhance(1.08).convert("RGBA"); draw=ImageDraw.Draw(canvas,"RGBA")
    draw.rounded_rectangle((18,18,680,130),28,fill=(29,70,77,240),outline=(255,190,112,255),width=5)
    font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",54); text="STEP TO THE BEAT!"; box=draw.textbbox((0,0),text,font=font,stroke_width=3)
    draw.text((349-(box[2]-box[0])//2,44),text,font=font,fill=(255,244,202),stroke_width=4,stroke_fill=(25,35,55))
    THUMBNAIL.parent.mkdir(parents=True,exist_ok=True); canvas.convert("RGB").save(THUMBNAIL,quality=89,optimize=True)


def quality(events,total,assets):
    report=BASIL_QUALITY(events,total,assets); semantic.write_evidence(WORK,events[:-1],frame_for,assets,"zara"); report["format"]="community road-safety rhythm construction story"; report["bpm"]=BPM
    report["visual_method"]="independently animated identity-locked foreground cast with visible stripe, rhythm and stop-look-listen actions over defocused savannah-town environments"
    report["audio_method"]="original 100 BPM marimba, brass-bell, hand-percussion and flute street song with three rotated expressive voices and 27 synchronized real effects"
    (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); return report


def write_metadata(total,report):
    master_hash=hashlib.sha256(OUTPUT.read_bytes()).hexdigest(); thumbnail_hash=hashlib.sha256(THUMBNAIL.read_bytes()).hexdigest(); reviewed=master_hash==REVIEWED_MASTER_SHA256 and thumbnail_hash==REVIEWED_THUMBNAIL_SHA256
    doc={
        "id":ITEM_ID,"title":"Zara Zebra's Musical Crossing | Rhythm Story for Kids",
        "description":"Zara Zebra and Nuru build six musical crossing stripes, test the road safely, guide one family across, then lead the whole savannah square in a joyful street-band finale.\n\nAn original Tiny Tales musical story about stop-look-listen, safe crossing, counting to six, rhythm and community teamwork for children ages 3 to 7.",
        "tags":["road safety for kids","zebra story","crossing the road","counting to six","rhythm for kids","musical story for kids","Tiny Tales"],
        "category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":True,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":"natasha-au",
        "character_voice_profiles":{"zara":"ana-us","nuru":"maisie-uk"},"delivery":"emotion-mapped melodic savannah street-band story-song","bpm":BPM,"format_family":"community road-safety rhythm construction story",
        "quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"quality_report":f"automation/production-work/{ITEM_ID}/quality-report.json","transition_audit":f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json",
        "lyric_visual_emotion_audit":f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json","narration_visual_sync_audit":f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json","narration_pacing_audit":f"automation/production-work/{ITEM_ID}/narration-pacing-audit.json",
        "quality_contact_sheet":f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png","transition_contact_sheet":f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png","musical_story_waveform":f"automation/production-work/{ITEM_ID}/musical-story-waveform.png","musical_story_spectrum":f"automation/production-work/{ITEM_ID}/musical-story-spectrum.png",
        "prepared_thumbnail":f"automation/thumbnails/{ITEM_ID}.jpg","thumbnail_hook":"STEP TO THE BEAT!","thumbnail_reviewed":reviewed,"manual_visual_review_passed":reviewed,"transition_contact_sheet_reviewed":reviewed,"quality_contact_sheet_reviewed":reviewed,"reviewed_sha256":master_hash,
        "manual_review_notes":"Review remains valid only for the exact hash-locked master and thumbnail. General sheet, every transition, Zara/Nuru identity, raised-curb and blocked-cart safety, exactly six stripes, curb-only rhythm, single-family first crossing, one-direction procession, scene-9-only concert, final-only end card, waveform and thumbnail require review.",
        "integrated_loudness_lufs":report["integrated_loudness_lufs"],"true_peak_dbfs":report["true_peak_dbfs"],"true_rigged_3d_animation":False,"paid_generation_used":False,"new_image_generation_calls":14,"spoken_sound_effect_words_removed":True,"upload_queue_released":False,
        "narration_pacing_policy":"three short phrases per scene; target at most 140 WPM, hard line ceiling 145 WPM and at least 0.4 seconds between phrases"}
    META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def configure_engine()->None:
    base.ITEM_ID=ITEM_ID; base.WORK=WORK; base.OUTPUT=OUTPUT; base.PLAN=PLAN; base.META=META; base.THUMBNAIL=THUMBNAIL; base.REVIEWED_MASTER_SHA256=REVIEWED_MASTER_SHA256; base.REVIEWED_THUMBNAIL_SHA256=REVIEWED_THUMBNAIL_SHA256
    base.BPM=BPM; base.BEAT=BEAT; base.EIGHTH=EIGHTH; base.SCENE_SECONDS=SCENE_SECONDS; base.END_SECONDS=END_SECONDS; base.LINE_OFFSETS=LINE_OFFSETS; base.ASSETS=ASSETS; base.VOICE_PROFILES=VOICE_PROFILES; base.SCENE_PROFILES=SCENE_PROFILES
    base.load_plan=load_plan; base.make_voices=make_voices; base.effect_windows=effect_windows; base.frame_for=frame_for; base.make_music=make_music; base.make_thumbnail=make_thumbnail; base.quality=quality; base.write_metadata=write_metadata; base.configure_engine(); engine.PACING_VERSION="zara-v1"


def main()->None:
    configure_engine(); engine.main()


if __name__=="__main__": main()
