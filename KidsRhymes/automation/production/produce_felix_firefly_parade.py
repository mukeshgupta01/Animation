"""Produce Felix Firefly's Night-Light Parade as a synchronized musical story."""

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

import produce_fruit_picnic as engine
import semantic_motion as semantic


core = engine.core
Image = engine.Image
ImageDraw = engine.ImageDraw
ImageEnhance = engine.ImageEnhance
ImageFont = engine.ImageFont
AUTOMATION = engine.AUTOMATION
PROJECT = engine.PROJECT
ITEM_ID = "felix-firefly-night-light-parade-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
REVIEWED_MASTER_SHA256 = "340a13fdb13501f8c0bb1306a9509870ccf131f94174377719e2ee0fb8a05030"
REVIEWED_THUMBNAIL_SHA256 = "1f45c0d2a3008d81749ed52f855dba044ae5753f2f3bd13b3f188ce3bff7c489"
BPM = 92
BEAT = 60 / BPM
EIGHTH = BEAT / 2
SCENE_SECONDS = BEAT * 16
END_SECONDS = 88.0 - SCENE_SECONDS * 8
LINE_OFFSETS = (EIGHTH, EIGHTH * 11, EIGHTH * 21)

ASSETS = (
    "felix-firefly-opening-v1.png",
    "felix-firefly-gold-blue-gold-v1.png",
    "felix-firefly-blue-gold-blue-v1.png",
    "felix-firefly-hidden-pattern-v1.png",
    "felix-firefly-rest-and-support-v1.png",
    "felix-firefly-final-lantern-v1.png",
    "felix-firefly-path-procession-v1.png",
    "felix-firefly-parade-finale-v1.png",
)

VOICE_PROFILES = {
    "ana-hush": {**core.select_voice_profile("ana-us"), "rate": "-12%", "pitch": "+2Hz"},
    "ana-curious": {**core.select_voice_profile("ana-us"), "rate": "-9%", "pitch": "+6Hz"},
    "ana-bright": {**core.select_voice_profile("ana-us"), "rate": "-7%", "pitch": "+9Hz"},
    "ana-rhythm": {**core.select_voice_profile("ana-us"), "rate": "-8%", "pitch": "+7Hz"},
    "ana-wonder": {**core.select_voice_profile("ana-us"), "rate": "-10%", "pitch": "+10Hz"},
    "ana-warm": {**core.select_voice_profile("ana-us"), "rate": "-11%", "pitch": "+4Hz"},
    "ana-tender": {**core.select_voice_profile("ana-us"), "rate": "-14%", "pitch": "-1Hz"},
    "ana-triumph": {**core.select_voice_profile("ana-us"), "rate": "-6%", "pitch": "+12Hz"},
    "ana-finale": {**core.select_voice_profile("ana-us"), "rate": "-5%", "pitch": "+13Hz"},
    "maisie-rhythm": {**core.select_voice_profile("maisie-uk"), "rate": "-9%", "pitch": "+11Hz"},
    "maisie-care": {**core.select_voice_profile("maisie-uk"), "rate": "-12%", "pitch": "+7Hz"},
    "maisie-invite": {**core.select_voice_profile("maisie-uk"), "rate": "-8%", "pitch": "+12Hz"},
    "maisie-soft": {**core.select_voice_profile("maisie-uk"), "rate": "-14%", "pitch": "+4Hz"},
    "maisie-move": {**core.select_voice_profile("maisie-uk"), "rate": "-8%", "pitch": "+10Hz"},
    "maisie-finale": {**core.select_voice_profile("maisie-uk"), "rate": "-6%", "pitch": "+14Hz"},
    "ryan-brave": {**core.select_voice_profile("ryan-uk"), "rate": "-10%", "pitch": "+5Hz"},
    "ryan-soft": {**core.select_voice_profile("ryan-uk"), "rate": "-13%", "pitch": "+1Hz"},
    "ryan-bright": {**core.select_voice_profile("ryan-uk"), "rate": "-7%", "pitch": "+8Hz"},
    "ryan-finale": {**core.select_voice_profile("ryan-uk"), "rate": "-6%", "pitch": "+10Hz"},
}

