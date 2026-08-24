"""Produce Tavi the Tiny Train's Shape Delivery Day."""

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
from PIL import Image, ImageDraw, ImageEnhance

import produce_snack_video as base
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
OUTPUT = AUTOMATION / "production-output" / "tavi-shape-delivery-day-01.mp4"
WORK = AUTOMATION / "production-work" / "tavi-shape-delivery-day-01"
META = AUTOMATION.parent / "metadata" / "tavi-shape-delivery-day-01.json"
ASSETS = {
    "depot": AUTOMATION / "production-assets" / "tavi-shape-depot-3d.png",
    "music": AUTOMATION / "production-assets" / "tavi-music-garden-3d.png",
    "reading": AUTOMATION / "production-assets" / "tavi-reading-nook-3d.png",
    "playground": AUTOMATION / "production-assets" / "tavi-playground-3d.png",
    "garden": AUTOMATION / "production-assets" / "tavi-community-garden-3d.png",
}
VOICE = select_voice_profile("natasha-au")
ART_FPS, VIDEO_FPS = 10, 30

SCRIPT = [
    ("welcome", "Tavi is a tiny train with a very important delivery list. Four community places are waiting for four different shapes."),
    ("plan", "At the depot, Tavi checks the order: first a circle, next a square, then a triangle, and last a rectangle."),
    ("circle_load", "First, a round drum rolls gently into Tavi's wagon. A circle is round with no straight sides."),
    ("circle_prompt", "Trace a big circle in the air. Start at the top, curve all the way around, and meet where you began."),
    ("circle_activity", None, "TRACE A BIG CIRCLE", 5.6),
    ("circle_travel", "Chug, chug! Tavi follows the curving track to the music garden. The round drum fits the round stand."),
    ("circle_deliver", "First delivery complete. The drum makes one happy boom, and Tavi remembers: circle came first."),
    ("square_load", "Next comes a soft square reading cushion. A square has four equal sides and four corners."),
    ("square_prompt", "Draw a square with your finger: across, down, across, and up. Four straight sides!"),
    ("square_activity", None, "DRAW FOUR STRAIGHT SIDES", 5.6),
    ("square_travel", "Tavi rolls to the reading nook. The square cushion sits neatly on the square platform."),
    ("square_deliver", "Second delivery complete. First was the circle, and next was the square."),
    ("triangle_load", "Then Tavi loads bright triangle flags. A triangle has three straight sides and three corners."),
    ("triangle_prompt", "Make a triangle with your hands. Point at the top, then make two sloping sides."),
    ("triangle_activity", None, "MAKE A TRIANGLE", 5.6),
    ("triangle_travel", "Tavi clickety-clacks to the playground, where the triangle flags flutter between the poles."),
    ("triangle_deliver", "Third delivery complete. Circle, square, then triangle. Only one shape remains."),
    ("rectangle_load", "Last, rectangular seed trays slide safely into the wagon. A rectangle has four sides, with two long and two short."),
    ("rectangle_prompt", "Stretch your arms wide for the long sides, then bring them closer for the short sides."),
    ("rectangle_activity", None, "LONG SIDES • SHORT SIDES", 5.8),
    ("rectangle_travel", "Tavi follows the golden track to the community garden. The rectangular trays fit the long garden tables."),
    ("rectangle_deliver", "Last delivery complete. Now every place has the shape it needs."),
    ("sequence_prompt", "Can you remember the whole delivery order? First circle, next square, then triangle, last rectangle."),
    ("sequence_activity", None, "CIRCLE • SQUARE • TRIANGLE • RECTANGLE", 6.2),
    ("finale", "The music garden taps, the reading nook feels cozy, the playground flags dance, and new seeds are ready to grow. Tavi did it step by step!"),
    ("goodbye", "When a job feels big, put it in order: first, next, then, and last. Toot-toot! See you next delivery day."),
]


def voice_path(index: int, phase: str) -> Path:
    return WORK / f"voice-{index:02d}-{phase}.mp3"


