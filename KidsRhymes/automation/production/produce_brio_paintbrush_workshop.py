"""Produce Brio's original 3D-look Paintbrush Colour Workshop."""

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
from PIL import Image, ImageDraw, ImageFilter

import produce_snack_video as base
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
OUTPUT = AUTOMATION / "production-output" / "brio-paintbrush-colour-workshop-01.mp4"
WORK = AUTOMATION / "production-work" / "brio-paintbrush-colour-workshop-01"
META = AUTOMATION.parent / "metadata" / "brio-paintbrush-colour-workshop-01.json"
ASSETS = AUTOMATION / "production-assets"
BRIO_SHEET = ASSETS / "brio-3d-pose-sheet.png"
DROP_SHEET = ASSETS / "paint-drop-friends-3d-sheet.png"
BACKGROUNDS = {
    "blank": ASSETS / "paintbrush-blank-workshop.png",
    "lab": ASSETS / "paintbrush-colour-lab.png",
    "meadow": ASSETS / "paintbrush-canvas-meadow.png",
    "gallery": ASSETS / "paintbrush-gallery-finale.png",
}
VOICE = select_voice_profile("ryan-uk")
ART_FPS, VIDEO_FPS = 10, 30

SCRIPT = [
    ("intro", "Welcome, artists! I am Brio the paintbrush. Our giant canvas has lost every colour. Will you help me paint it back?"),
    ("blank", "First, warm up your painting arm. Sweep left, sweep right, then make one giant circle."),
    ("warmup", None, "SWEEP • SWEEP • CIRCLE", 5.2),
    ("red", "Red Paint Drop rolls in. Air-paint a big red circle with me. Ready? Paint!"),
    ("red_action", None, "PAINT A RED CIRCLE", 5.2),
    ("yellow", "Yellow Paint Drop bounces in. Paint bright sun rays from the middle to the edge."),
    ("yellow_action", None, "PAINT YELLOW SUN RAYS", 5.2),
    ("blue", "Blue Paint Drop spins in. Paint three slow blue waves through the air."),
    ("blue_action", None, "PAINT THREE BLUE WAVES", 5.2),
    ("orange_mix", "Red and yellow swirl together. They make orange! Circle both hands to mix them."),
    ("orange_action", None, "MIX RED + YELLOW = ORANGE", 5.2),
    ("green_mix", "Yellow and blue dance together. They make green! Rub your hands, then open them wide."),
    ("green_action", None, "MIX YELLOW + BLUE = GREEN", 5.2),
    ("meadow", "Look! Our canvas is waking up. Sweep blue across the sky, green across the hills, and dot orange flowers."),
    ("sky_action", None, "SWEEP THE BLUE SKY", 5.0),
    ("hill_action", None, "WAVE THE GREEN HILLS", 5.0),
    ("flower_action", None, "DOT THE ORANGE FLOWERS", 5.0),
    ("chorus", "Brush up, brush down, colours all around. Swish left, swish right, make the canvas bright!"),
    ("chorus_action", None, "YOUR PAINTBRUSH DANCE", 6.0),
    ("finale", "We painted a whole world together! Every picture can begin with one brave little mark. Thank you, artists!"),
]


def voice_path(index: int, phase: str) -> Path:
    return WORK / f"voice-{index:02d}-{phase}.mp3"


async def make_voices() -> None:
    tasks = []
    for index, entry in enumerate(SCRIPT):
        phase, text = entry[:2]
        if text is None: continue
        target = voice_path(index, phase)
        if target.exists():
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(target)], capture_output=True, text=True)
            if probe.returncode != 0 or not probe.stdout.strip(): target.unlink()
        if not target.exists():
            tasks.append(edge_tts.Communicate(text, VOICE["voice"], rate=VOICE["rate"], pitch=VOICE["pitch"], volume="-1%").save(str(target)))
    if tasks: await asyncio.gather(*tasks)


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], text=True).strip())


def build_timeline() -> tuple[list[dict], list[tuple[Path, float]], float]:
    events = [{"phase": "title", "start": 0.0, "end": 5.0}]; voices = []; cursor = 5.0
    for index, entry in enumerate(SCRIPT):
        phase, text = entry[:2]
        if text is None:
            length = float(entry[3]); events.append({"phase": phase, "start": cursor, "end": cursor + length + .3, "text": entry[2], "activity": True}); cursor += length + .3
        else:
            path = voice_path(index, phase); length = duration(path)
            events.append({"phase": phase, "start": cursor, "end": cursor + length + .65, "text": text}); voices.append((path, cursor)); cursor += length + .65
    events.append({"phase": "end", "start": cursor, "end": cursor + 4.5}); return events, voices, cursor + 4.5