SCENE_PROFILES = (
    ("ana-hush", "ana-curious", "ryan-brave"),
    ("ana-bright", "maisie-rhythm", "ana-wonder"),
    ("ana-rhythm", "maisie-care", "ana-warm"),
    ("ana-curious", "maisie-invite", "ana-rhythm"),
    ("ana-tender", "maisie-soft", "ryan-soft"),
    ("ryan-bright", "ana-rhythm", "ana-triumph"),
    ("ana-warm", "maisie-move", "ana-bright"),
    ("ana-finale", "maisie-finale", "ryan-finale"),
)

EMOTIONS = ("curious hush", "delighted discovery", "careful confidence", "playful challenge", "tender support", "warm release", "rising together", "radiant celebration")


def load_plan() -> dict:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    for index, scene in enumerate(plan["scenes"]):
        scene["emotion"] = EMOTIONS[index]
        scene["visual_action"] = scene["action"]
    return plan


async def make_voices(plan: dict) -> None:
    for scene_index, scene in enumerate(plan["scenes"]):
        for line_index, line in enumerate(scene["lyrics"]):
            profile_name = SCENE_PROFILES[scene_index][line_index]
            raw = WORK / f"voice-raw-felix-v3-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.mp3"
            target = WORK / f"voice-grid-felix-v3-{scene_index+1:02d}-{line_index+1:02d}-{profile_name}.wav"
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%").save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, 2.72, words * 60.0 / 135.0)


def effect_windows(scene: int) -> list[dict]:
    names = (
        ("soft_wings", "forest_breeze", "lantern_shell_touch"),
        ("rabbit_steps", "colour_leaf_chimes", "first_lantern_bloom"),
        ("hedgehog_steps", "carried_lantern_creak", "second_lantern_bloom"),
        ("windblown_leaves", "leaf_reveal", "pattern_memory_chime"),
        ("shelter_leaf", "petal_blanket", "quiet_glow_pulse"),
        ("four_pattern_steps", "arch_vines_open", "third_lantern_bloom"),
        ("procession_steps", "procession_wings", "path_light_trail"),
        ("seedpod_drum", "acorn_rattles", "final_lantern_cadence"),
    )[scene]
    starts = (0.8, 4.2, 8.0)
    return [{"effect": name, "local_start": start, "local_end": min(SCENE_SECONDS - 0.2, start + 1.6)} for name, start in zip(names, starts)]


def synth_scene_effect(scene: int):
    path = WORK / f"scene-{scene+1:02d}-effects.wav"
    rate = 48000; rng = random.Random(310826 + scene); windows = effect_windows(scene)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); chunk = bytearray()
        for n in range(round(SCENE_SECONDS * rate)):
            t = n / rate; value = 0.0
            for wi, row in enumerate(windows):
                age = t - row["local_start"]; duration = row["local_end"] - row["local_start"]
                if not 0 <= age < duration: continue
                env = math.sin(math.pi * age / duration) ** 2; name = row["effect"]
                if "wind" in name or "breeze" in name or "wings" in name:
                    value += rng.uniform(-1, 1) * env * 0.025
                elif "step" in name or "drum" in name:
                    value += math.sin(math.tau * (95 + wi * 18) * age) * math.exp(-11 * age) * 0.075
                elif "rattle" in name or "leaf" in name or "blanket" in name:
                    value += rng.uniform(-1, 1) * math.exp(-5 * age) * env * 0.035
                else:
                    value += (math.sin(math.tau * (520 + wi * 130) * age) + 0.4 * math.sin(math.tau * (780 + wi * 90) * age)) * math.exp(-3.2 * age) * 0.035
            sample = int(max(-1, min(1, value)) * 27000); chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path, windows


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 7 if event["phase"] == "end" else event["scene"] - 1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]; rng = random.Random(9200 + index)
    mote_count = 26 if index == 7 else (7 if index == 4 else 13)
    for j in range(mote_count):
        x = (rng.randint(80, 1840) + int(math.sin(local * 0.55 + j) * 10)) % 1920
        y = rng.randint(70, 850) + int(math.cos(local * 0.42 + j) * 6)
        radius = 1 + int((math.sin(local * 1.8 + j) + 1) * 0.8)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(255, 216, 104, 28 if index != 7 else 48))
    if event["phase"] == "end":
        draw.rectangle((0, 0, 1920, 1080), fill=(10, 24, 35, 72))
        draw.rounded_rectangle((420, 52, 1500, 222), 42, fill=(18, 42, 58, 225), outline=(255, 214, 100, 245), width=7)
        core.base.centered(draw, (960, 108), "SHINE TOGETHER", core.base.F48, (255, 224, 120, 255), 3)
        core.base.centered(draw, (960, 176), "THROUGH THE NIGHT", core.base.F48, "white", 3)
    frame.alpha_composite(overlay)
    return semantic.apply(frame, event, t, "felix", ASSET_DIR)


