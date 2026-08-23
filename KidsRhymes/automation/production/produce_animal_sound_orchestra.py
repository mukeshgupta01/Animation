"""Render a one-off Tiny Tales animal-sound concert with call-and-response pauses."""

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
WORK = AUTOMATION / "production-work" / "animal-sound-orchestra-01"
OUTPUT = OUTPUT_DIR / "animal-sound-orchestra-01.mp4"
META = AUTOMATION.parent / "metadata" / "animal-sound-orchestra-01.json"
SPEC = {"id": "animal-sound-orchestra-01"}

PERFORMERS = [
    {"animal": "cow", "family": "farm", "sound": "MOO", "verb": "moo", "line": "First on the farm stage is Cow. A cow's low call is called a moo. Cows use calls to communicate with one another. Listen to the word: moo. Now warm up your voice!"},
    {"animal": "sheep", "family": "farm", "sound": "BAA", "verb": "baa", "line": "Sheep trots into the spotlight. A sheep's call is called a bleat, and we often write it as baa. Listen: baa. Get ready to echo Sheep!"},
    {"animal": "pig", "family": "farm", "sound": "OINK", "verb": "oink", "line": "Here comes Pig with a snuffly rhythm. Pigs can grunt, squeal, and make calls we write as oink. Listen: oink, oink. Your turn is next!"},
    {"animal": "chicken", "family": "farm", "sound": "CLUCK", "verb": "cluck", "line": "Chicken taps onto the farm stage. Chickens use several calls, including clucks. Listen: cluck, cluck. Can you copy that quick rhythm?"},
    {"animal": "lion", "family": "wild", "sound": "ROAR", "verb": "roar", "line": "The curtains open on Lion. A lion's powerful roar can carry across a long distance. Listen to the word: roar. Take a breath for your gentle pretend roar!"},
    {"animal": "elephant", "family": "wild", "sound": "TRUMPET", "verb": "trumpet", "line": "Elephant raises a long trunk. Elephants can trumpet, and they also communicate with deep rumbles. Listen: trumpet. Make a pretend trunk with your arm!"},
    {"animal": "owl", "family": "bird", "sound": "HOOT", "verb": "hoot", "line": "The lights dim for Owl. Many owls make hooting calls, though different owls use different sounds. Listen: hoo, hoo. Get ready for a soft nighttime echo."},
    {"animal": "parrot", "family": "bird", "sound": "SQUAWK", "verb": "squawk", "line": "Parrot brings a bright finale. Parrots use calls such as squawks, and some can copy sounds they hear. Listen: squawk. Give the orchestra one cheerful final echo!"},
]


def voice_path(key: str) -> Path:
    return WORK / f"voice-{key}.mp3"