def split_sheet(path: Path) -> list[Image.Image]:
    sheet = Image.open(path).convert("RGBA"); result = []
    for row in range(2):
        for col in range(3):
            cell = sheet.crop((col * sheet.width // 3, row * sheet.height // 2, (col + 1) * sheet.width // 3, (row + 1) * sheet.height // 2)); bbox = cell.getchannel("A").getbbox()
            if not bbox: raise RuntimeError(f"Empty sprite cell {row},{col}: {path}")
            result.append(cell.crop(bbox))
    return result


def fit_background(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB"); scale = max((base.W + 100) / image.width, (base.H + 70) / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def load_assets() -> dict:
    required = [BRIO_SHEET, DROP_SHEET, *BACKGROUNDS.values()]; missing = [str(p) for p in required if not p.exists()]
    if missing: raise FileNotFoundError(f"Missing Brio workshop assets: {missing}")
    return {"brio": split_sheet(BRIO_SHEET), "drops": split_sheet(DROP_SHEET)[:5], "backgrounds": {k: fit_background(v) for k, v in BACKGROUNDS.items()}}


def camera(source: Image.Image, t: float, phase: str) -> Image.Image:
    max_x, max_y = max(0, source.width - base.W), max(0, source.height - base.H)
    x = round(max_x * (.5 + .4 * math.sin(t * .09 + len(phase)))); y = round(max_y * (.5 + .25 * math.sin(t * .07 + 1.4)))
    return source.crop((x, y, x + base.W, y + base.H)).convert("RGBA")


def sprite(frame: Image.Image, image: Image.Image, center: tuple[float, float], height: float, bob: float = 0, tilt: float = 0) -> None:
    ratio = height / image.height; item = image.resize((max(1, round(image.width * ratio)), round(height)), Image.Resampling.LANCZOS)
    if tilt: item = item.rotate(tilt, Image.Resampling.BICUBIC, expand=True)
    cx, cy = center; layer = Image.new("RGBA", frame.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(layer, "RGBA"); w = max(80, item.width * .55)
    draw.ellipse((cx - w / 2, cy - 13, cx + w / 2, cy + 16), fill=(40, 31, 35, 70)); frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(7)))
    frame.alpha_composite(item, (round(cx - item.width / 2), round(cy - item.height + bob)))


def environment(phase: str) -> str:
    if phase in {"red", "red_action", "yellow", "yellow_action", "blue", "blue_action", "orange_mix", "orange_action", "green_mix", "green_action"}: return "lab"
    if phase in {"meadow", "sky_action", "hill_action", "flower_action", "chorus", "chorus_action"}: return "meadow"
    if phase in {"finale", "end", "title"}: return "gallery"
    return "blank"


POSE_BY_PHASE = {
    "intro": 4,
    "blank": 1,
    "warmup": 2,
    "red": 0,
    "red_action": 0,
    "yellow": 4,
    "yellow_action": 4,
    "blue": 5,
    "blue_action": 5,
    "orange_mix": 3,
    "orange_action": 3,
    "green_mix": 4,
    "green_action": 4,
    "meadow": 1,
    "sky_action": 1,
    "hill_action": 2,
    "flower_action": 0,
    "chorus": 3,
    "chorus_action": 3,
    "finale": 4,
    "end": 5,
}


def activity_panel(draw: ImageDraw.ImageDraw, event: dict, t: float) -> None:
    progress = max(0, min(1, (t - event["start"]) / (event["end"] - event["start"])))
    base.panel(draw, (360, 820, 1560, 1022), radius=40, fill=(255, 250, 235, 240), outline=(255, 169, 42, 255), width=6)
    base.centered(draw, (960, 882), event["text"], base.F38, (43, 75, 104, 255), 2)
    for i in range(5):
        cx = 710 + i * 125; active = progress >= i / 5; r = 29 + (6 if active and int(t * 5) % 2 == 0 else 0)
        draw.ellipse((cx-r, 962-r, cx+r, 962+r), fill=(255, 155, 40, 255) if active else (210, 218, 220, 255), outline=(255,255,255,255), width=3)


def paint_marks(draw: ImageDraw.ImageDraw, phase: str, p: float, t: float) -> None:
    if phase in {"red", "red_action"}:
        box = (790, 240, 1220, 670); draw.arc(box, 0, 360 * p if phase.endswith("action") else 90, fill=(235, 50, 48, 230), width=40)
    elif phase in {"yellow", "yellow_action"}:
        cx, cy = 1005, 455; count = max(2, round(12 * p)) if phase.endswith("action") else 3
        draw.ellipse((cx-85,cy-85,cx+85,cy+85), fill=(255,213,30,210))
        for i in range(count):
            a=2*math.pi*i/12; draw.line((cx+110*math.cos(a),cy+110*math.sin(a),cx+190*math.cos(a),cy+190*math.sin(a)), fill=(255,213,30,230), width=24)
    elif phase in {"blue", "blue_action"}:
        for row in range(3):
            points=[]
            for i in range(max(3, round(30*p))):
                x=760+i*18; y=360+row*125+35*math.sin(i*.55+t)
                points.append((x,y))
            if len(points)>1: draw.line(points, fill=(35,115,225,225), width=25)


def frame_for(event: dict, t: float, assets: dict) -> Image.Image:
    phase = event["phase"]; env = environment(phase); frame = camera(assets["backgrounds"][env], t, phase); draw = ImageDraw.Draw(frame, "RGBA")
    p = max(0, min(1, (t-event["start"]) / max(.01,event["end"]-event["start"])))
    if phase == "title":
        frame.alpha_composite(Image.new("RGBA", frame.size, (25,35,72,55))); sprite(frame, assets["brio"][0], (420,1045), 820, bob=-20*abs(math.sin(t*3)))
        base.panel(draw,(650,165,1750,650),radius=55,fill=(255,250,235,240),outline=(255,169,42,255),width=8)
        base.centered(draw,(1200,285),"BRIO'S PAINTBRUSH",base.F62,(44,103,153,255),2); base.centered(draw,(1200,415),"COLOUR WORKSHOP",base.F62,(225,70,78,255),2); base.centered(draw,(1200,540),"PAINT • MIX • MOVE",base.F48,(55,145,92,255),2)
        return frame.convert("RGB")
    if phase in {"red","red_action","yellow","yellow_action","blue","blue_action"}: paint_marks(draw,phase,p,t)
    brio_pose = POSE_BY_PHASE.get(phase, 0); brio_x = 400 if env in {"blank","meadow"} else 1480; sprite(frame,assets["brio"][brio_pose],(brio_x,1040),700,bob=-12*abs(math.sin(t*2.2)),tilt=2*math.sin(t*1.2))
    colour_map = {"red":0,"red_action":0,"yellow":1,"yellow_action":1,"blue":2,"blue_action":2,"orange_mix":3,"orange_action":3,"green_mix":4,"green_action":4}
    if phase in colour_map:
        idx=colour_map[phase]; sprite(frame,assets["drops"][idx],(960,940),570,bob=-35*abs(math.sin(t*4.5)),tilt=6*math.sin(t*2.2))
        if phase.startswith("orange"):
            sprite(frame,assets["drops"][0],(700,860),360,bob=-20*abs(math.sin(t*4))); sprite(frame,assets["drops"][1],(1210,860),360,bob=-20*abs(math.sin(t*4+1)))
        if phase.startswith("green"):
            sprite(frame,assets["drops"][1],(700,860),360,bob=-20*abs(math.sin(t*4))); sprite(frame,assets["drops"][2],(1210,860),360,bob=-20*abs(math.sin(t*4+1)))
    if env == "meadow":
        colours=((35,125,235,180),(66,175,85,180),(255,145,38,180),(240,70,80,170))
        for i in range(18):
            x=700+(i*83+int(t*50))%1050; y=160+(i*137)%650; r=7+i%5; draw.ellipse((x-r,y-r,x+r,y+r),fill=colours[i%4])
    headings={"intro":"THE CANVAS LOST ITS COLOURS","blank":"WARM UP YOUR PAINTING ARM","warmup":"ARTIST WARM-UP","red":"RED PAINT DROP","red_action":"PAINT WITH RED","yellow":"YELLOW PAINT DROP","yellow_action":"PAINT WITH YELLOW","blue":"BLUE PAINT DROP","blue_action":"PAINT WITH BLUE","orange_mix":"RED + YELLOW","orange_action":"HELLO, ORANGE!","green_mix":"YELLOW + BLUE","green_action":"HELLO, GREEN!","meadow":"THE CANVAS WAKES UP","sky_action":"BLUE SKY","hill_action":"GREEN HILLS","flower_action":"ORANGE FLOWERS","chorus":"BRUSH UP, BRUSH DOWN","chorus_action":"PAINTBRUSH DANCE","finale":"OUR COLOUR GALLERY","end":"ONE BRAVE LITTLE MARK"}
    base.panel(draw,(350,42,1570,145),radius=32,fill=(255,250,235,232),outline=(255,169,42,255),width=5); base.centered(draw,(960,94),headings.get(phase,"BRIO'S COLOUR WORKSHOP"),base.F38,(43,75,104,255),2)
    if event.get("activity"): activity_panel(draw,event,t)
    if phase in {"finale","end"}:
        for i,drop in enumerate(assets["drops"]): sprite(frame,drop,(620+i*190,1000),300,bob=-15*abs(math.sin(t*4+i)),tilt=4*math.sin(t*2+i))
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target=WORK/"paintbrush-workshop-music.wav"
    if target.exists(): return target
    rate=48000; rng=random.Random(824); notes=(261.63,329.63,392.0,440.0,523.25)
    with wave.open(str(target),"wb") as h:
        h.setnchannels(2);h.setsampwidth(2);h.setframerate(rate);block=bytearray()
        for i in range(round(total*rate)):
            t=i/rate; beat=t%.5; eighth=t%.25; n=notes[int(t/1.5)%len(notes)]
            kick=math.sin(2*math.pi*(72-22*min(1,beat/.14))*beat)*math.exp(-25*beat)*.08; brush=(rng.random()*2-1)*(.010 if int(t*8)%2 else .018); bass=math.sin(2*math.pi*n/2*t)*.02; bell=math.sin(2*math.pi*notes[int(t/.25)%5]*t)*math.exp(-12*eighth)*.024; fade=min(1,t/1.1,(total-t)/1.5);s=round(max(-1,min(1,(kick+brush+bass+bell)*fade))*32767);block+=struct.pack("<hh",s,s)
            if len(block)>=131072:h.writeframes(block);block.clear()
        if block:h.writeframes(block)
    return target


def render(events:list[dict],voices:list[tuple[Path,float]],total:float,assets:dict)->None:
    silent=WORK/"silent.mp4";p=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{base.W}x{base.H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","veryfast","-crf","19","-profile:v","high","-pix_fmt","yuv420p",str(silent)],stdin=subprocess.PIPE);assert p.stdin
    for number in range(math.ceil(total*ART_FPS)):
        t=number/ART_FPS;e=next((x for x in events if x["start"]<=t<x["end"]),None)
        if e is None: raise RuntimeError(f"Brio workshop timeline has no visual event at {t:.3f}s")
        p.stdin.write(frame_for(e,t,assets).tobytes())
        if number%(ART_FPS*15)==0:print(f"Rendered {t:.0f}/{total:.0f}s",flush=True)
    p.stdin.close()
    if p.wait()!=0:raise RuntimeError("Brio workshop silent render failed")
    bed=make_music(total);inputs=["-i",str(silent),"-i",str(bed)];filters=["[1:a]volume=.70[bed]"];labels=["[bed]"]
    for stream,(voice,start) in enumerate(voices,2):inputs += ["-i",str(voice)];delay=round(start*1000);filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.24[v{stream}]");labels.append(f"[v{stream}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg","-y","-loglevel","error",*inputs,"-filter_complex",";".join(filters),"-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t",f"{total:.3f}","-movflags","+faststart",str(OUTPUT)],check=True)


def quality(events:list[dict],total:float,assets:dict)->None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True))
    video=next(s for s in probe["streams"] if s["codec_type"]=="video");audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    full_decode=subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],capture_output=True,text=True,check=False)
    gaps=[{"phase":e["phase"],"quiet_gap_seconds":e["end"]-e["start"]} for e in events if e.get("activity")]
    transitions=[{"from_phase":a["phase"],"to_phase":b["phase"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]
    (WORK/"activity-gap-audit.json").write_text(json.dumps(gaps,indent=2)+"\n",encoding="utf-8")
    (WORK/"timeline-gap-audit.json").write_text(json.dumps(transitions,indent=2)+"\n",encoding="utf-8")
    pose_sequence=[POSE_BY_PHASE[e["phase"]] for e in events if e["phase"] in POSE_BY_PHASE]
    pose_changes=sum(a!=b for a,b in zip(pose_sequence,pose_sequence[1:]));pose_changes_per_minute=pose_changes/(total/60)
    checks={"size":OUTPUT.stat().st_size>2_000_000,"duration":110<=float(probe["format"]["duration"])<=240 and abs(float(probe["format"]["duration"])-total)<.3,"video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,"audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"full_decode":full_decode.returncode==0,"ten_response_gaps":len(gaps)==10 and all(g["quiet_gap_seconds"]>=5 for g in gaps),"continuous_visual_timeline":all(abs(item["gap_seconds"])<.000001 for item in transitions),"end_card_is_final_event_only":events[-1]["phase"]=="end" and all(e["phase"]!="end" for e in events[:-1]),"stable_brio_pose_per_event":all(e["phase"] in POSE_BY_PHASE for e in events if e["phase"]!="title"),"controlled_pose_changes":pose_changes_per_minute<=10,"six_brio_poses":len(assets["brio"])==6,"five_clean_colour_friends":len(assets["drops"])==5,"four_art_worlds":len(assets["backgrounds"])==4,"voice_rotation":VOICE["name"]=="ryan-uk"}
    report={"format":"3d-canvas-restoration-music-story","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"voice_profile":VOICE["name"],"pose_changes":pose_changes,"pose_changes_per_minute":pose_changes_per_minute,"new_image_generation_calls":6,"rejected_image_variants":1,"true_rigged_3d_animation":False,"visual_method":"original 3D-rendered pose assets with code-painted canvas marks, colour mixing, camera travel and compositing","checks":checks,"passed":all(checks.values())};(WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[e for e in events if e["phase"] in {"title","intro","warmup","red_action","yellow_action","blue_action","orange_action","green_action","meadow","sky_action","hill_action","flower_action","chorus_action","finale","end"}];contact=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for i,e in enumerate(samples):t=e["start"]+min(2,(e["end"]-e["start"])/2);im=frame_for(e,t,assets).resize((240,135),Image.Resampling.LANCZOS);contact.paste(im,((i%4)*240,(i//4)*135))
    contact.save(WORK/"quality-contact-sheet.png")
    boundary_samples=[]
    for current,following in zip(events,events[1:]):
        boundary_samples.extend([(current,max(current["start"],current["end"]-.12)),(following,min(following["end"]-.01,following["start"]+.12))])
    transition_sheet=Image.new("RGB",(1200,math.ceil(len(boundary_samples)/5)*135),"white")
    for i,(event,t) in enumerate(boundary_samples):
        im=frame_for(event,t,assets).resize((240,135),Image.Resampling.LANCZOS);d=ImageDraw.Draw(im);d.rectangle((0,0,110,19),fill="black");d.text((3,2),f"{t:.1f}s {event['phase']}",font=base.font(12,True),fill="white");transition_sheet.paste(im,((i%5)*240,(i//5)*135))
    transition_sheet.save(WORK/"transition-contact-sheet.png")
    if not report["passed"]:raise RuntimeError(f"Brio workshop quality gate failed: {report}")


def write_metadata(total:float)->None:
    doc={"id":"brio-paintbrush-colour-workshop-01","title":"Brio's Paintbrush Colour Workshop | Paint, Mix and Move for Kids","description":"Help Brio restore a giant blank canvas in an original colour-and-movement music story. Children air-paint red circles, yellow rays and blue waves, mix orange and green, then bring a whole canvas meadow to life.\n\nA Tiny Tales 3D-look art adventure supporting primary colours, early colour mixing, creative movement, listening and imagination for children ages 3 to 7.","tags":["paintbrush song","colours for kids","colour mixing for kids","art for kids","movement song","preschool learning","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":VOICE["name"],"format_family":"3d-canvas-restoration-music-story","visual_system":"3d-magical-art-studio-with-code-painted-canvas","interaction_style":"air-painting-and-primary-colour-mixing","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"transition_contact_sheet_reviewed":False,"quality_report":"automation/production-work/brio-paintbrush-colour-workshop-01/quality-report.json","transition_audit":"automation/production-work/brio-paintbrush-colour-workshop-01/timeline-gap-audit.json","quality_contact_sheet":"automation/production-work/brio-paintbrush-colour-workshop-01/quality-contact-sheet.png","transition_contact_sheet":"automation/production-work/brio-paintbrush-colour-workshop-01/transition-contact-sheet.png","new_image_generation_calls":6,"rejected_image_variants":1,"true_rigged_3d_animation":False};META.parent.mkdir(parents=True,exist_ok=True);META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main()->None:
    WORK.mkdir(parents=True,exist_ok=True);OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    if OUTPUT.exists() and (WORK/"quality-report.json").exists() and json.loads((WORK/"quality-report.json").read_text(encoding="utf-8")).get("passed"):print(f"Completed output already exists; preserving without regeneration: {OUTPUT}");return
    asyncio.run(make_voices());events,voices,total=build_timeline();assets=load_assets();render(events,voices,total,assets);quality(events,total,assets);write_metadata(total);print(json.dumps({"id":"brio-paintbrush-colour-workshop-01","duration_seconds":total,"status":"completed"},indent=2))


if __name__=="__main__":main()
