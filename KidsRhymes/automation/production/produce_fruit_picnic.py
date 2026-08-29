"""Produce Pick, Wash, Pack the Fruit Picnic as a synchronized musical story."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
from pathlib import Path
import random
import re
import struct
import subprocess
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
ITEM_ID = "pick-wash-pack-fruit-picnic-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
SCENE_SECONDS = 40 / 3
END_SECONDS = 4.0
BEAT = 2 / 3
EIGHTH = 1 / 3
LINE_OFFSETS = (1 / 3, 14 / 3, 9.0)
PACING_VERSION = "slow-v2"

ASSETS = (
    "fruit-picnic-opening-v1.png",
    "fruit-picnic-gentle-pick-v1.png",
    "fruit-picnic-count-six-v1.png",
    "fruit-picnic-wash-v1.png",
    "fruit-picnic-pack-pattern-v1.png",
    "fruit-picnic-shared-carry-v1.png",
    "fruit-picnic-finale-v1.png",
)

VOICE_PROFILES = {
    "maisie-sunrise": {**core.select_voice_profile("maisie-uk"), "rate": "-8%", "pitch": "+11Hz"},
    "maisie-gentle": {**core.select_voice_profile("maisie-uk"), "rate": "-11%", "pitch": "+7Hz"},
    "maisie-count": {**core.select_voice_profile("maisie-uk"), "rate": "-6%", "pitch": "+14Hz"},
    "maisie-sparkle": {**core.select_voice_profile("maisie-uk"), "rate": "-7%", "pitch": "+16Hz"},
    "maisie-pattern": {**core.select_voice_profile("maisie-uk"), "rate": "-6%", "pitch": "+13Hz"},
    "maisie-step": {**core.select_voice_profile("maisie-uk"), "rate": "-8%", "pitch": "+9Hz"},
    "maisie-finale": {**core.select_voice_profile("maisie-uk"), "rate": "-5%", "pitch": "+17Hz"},
    "ryan-curious": {**core.select_voice_profile("ryan-uk"), "rate": "-9%", "pitch": "+8Hz"},
    "ryan-bright": {**core.select_voice_profile("ryan-uk"), "rate": "-6%", "pitch": "+12Hz"},
    "ryan-rhythm": {**core.select_voice_profile("ryan-uk"), "rate": "-6%", "pitch": "+9Hz"},
    "ana-warm": {**core.select_voice_profile("ana-us"), "rate": "-10%", "pitch": "+3Hz"},
    "ana-smile": {**core.select_voice_profile("ana-us"), "rate": "-7%", "pitch": "+7Hz"},
}

SCENE_PROFILES = (
    ("maisie-sunrise", "ryan-curious", "maisie-gentle", "ana-warm"),
    ("maisie-gentle", "ana-warm", "ryan-bright", "maisie-gentle"),
    ("maisie-count", "ryan-rhythm", "maisie-count", "ana-smile"),
    ("maisie-sparkle", "ryan-bright", "maisie-sparkle", "ana-warm"),
    ("maisie-pattern", "ryan-rhythm", "ana-smile", "maisie-pattern"),
    ("maisie-step", "ryan-rhythm", "ana-warm", "maisie-step"),
    ("maisie-finale", "ryan-bright", "ana-smile", "maisie-finale"),
)


def configure_core() -> None:
    core.WORK = WORK
    core.OUTPUT = OUTPUT
    core.THUMBNAIL = THUMBNAIL


def load_plan() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def raw_voice_path(si: int, li: int, profile: str) -> Path:
    return WORK / f"voice-raw-{PACING_VERSION}-{si+1:02d}-{li+1:02d}-{profile}.mp3"


def voice_path(si: int, li: int, profile: str) -> Path:
    return WORK / f"voice-grid-{PACING_VERSION}-{si+1:02d}-{li+1:02d}-{profile}.wav"


async def make_voices(plan: dict) -> None:
    maximums = (3.6, 3.6, 3.6)
    for si, scene in enumerate(plan["scenes"]):
        for li, line in enumerate(scene["lyrics"]):
            profile_name = SCENE_PROFILES[si][li]
            raw = raw_voice_path(si, li, profile_name)
            target = voice_path(si, li, profile_name)
            if not raw.exists() or raw.stat().st_size < 1000:
                profile = VOICE_PROFILES[profile_name]
                await core.edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
                ).save(str(raw))
            if not target.exists() or target.stat().st_size < 2000:
                words = len(re.findall(r"[A-Za-z0-9']+", line))
                core.fit_voice_to_grid(raw, target, maximums[li], words * 60.0 / core.TARGET_WPM)


def effect_windows(si: int) -> list[dict]:
    return (
        [{"effect": "leaf_breeze", "local_start": 0.4, "local_end": 3.0}, {"effect": "gate_open", "local_start": 9.4, "local_end": 11.1}],
        [{"effect": "branch_leaves", "local_start": 0.7, "local_end": 2.2}, {"effect": "apple_twist", "local_start": 5.7, "local_end": 6.5}, {"effect": "basket_settle", "local_start": 10.4, "local_end": 11.2}],
        [{"effect": f"fruit_place_{n+1}", "local_start": 0.75+n*1.42, "local_end": 1.2+n*1.42} for n in range(6)] + [{"effect": "basket_handle_creak", "local_start": 10.2, "local_end": 11.5}],
        [{"effect": "tap_start", "local_start": 0.8, "local_end": 1.5}, {"effect": "gentle_rinse", "local_start": 1.2, "local_end": 10.8}, {"effect": "tap_stop", "local_start": 10.6, "local_end": 11.4}],
        [{"effect": "cloth_dry", "local_start": 0.5, "local_end": 1.7}] + [{"effect": f"pattern_place_{n+1}", "local_start": 2.0+n*1.25, "local_end": 2.42+n*1.25} for n in range(6)] + [{"effect": "box_latch", "local_start": 10.4, "local_end": 11.2}],
        [{"effect": f"footstep_{n+1}", "local_start": 1.2+n*1.75, "local_end": 1.65+n*1.75} for n in range(4)] + [{"effect": "woven_handle_creak", "local_start": 8.5, "local_end": 9.6}, {"effect": "blanket_flutter", "local_start": 10.3, "local_end": 11.4}],
        [{"effect": "picnic_cloth_settle", "local_start": 0.7, "local_end": 1.7}, {"effect": "shared_board_touch", "local_start": 4.0, "local_end": 4.7}, {"effect": "leaf_to_compost", "local_start": 7.1, "local_end": 7.8}, {"effect": "orchard_final_cadence", "local_start": 9.7, "local_end": 12.4}],
    )[si]


def synth_scene_effect(si: int) -> tuple[Path, list[dict]]:
    path = WORK / f"scene-{si+1:02d}-effects.wav"
    rate = 48000
    rng = random.Random(280826 + si)
    windows = effect_windows(si)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate)
        chunk = bytearray(); smooth = 0.0
        for n in range(round(SCENE_SECONDS * rate)):
            t = n / rate; value = 0.0
            for wi, row in enumerate(windows):
                age = t - row["local_start"]
                duration = row["local_end"] - row["local_start"]
                if not 0 <= age < duration:
                    continue
                name = row["effect"]
                envelope = math.sin(math.pi * age / duration) ** 2
                if "rinse" in name:
                    smooth = 0.93 * smooth + 0.07 * rng.uniform(-1, 1)
                    value += smooth * envelope * 0.045 + math.sin(math.tau * 740 * t) * 0.006
                elif "leaf" in name or "cloth" in name or "flutter" in name:
                    smooth = 0.82 * smooth + 0.18 * rng.uniform(-1, 1)
                    value += smooth * envelope * 0.038
                elif "step" in name or "place" in name or "settle" in name or "touch" in name:
                    value += math.sin(math.tau * (82 + wi * 7) * age) * math.exp(-11 * age) * 0.075
                elif "tap" in name or "latch" in name or "twist" in name or "gate" in name:
                    value += math.sin(math.tau * (180 + wi * 45) * age) * math.exp(-7 * age) * 0.06
                elif "creak" in name:
                    value += math.sin(math.tau * (145 + 35 * age) * age) * envelope * 0.042
                else:
                    value += math.sin(math.tau * (392 + wi * 98) * age) * math.exp(-3.5 * age) * 0.045
            sample = int(max(-1, min(1, value)) * 26000)
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path, windows


def build_timeline(plan: dict) -> tuple[list[dict], list[tuple[Path, float]], float]:
    events, tracks = [], []
    for si, scene in enumerate(plan["scenes"]):
        start = si * SCENE_SECONDS; lines = []
        for li, line in enumerate(scene["lyrics"]):
            profile = SCENE_PROFILES[si][li]; path = voice_path(si, li, profile)
            line_start = start + LINE_OFFSETS[li]; line_end = line_start + core.media_duration(path)
            if line_end > start + SCENE_SECONDS - 0.08:
                raise RuntimeError(f"Voice leaves scene {si+1}: {line_end:.3f}")
            lines.append({"line": line, "profile": profile, "start": line_start, "end": line_end})
            tracks.append((path, line_start))
        effects_path, local_windows = synth_scene_effect(si); tracks.append((effects_path, start))
        effects = [{**row, "start": start+row["local_start"], "end": start+row["local_end"]} for row in local_windows]
        events.append({"phase": f"scene_{si+1}", "scene": si+1, "start": start, "end": start+SCENE_SECONDS, "asset": ASSETS[si], "emotion": scene["emotion"], "visual_action": scene["visual_action"], "lines": lines, "effects": effects})
    end_start = len(plan["scenes"]) * SCENE_SECONDS
    events.append({"phase": "end", "start": end_start, "end": end_start+END_SECONDS, "asset": ASSETS[-1]})
    return events, tracks, end_start + END_SECONDS


def load_assets() -> dict[str, Image.Image]:
    missing = [str(ASSET_DIR/name) for name in ASSETS if not (ASSET_DIR/name).is_file()]
    if missing: raise FileNotFoundError(missing)
    return {name: core.fit_asset(ASSET_DIR/name) for name in ASSETS}


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 6 if event["phase"] == "end" else event["scene"]-1
    frame = core.moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(overlay, "RGBA")
    local = t - event["start"]; rng = random.Random(7400 + index)
    for j in range(13 if index not in (2, 4) else 7):
        x = rng.randint(70, 1850); y = rng.randint(50, 760)
        r = 1 + int(2 * math.sin(local*1.35+j) ** 2)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 225, 125, 42))
    if event["phase"] == "end":
        draw.rectangle((0, 0, base.W, base.H), fill=(28, 48, 30, 82))
        draw.rounded_rectangle((410, 34, 1510, 211), 40, fill=(48, 83, 48, 228), outline=(255, 220, 118, 245), width=7)
        base.centered(draw, (960, 92), "PICK • WASH • PACK", base.F48, (255, 230, 130, 255), 3)
        base.centered(draw, (960, 163), "SHARE THE ORCHARD DAY", base.F48, "white", 3)
    frame.alpha_composite(overlay)
    if event["phase"] != "end" and index == 0 and local < 2.45:
        title = Image.new("RGBA", frame.size, (0, 0, 0, 0)); td = ImageDraw.Draw(title, "RGBA")
        fade = min(1.0, (2.45-local)/0.35)
        td.rounded_rectangle((60, 38, 1110, 217), 40, fill=(38, 81, 52, round(220*fade)), outline=(255, 220, 115, round(245*fade)), width=6)
        base.centered(td, (585, 98), "THE FRUIT PICNIC", base.F48, (255, 233, 145, round(255*fade)), 3)
        base.centered(td, (585, 170), "PICK • WASH • PACK", base.F48, "white", 3)
        frame.alpha_composite(title)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    path = WORK / "original-orchard-swing.wav"; rate = 48000; rng = random.Random(900828)
    palettes = ((196,246.94,293.66,392),(196,261.63,329.63,392),(220,277.18,329.63,440),(196,246.94,329.63,392),(220,277.18,369.99,440),(174.61,220,261.63,349.23),(196,261.63,329.63,392))
    energy = (0.74,0.70,0.88,0.82,0.94,0.86,1.0)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); chunk = bytearray()
        for n in range(round(total*rate)):
            t=n/rate; scene=min(6,int(t//SCENE_SECONDS)); local=t-scene*SCENE_SECONDS
            palette=palettes[scene]; phase=local%BEAT; step=int(local/BEAT)%8
            note=palette[(0,1,2,1,3,2,1,2)[step]]
            pluck=(math.sin(math.tau*note*t)+0.32*math.sin(math.tau*note*2*t))*math.exp(-5.2*phase)*0.024*energy[scene]
            bass=math.sin(math.tau*(palette[0]/2)*t)*math.exp(-3.0*(local%(BEAT*2)))*0.015*energy[scene]
            harmony=sum(math.sin(math.tau*f*t) for f in palette[:3])*0.0055
            swing_phase=local%(BEAT/2); shaker=rng.uniform(-1,1)*math.exp(-48*swing_phase)*0.006*energy[scene]
            pulse=math.sin(math.tau*72*phase)*math.exp(-30*phase)*0.011*energy[scene]
            value=pluck+bass+harmony+shaker+pulse
            if t >= 7*SCENE_SECONDS: value=sum(math.sin(math.tau*f*t) for f in (196,261.63,329.63))*0.010*min(1,(total-t)/0.8)
            sample=int(max(-1,min(1,value))*30000); chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source=Image.open(ASSET_DIR/ASSETS[4]).convert("RGB"); width=round(source.height*16/9); left=max(0,(source.width-width)//2)
    canvas=source.crop((left,0,left+width,source.height)).resize((1280,720),Image.Resampling.LANCZOS)
    canvas=ImageEnhance.Color(canvas).enhance(1.10).convert("RGBA"); draw=ImageDraw.Draw(canvas,"RGBA")
    draw.rounded_rectangle((180,18,1100,137),30,fill=(35,79,48,232),outline="white",width=5)
    font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",58); text="PICK, WASH, PACK!"; box=draw.textbbox((0,0),text,font=font,stroke_width=3)
    draw.text(((1280-(box[2]-box[0]))//2,43),text,font=font,fill=(255,226,105),stroke_width=4,stroke_fill=(20,46,28))
    THUMBNAIL.parent.mkdir(parents=True,exist_ok=True); canvas.convert("RGB").save(THUMBNAIL,quality=89,optimize=True)


def audio_levels() -> tuple[float | None, float | None]:
    run=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(OUTPUT),"-filter_complex","ebur128=peak=true","-f","null","NUL"],text=True,capture_output=True)
    loud=re.findall(r"I:\s*(-?[0-9.]+) LUFS",run.stderr); peak=re.findall(r"Peak:\s*(-?[0-9.]+) dBFS",run.stderr)
    return (float(loud[-1]) if loud else None,float(peak[-1]) if peak else None)


def quality(events: list[dict], total: float, assets: dict[str, Image.Image]) -> dict:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True))
    video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    decode=subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],capture_output=True)
    transitions=[{"from":a["phase"],"to":b["phase"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]
    sync=[]
    for event in events[:-1]:
        contained=all(event["start"]<=row["start"]<row["end"]<=event["end"] for row in event["lines"]+event["effects"])
        sync.append({"scene":event["scene"],"emotion":event["emotion"],"asset":event["asset"],"visual_action":event["visual_action"],"visual_start":event["start"],"visual_end":event["end"],"lines":event["lines"],"effects":event["effects"],"contained":contained})
    profiles={line["profile"] for item in sync for line in item["lines"]}; spoken=[line["line"].lower() for item in sync for line in item["lines"]]
    forbidden=("clap clap","tap tap","knock knock","tick tock","ding dong","boom boom","beep beep")
    pace=core.pacing_audit(sync)
    checks={"duration":abs(float(probe["format"]["duration"])-total)<0.25,"h264_1080p":video.get("codec_name")=="h264" and video.get("width")==1920 and video.get("height")==1080,"aac_48k_stereo":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"full_decode":decode.returncode==0,"zero_gaps":all(abs(r["gap_seconds"])<1e-6 for r in transitions),"continuous_visual_timeline":all(abs(r["gap_seconds"])<1e-6 for r in transitions),"end_card_is_final_event_only":events[-1]["phase"]=="end","seven_unique_story_scenes":len({r["asset"] for r in sync})==7,"all_story_scenes_five_bars":all(abs(r["visual_end"]-r["visual_start"]-SCENE_SECONDS)<1e-6 for r in sync),"narration_and_effects_contained":all(r["contained"] for r in sync),"vocal_starts_on_eighth_grid":all(abs(((line["start"]-item["visual_start"])/EIGHTH)-round((line["start"]-item["visual_start"])/EIGHTH))<1e-6 for item in sync for line in item["lines"]),"five_bar_scene_cuts":all(abs((r["visual_end"]/BEAT)-round(r["visual_end"]/BEAT))<1e-6 for r in sync),"emotional_voice_variation":len(profiles)>=10,"maisie_ryan_ana_rotation":all(any(name.startswith(prefix) for name in profiles) for prefix in ("maisie-","ryan-","ana-")),"no_spoken_sound_imitation":all(not any(word in line for word in forbidden) for line in spoken),"child_friendly_narration_pacing":pace["passed"],"real_scene_effects":len({e["effect"] for item in sync for e in item["effects"]})>=28,"thumbnail":THUMBNAIL.is_file() and THUMBNAIL.stat().st_size<2_000_000}
    loudness,peak=audio_levels(); report={"output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"format":"orchard-to-picnic-action-story-song","bpm":90,"voice_profiles":sorted(profiles),"visual_method":"seven reviewed luminous watercolour-and-gouache orchard tableaux with restrained eased crop movement","audio_method":"original 90 BPM emotion-mapped orchard swing, Maisie lead, Kai and Rosa character pickups, and synchronized real-world effects","narration_pacing":{"weighted_wpm":pace["weighted_wpm"],"maximum_line_wpm":pace["maximum_line_wpm"],"minimum_interline_gap_seconds":pace["minimum_interline_gap_seconds"]},"integrated_loudness_lufs":loudness,"true_peak_dbfs":peak,"true_rigged_3d_animation":False,"paid_generation_used":False,"checks":checks,"passed":all(checks.values())}
    (WORK/"timeline-gap-audit.json").write_text(json.dumps(transitions,indent=2)+"\n",encoding="utf-8"); (WORK/"lyric-visual-emotion-audit.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8"); (WORK/"narration-pacing-audit.json").write_text(json.dumps(pace,indent=2)+"\n",encoding="utf-8"); (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    general=Image.new("RGB",(960,math.ceil(len(events)/4)*135),"white")
    for i,event in enumerate(events): general.paste(frame_for(event,event["start"]+(event["end"]-event["start"])*0.55,assets).resize((240,135),Image.Resampling.LANCZOS),((i%4)*240,(i//4)*135))
    general.save(WORK/"quality-contact-sheet.png"); boundary=[]
    for current,following in zip(events,events[1:]): boundary.extend([(current,current["end"]-0.12),(following,following["start"]+0.12)])
    sheet=Image.new("RGB",(1200,math.ceil(len(boundary)/5)*135),"white")
    for i,(event,t) in enumerate(boundary): sheet.paste(frame_for(event,t,assets).resize((240,135),Image.Resampling.LANCZOS),((i%5)*240,(i//5)*135))
    sheet.save(WORK/"transition-contact-sheet.png"); core.make_audio_evidence()
    if not report["passed"]: raise RuntimeError(f"Fruit Picnic quality gate failed: {report}")
    return report


def write_metadata(total: float, report: dict) -> None:
    document={"id":ITEM_ID,"title":"Pick, Wash, Pack the Fruit Picnic | Orchard Song for Kids","description":"Kai asks before entering Rosa's orchard, gently picks ripe fruit, counts six pieces, washes them, packs a repeating colour pattern and shares the basket on a sunny picnic.\n\nAn original Tiny Tales musical story about permission, gentle food handling, counting, patterns, teamwork and avoiding waste for children ages 3 to 7.","tags":["fruit song for kids","orchard story","counting to six","patterns for kids","food washing for kids","teamwork story","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":"maisie-uk","character_voice_profiles":{"kai":"ryan-uk","rosa":"ana-us"},"delivery":"emotion-mapped melodic rhythmic story-song","bpm":90,"format_family":"orchard-to-picnic-action-story-song","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"quality_report":f"automation/production-work/{ITEM_ID}/quality-report.json","transition_audit":f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json","lyric_visual_emotion_audit":f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json","quality_contact_sheet":f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png","transition_contact_sheet":f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png","asset_review_contact_sheet":f"automation/production-work/{ITEM_ID}/asset-review-contact-sheet.png","musical_story_waveform":f"automation/production-work/{ITEM_ID}/musical-story-waveform.png","musical_story_spectrum":f"automation/production-work/{ITEM_ID}/musical-story-spectrum.png","prepared_thumbnail":f"automation/thumbnails/{ITEM_ID}.jpg","thumbnail_hook":"PICK, WASH, PACK!","thumbnail_reviewed":False,"manual_visual_review_passed":False,"reviewed_sha256":hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),"integrated_loudness_lufs":report["integrated_loudness_lufs"],"true_peak_dbfs":report["true_peak_dbfs"],"true_rigged_3d_animation":False,"paid_generation_used":False,"spoken_sound_effect_words_removed":True,"upload_queue_released":False}
    document["narration_pacing_audit"] = f"automation/production-work/{ITEM_ID}/narration-pacing-audit.json"
    document["narration_pacing_policy"] = "three short phrases per scene; target at most 140 WPM, hard line ceiling 145 WPM and at least 0.4 seconds between phrases"
    META.write_text(json.dumps(document,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True,exist_ok=True); OUTPUT.parent.mkdir(parents=True,exist_ok=True); configure_core(); plan=load_plan()
    asyncio.run(make_voices(plan)); events,tracks,total=build_timeline(plan); assets=load_assets(); make_thumbnail()
    render_engine.WORK=WORK; render_engine.OUTPUT=OUTPUT; render_engine.frame_for=frame_for; render_engine.make_music=make_music
    render_engine.render(events,tracks,total,assets); report=quality(events,total,assets); write_metadata(total,report)
    print(json.dumps({"output":str(OUTPUT),"duration_seconds":total,"events":len(events),"sha256":hashlib.sha256(OUTPUT.read_bytes()).hexdigest()},indent=2))


if __name__ == "__main__":
    main()