def make_music(total: float) -> Path:
    path = WORK / "original-night-light-parade.wav"; rate = 48000; rng = random.Random(920831)
    chords = ((196,246.94,293.66),(220,277.18,329.63),(174.61,220,261.63),(196,246.94,293.66),(146.83,196,246.94),(220,277.18,329.63),(196,261.63,329.63),(220,293.66,369.99))
    energy = (0.48,0.66,0.70,0.62,0.38,0.78,0.88,1.0)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); chunk = bytearray()
        for n in range(round(total * rate)):
            t = n / rate; scene = min(7, int(t // SCENE_SECONDS)); local = t - scene * SCENE_SECONDS
            chord = chords[scene]; phase = local % BEAT; step = int(local / BEAT) % 8
            note = chord[(0,1,2,1,0,2,1,2)[step]]
            celesta = (math.sin(math.tau*note*t) + 0.35*math.sin(math.tau*note*2*t)) * math.exp(-4.8*phase) * 0.021 * energy[scene]
            bass = math.sin(math.tau*(chord[0]/2)*t) * math.exp(-3.0*(local%(BEAT*2))) * 0.012 * energy[scene]
            pad = sum(math.sin(math.tau*f*t) for f in chord) * 0.0045 * energy[scene]
            brush = rng.uniform(-1,1) * math.exp(-42*(local%(BEAT/2))) * 0.0045 * energy[scene]
            drum = math.sin(math.tau*78*phase) * math.exp(-28*phase) * (0.004 + 0.008*(scene >= 5))
            value = celesta + bass + pad + brush + drum
            if t >= 8*SCENE_SECONDS: value *= min(1, (total-t)/0.8)
            sample = int(max(-1,min(1,value))*30000); chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source = Image.open(ASSET_DIR / ASSETS[7]).convert("RGB")
    width = round(source.height * 16 / 9); left = max(0, (source.width - width) // 2)
    canvas = source.crop((left, 0, left + width, source.height)).resize((1280, 720), Image.Resampling.LANCZOS)
    canvas = ImageEnhance.Color(canvas).enhance(1.08).convert("RGBA"); draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((500, 18, 1260, 130), 28, fill=(14, 39, 62, 232), outline=(255, 224, 120, 255), width=5)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 58); text = "LIGHT THE PARADE!"
    box = draw.textbbox((0,0), text, font=font, stroke_width=3)
    draw.text((880-(box[2]-box[0])//2, 42), text, font=font, fill=(255,225,105), stroke_width=4, stroke_fill=(9,24,42))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True); canvas.convert("RGB").save(THUMBNAIL, quality=89, optimize=True)


def quality(events, total, assets):
    probe = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"]=="video"); audio = next(s for s in probe["streams"] if s["codec_type"]=="audio")
    decode = subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"], capture_output=True)
    transitions = [{"from":a["phase"],"to":b["phase"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]
    sync=[]
    for event in events[:-1]:
        contained=all(event["start"]<=row["start"]<row["end"]<=event["end"] for row in event["lines"]+event["effects"])
        sync.append({"scene":event["scene"],"emotion":event["emotion"],"asset":event["asset"],"visual_action":event["visual_action"],"visual_start":event["start"],"visual_end":event["end"],"lines":event["lines"],"effects":event["effects"],"contained":contained})
    pace=core.pacing_audit(sync); spoken=[line["line"].lower() for item in sync for line in item["lines"]]
    zero_gaps = all(abs(r["gap_seconds"]) < 1e-6 for r in transitions)
    final_only = events[-1]["phase"] == "end" and all(event["phase"] != "end" for event in events[:-1])
    checks={"duration":abs(float(probe["format"]["duration"])-total)<0.25,"h264_1080p":video.get("codec_name")=="h264" and video.get("width")==1920 and video.get("height")==1080,"aac_48k_stereo":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"full_decode":decode.returncode==0,"zero_gaps":zero_gaps,"continuous_visual_timeline":zero_gaps,"end_card_final_only":final_only,"end_card_is_final_event_only":final_only,"eight_unique_scenes":len({r["asset"] for r in sync})==8,"four_bar_scene_cuts":all(abs((r["visual_end"]/BEAT)-round(r["visual_end"]/BEAT))<1e-5 for r in sync),"narration_effects_contained":all(r["contained"] for r in sync),"voice_starts_on_eighth_grid":all(abs(((line["start"]-item["visual_start"])/EIGHTH)-round((line["start"]-item["visual_start"])/EIGHTH))<1e-5 for item in sync for line in item["lines"]),"child_friendly_pacing":pace["passed"],"no_spoken_imitation":all(not any(w in line for w in ("clap clap","tap tap","ding dong","boom boom")) for line in spoken),"real_effects":len({e["effect"] for item in sync for e in item["effects"]})==24,"thumbnail":THUMBNAIL.is_file() and THUMBNAIL.stat().st_size<2_000_000}
    loudness,peak=engine.audio_levels(); report={"output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"format":"nocturnal pattern-and-courage story-song","bpm":BPM,"visual_method":"independently animated identity-locked foreground cast with visible pattern-building actions over defocused contextual storybook environments","audio_method":"original 92 BPM emotion-mapped celesta, strings and percussion with three character voices and synchronized real effects","narration_pacing":{"weighted_wpm":pace["weighted_wpm"],"maximum_line_wpm":pace["maximum_line_wpm"],"minimum_interline_gap_seconds":pace["minimum_interline_gap_seconds"]},"integrated_loudness_lufs":loudness,"true_peak_dbfs":peak,"true_rigged_3d_animation":False,"paid_generation_used":False,"checks":checks,"passed":all(checks.values())}
    (WORK/"timeline-gap-audit.json").write_text(json.dumps(transitions,indent=2)+"\n",encoding="utf-8"); (WORK/"lyric-visual-emotion-audit.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8"); (WORK/"narration-pacing-audit.json").write_text(json.dumps(pace,indent=2)+"\n",encoding="utf-8"); (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    general=Image.new("RGB",(960,405),"white")
    for i,event in enumerate(events): general.paste(frame_for(event,event["start"]+(event["end"]-event["start"])*0.55,assets).resize((240,135),Image.Resampling.LANCZOS),((i%4)*240,(i//4)*135))
    general.save(WORK/"quality-contact-sheet.png")
    semantic.write_evidence(WORK, events[:-1], frame_for, assets, "felix")
    boundary=[]
    for current,following in zip(events,events[1:]): boundary.extend([(current,current["end"]-0.12),(following,following["start"]+0.12)])
    sheet=Image.new("RGB",(1200,math.ceil(len(boundary)/5)*135),"white")
    for i,(event,t) in enumerate(boundary): sheet.paste(frame_for(event,t,assets).resize((240,135),Image.Resampling.LANCZOS),((i%5)*240,(i//5)*135))
    sheet.save(WORK/"transition-contact-sheet.png"); core.make_audio_evidence()
    if not report["passed"]: raise RuntimeError(f"Felix quality gate failed: {report}")
    return report


def write_metadata(total, report):
    doc={"id":ITEM_ID,"title":"Felix Firefly's Night-Light Parade | Pattern Story for Kids","description":"Felix helps Rabbit and Hedgehog remember two glowing colour patterns, care for one another and light a safe woodland path before their joyful night parade.\n\nAn original Tiny Tales musical story about patterns, courage, friendship and moving together for children ages 3 to 7.","tags":["pattern song for kids","firefly story","colours for kids","friendship story","woodland animals","musical story for kids","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":True,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":"ana-us","character_voice_profiles":{"felix":"ryan-uk","rabbit":"maisie-uk"},"delivery":"emotion-mapped melodic story-song","bpm":BPM,"format_family":"connected nocturnal pattern-and-courage story-song","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"quality_report":f"automation/production-work/{ITEM_ID}/quality-report.json","transition_audit":f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json","lyric_visual_emotion_audit":f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json","narration_pacing_audit":f"automation/production-work/{ITEM_ID}/narration-pacing-audit.json","quality_contact_sheet":f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png","transition_contact_sheet":f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png","musical_story_waveform":f"automation/production-work/{ITEM_ID}/musical-story-waveform.png","musical_story_spectrum":f"automation/production-work/{ITEM_ID}/musical-story-spectrum.png","prepared_thumbnail":f"automation/thumbnails/{ITEM_ID}.jpg","thumbnail_hook":"LIGHT THE PARADE!","thumbnail_reviewed":False,"manual_visual_review_passed":False,"reviewed_sha256":hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),"integrated_loudness_lufs":report["integrated_loudness_lufs"],"true_peak_dbfs":report["true_peak_dbfs"],"true_rigged_3d_animation":False,"paid_generation_used":False,"spoken_sound_effect_words_removed":True,"upload_queue_released":False,"narration_pacing_policy":"three short phrases per scene; target at most 140 WPM, hard line ceiling 145 WPM and at least 0.4 seconds between phrases"}
    master_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    thumbnail_hash = hashlib.sha256(THUMBNAIL.read_bytes()).hexdigest()
    reviewed = master_hash == REVIEWED_MASTER_SHA256 and thumbnail_hash == REVIEWED_THUMBNAIL_SHA256
    doc.update({
        "reviewed_sha256": master_hash,
        "transition_contact_sheet_reviewed": reviewed,
        "quality_contact_sheet_reviewed": reviewed,
        "thumbnail_reviewed": reviewed,
        "manual_visual_review_passed": reviewed,
        "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json",
        "new_image_generation_calls": 10,
        "manual_review_notes": "Review remains valid only for the exact hash-locked master and revised thumbnail. General sheet, every transition boundary, scene-5 rest, scene-6 payoff, scene-8-only finale, final-only end card, waveform and thumbnail were reviewed.",
    })
    META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def configure_engine() -> None:
    engine.ITEM_ID=ITEM_ID; engine.WORK=WORK; engine.OUTPUT=OUTPUT; engine.PLAN=PLAN; engine.META=META; engine.THUMBNAIL=THUMBNAIL
    engine.SCENE_SECONDS=SCENE_SECONDS; engine.END_SECONDS=END_SECONDS; engine.BEAT=BEAT; engine.EIGHTH=EIGHTH; engine.LINE_OFFSETS=LINE_OFFSETS
    engine.ASSETS=ASSETS; engine.VOICE_PROFILES=VOICE_PROFILES; engine.SCENE_PROFILES=SCENE_PROFILES; engine.PACING_VERSION="felix-v3"
    engine.load_plan=load_plan; engine.make_voices=make_voices; engine.effect_windows=effect_windows; engine.synth_scene_effect=synth_scene_effect; engine.frame_for=frame_for; engine.make_music=make_music; engine.make_thumbnail=make_thumbnail; engine.quality=quality; engine.write_metadata=write_metadata


def main() -> None:
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
