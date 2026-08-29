"""Produce Lumi's Shadow Theatre Surprise as a slow musical contrast story."""

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

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

import produce_eddie_rain_garden_musical as core
from voice_profiles import select_voice_profile


AUTOMATION = core.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "lumi-shadow-theatre-surprise-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
SCENE_SECONDS = 80.0 / 7.0
END_SECONDS = 4.0
LINE_OFFSETS = (0.35, 4.05, 7.75)
TARGET_WPM = 135.0
MAX_LINE_WPM = 145.0
PACING_VERSION = "slow-v1"

ASSETS = (
    "lumi-shadow-theatre-opening-v1.png",
    "lumi-shadow-theatre-small-shadow-v1.png",
    "lumi-shadow-theatre-large-shadow-v1.png",
    "lumi-shadow-theatre-shape-owl-v1.png",
    "lumi-shadow-theatre-safe-reveal-v1.png",
    "lumi-shadow-theatre-three-sizes-local-v1.png",
    "lumi-shadow-theatre-finale-local-v1.png",
)

VOICE_PROFILES = {
    "ryan-curious": {**select_voice_profile("ryan-uk"), "rate": "-10%", "pitch": "+4Hz"},
    "ryan-wonder": {**select_voice_profile("ryan-uk"), "rate": "-9%", "pitch": "+8Hz"},
    "ryan-suspense": {**select_voice_profile("ryan-uk"), "rate": "-14%", "pitch": "-3Hz"},
    "ryan-celebrate": {**select_voice_profile("ryan-uk"), "rate": "-7%", "pitch": "+12Hz"},
    "natasha-curious": {**select_voice_profile("natasha-au"), "rate": "-11%", "pitch": "+6Hz"},
    "natasha-relief": {**select_voice_profile("natasha-au"), "rate": "-13%", "pitch": "+2Hz"},
    "natasha-bright": {**select_voice_profile("natasha-au"), "rate": "-8%", "pitch": "+10Hz"},
    "ana-guide": {**select_voice_profile("ana-us"), "rate": "-12%", "pitch": "+1Hz"},
    "ana-warm": {**select_voice_profile("ana-us"), "rate": "-13%", "pitch": "-2Hz"},
}

SCENE_PROFILES = (
    ("ryan-curious", "natasha-curious", "ana-guide"),
    ("ryan-wonder", "natasha-curious", "ana-guide"),
    ("ryan-wonder", "natasha-bright", "ryan-wonder"),
    ("natasha-bright", "ana-guide", "ryan-wonder"),
    ("ryan-suspense", "natasha-relief", "ana-warm"),
    ("ryan-wonder", "natasha-bright", "ana-guide"),
    ("ryan-celebrate", "natasha-bright", "ana-warm"),
)


def load_plan() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def rabbit(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, fill=(52, 37, 49, 235)) -> None:
    draw.ellipse((cx-38*scale, cy-42*scale, cx+42*scale, cy+48*scale), fill=fill)
    draw.ellipse((cx-25*scale, cy-92*scale, cx+27*scale, cy-35*scale), fill=fill)
    draw.ellipse((cx-25*scale, cy-165*scale, cx-5*scale, cy-82*scale), fill=fill)
    draw.ellipse((cx+8*scale, cy-160*scale, cx+28*scale, cy-82*scale), fill=fill)
    draw.ellipse((cx+34*scale, cy+20*scale, cx+78*scale, cy+60*scale), fill=fill)
    draw.ellipse((cx-48*scale, cy+30*scale, cx-5*scale, cy+70*scale), fill=fill)


