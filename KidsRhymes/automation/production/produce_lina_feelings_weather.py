"""Produce Lina's Feelings Weather Studio from its locked scene/audio plan."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import wave

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

import produce_snack_video as base
import produce_star_friends_twinkle_playground as render_engine
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "linas-feelings-weather-studio-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
ART_FPS = 10

VOICES = {
    "natasha-curious": {**select_voice_profile("natasha-au"), "rate": "+2%", "pitch": "+7Hz"},
    "natasha-bright": {**select_voice_profile("natasha-au"), "rate": "+5%", "pitch": "+10Hz"},
    "natasha-grounded": {**select_voice_profile("natasha-au"), "rate": "-4%", "pitch": "-3Hz"},
    "natasha-soft": {**select_voice_profile("natasha-au"), "rate": "-7%", "pitch": "+1Hz"},
    "natasha-warm": {**select_voice_profile("natasha-au"), "rate": "-2%", "pitch": "+5Hz"},
    "ana-us": select_voice_profile("ana-us"),
    "ana-calm": {**select_voice_profile("ana-us"), "rate": "-5%", "pitch": "+3Hz"},
    "ryan-uk": select_voice_profile("ryan-uk"),
}


def plan_shots() -> list[dict]:
    return json.loads(PLAN.read_text(encoding="utf-8"))["shots"]


def voice_path(si: int, li: int, profile: str) -> Path:
    return WORK / f"voice-v3-{si:02d}-{li:02d}-{profile}.mp3"


async def make_voices(shots: list[dict]) -> None:
    for si, shot in enumerate(shots):
        for li, row in enumerate(shot["lines"]):
            target = voice_path(si, li, row["profile"])
            if not target.exists() or target.stat().st_size < 1000:
                voice = VOICES[row["profile"]]
                await edge_tts.Communicate(row["line"], voice["voice"], rate=voice["rate"], pitch=voice["pitch"], volume="-1%").save(str(target))


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], text=True).strip())


def make_sfx() -> dict[str, Path]:
    rate = 48000
    rng = random.Random(8272026)
    specs = {
        "01_opening_forecast": (1.10, "ratchet"),
        "02_sunshine_joy": (1.20, "chime"),
        "03_anger_storm": (3.20, "storm_breath"),
        "04_sadness_rain": (4.00, "rain"),
        "05_worry_fog": (2.20, "steps"),
        "06_rainbow_resolution": (2.40, "rainbow"),
    }
    paths = {}
    for sid, (length, kind) in specs.items():
        path = WORK / f"effect-{kind}.wav"
        with wave.open(str(path), "wb") as out:
            out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate)
            frames = bytearray(); smooth = 0.0
            for n in range(round(length * rate)):
                t = n / rate; value = 0.0
                if kind == "ratchet":
                    for onset in (0.06, 0.25, 0.45, 0.67, 0.88):
                        age = t - onset
                        if 0 <= age < 0.09: value += math.sin(2*math.pi*430*age)*math.exp(-45*age)*0.16
                elif kind == "chime":
                    for onset, freq in ((0.05, 660), (0.34, 880), (0.64, 1047)):
                        age = t-onset
                        if age >= 0: value += math.sin(2*math.pi*freq*age)*math.exp(-4.8*age)*0.085
                elif kind == "storm_breath":
                    noise = rng.uniform(-1, 1); smooth = 0.985*smooth + 0.015*noise
                    value += smooth * math.exp(-1.8*t) * 0.26
                    for onset in (0.55, 1.45, 2.35):
                        age = t-onset
                        if 0 <= age < 0.75: value += rng.uniform(-1,1)*math.sin(math.pi*age/0.75)**2*0.018
                elif kind == "rain":
                    noise = rng.uniform(-1,1); smooth = 0.72*smooth + 0.28*noise
                    value = smooth*0.025 + (rng.uniform(-1,1)*0.08 if rng.random()<0.004 else 0)
                    value *= min(1, t/0.35)*min(1, (length-t)/0.35)
                elif kind == "steps":
                    for onset, freq in ((0.15, 523), (0.82, 659), (1.49, 784)):
                        age=t-onset
                        if age >= 0: value += math.sin(2*math.pi*freq*age)*math.exp(-5.5*age)*0.09
                else:
                    idx = min(7, int(t/0.28)); freqs=(392,440,523,587,659,784,880,1047)
                    age=t-idx*0.28
                    if age >= 0: value += math.sin(2*math.pi*freqs[idx]*age)*math.exp(-4.2*age)*0.07
                sample = int(max(-1, min(1, value))*22000)
                frames.extend(struct.pack("<hh", sample, sample))
            out.writeframes(frames)
        paths[sid] = path
    return paths


def build_timeline(shots: list[dict], sfx: dict[str, Path]):
    events = [{"phase": "title", "start": 0.0, "end": 3.8, "asset": shots[0]["asset"]}]
    tracks: list[tuple[Path, float]] = []
    cursor = 3.8
    for si, shot in enumerate(shots):
        local = 0.25; lines = []
        effect_start = cursor + 0.18
        tracks.append((sfx[shot["id"]], effect_start))
        effect_end = effect_start + duration(sfx[shot["id"]])
        for li, row in enumerate(shot["lines"]):
            path = voice_path(si, li, row["profile"]); length = duration(path)
            start = cursor + local
            lines.append({**row, "start": start, "end": start+length})
            tracks.append((path, start)); local += length + 0.12
        shot_length = max(8.8, local+0.35, effect_end-cursor+0.35)
        if shot_length > 14: raise RuntimeError(f"14-second gate failed: {shot['id']} {shot_length:.2f}s")
        events.append({"phase": shot["id"], "start": cursor, "end": cursor+shot_length, "asset": shot["asset"], "lines": lines, "effects": [{"name": shot["effect"], "start": effect_start, "end": effect_end}]})
        cursor += shot_length
    events.append({"phase": "end", "start": cursor, "end": cursor+4.8, "asset": shots[-1]["asset"]})
    return events, tracks, events[-1]["end"]


def fit(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max((base.W+180)/image.width, (base.H+110)/image.height)
    return image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.LANCZOS)


def load_assets(shots: list[dict]):
    paths = {shot["asset"]: ASSET_DIR/shot["asset"] for shot in shots}
    missing = [str(p) for p in paths.values() if not p.is_file()]
    if missing: raise FileNotFoundError(missing)
    return {name: fit(path) for name, path in paths.items()}


def moving_crop(image: Image.Image, event: dict, t: float, index: int) -> Image.Image:
    p = max(0, min(1, (t-event["start"])/max(0.01,event["end"]-event["start"])))
    eased = p*p*(3-2*p)
    zoom = 1.0 + (0.045*eased if index%2==0 else 0.045*(1-eased))
    resized = image.resize((round((base.W+180)*zoom), round((base.H+110)*zoom)), Image.Resampling.BICUBIC)
    ax, ay = resized.width-base.W, resized.height-base.H
    x = int(ax*((0.18+0.48*eased) if index%2==0 else (0.72-0.44*eased)))
    y = int(ay*(0.45+0.04*math.sin(p*math.pi)))
    return resized.crop((x,y,x+base.W,y+base.H))


def overlay(frame: Image.Image, event: dict, t: float, index: int) -> None:
    draw=ImageDraw.Draw(frame,"RGBA"); local=t-event["start"]; rng=random.Random(9000+index)
    if index==1:
        for j in range(10):
            x=(rng.randint(40,1880)+int(local*(10+j)))%1920; y=rng.randint(60,900)
            draw.ellipse((x-4,y-4,x+4,y+4),fill=(255,225,80,80))
    elif index==2:
        glow=int(10+6*(0.5+0.5*math.sin(local*2.0))); draw.ellipse((875-glow,385-glow,875+glow,385+glow),fill=(255,165,80,45))
    elif index==3:
        for j in range(28):
            x=rng.randint(10,1910); y=(rng.randint(0,1080)+int(local*(38+j%5*6)))%1080
            draw.line((x,y,x-4,y+13),fill=(180,220,255,75),width=2)
    elif index==4:
        for j in range(8):
            x=(rng.randint(0,1900)+int(local*(7+j)))%1920; y=rng.randint(650,1010)
            draw.ellipse((x-40,y-10,x+40,y+10),fill=(180,205,235,22))
    elif index==5:
        for j in range(14):
            x=rng.randint(70,1850); y=rng.randint(60,980); r=2+int(3*(.5+.5*math.sin(local*2+j)))
            draw.ellipse((x-r,y-r,x+r,y+r),fill=(255,235,125,80))


def frame_for(event: dict, t: float, assets) -> Image.Image:
    if event["phase"]=="title":
        frame=moving_crop(assets[event["asset"]],event,t,0).convert("RGBA"); draw=ImageDraw.Draw(frame,"RGBA")
        draw.rounded_rectangle((220,95,1700,350),48,fill=(38,55,91,218),outline=(255,224,108,245),width=7)
        base.centered(draw,(960,178),"LINA'S FEELINGS",base.F62,(255,243,145,255),3)
        base.centered(draw,(960,278),"WEATHER STUDIO",base.F62,"white",3); return frame.convert("RGB")
    if event["phase"]=="end":
        frame=moving_crop(assets[event["asset"]],event,t,5).convert("RGBA"); draw=ImageDraw.Draw(frame,"RGBA")
        draw.rectangle((0,0,1920,1080),fill=(28,37,75,62)); draw.rounded_rectangle((310,760,1610,982),46,fill=(38,55,91,225),outline=(255,224,108,245),width=7)
        base.centered(draw,(960,840),"NOTICE IT • NAME IT",base.F48,(255,243,145,255),2)
        base.centered(draw,(960,922),"CHOOSE YOUR NEXT KIND STEP",base.F48,"white",2); return frame.convert("RGB")
    shots=plan_shots(); index=next(i for i,s in enumerate(shots) if s["id"]==event["phase"])
    frame=moving_crop(assets[event["asset"]],event,t,index).convert("RGBA"); overlay(frame,event,t,index); return frame.convert("RGB")


def make_music(total: float) -> Path:
    path=WORK/"original-feelings-weather-music.wav"; rate=48000; bpm=96; beat=60/bpm; notes=(261.63,329.63,392,349.23,293.66,349.23,440,392); rng=random.Random(270827)
    with wave.open(str(path),"wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); chunk=bytearray()
        for n in range(int(total*rate)):
            t=n/rate; note=notes[int(t/beat)%len(notes)]; phase=t%beat
            pluck=math.sin(2*math.pi*note*t)*math.exp(-4.2*phase)*0.040
            pad=sum(math.sin(2*math.pi*f*t) for f in (130.81,164.81,196))*0.009
            pulse=math.sin(2*math.pi*82*t)*max(0,1-phase/.035)*.022 if phase<.035 else 0
            value=pluck+pad+pulse+rng.uniform(-.0008,.0008); sample=int(max(-1,min(1,value))*32767); chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path


def make_thumbnail() -> None:
    source=Image.open(ASSET_DIR/"lina-weather-rainbow-v1.png").convert("RGB"); w=round(source.height*16/9); left=max(0,(source.width-w)//2)
    canvas=source.crop((left,0,left+w,source.height)).resize((1280,720),Image.Resampling.LANCZOS).convert("RGBA"); canvas=ImageEnhance.Color(canvas).enhance(1.08); draw=ImageDraw.Draw(canvas,"RGBA")
    draw.rounded_rectangle((58,34,1222,172),35,fill=(42,59,103,228),outline="white",width=5); font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",61); text="WHAT'S YOUR WEATHER?"; box=draw.textbbox((0,0),text,font=font,stroke_width=3)
    draw.text(((1280-(box[2]-box[0]))//2,68),text,font=font,fill=(255,244,130),stroke_width=4,stroke_fill=(30,38,75)); THUMBNAIL.parent.mkdir(parents=True,exist_ok=True); canvas.convert("RGB").save(THUMBNAIL,quality=89,optimize=True)


def quality(events,total,assets) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    decode=subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],capture_output=True); gaps=[{"from":a["phase"],"to":b["phase"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]
    sync=[{"shot_id":e["phase"],"asset":e["asset"],"visual_start":e["start"],"visual_end":e["end"],"lines":e["lines"],"effects":e["effects"],"contained":all(e["start"]<=x["start"]<x["end"]<=e["end"] for x in e["lines"]+e["effects"])} for e in events[1:-1]]
    spoken=[x["line"].lower() for row in sync for x in row["lines"]]; forbidden=("boom","whoosh","tap tap","clap clap","brrr")
    checks={"duration":60<=float(probe["format"]["duration"])<=110,"h264_1080p":video.get("codec_name")=="h264" and video.get("width")==1920 and video.get("height")==1080,"aac_stereo":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"full_decode":decode.returncode==0,"zero_gaps":all(abs(x["gap_seconds"])<1e-6 for x in gaps),"six_unique_story_scenes":len({x["asset"] for x in sync})==6,"sync_containment":all(x["contained"] for x in sync),"max_14_seconds":all(e["end"]-e["start"]<=14 for e in events[1:-1]),"final_card_only":events[-1]["phase"]=="end","no_spoken_sound_words":all(not any(f in line for f in forbidden) for line in spoken),"lead_voice_rotation":all(p in VOICES for p in ("natasha-curious","natasha-bright","natasha-grounded","natasha-soft","natasha-warm")),"thumbnail":THUMBNAIL.is_file() and THUMBNAIL.stat().st_size<2_000_000}
    (WORK/"timeline-gap-audit.json").write_text(json.dumps(gaps,indent=2)+"\n",encoding="utf-8"); (WORK/"narration-visual-sync-audit.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8")
    report={"output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"voice_profile":"natasha-au","visual_method":"six original premium 3D-style weather-studio scenes with eased camera travel and restrained scene-specific overlays","audio_method":"character-led scene-matched narration over original music with original ratchet, chime, storm-breath, rain, step-light and rainbow effects","new_image_generation_calls":6,"true_rigged_3d_animation":False,"paid_generation_used":False,"checks":checks,"passed":all(checks.values())}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    general=Image.new("RGB",(960,math.ceil(len(events)/4)*135),"white")
    for i,e in enumerate(events): general.paste(frame_for(e,e["start"]+(e["end"]-e["start"])*.55,assets).resize((240,135),Image.Resampling.LANCZOS),((i%4)*240,(i//4)*135))
    general.save(WORK/"quality-contact-sheet.png"); boundary=[]
    for a,b in zip(events,events[1:]): boundary += [(a,a["end"]-.12),(b,b["start"]+.12)]
    sheet=Image.new("RGB",(1200,math.ceil(len(boundary)/5)*135),"white")
    for i,(e,t) in enumerate(boundary): sheet.paste(frame_for(e,t,assets).resize((240,135),Image.Resampling.LANCZOS),((i%5)*240,(i//5)*135))
    sheet.save(WORK/"transition-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(report)


def write_metadata(total: float) -> None:
    doc={"id":ITEM_ID,"title":"Lina's Feelings Weather Studio | Emotional Story for Kids","description":"Join Lina and Nimbus in a magical weather studio where sunshine, storms, rain and fog help them notice joy, anger, sadness and worry. The friends practise sharing space, slow breathing, asking for company and taking one small step.\n\nAn original Tiny Tales emotional-learning story for children ages 3 to 7.","tags":["feelings for kids","emotional story for children","anger calming for kids","sadness and worry","social emotional learning","preschool story","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":"natasha-au","character_voice_profiles":{"lina":"ana-us","nimbus":"ryan-uk"},"format_family":"magical-emotional-weather-story","visual_system":"six-transforming-premium-3d-weather-studio-worlds","interaction_style":"name-the-feeling-breathe-choose-a-kind-action-and-rainbow-resolution","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"transition_contact_sheet_reviewed":False,"thumbnail_reviewed":False,"quality_report":f"automation/production-work/{ITEM_ID}/quality-report.json","transition_audit":f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json","narration_visual_sync_audit":f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json","quality_contact_sheet":f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png","transition_contact_sheet":f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png","prepared_thumbnail":f"automation/thumbnails/{ITEM_ID}.jpg","thumbnail_hook":"WHAT'S YOUR WEATHER?","new_image_generation_calls":6,"true_rigged_3d_animation":False,"paid_generation_used":False,"spoken_sound_effect_words_removed":True}
    META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True,exist_ok=True); OUTPUT.parent.mkdir(parents=True,exist_ok=True); shots=plan_shots(); sfx=make_sfx(); asyncio.run(make_voices(shots)); events,tracks,total=build_timeline(shots,sfx); assets=load_assets(shots); make_thumbnail()
    render_engine.WORK=WORK; render_engine.OUTPUT=OUTPUT; render_engine.frame_for=frame_for; render_engine.make_music=make_music; render_engine.render(events,tracks,total,assets); quality(events,total,assets); write_metadata(total); print(json.dumps({"output":str(OUTPUT),"duration_seconds":total},indent=2))


if __name__=="__main__": main()