async def make_voices() -> None:
    tasks = []
    for index, entry in enumerate(SCRIPT):
        phase, text = entry[:2]
        if text is None:
            continue
        target = voice_path(index, phase)
        if not target.exists():
            tasks.append(edge_tts.Communicate(
                text, VOICE["voice"], rate=VOICE["rate"], pitch=VOICE["pitch"], volume="-1%"
            ).save(str(target)))
    if tasks:
        await asyncio.gather(*tasks)


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def build_timeline() -> tuple[list[dict], list[tuple[Path, float]], float]:
    events = [{"phase": "title", "start": 0.0, "end": 5.0, "scene": "depot"}]
    voices: list[tuple[Path, float]] = []
    cursor = 5.0
    for index, entry in enumerate(SCRIPT):
        phase, text = entry[:2]
        if text is None:
            length = float(entry[3])
            end = cursor + length + 0.35
            events.append({"phase": phase, "start": cursor, "end": end, "text": entry[2], "activity": True})
        else:
            path = voice_path(index, phase)
            end = cursor + duration(path) + 0.7
            events.append({"phase": phase, "start": cursor, "end": end, "text": text})
            voices.append((path, cursor))
        cursor = end
    events.append({"phase": "end", "start": cursor, "end": cursor + 5.0, "scene": "garden"})
    return events, voices, cursor + 5.0


def scene_for(phase: str) -> str:
    if phase in {"title", "welcome", "plan", "circle_load", "circle_prompt", "circle_activity", "square_load", "triangle_load", "rectangle_load"}:
        return "depot"
    if phase in {"circle_travel", "circle_deliver"}:
        return "music"
    if phase in {"square_prompt", "square_activity", "square_travel", "square_deliver"}:
        return "reading"
    if phase in {"triangle_prompt", "triangle_activity", "triangle_travel", "triangle_deliver"}:
        return "playground"
    return "garden"


def cargo_for(phase: str) -> str | None:
    if phase.startswith("circle"): return "circle"
    if phase.startswith("square"): return "square"
    if phase.startswith("triangle"): return "triangle"
    if phase.startswith("rectangle"): return "rectangle"
    return None


