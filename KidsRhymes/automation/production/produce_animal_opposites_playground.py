"""Render a one-off split-screen Tiny Tales opposites and movement adventure."""

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
WORK = AUTOMATION / "production-work" / "animal-opposites-playground-01"
OUTPUT = OUTPUT_DIR / "animal-opposites-playground-01.mp4"
META = AUTOMATION.parent / "metadata" / "animal-opposites-playground-01.json"
SPEC = {"id": "animal-opposites-playground-01"}

PAIRS = [
    {"pair": "UP / DOWN", "scene": "updown", "animal": "parrot", "line": "Parrot shows our first opposites. On one side, Parrot is up, high in the sky. On the other side, Parrot is down, close to the ground. Up and down point in opposite directions.", "prompt": "REACH UP - THEN BEND DOWN"},
    {"pair": "IN / OUT", "scene": "inout", "animal": "pig", "line": "Pig explores in and out. First, Pig is in the barn, surrounded by its walls. Then Pig is out of the barn, standing beyond the doorway. In and out are opposites.", "prompt": "MOVE HANDS IN - THEN OUT"},
    {"pair": "NEAR / FAR", "scene": "nearfar", "animal": "elephant", "line": "Elephant helps us compare near and far. The large elephant looks near to us. The tiny elephant by the hills looks far away. Near and far describe distance.", "prompt": "HANDS NEAR - THEN FAR APART"},
    {"pair": "OVER / UNDER", "scene": "overunder", "animal": "dolphin", "line": "Dolphin moves over and under the wave marker. Over means higher than something. Under means lower than it. Watch the marker to compare both positions.", "prompt": "ONE HAND OVER - ONE UNDER"},
    {"pair": "OPEN / CLOSED", "scene": "openclosed", "animal": "goat", "line": "Goat waits by two farm gates. The open gate leaves a space to pass through. The closed gate blocks the space. Open and closed are opposites.", "prompt": "OPEN HANDS - THEN CLOSE THEM"},
    {"pair": "DAY / NIGHT", "scene": "daynight", "animal": "owl", "line": "Our final pair is day and night. Day is bright when the sun lights our part of Earth. Night is dark when our part of Earth faces away from the sun. Day and night take turns.", "prompt": "STRETCH LIKE DAY - CURL LIKE NIGHT"},
]


def voice_path(key: str) -> Path:
    return WORK / f"voice-{key}.mp3"


async def make_voices() -> list[tuple[str, str]]:
    lines=[("intro","Welcome to the Tiny Tales Animal Opposites Playground! We will see two ideas side by side, learn how they differ, and move our bodies to remember each pair.")]
    lines += [(f"p{index}",item["line"]) for index,item in enumerate(PAIRS,1)]
    lines.append(("outro","You explored up and down, in and out, near and far, over and under, open and closed, and day and night. Opposites help us describe how things differ. Great moving and learning!"))
    for key,wording in lines:
        target=voice_path(key)
        if not target.exists(): await edge_tts.Communicate(wording,base.VOICE,rate=base.VOICE_RATE,pitch=base.VOICE_PITCH,volume="-2%").save(str(target))
    return lines


def make_timeline(lines: list[tuple[str,str]]) -> tuple[list[dict],list[tuple[str,float]],float]:
    lengths={key:base.duration(voice_path(key)) for key,_ in lines}; events=[]; tracks=[]; cursor=.3
    def add(kind: str,length: float,**data: object) -> dict:
        nonlocal cursor
        event={"kind":kind,"start":cursor,"end":cursor+length,**data}; events.append(event); cursor=event["end"]; return event
    event=add("intro",max(9.0,lengths["intro"]+1)); tracks.append(("intro",event["start"]+.15))
    for index,item in enumerate(PAIRS,1):
        event=add("reveal",lengths[f"p{index}"]+1,index=index,item=item); tracks.append((f"p{index}",event["start"]+.15)); add("think",5.0,index=index,item=item)
    event=add("outro",max(10.0,lengths["outro"]+1)); tracks.append(("outro",event["start"]+.15)); return events,tracks,math.ceil(cursor*base.ART_FPS)/base.ART_FPS


def paste(frame: Image.Image, animals: dict, name: str, center: tuple[int,int], size: tuple[int,int]) -> None:
    sprite=animals[name].copy(); sprite.thumbnail(size,Image.Resampling.LANCZOS); frame.alpha_composite(sprite,(center[0]-sprite.width//2,center[1]-sprite.height//2))


def split_base(t: float) -> Image.Image:
    frame=Image.new("RGBA",(base.W,base.H),(255,246,192,255)); draw=ImageDraw.Draw(frame,"RGBA"); draw.polygon([(960,0),(1920,0),(1920,1080),(960,1080),(920,990),(1000,900),(920,810),(1000,720),(920,630),(1000,540),(920,450),(1000,360),(920,270),(1000,180),(920,90)],fill=(179,231,231,255));
    for x,y,r in [(95,260,26),(1780,230,34),(160,840,20),(1730,850,27)]:
        draw.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,255,80))
    return frame