async def make_voices() -> list[tuple[str, str]]:
    lines = [("intro", "Welcome to the Tiny Tales Animal Sound Orchestra! Eight animal performers will take the stage. Listen to the name of each call, then echo the sound during your turn.")]
    lines += [(f"p{index}", item["line"]) for index, item in enumerate(PERFORMERS, 1)]
    lines.append(("outro", "Bravo! You met moos, bleats, oinks, clucks, roars, trumpets, hoots, and squawks. Animal calls can warn, greet, locate, and communicate. Which sound was your favourite?"))
    for key, wording in lines:
        target = voice_path(key)
        if not target.exists():
            await edge_tts.Communicate(wording, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def make_timeline(lines: list[tuple[str, str]]) -> tuple[list[dict], list[tuple[str, float]], float]:
    lengths = {key: base.duration(voice_path(key)) for key, _ in lines}; events=[]; tracks=[]; cursor=.3
    def add(kind: str, length: float, **data: object) -> dict:
        nonlocal cursor
        event={"kind":kind,"start":cursor,"end":cursor+length,**data}; events.append(event); cursor=event["end"]; return event
    event=add("intro",max(9.0,lengths["intro"]+1.0)); tracks.append(("intro",event["start"]+.15))
    for index,item in enumerate(PERFORMERS,1):
        event=add("reveal",lengths[f"p{index}"]+.8,index=index,item=item); tracks.append((f"p{index}",event["start"]+.15))
        add("think",4.8,index=index,item=item)
    event=add("outro",max(10.0,lengths["outro"]+1.0)); tracks.append(("outro",event["start"]+.15))
    return events,tracks,math.ceil(cursor*base.ART_FPS)/base.ART_FPS


def stage(frame: Image.Image, family: str, t: float) -> None:
    draw=ImageDraw.Draw(frame,"RGBA"); colors={"farm":((255,221,135,255),(174,61,58,255)),"wild":((250,184,94,255),(62,126,76,255)),"bird":((164,211,248,255),(105,78,155,255))}; floor,curtain=colors[family]
    draw.rectangle((0,0,1920,1080),fill=(31,35,65,255)); draw.polygon([(0,0),(630,0),(830,760),(0,760)],fill=(*floor[:3],105)); draw.polygon([(1920,0),(1290,0),(1090,760),(1920,760)],fill=(*floor[:3],105));
    draw.polygon([(0,0),(430,0),(330,870),(0,980)],fill=curtain); draw.polygon([(1920,0),(1490,0),(1590,870),(1920,980)],fill=curtain); draw.rectangle((0,850,1920,1080),fill=floor)
    for x in range(250,1750,180): draw.ellipse((x-15,920,x+15,950),fill=(255,248,205,180))
    for x in (620,960,1300): draw.line((x,0,x+int(30*math.sin(t)),700),fill=(255,247,185,70),width=65)


def notes(draw: ImageDraw.ImageDraw, t: float, color: tuple[int,int,int,int]) -> None:
    for index,(x,y) in enumerate([(370,480),(510,350),(1360,380),(1510,520),(1180,270)]):
        bob=int(18*math.sin(t*2+index)); draw.ellipse((x-22,y-15+bob,x+22,y+22+bob),fill=color); draw.line((x+19,y+bob,x+19,y-95+bob),fill=color,width=9); draw.line((x+19,y-95+bob,x+70,y-70+bob),fill=color,width=9)


def paste_animal(frame: Image.Image, animals: dict, name: str, box: tuple[int,int,int,int], pulse: float=1.0) -> None:
    sprite=animals[name].copy(); maxw=int((box[2]-box[0])*pulse); maxh=int((box[3]-box[1])*pulse); sprite.thumbnail((maxw,maxh),Image.Resampling.LANCZOS); cx=(box[0]+box[2])//2; frame.alpha_composite(sprite,(cx-sprite.width//2,box[3]-sprite.height))


def intro_frame(t: float, animals: dict, outro: bool=False) -> Image.Image:
    frame=Image.new("RGBA",(base.W,base.H)); stage(frame,"bird",t); draw=ImageDraw.Draw(frame,"RGBA"); base.panel(draw,(260,100,1660,470),radius=55,width=9)
    base.centered(draw,(960,220),"ANIMAL SOUND",base.F78,(224,74,67,255),2); base.centered(draw,(960,340),"ORCHESTRA" if not outro else "BRAVO!",base.F78,(29,76,106,255),2)
    names=["cow","sheep","pig","chicken","lion","elephant","owl","parrot"]
    for index,name in enumerate(names): paste_animal(frame,animals,name,(120+index*210,550,300+index*210,850),.92)
    base.centered(draw,(960,945),"LISTEN - ECHO - PERFORM" if not outro else "WHICH SOUND WAS YOUR FAVOURITE?",base.F38,(255,255,255,255),2); return frame.convert("RGB")


def frame_for(event: dict, t: float, spec: dict, animals: dict) -> Image.Image:
    if event["kind"]=="intro": return intro_frame(t,animals)
    if event["kind"]=="outro": return intro_frame(t,animals,True)
    item=event["item"]; echo=event["kind"]=="think"; frame=Image.new("RGBA",(base.W,base.H)); stage(frame,item["family"],t); draw=ImageDraw.Draw(frame,"RGBA"); notes(draw,t,(255,224,88,230))
    base.header(frame,"TINY TALES ANIMAL SOUND ORCHESTRA",f"PERFORMER {event['index']} OF {len(PERFORMERS)}")
    pulse=1.0+(0.045*math.sin(t*5) if echo else 0); paste_animal(frame,animals,item["animal"],(540,220,1380,875),pulse)
    draw.rounded_rectangle((250,735,1670,965),radius=55,fill=(255,253,235,242),outline=(255,188,50,255),width=8)
    base.centered(draw,(960,805),f"{item['animal'].upper()} SAYS",base.F38,(29,76,106,255)); base.centered(draw,(960,900),item["sound"],base.F78,(46,151,84,255) if not echo else (224,74,67,255),3)
    if echo:
        base.centered(draw,(960,1015),f"YOUR TURN - {item['verb'].upper()}!",base.F38,(255,255,255,255),2)
        elapsed=t-event["start"]; total=event["end"]-event["start"]; draw.rounded_rectangle((430,170,1490,205),radius=15,fill=(255,255,255,110)); draw.rounded_rectangle((430,170,430+int(1060*min(1,elapsed/total)),205),radius=15,fill=(255,211,57,230))
    return frame.convert("RGB")


def validate(total: float, events: list[dict], animals: dict) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    checks={"size":OUTPUT.stat().st_size>1_000_000,"duration":abs(float(probe["format"]["duration"])-total)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,"audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"eight_performers":len([e for e in events if e["kind"]=="reveal"])==8,"eight_echo_windows":len([e for e in events if e["kind"]=="think"])==8}
    report={"format":"animal-sound-orchestra","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values()),"upload_authorized":False}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[events[0]]+[e for e in events if e["kind"] in {"reveal","think"}]+[events[-1]]; contact=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for index,event in enumerate(samples): contact.paste(frame_for(event,event["start"]+min(1.0,(event["end"]-event["start"])/2),SPEC,animals).resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    contact.save(WORK/"quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc={"id":SPEC["id"],"title":"Animal Sound Orchestra | Moo, Roar, Hoot and More for Kids","description":"Eight friendly performers take the Tiny Tales concert stage. Children meet farm, wild, and bird calls—including moo, bleat, oink, cluck, roar, trumpet, hoot, and squawk—then get a clear pause to echo every sound.\n\nA playful listening and speech adventure supporting animal vocabulary, memory, rhythm, and confident participation for children ages 3 to 7.","tags":["animal sounds","animal sounds for kids","farm animal sounds","wild animal sounds","preschool music","listen and repeat","Tiny Tales","kids learning"],"category_id":"27","made_for_kids":True,"privacy":"private","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"new_image_generation_calls":0}; META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True); report=WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {OUTPUT}",flush=True); return
    farm=games.extract_grid(AUTOMATION/"production-assets"/"farm-animals-sheet.png",["cow","pig","sheep","horse","chicken","goat"]); wild=games.extract_grid(AUTOMATION/"production-assets"/"jungle-animals-sheet.png",["lion","tiger","elephant","zebra","hippopotamus","crocodile"]); birds=games.extract_grid(AUTOMATION/"production-assets"/"bird-animals-sheet.png",["owl","parrot","flamingo","penguin","peacock","toucan"]); animals={**farm,**wild,**birds}
    lines=asyncio.run(make_voices()); events,tracks,total=make_timeline(lines); shared.frame_for=frame_for; shared.render(WORK,OUTPUT,total,events,tracks,SPEC,animals); validate(total,events,animals); write_metadata(total); print(json.dumps({"id":SPEC["id"],"status":"completed","duration_seconds":total}),flush=True)


if __name__=="__main__": main()
