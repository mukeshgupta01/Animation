"""Render a connected Tiny Tales water-cycle story with changing scenes."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import subprocess

import edge_tts
from PIL import Image, ImageDraw

import produce_animal_games as games
import produce_clue_detective_batch as shared
import produce_snack_video as base


AUTOMATION = base.AUTOMATION
OUTPUT_DIR = AUTOMATION / "production-output"
WORK = AUTOMATION / "production-work" / "little-raindrop-water-cycle-01"
OUTPUT = OUTPUT_DIR / "little-raindrop-water-cycle-01.mp4"
META = AUTOMATION.parent / "metadata" / "little-raindrop-water-cycle-01.json"
SPEC = {"id": "little-raindrop-water-cycle-01"}

STORY = [
    ("ocean", "SUNSHINE WARMS THE OCEAN", "Sunlight warms the water", "Dot the little water drop lived in the sparkling ocean with Turtle and Dolphin. One bright morning, warm sunshine touched the waves. Dot felt warmer and lighter."),
    ("rise", "UP, UP INTO THE AIR", "Evaporation", "Dot changed into invisible water vapour and floated upward. This part of the water cycle is called evaporation. Can you slowly lift your hands like rising water vapour?"),
    ("cloud", "COOL AIR MAKES A CLOUD", "Condensation", "Higher in the sky, the air was cooler. Dot joined many tiny drops to make a cloud. This change is called condensation. Puff your cheeks and make a big cloud shape with your arms."),
    ("rain", "THE CLOUD RELEASES RAIN", "Precipitation", "More and more drops gathered until the cloud became heavy. Dot fell gently as rain. Rain, snow, sleet, and hail are forms of precipitation. Wiggle your fingers downward like falling rain."),
    ("farm", "RAIN HELPS LIVING THINGS", "Water for plants and animals", "Dot landed beside a thirsty farm garden. The soil soaked up some rain, plant roots drank water, and the animals had fresh water too. Rain helps many living things grow."),
    ("river", "STREAMS FLOW BACK", "Collection and runoff", "Extra water trickled into a stream. Small streams joined a winding river that carried Dot downhill. Water collecting and flowing over land is part of the journey back to the ocean."),
    ("return", "BACK HOME TO THE OCEAN", "The cycle begins again", "At last, the river reached the ocean. Dot greeted Turtle and Dolphin again. The sun was still shining, so the water cycle could begin another journey."),
]


def voice_path(key: str) -> Path:
    return WORK / f"voice-{key}.mp3"


async def make_voices() -> list[tuple[str, str]]:
    lines = [("intro", "Meet Dot the little raindrop! Follow Dot from the ocean to a cloud, down to a farm, through a river, and home again while we discover the water cycle.")]
    lines += [(f"s{index}", narration) for index, (_, _, _, narration) in enumerate(STORY, 1)]
    lines.append(("outro", "Dot's journey showed evaporation, condensation, precipitation, collection, and the return to the ocean. The water cycle keeps moving around and around. Where might Dot travel next?"))
    for key, wording in lines:
        target = voice_path(key)
        if not target.exists():
            await edge_tts.Communicate(wording, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def make_timeline(lines: list[tuple[str, str]]) -> tuple[list[dict], list[tuple[str, float]], float]:
    lengths = {key: base.duration(voice_path(key)) for key, _ in lines}; events = []; tracks = []; cursor = 0.3
    def add(kind: str, length: float, **data: object) -> dict:
        nonlocal cursor
        event = {"kind": kind, "start": cursor, "end": cursor + length, **data}; events.append(event); cursor = event["end"]; return event
    event = add("intro", max(9.0, lengths["intro"] + 1.2)); tracks.append(("intro", event["start"] + 0.15))
    for index, story in enumerate(STORY, 1):
        event = add("story", lengths[f"s{index}"] + 1.0, index=index, scene=story[0], heading=story[1], label=story[2]); tracks.append((f"s{index}", event["start"] + 0.15))
        if story[0] in {"rise", "cloud", "rain"}: add("participate", 4.5, index=index, scene=story[0], heading=story[1], label=story[2])
    event = add("outro", max(10.0, lengths["outro"] + 1.0)); tracks.append(("outro", event["start"] + 0.15))
    return events, tracks, math.ceil(cursor * base.ART_FPS) / base.ART_FPS


def draw_drop(frame: Image.Image, x: int, y: int, scale: float, happy: bool = True) -> None:
    layer = Image.new("RGBA", frame.size); draw = ImageDraw.Draw(layer, "RGBA"); s = scale
    points = [(x, y-int(150*s)), (x-int(105*s), y+int(25*s)), (x-int(85*s), y+int(105*s)), (x, y+int(145*s)), (x+int(85*s), y+int(105*s)), (x+int(105*s), y+int(25*s))]
    draw.polygon(points, fill=(76, 188, 237, 255), outline=(24, 116, 179, 255)); draw.ellipse((x-int(105*s), y-int(25*s), x+int(105*s), y+int(150*s)), fill=(76, 188, 237, 255), outline=(24, 116, 179, 255), width=max(3, int(8*s)))
    draw.ellipse((x-int(48*s), y+int(20*s), x-int(25*s), y+int(47*s)), fill=(29, 76, 106, 255)); draw.ellipse((x+int(25*s), y+int(20*s), x+int(48*s), y+int(47*s)), fill=(29, 76, 106, 255))
    if happy: draw.arc((x-int(48*s), y+int(37*s), x+int(48*s), y+int(98*s)), 15, 165, fill=(29, 76, 106, 255), width=max(3, int(7*s)))
    frame.alpha_composite(layer)


def paste_animal(frame: Image.Image, animals: dict, name: str, box: tuple[int, int, int, int]) -> None:
    sprite = animals[name].copy(); sprite.thumbnail((box[2]-box[0], box[3]-box[1]), Image.Resampling.LANCZOS); frame.alpha_composite(sprite, ((box[0]+box[2]-sprite.width)//2, box[3]-sprite.height))


def sky(draw: ImageDraw.ImageDraw, rain: bool = False) -> None:
    draw.rectangle((0, 0, 1920, 1080), fill=(135, 215, 247, 255)); draw.ellipse((1470, 80, 1750, 360), fill=(255, 217, 71, 255))
    cloud = (94, 103, 120, 255) if rain else (249, 253, 255, 255)
    for x, y, r in [(760, 260, 140), (910, 205, 180), (1090, 255, 150), (1250, 285, 115)]: draw.ellipse((x-r, y-r, x+r, y+r), fill=cloud)


def story_scene(event: dict, t: float, animals: dict) -> Image.Image:
    scene = event["scene"]; frame = Image.new("RGBA", (base.W, base.H)); draw = ImageDraw.Draw(frame, "RGBA"); local = t-event["start"]; span=max(0.1,event["end"]-event["start"]); p=min(1,local/span)
    if scene in {"ocean", "return"}:
        sky(draw); draw.rectangle((0, 560, 1920, 1080), fill=(31, 157, 202, 255));
        for x in range(-100, 2000, 240): draw.arc((x, 515, x+300, 650), 190, 350, fill=(215, 250, 255, 220), width=8)
        paste_animal(frame, animals, "dolphin", (160, 565, 620, 950)); paste_animal(frame, animals, "sea turtle", (1290, 600, 1740, 960)); draw_drop(frame, 960, 650, .8)
    elif scene == "rise":
        sky(draw); draw.rectangle((0, 790, 1920, 1080), fill=(31, 157, 202, 255)); y=int(770-p*430); draw_drop(frame, 960, y, .62); [draw.line((960+dx, y+160, 960+dx, y+245), fill=(255,255,255,170), width=9) for dx in (-80,0,80)]
    elif scene == "cloud":
        sky(draw); draw_drop(frame, 960, 310, .52); [draw_drop(frame, x, 360+(x%3)*20, .18) for x in range(720, 1260, 105)]
    elif scene == "rain":
        sky(draw, rain=True); draw.rectangle((0, 855, 1920, 1080), fill=(75, 170, 88, 255));
        for i, x in enumerate(range(250, 1750, 125)):
            y=470+int(((local*180+i*57)%360)); draw.line((x,y,x-18,y+55),fill=(87,190,237,230),width=8)
        draw_drop(frame, 960, 650, .55)
    elif scene == "farm":
        sky(draw); draw.rectangle((0, 650, 1920, 1080), fill=(102, 187, 86, 255)); draw.rectangle((1320, 420, 1800, 780), fill=(190, 72, 55, 255)); draw.polygon([(1260,430),(1560,210),(1860,430)],fill=(127,58,46,255));
        for x in range(180, 1100, 150): draw.line((x,850,x,690),fill=(57,137,65,255),width=12); draw.ellipse((x-40,700,x+10,770),fill=(78,177,78,255)); draw.ellipse((x-5,670,x+50,745),fill=(78,177,78,255))
        paste_animal(frame, animals, "cow", (1110, 590, 1500, 1000)); draw_drop(frame, 560, 530, .52)
    else:
        sky(draw); draw.rectangle((0, 650, 1920, 1080), fill=(84, 172, 83, 255)); draw.polygon([(0,900),(300,760),(570,820),(830,700),(1130,780),(1470,680),(1920,820),(1920,1080),(0,1080)],fill=(53,142,181,255));
        for offset in range(4): draw.arc((200+offset*400,720,800+offset*400,1040),180,340,fill=(216,250,255,190),width=7)
        paste_animal(frame, animals, "parrot", (1450, 380, 1770, 720)); draw_drop(frame, int(420+p*900), 760, .48)
    base.header(frame, event["heading"], event["label"].upper())
    draw.rounded_rectangle((315, 925, 1605, 1035), radius=34, fill=(255, 255, 245, 235), outline=(255, 190, 49, 255), width=6)
    prompt = {"rise":"LIFT YOUR HANDS UP SLOWLY", "cloud":"MAKE A BIG CLOUD SHAPE", "rain":"WIGGLE YOUR FINGERS DOWN"}.get(scene, "FOLLOW DOT'S JOURNEY") if event["kind"] == "participate" else "WATCH HOW WATER MOVES"
    base.centered(draw, (960, 980), prompt, base.F38, (224, 74, 67, 255) if event["kind"] == "participate" else (29, 76, 106, 255))
    return frame.convert("RGB")


def cycle_diagram(t: float, animals: dict, outro: bool = False) -> Image.Image:
    frame = base.gradient_background(7 if outro else 1, t).convert("RGBA"); draw = ImageDraw.Draw(frame, "RGBA"); base.panel(draw, (180, 120, 1740, 960), radius=60, width=9)
    base.centered(draw, (960, 235), "DOT'S WATER-CYCLE JOURNEY" if not outro else "THE WATER CYCLE KEEPS MOVING!", base.F62, (29, 76, 106, 255), 2)
    points=[(410,590,"OCEAN"),(790,365,"EVAPORATION"),(1160,365,"CLOUD"),(1510,590,"RAIN"),(960,820,"RIVER")]
    for index,(x,y,label) in enumerate(points):
        draw.ellipse((x-125,y-85,x+125,y+85),fill=(225,248,255,255),outline=(49,151,190,255),width=7); base.centered(draw,(x,y),label,base.F30,(29,76,106,255)); nx,ny=points[(index+1)%len(points)][:2]; draw.line((x+90 if nx>x else x-90,y,nx-90 if nx>x else nx+90,ny),fill=(44,151,103,210),width=12)
    draw_drop(frame, 960, 590, .65); return frame.convert("RGB")


def frame_for(event: dict, t: float, spec: dict, animals: dict) -> Image.Image:
    if event["kind"] == "intro": return cycle_diagram(t, animals)
    if event["kind"] == "outro": return cycle_diagram(t, animals, True)
    return story_scene(event, t, animals)


def validate(output: Path, total: float, events: list[dict], animals: dict) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(output)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    checks={"size":output.stat().st_size>1_000_000,"duration":abs(float(probe["format"]["duration"])-total)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,"audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"story_scenes":len([e for e in events if e["kind"]=="story"])==7,"participation_windows":len([e for e in events if e["kind"]=="participate"])==3}
    report={"format":"connected-water-cycle-story","output":str(output),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values()),"upload_authorized":False}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[events[0]]+[e for e in events if e["kind"] in {"story","participate"}]+[events[-1]]; contact=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for index,event in enumerate(samples): contact.paste(frame_for(event,event["start"]+min(1.2,(event["end"]-event["start"])/2),SPEC,animals).resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    contact.save(WORK/"quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc={"id":SPEC["id"],"title":"The Little Raindrop's Big Journey | Water Cycle Story for Kids","description":"Follow Dot the little raindrop from the ocean into a cloud, down as rain, across a farm, through a river, and home again. Changing story scenes introduce evaporation, condensation, precipitation, collection, and why water helps living things.\n\nA gentle Tiny Tales science story with movement moments for children ages 3 to 7.","tags":["water cycle for kids","raindrop story","evaporation","condensation","precipitation","science for kids","preschool learning","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"private","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"new_image_generation_calls":0}; META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True); report=WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {OUTPUT}",flush=True); return
    ocean=games.extract_grid(AUTOMATION/"production-assets"/"ocean-animals-sheet.png",["dolphin","sea turtle","octopus","seahorse","crab","whale"]); farm=games.extract_grid(AUTOMATION/"production-assets"/"farm-animals-sheet.png",["cow","pig","sheep","horse","chicken","goat"]); birds=games.extract_grid(AUTOMATION/"production-assets"/"bird-animals-sheet.png",["owl","parrot","flamingo","penguin","peacock","toucan"]); animals={**ocean,**farm,**birds}
    lines=asyncio.run(make_voices()); events,tracks,total=make_timeline(lines); shared.frame_for=frame_for; shared.render(WORK,OUTPUT,total,events,tracks,SPEC,animals); validate(OUTPUT,total,events,animals); write_metadata(total); print(json.dumps({"id":SPEC["id"],"status":"completed","duration_seconds":total}),flush=True)


if __name__=="__main__": main()