def prepare_local_scene_assets() -> None:
    for name in ASSETS[:5]:
        if not (ASSET_DIR / name).is_file():
            raise FileNotFoundError(ASSET_DIR / name)
    three_path = ASSET_DIR / ASSETS[5]
    finale_path = ASSET_DIR / ASSETS[6]
    if not three_path.exists():
        base_image = Image.open(ASSET_DIR / ASSETS[2]).convert("RGBA")
        draw = ImageDraw.Draw(base_image, "RGBA")
        panel = (870, 115, 1640, 785)
        draw.rounded_rectangle(panel, 28, fill=(245, 185, 79, 242), outline=(69, 43, 60, 245), width=10)
        widths = [(905, 126, 1125, 668), (1130, 126, 1370, 668), (1375, 126, 1610, 668)]
        for box in widths:
            draw.rounded_rectangle(box, 18, fill=(255, 211, 115, 205), outline=(79, 51, 66, 230), width=6)
        rabbit(draw, 1015, 470, 0.62)
        rabbit(draw, 1248, 455, 0.88)
        rabbit(draw, 1492, 425, 1.16)
        for index, radius in enumerate((20, 31, 43)):
            x = 1015 + index * 235
            draw.ellipse((x-radius, 710-radius, x+radius, 710+radius), fill=(54, 151, 159, 230), outline="white", width=4)
        base_image.convert("RGB").save(three_path, quality=96)
    if not finale_path.exists():
        base_image = Image.open(ASSET_DIR / ASSETS[3]).convert("RGBA")
        draw = ImageDraw.Draw(base_image, "RGBA")
        draw.rectangle((0, 700, base_image.width, base_image.height), fill=(12, 18, 38, 118))
        for index in range(11):
            x = 80 + index * 150
            y = 855 + (index % 2) * 15
            draw.ellipse((x-35, y-55, x+35, y+15), fill=(22, 20, 36, 238))
            draw.rectangle((x-42, y, x+42, y+105), fill=(22, 20, 36, 238))
        # Add a paper bird beside the existing owl and a small rabbit finale cue.
        draw.polygon([(1245, 410), (1325, 350), (1400, 410), (1325, 390)], fill=(56, 41, 55, 225))
        draw.polygon([(1325, 390), (1390, 330), (1370, 425)], fill=(56, 41, 55, 225))
        rabbit(draw, 1510, 565, 0.55, (56, 41, 55, 225))
        base_image.convert("RGB").save(finale_path, quality=96)


def raw_voice_path(scene: int, line: int, profile: str) -> Path:
    return WORK / f"voice-raw-{PACING_VERSION}-{scene+1:02d}-{line+1:02d}-{profile}.mp3"


def voice_path(scene: int, line: int, profile: str) -> Path:
    return WORK / f"voice-grid-{PACING_VERSION}-{scene+1:02d}-{line+1:02d}-{profile}.wav"


async def make_voices(plan: dict) -> None:
    for si, scene in enumerate(plan["scenes"]):
        for li, line in enumerate(scene["lyrics"]):
            profile_name = SCENE_PROFILES[si][li]
            profile = VOICE_PROFILES[profile_name]
            raw = raw_voice_path(si, li, profile_name)
            fitted = voice_path(si, li, profile_name)
            if not raw.exists() or raw.stat().st_size < 1000:
                await edge_tts.Communicate(
                    line, profile["voice"], rate=profile["rate"], pitch=profile["pitch"], volume="-1%"
                ).save(str(raw))
            words = len(re.findall(r"[A-Za-z0-9']+", line))
            core.fit_voice_to_grid(raw, fitted, 3.12, words * 60.0 / TARGET_WPM)


def make_effect(scene_index: int) -> tuple[Path, list[dict]]:
    path = WORK / f"scene-{scene_index+1:02d}-effects.wav"
    rate = 48000
    cues = {
        0: [(1.0, 240, "curtain"), (8.6, 880, "lamp_switch")],
        1: [(1.2, 520, "paper_lift"), (8.8, 680, "rod_settle")],
        2: [(1.0, 260, "track_slide"), (7.7, 740, "shadow_swell")],
        3: [(0.8, 620, "circle_place"), (4.5, 720, "triangles_place"), (8.4, 1040, "owl_chime")],
        4: [(0.8, 190, "paper_sweep"), (4.3, 430, "calm_breath"), (7.5, 610, "curtain_reveal")],
        5: [(1.0, 480, "three_steps"), (4.7, 640, "size_taps"), (8.3, 820, "size_resolve")],
        6: [(0.5, 360, "curtain_open"), (4.3, 760, "puppet_parade"), (8.3, 980, "audience_applause")],
    }[scene_index]
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate)
        chunk = bytearray()
        rng = random.Random(8400 + scene_index)
        for n in range(round(SCENE_SECONDS * rate)):
            t = n / rate
            value = rng.uniform(-1, 1) * 0.0015
            for onset, freq, _name in cues:
                age = t - onset
                if 0 <= age < 0.75:
                    value += math.sin(math.tau * freq * age) * math.exp(-6.5 * age) * 0.055
                    value += math.sin(math.tau * freq * 1.5 * age) * math.exp(-9 * age) * 0.018
            sample = int(max(-1, min(1, value)) * 26000)
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4:
                output.writeframesraw(chunk); chunk.clear()
        if chunk: output.writeframesraw(chunk)
    windows = [{"effect": name, "local_start": onset, "local_end": min(SCENE_SECONDS, onset + 0.75)} for onset, _freq, name in cues]
    return path, windows