def arrow(draw: ImageDraw.ImageDraw,x: int,y1: int,y2: int,color: tuple[int,int,int,int]) -> None:
    draw.line((x,y1,x,y2),fill=color,width=22); direction=1 if y2>y1 else -1; draw.polygon([(x,y2+direction*3),(x-35,y2-direction*55),(x+35,y2-direction*55)],fill=color)


def barn(draw: ImageDraw.ImageDraw,x: int,door_open: bool) -> tuple[int,int,int,int]:
    draw.rectangle((x-270,350,x+270,805),fill=(194,75,60,255),outline=(120,56,47,255),width=8); draw.polygon([(x-320,350),(x,130),(x+320,350)],fill=(126,58,49,255)); door=(x-105,560,x+105,805); draw.rectangle(door,fill=(45,37,52,255) if door_open else (142,91,57,255),outline=(255,226,172,255),width=7)
    if not door_open:
        for y in range(600,800,65): draw.line((x-95,y,x+95,y),fill=(92,57,40,255),width=8)
    return door


def scene_frame(event: dict,t: float,animals: dict) -> Image.Image:
    item=event["item"]; scene=item["scene"]; action=event["kind"]=="think"; frame=split_base(t); draw=ImageDraw.Draw(frame,"RGBA"); base.header(frame,"ANIMAL OPPOSITES PLAYGROUND",f"PAIR {event['index']} OF {len(PAIRS)}")
    if scene=="updown":
        paste(frame,animals,"parrot",(485,380),(430,430)); paste(frame,animals,"parrot",(1435,730),(430,430)); arrow(draw,220,650,270,(224,74,67,255)); arrow(draw,1690,340,730,(29,76,106,255))
    elif scene=="inout":
        barn(draw,480,True); barn(draw,1440,False); paste(frame,animals,"pig",(480,680),(300,300)); paste(frame,animals,"pig",(1730,745),(300,300))
    elif scene=="nearfar":
        draw.rectangle((0,700,1920,1080),fill=(102,184,91,170)); draw.polygon([(1050,700),(1250,430),(1450,700)],fill=(87,142,91,200)); draw.polygon([(1420,700),(1620,500),(1810,700)],fill=(72,126,83,200)); paste(frame,animals,"elephant",(480,630),(650,650)); paste(frame,animals,"elephant",(1510,600),(210,210))
    elif scene=="overunder":
        draw.line((160,580,1760,580),fill=(255,255,255,255),width=22); [draw.arc((x,520,x+260,650),180,355,fill=(49,151,190,255),width=10) for x in range(120,1700,240)]; paste(frame,animals,"dolphin",(480,360),(520,430)); paste(frame,animals,"dolphin",(1440,790),(520,430))
    elif scene=="openclosed":
        draw.rectangle((0,760,1920,1080),fill=(102,184,91,180));
        for cx,opened in [(480,True),(1440,False)]:
            draw.line((cx-300,420,cx-300,820),fill=(118,75,46,255),width=34); draw.line((cx+300,420,cx+300,820),fill=(118,75,46,255),width=34)
            if opened:
                draw.line((cx-285,470,cx-80,690),fill=(175,117,66,255),width=35); draw.line((cx-285,650,cx-80,810),fill=(175,117,66,255),width=35)
            else:
                for y in (500,650,800): draw.line((cx-285,y,cx+285,y),fill=(175,117,66,255),width=35)
        paste(frame,animals,"goat",(480,670),(310,310)); paste(frame,animals,"goat",(1440,670),(310,310))
    else:
        draw.rectangle((0,0,960,1080),fill=(139,216,248,190)); draw.ellipse((610,190,820,400),fill=(255,218,65,255)); draw.rectangle((960,0,1920,1080),fill=(36,52,103,230)); draw.ellipse((1400,180,1600,380),fill=(244,244,202,255)); draw.ellipse((1460,140,1620,320),fill=(36,52,103,255));
        for x,y in [(1100,280),(1260,180),(1710,260),(1810,430),(1200,610)]:
            draw.ellipse((x-6,y-6,x+6,y+6),fill=(255,248,185,255))
        paste(frame,animals,"owl",(480,650),(480,480)); paste(frame,animals,"owl",(1440,650),(480,480))
    left,right=item["pair"].split(" / ");
    for x,label,color in [(480,left,(224,74,67,255)),(1440,right,(29,76,106,255))]: draw.rounded_rectangle((220 if x<960 else 1180,845,740 if x<960 else 1700,960),radius=38,fill=(255,255,245,245),outline=color,width=8); base.centered(draw,(x,902),label,base.F62,color,2)
    if action:
        draw.rounded_rectangle((300,975,1620,1060),radius=30,fill=(39,79,111,245)); base.centered(draw,(960,1018),item["prompt"],base.F38,(255,255,255,255)); elapsed=t-event["start"]; total=event["end"]-event["start"]; draw.rounded_rectangle((430,165,1490,195),radius=14,fill=(255,255,255,130)); draw.rounded_rectangle((430,165,430+int(1060*min(1,elapsed/total)),195),radius=14,fill=(255,198,50,240))
    return frame.convert("RGB")