def load_assets() -> dict[str, Image.Image]:
    missing = [str(path) for path in ASSETS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Tavi backgrounds: {missing}")
    result = {}
    for name, path in ASSETS.items():
        image = Image.open(path).convert("RGB")
        ratio = max(base.W / image.width, base.H / image.height)
        resized = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
        left = (resized.width - base.W) // 2
        top = (resized.height - base.H) // 2
        result[name] = resized.crop((left, top, left + base.W, top + base.H))
    return result


def shape_icon(draw: ImageDraw.ImageDraw, kind: str, center: tuple[int, int], size: int, fill: tuple[int, int, int, int]) -> None:
    x, y = center
    if kind == "circle":
        draw.ellipse((x-size, y-size, x+size, y+size), fill=fill, outline="white", width=7)
    elif kind == "square":
        draw.rounded_rectangle((x-size, y-size, x+size, y+size), 18, fill=fill, outline="white", width=7)
    elif kind == "triangle":
        draw.polygon([(x, y-size), (x-size, y+size), (x+size, y+size)], fill=fill)
        draw.line([(x, y-size), (x-size, y+size), (x+size, y+size), (x, y-size)], fill="white", width=7, joint="curve")
    else:
        draw.rounded_rectangle((x-size-28, y-size+18, x+size+28, y+size-18), 18, fill=fill, outline="white", width=7)


SHAPE_COLORS = {"circle": (243, 86, 74, 255), "square": (99, 89, 214, 255), "triangle": (255, 174, 34, 255), "rectangle": (44, 170, 111, 255)}


def draw_train(frame: Image.Image, event: dict, t: float) -> None:
    phase = event["phase"]
    progress = max(0.0, min(1.0, (t-event["start"]) / max(0.001, event["end"]-event["start"])))
    travelling = phase.endswith("travel")
    x = int(-520 + progress * 2500) if travelling else 360
    y = 770 + int(7 * math.sin(t * 2.4))
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.ellipse((x+20, y+175, x+650, y+260), fill=(22, 28, 42, 85))
    # Wagon and cargo.
    draw.rounded_rectangle((x+20, y+35, x+305, y+180), 34, fill=(244, 96, 69, 255), outline=(255, 218, 111, 255), width=9)
    draw.rectangle((x+60, y+5, x+265, y+70), fill=(255, 188, 54, 255), outline="white", width=6)
    cargo = cargo_for(phase)
    if cargo:
        shape_icon(draw, cargo, (x+162, y+35), 52, SHAPE_COLORS[cargo])
    # Engine body, cab and chimney.
    draw.rounded_rectangle((x+320, y+25, x+650, y+185), 55, fill=(26, 171, 176, 255), outline=(255, 245, 190, 255), width=9)
    draw.rounded_rectangle((x+430, y-80, x+610, y+90), 35, fill=(64, 97, 210, 255), outline="white", width=8)
    draw.rectangle((x+475, y-42, x+565, y+38), fill=(149, 230, 255, 255), outline=(12, 43, 88, 255), width=6)
    draw.rectangle((x+345, y-68, x+395, y+40), fill=(43, 74, 150, 255))
    draw.ellipse((x+325, y-92, x+415, y-46), fill=(255, 188, 54, 255), outline="white", width=6)
    # Friendly face.
    draw.ellipse((x+580, y+55, x+640, y+118), fill=(255, 238, 197, 255), outline=(22, 61, 102, 255), width=5)
    draw.ellipse((x+592, y+70, x+604, y+86), fill=(18, 35, 55, 255)); draw.ellipse((x+618, y+70, x+630, y+86), fill=(18, 35, 55, 255))
    draw.arc((x+600, y+82, x+628, y+108), 5, 175, fill=(148, 47, 48, 255), width=4)
    # Wheels with rotating spokes.
    angle = t * 5.5
    for wx in (x+105, x+245, x+405, x+575):
        wy = y+185
        draw.ellipse((wx-48, wy-48, wx+48, wy+48), fill=(34, 44, 66, 255), outline=(255, 188, 54, 255), width=9)
        for spoke in range(4):
            a = angle + spoke * math.pi / 2
            draw.line((wx, wy, wx+34*math.cos(a), wy+34*math.sin(a)), fill="white", width=5)
    # Steam puffs are continuous, not image swaps.
    for index in range(3):
        puff_x = x+370-index*42-int((t*22)%34)
        puff_y = y-110-index*28
        radius = 22+index*7
        draw.ellipse((puff_x-radius, puff_y-radius, puff_x+radius, puff_y+radius), fill=(255,255,255,170-index*25))
    frame.alpha_composite(overlay)


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    phase = event["phase"]
    scene = event.get("scene") or scene_for(phase)
    background = assets[scene]
    zoom = 1.025 + 0.012 * math.sin(t * 0.18)
    resized = background.resize((round(base.W*zoom), round(base.H*zoom)), Image.Resampling.BICUBIC)
    left = (resized.width-base.W)//2 + int(10*math.sin(t*0.09))
    top = (resized.height-base.H)//2
    frame = resized.crop((left, top, left+base.W, top+base.H)).convert("RGBA")
    draw = ImageDraw.Draw(frame, "RGBA")
    if phase == "title":
        draw_train(frame, {"phase":"welcome","start":event["start"],"end":event["end"]}, t)
        base.panel(draw, (225, 110, 1695, 420), radius=54, fill=(255, 249, 225, 245), outline=(255, 177, 46, 255), width=9)
        base.centered(draw, (960, 195), "TAVI THE TINY TRAIN", base.F62, (35, 77, 126, 255), 3)
        base.centered(draw, (960, 300), "SHAPE DELIVERY DAY", base.F62, (230, 83, 65, 255), 3)
        return frame.convert("RGB")
    if phase == "end":
        draw.rectangle((0,0,base.W,base.H), fill=(17,35,62,105))
        base.panel(draw, (210, 160, 1710, 870), radius=58, fill=(255, 249, 225, 246), outline=(255, 177, 46, 255), width=9)
        base.centered(draw, (960, 260), "STEP BY STEP!", base.F62, (35, 77, 126, 255), 3)
        for index, kind in enumerate(("circle","square","triangle","rectangle")):
            x = 480 + index*320
            shape_icon(draw, kind, (x, 485), 82, SHAPE_COLORS[kind])
        base.centered(draw, (960, 690), "FIRST • NEXT • THEN • LAST", base.F48, (230, 83, 65, 255), 2)
        return frame.convert("RGB")
    draw_train(frame, event, t)
    cargo = cargo_for(phase)
    if cargo:
        base.panel(draw, (1510, 55, 1845, 320), radius=42, fill=(19, 39, 68, 225), outline=(255,255,255,235), width=6)
        shape_icon(draw, cargo, (1678, 170), 78, SHAPE_COLORS[cargo])
        base.centered(draw, (1678, 270), cargo.upper(), base.F30, (255,255,255,255), 2)
    if event.get("activity"):
        base.panel(draw, (250, 850, 1670, 1030), radius=42, fill=(255, 249, 225, 245), outline=(255, 177, 46, 255), width=7)
        base.centered(draw, (960, 935), event["text"], base.F48, (35, 77, 126, 255), 2)
        dots = 8
        completed = int(max(0,min(1,(t-event["start"])/(event["end"]-event["start"]))) * dots)
        for index in range(dots):
            color=(255,118,60,255) if index<completed else (205,213,215,255)
            draw.ellipse((720+index*70,995,744+index*70,1019),fill=color)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "music.wav"
    rate = 48000
    rng = random.Random(42017)
    chords = [(261.63,329.63,392.0),(293.66,369.99,440.0),(220.0,277.18,329.63),(196.0,246.94,392.0)]
    with wave.open(str(target), "wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate)
        chunk = bytearray()
        for index in range(int(total*rate)):
            t=index/rate; chord=chords[int(t/4)%len(chords)]
            value=sum(math.sin(2*math.pi*f*t) for f in chord)*0.025
            beat=t%0.5
            if beat<0.055: value += math.sin(2*math.pi*92*t)*0.09*(1-beat/0.055)
            if int(t*2)%4==2 and beat<0.03: value += rng.uniform(-1,1)*0.035*(1-beat/0.03)
            sample=max(-32767,min(32767,int(value*32767)))
            chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: output.writeframesraw(chunk); chunk.clear()
        if chunk: output.writeframesraw(chunk)
    return target


def render(events: list[dict], voices: list[tuple[Path,float]], total: float, assets: dict[str,Image.Image]) -> None:
    silent=WORK/"silent.mp4"
    process=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{base.W}x{base.H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","veryfast","-crf","19","-profile:v","high","-pix_fmt","yuv420p",str(silent)],stdin=subprocess.PIPE)
    assert process.stdin
    for number in range(math.ceil(total*ART_FPS)):
        t=number/ART_FPS
        event=next((item for item in events if item["start"]<=t<item["end"]),None)
        if event is None: raise RuntimeError(f"Tavi timeline has no visual event at {t:.3f}s")
        process.stdin.write(frame_for(event,t,assets).tobytes())
        if number%(ART_FPS*15)==0: print(f"Rendered {t:.0f}/{total:.0f}s",flush=True)
    process.stdin.close()
    if process.wait()!=0: raise RuntimeError("Tavi silent render failed")
    music=make_music(total); inputs=["-i",str(silent),"-i",str(music)]; filters=["[1:a]volume=0.38[m]"]; labels=["[m]"]
    for index,(path,start) in enumerate(voices,2):
        inputs += ["-i",str(path)]; delay=round(start*1000); filters.append(f"[{index}:a]adelay={delay}|{delay},volume=1.65[v{index}]"); labels.append(f"[v{index}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:duration=longest:normalize=0,alimiter=limit=0.94[a]")
    subprocess.run(["ffmpeg","-y","-loglevel","error",*inputs,"-filter_complex",";".join(filters),"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t",f"{total:.3f}","-movflags","+faststart",str(OUTPUT)],check=True)


def quality(events: list[dict], total: float, assets: dict[str,Image.Image]) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True))
    video=next(stream for stream in probe["streams"] if stream["codec_type"]=="video"); audio=next(stream for stream in probe["streams"] if stream["codec_type"]=="audio")
    decode=subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],capture_output=True,text=True,check=False)
    transitions=[{"from_phase":a["phase"],"to_phase":b["phase"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]
    activities=[{"phase":e["phase"],"quiet_gap_seconds":e["end"]-e["start"]} for e in events if e.get("activity")]
    (WORK/"timeline-gap-audit.json").write_text(json.dumps(transitions,indent=2)+"\n",encoding="utf-8")
    (WORK/"activity-gap-audit.json").write_text(json.dumps(activities,indent=2)+"\n",encoding="utf-8")
    scene_sequence=[scene_for(e["phase"]) if e["phase"] not in {"title","end"} else e.get("scene") for e in events]
    scene_changes=sum(a!=b for a,b in zip(scene_sequence,scene_sequence[1:]))
    checks={
        "size":OUTPUT.stat().st_size>2_000_000,
        "duration":120<=float(probe["format"]["duration"])<=260 and abs(float(probe["format"]["duration"])-total)<.3,
        "video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,
        "audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,
        "full_decode":decode.returncode==0,
        "continuous_visual_timeline":all(abs(item["gap_seconds"])<.000001 for item in transitions),
        "end_card_is_final_event_only":events[-1]["phase"]=="end" and all(e["phase"]!="end" for e in events[:-1]),
        "stable_visual_state_per_event":all(scene_for(e["phase"]) in assets for e in events if e["phase"] not in {"title","end"}),
        "controlled_scene_changes":scene_changes<=10,
        "five_response_gaps":len(activities)==5 and all(item["quiet_gap_seconds"]>=5 for item in activities),
        "five_original_backgrounds":len(assets)==5,
        "voice_rotation":VOICE["name"]=="natasha-au",
    }
    report={"format":"community-shape-delivery-sequencing-story","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"voice_profile":VOICE["name"],"scene_changes":scene_changes,"new_image_generation_calls":5,"true_rigged_3d_animation":False,"visual_method":"original 3D-rendered toy-railway environments with deterministic code-animated train, cargo shapes, wheel motion, steam and camera travel","checks":checks,"passed":all(checks.values())}
    (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[events[0],*events[2:-1:2],events[-1]]
    sheet=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for index,event in enumerate(samples):
        t=event["start"]+min(2,(event["end"]-event["start"])/2); image=frame_for(event,t,assets).resize((240,135),Image.Resampling.LANCZOS); sheet.paste(image,((index%4)*240,(index//4)*135))
    sheet.save(WORK/"quality-contact-sheet.png")
    boundary=[]
    for current,following in zip(events,events[1:]): boundary.extend([(current,max(current["start"],current["end"]-.12)),(following,min(following["end"]-.01,following["start"]+.12))])
    transition_sheet=Image.new("RGB",(1200,math.ceil(len(boundary)/5)*135),"white")
    for index,(event,t) in enumerate(boundary):
        image=frame_for(event,t,assets).resize((240,135),Image.Resampling.LANCZOS); draw=ImageDraw.Draw(image); draw.rectangle((0,0,125,19),fill="black"); draw.text((3,2),f"{t:.1f}s {event['phase']}",font=base.font(12,True),fill="white"); transition_sheet.paste(image,((index%5)*240,(index//5)*135))
    transition_sheet.save(WORK/"transition-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Tavi quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc={"id":"tavi-shape-delivery-day-01","title":"Tavi the Tiny Train's Shape Delivery Day | Shapes and Sequencing for Kids","description":"Ride with Tavi through a cheerful community as four important deliveries arrive in order: first a round drum, next a square reading cushion, then triangle playground flags, and last rectangular seed trays. Children trace shapes, move their arms, and remember first, next, then and last.\n\nAn original Tiny Tales 3D-look railway story supporting shape recognition, sequencing, listening and movement for children ages 3 to 7.","tags":["shapes for kids","sequencing for kids","train story for kids","preschool learning","circle square triangle rectangle","first next then last","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":VOICE["name"],"format_family":"community-shape-delivery-sequencing-story","visual_system":"3d-toy-railway-with-code-animated-train-and-cargo","interaction_style":"shape-tracing-and-first-next-then-last-recall","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"transition_contact_sheet_reviewed":False,"quality_report":"automation/production-work/tavi-shape-delivery-day-01/quality-report.json","transition_audit":"automation/production-work/tavi-shape-delivery-day-01/timeline-gap-audit.json","quality_contact_sheet":"automation/production-work/tavi-shape-delivery-day-01/quality-contact-sheet.png","transition_contact_sheet":"automation/production-work/tavi-shape-delivery-day-01/transition-contact-sheet.png","new_image_generation_calls":5,"true_rigged_3d_animation":False}
    META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True,exist_ok=True); OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    asyncio.run(make_voices()); events,voices,total=build_timeline(); assets=load_assets(); render(events,voices,total,assets); quality(events,total,assets); write_metadata(total); print(json.dumps({"output":str(OUTPUT),"duration_seconds":total,"events":len(events)},indent=2))


if __name__=="__main__": main()