def build_timeline(plan: dict) -> tuple[list[dict], list[tuple[Path, float]], float]:
    events, tracks = [], []
    for si, scene in enumerate(plan["scenes"]):
        start = si * SCENE_SECONDS
        lines = []
        for li, line in enumerate(scene["lyrics"]):
            profile = SCENE_PROFILES[si][li]
            path = voice_path(si, li, profile)
            line_start = start + LINE_OFFSETS[li]
            line_end = line_start + core.media_duration(path)
            if line_end > start + SCENE_SECONDS - 0.15:
                raise RuntimeError(f"Voice leaves scene {si+1}")
            lines.append({"line": line, "profile": profile, "start": line_start, "end": line_end})
            tracks.append((path, line_start))
        sfx, windows = make_effect(si)
        tracks.append((sfx, start))
        effects = [{"effect": row["effect"], "start": start+row["local_start"], "end": start+row["local_end"]} for row in windows]
        events.append({
            "phase": f"scene_{si+1}", "scene": si+1, "start": start, "end": start+SCENE_SECONDS,
            "asset": ASSETS[si], "emotion": scene["emotion"], "visual_action": scene["visual_action"],
            "lines": lines, "effects": effects,
        })
    end_start = 7 * SCENE_SECONDS
    events.append({"phase": "end", "start": end_start, "end": end_start+END_SECONDS, "asset": ASSETS[-1]})
    return events, tracks, end_start + END_SECONDS


def fit_asset(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max((core.base.W + 180) / image.width, (core.base.H + 100) / image.height)
    return image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.LANCZOS)


def load_assets() -> dict[str, Image.Image]:
    return {name: fit_asset(ASSET_DIR / name) for name in ASSETS}