def title_frame(t: float,animals: dict,outro: bool=False) -> Image.Image:
    frame=base.gradient_background(21 if outro else 3,t).convert("RGBA"); draw=ImageDraw.Draw(frame,"RGBA"); base.panel(draw,(220,120,1700,930),radius=60,width=9); base.centered(draw,(960,260),"ANIMAL OPPOSITES",base.F78,(224,74,67,255),2); base.centered(draw,(960,380),"PLAYGROUND" if not outro else "AMAZING OPPOSITES!",base.F62,(29,76,106,255),2)
    for index,name in enumerate(["parrot","pig","elephant","dolphin","goat","owl"]): paste(frame,animals,name,(390+index*230,650),(210,250))
    base.centered(draw,(960,835),"SEE BOTH SIDES - MOVE - REMEMBER" if not outro else "UP / DOWN - IN / OUT - AND MORE!",base.F38,(46,151,84,255)); return frame.convert("RGB")


def frame_for(event: dict,t: float,spec: dict,animals: dict) -> Image.Image:
    if event["kind"]=="intro": return title_frame(t,animals)
    if event["kind"]=="outro": return title_frame(t,animals,True)
    return scene_frame(event,t,animals)


def validate(total: float,events: list[dict],animals: dict) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio"); checks={"size":OUTPUT.stat().st_size>1_000_000,"duration":abs(float(probe["format"]["duration"])-total)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,"audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"six_pairs":len([e for e in events if e["kind"]=="reveal"])==6,"six_movement_windows":len([e for e in events if e["kind"]=="think"])==6}
    report={"format":"animal-opposites-playground","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values()),"upload_authorized":False}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[events[0]]+[e for e in events if e["kind"] in {"reveal","think"}]+[events[-1]]; contact=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for index,event in enumerate(samples): contact.paste(frame_for(event,event["start"]+min(1,(event["end"]-event["start"])/2),SPEC,animals).resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    contact.save(WORK/"quality-contact-sheet.png");
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc={"id":SPEC["id"],"title":"Animal Opposites Playground | Up, Down, In, Out and More for Kids","description":"Explore six opposite pairs in colourful split-screen animal scenes: up/down, in/out, near/far, over/under, open/closed, and day/night. Each pair includes a simple explanation and a five-second movement prompt.\n\nA Tiny Tales vocabulary adventure supporting spatial language, comparison, listening, and whole-body learning for children ages 3 to 7.","tags":["opposites for kids","up and down","in and out","near and far","preschool vocabulary","movement learning","Tiny Tales","kids learning"],"category_id":"27","made_for_kids":True,"privacy":"private","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"new_image_generation_calls":0}; META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True); report=WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {OUTPUT}",flush=True); return
    farm=games.extract_grid(AUTOMATION/"production-assets"/"farm-animals-sheet.png",["cow","pig","sheep","horse","chicken","goat"]); wild=games.extract_grid(AUTOMATION/"production-assets"/"jungle-animals-sheet.png",["lion","tiger","elephant","zebra","hippopotamus","crocodile"]); ocean=games.extract_grid(AUTOMATION/"production-assets"/"ocean-animals-sheet.png",["dolphin","sea turtle","octopus","seahorse","crab","whale"]); birds=games.extract_grid(AUTOMATION/"production-assets"/"bird-animals-sheet.png",["owl","parrot","flamingo","penguin","peacock","toucan"]); animals={**farm,**wild,**ocean,**birds}
    lines=asyncio.run(make_voices()); events,tracks,total=make_timeline(lines); shared.frame_for=frame_for; shared.render(WORK,OUTPUT,total,events,tracks,SPEC,animals); validate(total,events,animals); write_metadata(total); print(json.dumps({"id":SPEC["id"],"status":"completed","duration_seconds":total}),flush=True)


if __name__=="__main__": main()