def moving_crop(image: Image.Image, event: dict, t: float, index: int) -> Image.Image:
    p = max(0, min(1, (t-event["start"]) / max(0.01, event["end"]-event["start"])))
    eased = p*p*(3-2*p)
    zoom = 1.015 + 0.025*eased
    resized = image.resize((round(image.width*zoom), round(image.height*zoom)), Image.Resampling.BICUBIC)
    room_x, room_y = resized.width-core.base.W, resized.height-core.base.H
    x = round(room_x * ((0.28+0.38*eased) if index%2==0 else (0.68-0.38*eased)))
    y = round(room_y * 0.48)
    return resized.crop((max(0,x), max(0,y), max(0,x)+core.base.W, max(0,y)+core.base.H))


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    index = 6 if event["phase"] == "end" else event["scene"]-1
    frame = moving_crop(assets[event["asset"]], event, t, index).convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay, "RGBA")
    local = t-event["start"]
    rng = random.Random(20260829+index)
    for j in range(20):
        x = rng.randint(40, 1880); y = rng.randint(30, 920)
        r = 1 + int((math.sin(local*1.4+j)+1)*0.8)
        draw.ellipse((x-r,y-r,x+r,y+r), fill=(255,220,130,40))
    if event["phase"] == "end":
        draw.rectangle((0,0,core.base.W,core.base.H), fill=(18,16,45,80))
        draw.rounded_rectangle((300,770,1620,985),44,fill=(39,35,85,230),outline=(255,210,106,245),width=7)
        core.base.centered(draw,(960,850),"SMALL • MEDIUM • LARGE",core.base.F48,(255,238,139,255),3)
        core.base.centered(draw,(960,930),"LIGHT MAKES SHADOWS CHANGE",core.base.F48,"white",3)
    elif index == 0 and local < 2.3:
        alpha = round(235 * min(1, (2.3-local)/0.35))
        draw.rounded_rectangle((250,60,1670,245),42,fill=(35,31,82,alpha),outline=(255,211,105,alpha),width=7)
        core.base.centered(draw,(960,130),"LUMI'S SHADOW",core.base.F62,(255,235,132,alpha),3)
        core.base.centered(draw,(960,205),"THEATRE SURPRISE",core.base.F62,(255,255,255,alpha),3)
    frame.alpha_composite(overlay)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    path = WORK / "original-lumi-shadow-song.wav"
    rate = 48000; beat = 60/84
    palettes = (
        (220.0,261.63,329.63,392.0), (246.94,293.66,369.99,440.0),
        (196.0,246.94,293.66,392.0), (261.63,329.63,392.0,523.25),
        (164.81,196.0,246.94,293.66), (220.0,277.18,329.63,440.0),
        (261.63,329.63,392.0,523.25),
    )
    rng = random.Random(842026)
    with wave.open(str(path),"wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate)
        chunk=bytearray()
        for n in range(round(total*rate)):
            t=n/rate; scene=min(6,int(t//SCENE_SECONDS)); local=t-scene*SCENE_SECONDS
            phase=local%beat; half=local%(beat/2); palette=palettes[scene]
            note=palette[int(local/beat)%4]
            pluck=math.sin(math.tau*note*t)*math.exp(-5.8*phase)*0.034
            harmony=sum(math.sin(math.tau*f*t) for f in palette[:3])*0.0065
            bass=math.sin(math.tau*(palette[0]/2)*t)*math.exp(-3.8*(local%(beat*2)))*0.018
            shaker=rng.uniform(-1,1)*math.exp(-60*half)*(0.008 if scene in (2,3,5,6) else 0.003)
            value=(pluck+harmony+bass+shaker)*(0.68 if scene==4 else 1.0)
            if t>=80: value*=max(0,(total-t)/4)
            sample=int(max(-1,min(1,value))*30000); chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: output.writeframesraw(chunk); chunk.clear()
        if chunk: output.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source=Image.open(ASSET_DIR/ASSETS[5]).convert("RGB")
    width=round(source.height*16/9); left=max(0,(source.width-width)//2)
    canvas=source.crop((left,0,left+width,source.height)).resize((1280,720),Image.Resampling.LANCZOS)
    canvas=ImageEnhance.Color(canvas).enhance(1.12).convert("RGBA"); draw=ImageDraw.Draw(canvas,"RGBA")
    draw.rounded_rectangle((44,38,690,188),34,fill=(39,35,93,230),outline="white",width=5)
    font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",58); text="WATCH IT GROW!"
    draw.text((79,76),text,font=font,fill=(255,239,127),stroke_width=4,stroke_fill=(19,18,50))
    THUMBNAIL.parent.mkdir(parents=True,exist_ok=True); canvas.convert("RGB").save(THUMBNAIL,quality=90,optimize=True)


def quality(events: list[dict], total: float, assets: dict[str, Image.Image]) -> dict:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True))
    video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    decode=subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],capture_output=True)
    transitions=[{"from":a["phase"],"to":b["phase"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]
    sync=[]
    for event in events[:-1]:
        contained=all(event["start"]<=row["start"]<row["end"]<=event["end"] for row in event["lines"]+event["effects"])
        sync.append({"scene":event["scene"],"emotion":event["emotion"],"asset":event["asset"],"visual_action":event["visual_action"],"visual_start":event["start"],"visual_end":event["end"],"lines":event["lines"],"effects":event["effects"],"contained":contained})
    pace=core.pacing_audit(sync)
    checks={
        "duration":abs(float(probe["format"]["duration"])-total)<0.25,
        "h264_1080p":video.get("codec_name")=="h264" and video.get("width")==1920 and video.get("height")==1080,
        "aac_48k_stereo":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,
        "full_decode":decode.returncode==0,
        "zero_gaps":all(abs(row["gap_seconds"])<1e-6 for row in transitions),
        "continuous_visual_timeline":all(abs(row["gap_seconds"])<1e-6 for row in transitions),
        "end_card_is_final_event_only":events[-1]["phase"]=="end",
        "seven_unique_story_scenes":len({row["asset"] for row in sync})==7,
        "all_story_scenes_under_14_seconds":all(row["visual_end"]-row["visual_start"]<14 for row in sync),
        "narration_and_effects_contained":all(row["contained"] for row in sync),
        "child_friendly_narration_pacing":pace["passed"],
        "three_voice_rotation":len({line["profile"].split("-")[0] for row in sync for line in row["lines"]})==3,
        "no_spoken_sound_imitation":all(not any(word in line["line"].lower() for word in ("clap clap","tap tap","knock knock","whoosh")) for row in sync for line in row["lines"]),
        "thumbnail":THUMBNAIL.is_file() and THUMBNAIL.stat().st_size<2_000_000,
    }
    report={"output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"format":"backlit-paper-theatre-size-contrast-story-song","bpm":84,"voice_profiles":sorted({line["profile"] for row in sync for line in row["lines"]}),"visual_method":"five reviewed generated handcrafted-theatre compositions plus two deterministic local paper-theatre composites with restrained camera travel","narration_pacing":{"weighted_wpm":pace["weighted_wpm"],"maximum_line_wpm":pace["maximum_line_wpm"],"minimum_interline_gap_seconds":pace["minimum_interline_gap_seconds"]},"true_rigged_3d_animation":False,"paid_generation_used":False,"checks":checks,"passed":all(checks.values())}
    (WORK/"timeline-gap-audit.json").write_text(json.dumps(transitions,indent=2)+"\n",encoding="utf-8")
    (WORK/"lyric-visual-emotion-audit.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8")
    (WORK/"narration-pacing-audit.json").write_text(json.dumps(pace,indent=2)+"\n",encoding="utf-8")
    (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    general=Image.new("RGB",(960,270),"white")
    for index,event in enumerate(events): general.paste(frame_for(event,event["start"]+(event["end"]-event["start"])*0.55,assets).resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    general.save(WORK/"quality-contact-sheet.png")
    boundary=[]
    for current,following in zip(events,events[1:]): boundary.extend([(current,current["end"]-0.12),(following,following["start"]+0.12)])
    sheet=Image.new("RGB",(1200,math.ceil(len(boundary)/5)*135),"white")
    for index,(event,t) in enumerate(boundary): sheet.paste(frame_for(event,t,assets).resize((240,135),Image.Resampling.LANCZOS),((index%5)*240,(index//5)*135))
    sheet.save(WORK/"transition-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Lumi quality gate failed: {report}")
    return report


def write_metadata(total: float, report: dict) -> None:
    pace=report["narration_pacing"]
    doc={"id":ITEM_ID,"title":"Lumi's Shadow Theatre Surprise | Big and Small Song for Kids","description":"Join Lumi and Ms Noor in a handcrafted theatre where one small paper rabbit makes small, medium and giant shadows. Layer simple shapes into an owl, solve a gentle curtain surprise, and sing the shadow-size finale.\n\nAn original Tiny Tales musical story about light, shadows, size words, careful observation and calm curiosity for children ages 3 to 7.","tags":["shadows for kids","big and small for kids","light and shadow","theatre story for kids","size words for preschool","musical science story","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":"ryan-uk","character_voice_profiles":{"lumi":"natasha-au","ms_noor":"ana-us"},"delivery":"emotion-mapped melodic rhythmic story-song","bpm":84,"format_family":"backlit-paper-theatre-size-contrast-story-song","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"transition_contact_sheet_reviewed":False,"thumbnail_reviewed":False,"manual_visual_review_passed":False,"quality_report":f"automation/production-work/{ITEM_ID}/quality-report.json","transition_audit":f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json","lyric_visual_emotion_audit":f"automation/production-work/{ITEM_ID}/lyric-visual-emotion-audit.json","narration_pacing_audit":f"automation/production-work/{ITEM_ID}/narration-pacing-audit.json","narration_pacing":pace,"quality_contact_sheet":f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png","transition_contact_sheet":f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png","prepared_thumbnail":f"automation/thumbnails/{ITEM_ID}.jpg","thumbnail_hook":"WATCH IT GROW!","reviewed_sha256":hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),"true_rigged_3d_animation":False,"paid_generation_used":False,"spoken_sound_effect_words_removed":True,"upload_queue_released":False}
    META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True,exist_ok=True); OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    prepare_local_scene_assets(); plan=load_plan(); asyncio.run(make_voices(plan))
    events,tracks,total=build_timeline(plan); assets=load_assets(); make_thumbnail()
    core.render_engine.WORK=WORK; core.render_engine.OUTPUT=OUTPUT; core.render_engine.frame_for=frame_for; core.render_engine.make_music=make_music
    core.render_engine.render(events,tracks,total,assets)
    report=quality(events,total,assets); write_metadata(total,report)
    print(json.dumps({"output":str(OUTPUT),"duration_seconds":total,"pacing":report["narration_pacing"],"passed":report["passed"]},indent=2))


if __name__ == "__main__":
    main()
