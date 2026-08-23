"""Render a one-off Tiny Tales shape-building story with six changing environments."""

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


AUTOMATION=base.AUTOMATION
OUTPUT_DIR=AUTOMATION/"production-output"
WORK=AUTOMATION/"production-work"/"animal-shape-builders-01"
OUTPUT=OUTPUT_DIR/"animal-shape-builders-01.mp4"
META=AUTOMATION.parent/"metadata"/"animal-shape-builders-01.json"
SPEC={"id":"animal-shape-builders-01"}

BUILDS=[
    {"shape":"CIRCLE","scene":"ocean","animal":"dolphin","feature":"ONE CURVED EDGE - NO CORNERS","line":"Dolphin needs round bubbles for the water playground. A circle has one curved edge and no corners. Round circles become bubbles, portholes, and a bright sun. Our first shape is ready!","prompt":"DRAW A CIRCLE IN THE AIR"},
    {"shape":"TRIANGLE","scene":"mountain","animal":"goat","feature":"THREE STRAIGHT SIDES - THREE CORNERS","line":"Goat brings triangle pieces for pointy mountain tops and a barn roof. A triangle has three straight sides and three corners. Count them with Goat: one, two, three.","prompt":"TRACE THREE TRIANGLE SIDES"},
    {"shape":"SQUARE","scene":"barn","animal":"pig","feature":"FOUR EQUAL SIDES - FOUR CORNERS","line":"Pig adds square windows to the little red barn. A square has four straight sides that are all the same length, and it has four corners. The square windows fit perfectly.","prompt":"DRAW FOUR EQUAL SIDES"},
    {"shape":"RECTANGLE","scene":"bridge","animal":"elephant","feature":"TWO LONG SIDES - TWO SHORT SIDES","line":"Elephant carries rectangle planks for a bridge. A rectangle has four corners, two long sides, and two short sides. Strong rectangles stretch across the stream.","prompt":"TRACE LONG, SHORT, LONG, SHORT"},
    {"shape":"OVAL","scene":"nest","animal":"owl","feature":"CURVED LIKE A STRETCHED CIRCLE","line":"Owl discovers smooth oval eggs in a cosy nest. An oval is curved like a circle that has been gently stretched. It has no corners. We can spot ovals in eggs and leaves.","prompt":"DRAW A LONG, CURVED OVAL"},
    {"shape":"STAR","scene":"night","animal":"parrot","feature":"FIVE POINTS IN OUR PICTURE STAR","line":"Parrot hangs star decorations for the playground celebration. Our picture star has five points. Follow each point around the edge. Now every animal has helped build the shape playground!","prompt":"POINT TO FIVE STAR TIPS"},
]


def voice_path(key: str) -> Path: return WORK/f"voice-{key}.mp3"


async def make_voices() -> list[tuple[str,str]]:
    lines=[("intro","Welcome to the Tiny Tales Animal Shape Builders! Six animal helpers will use circles, triangles, squares, rectangles, ovals, and stars to build a colourful new playground.")]
    lines += [(f"b{index}",item["line"]) for index,item in enumerate(BUILDS,1)]
    lines.append(("outro","The shape playground is complete! Circles made bubbles, triangles made roofs, squares made windows, rectangles made a bridge, ovals made eggs, and stars made decorations. Which shape will you build with?"))
    for key,wording in lines:
        target=voice_path(key)
        if not target.exists(): await edge_tts.Communicate(wording,base.VOICE,rate=base.VOICE_RATE,pitch=base.VOICE_PITCH,volume="-2%").save(str(target))
    return lines


def timeline(lines: list[tuple[str,str]]) -> tuple[list[dict],list[tuple[str,float]],float]:
    lengths={key:base.duration(voice_path(key)) for key,_ in lines}; events=[]; tracks=[]; cursor=.3
    def add(kind: str,length: float,**data: object) -> dict:
        nonlocal cursor
        event={"kind":kind,"start":cursor,"end":cursor+length,**data}; events.append(event); cursor=event["end"]; return event
    event=add("intro",max(9.0,lengths["intro"]+1)); tracks.append(("intro",event["start"]+.15))
    for index,item in enumerate(BUILDS,1):
        event=add("reveal",lengths[f"b{index}"]+1,index=index,item=item); tracks.append((f"b{index}",event["start"]+.15)); add("think",4.8,index=index,item=item)
    event=add("outro",max(10.0,lengths["outro"]+1)); tracks.append(("outro",event["start"]+.15)); return events,tracks,math.ceil(cursor*base.ART_FPS)/base.ART_FPS


def star_points(cx: int,cy: int,outer: int,inner: int) -> list[tuple[int,int]]:
    points=[]
    for index in range(10):
        angle=-math.pi/2+index*math.pi/5; radius=outer if index%2==0 else inner; points.append((int(cx+math.cos(angle)*radius),int(cy+math.sin(angle)*radius)))
    return points


def draw_shape(draw: ImageDraw.ImageDraw,name: str,cx: int,cy: int,size: int,active: bool=False) -> None:
    fill=(255,221,91,235); outline=(224,74,67,255) if not active else (46,171,102,255); width=18 if active else 12
    if name=="CIRCLE": draw.ellipse((cx-size,cy-size,cx+size,cy+size),fill=fill,outline=outline,width=width)
    elif name=="TRIANGLE": draw.polygon([(cx,cy-size),(cx-size,cy+size),(cx+size,cy+size)],fill=fill,outline=outline); draw.line([(cx,cy-size),(cx-size,cy+size),(cx+size,cy+size),(cx,cy-size)],fill=outline,width=width,joint="curve")
    elif name=="SQUARE": draw.rounded_rectangle((cx-size,cy-size,cx+size,cy+size),radius=8,fill=fill,outline=outline,width=width)
    elif name=="RECTANGLE": draw.rounded_rectangle((cx-int(size*1.25),cy-int(size*.72),cx+int(size*1.25),cy+int(size*.72)),radius=8,fill=fill,outline=outline,width=width)
    elif name=="OVAL": draw.ellipse((cx-int(size*1.25),cy-int(size*.72),cx+int(size*1.25),cy+int(size*.72)),fill=fill,outline=outline,width=width)
    else: draw.polygon(star_points(cx,cy,size,int(size*.43)),fill=fill,outline=outline); draw.line(star_points(cx,cy,size,int(size*.43))+[star_points(cx,cy,size,int(size*.43))[0]],fill=outline,width=width,joint="curve")


def paste(frame: Image.Image,animals: dict,name: str,box: tuple[int,int,int,int]) -> None:
    sprite=animals[name].copy(); sprite.thumbnail((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS); frame.alpha_composite(sprite,((box[0]+box[2]-sprite.width)//2,box[3]-sprite.height))


def environment(frame: Image.Image,item: dict,t: float,animals: dict) -> None:
    draw=ImageDraw.Draw(frame,"RGBA"); scene=item["scene"]
    if scene=="ocean":
        draw.rectangle((960,180,1920,1080),fill=(57,174,213,255)); draw.ellipse((1660,210,1810,360),fill=(255,220,68,255));
        for x,y,r in [(1100,350,45),(1260,250,65),(1590,470,55),(1770,650,38)]: draw.ellipse((x-r,y-r,x+r,y+r),outline=(235,253,255,220),width=8)
    elif scene=="mountain":
        draw.rectangle((960,180,1920,1080),fill=(153,221,246,255)); draw.rectangle((960,760,1920,1080),fill=(106,188,89,255)); draw.polygon([(1020,760),(1300,330),(1580,760)],fill=(91,150,101,255)); draw.polygon([(1370,760),(1640,420),(1910,760)],fill=(73,132,92,255)); draw.polygon([(1215,460),(1300,330),(1388,465)],fill=(250,250,239,255))
    elif scene=="barn":
        draw.rectangle((960,180,1920,1080),fill=(151,218,243,255)); draw.rectangle((960,760,1920,1080),fill=(106,188,89,255)); draw.rectangle((1190,360,1740,850),fill=(195,73,57,255)); draw.polygon([(1120,360),(1465,130),(1810,360)],fill=(127,57,47,255));
        for x in (1320,1600): draw.rectangle((x-70,470,x+70,610),fill=(255,231,112,255),outline=(255,255,244,255),width=8)
    elif scene=="bridge":
        draw.rectangle((960,180,1920,1080),fill=(142,217,247,255)); draw.rectangle((960,720,1920,1080),fill=(55,156,196,255));
        for x in range(1050,1850,120): draw.rectangle((x,570,x+95,700),fill=(171,111,64,255),outline=(104,67,43,255),width=7)
        draw.line((1030,545,1900,545),fill=(105,67,43,255),width=20); draw.line((1030,715,1900,715),fill=(105,67,43,255),width=20)
    elif scene=="nest":
        draw.rectangle((960,180,1920,1080),fill=(164,220,247,255)); draw.line((1060,780,1890,520),fill=(117,76,45,255),width=55); draw.arc((1280,470,1770,850),5,175,fill=(128,82,45,255),width=45)
        for x in (1410,1530,1650): draw.ellipse((x-58,610,x+58,770),fill=(247,240,205,255),outline=(178,148,99,255),width=7)
    else:
        draw.rectangle((960,180,1920,1080),fill=(39,53,104,255));
        for x,y,r in [(1080,320,30),(1280,250,22),(1510,360,36),(1740,260,25),(1830,520,18)]: draw.polygon(star_points(x,y,r,int(r*.43)),fill=(255,226,79,255))
    paste(frame,animals,item["animal"],(1190,540,1740,980))


def build_frame(event: dict,t: float,animals: dict) -> Image.Image:
    item=event["item"]; active=event["kind"]=="think"; frame=Image.new("RGBA",(base.W,base.H),(255,247,214,255)); draw=ImageDraw.Draw(frame,"RGBA"); environment(frame,item,t,animals); draw.rectangle((0,180,960,1080),fill=(255,247,214,255)); base.header(frame,"ANIMAL SHAPE BUILDERS",f"BUILD {event['index']} OF {len(BUILDS)}")
    draw_shape(draw,item["shape"],480,525,220,active); base.centered(draw,(480,795),item["shape"],base.F62,(224,74,67,255),2); base.centered(draw,(480,865),item["feature"],base.F24,(29,76,106,255))
    draw.rounded_rectangle((1050,870,1830,970),radius=32,fill=(255,255,245,235),outline=(46,151,84,255),width=7); base.centered(draw,(1440,920),f"{item['animal'].upper()} BUILDS WITH {item['shape']}",base.F30,(29,76,106,255))
    if active:
        draw.rounded_rectangle((260,980,1660,1060),radius=28,fill=(39,79,111,245)); base.centered(draw,(960,1020),item["prompt"],base.F38,(255,255,255,255)); elapsed=t-event["start"]; total=event["end"]-event["start"]; draw.rounded_rectangle((430,165,1490,195),radius=14,fill=(255,255,255,130)); draw.rounded_rectangle((430,165,430+int(1060*min(1,elapsed/total)),195),radius=14,fill=(255,198,50,240))
    return frame.convert("RGB")


def title_frame(t: float,animals: dict,outro: bool=False) -> Image.Image:
    frame=base.gradient_background(9 if outro else 4,t).convert("RGBA"); draw=ImageDraw.Draw(frame,"RGBA"); base.panel(draw,(200,110,1720,950),radius=60,width=9); base.centered(draw,(960,245),"ANIMAL SHAPE",base.F78,(224,74,67,255),2); base.centered(draw,(960,360),"BUILDERS" if not outro else "PLAYGROUND COMPLETE!",base.F62,(29,76,106,255),2)
    names=["CIRCLE","TRIANGLE","SQUARE","RECTANGLE","OVAL","STAR"]
    for index,name in enumerate(names): draw_shape(draw,name,360+index*240,575,78)
    for index,name in enumerate(["dolphin","goat","pig","elephant","owl","parrot"]): paste(frame,animals,name,(260+index*240,670,460+index*240,860))
    base.centered(draw,(960,880),"FIND - TRACE - BUILD" if not outro else "SIX SHAPES MADE ONE BIG ADVENTURE",base.F38,(46,151,84,255)); return frame.convert("RGB")


def frame_for(event: dict,t: float,spec: dict,animals: dict) -> Image.Image:
    if event["kind"]=="intro": return title_frame(t,animals)
    if event["kind"]=="outro": return title_frame(t,animals,True)
    return build_frame(event,t,animals)


def validate(total: float,events: list[dict],animals: dict) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio"); checks={"size":OUTPUT.stat().st_size>1_000_000,"duration":abs(float(probe["format"]["duration"])-total)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,"audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"six_shape_builds":len([e for e in events if e["kind"]=="reveal"])==6,"six_tracing_windows":len([e for e in events if e["kind"]=="think"])==6}
    report={"format":"animal-shape-builders","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values()),"upload_authorized":False}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[events[0]]+[e for e in events if e["kind"] in {"reveal","think"}]+[events[-1]]; contact=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for index,event in enumerate(samples): contact.paste(frame_for(event,event["start"]+min(1,(event["end"]-event["start"])/2),SPEC,animals).resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    contact.save(WORK/"quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc={"id":SPEC["id"],"title":"Animal Shape Builders | Circle, Triangle, Square and More for Kids","description":"Six animal builders use circles, triangles, squares, rectangles, ovals, and stars to create bubbles, mountains, barn windows, a bridge, nest eggs, and celebration decorations. Each changing scene explains the shape and includes a tracing movement.\n\nA Tiny Tales early-geometry story supporting shape recognition, side and corner vocabulary, listening, and fine-motor practice for children ages 3 to 7.","tags":["shapes for kids","circle triangle square","preschool geometry","shape tracing","early maths","animals for kids","Tiny Tales","kids learning"],"category_id":"27","made_for_kids":True,"privacy":"private","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"new_image_generation_calls":0}; META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True); report=WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {OUTPUT}",flush=True); return
    farm=games.extract_grid(AUTOMATION/"production-assets"/"farm-animals-sheet.png",["cow","pig","sheep","horse","chicken","goat"]); wild=games.extract_grid(AUTOMATION/"production-assets"/"jungle-animals-sheet.png",["lion","tiger","elephant","zebra","hippopotamus","crocodile"]); ocean=games.extract_grid(AUTOMATION/"production-assets"/"ocean-animals-sheet.png",["dolphin","sea turtle","octopus","seahorse","crab","whale"]); birds=games.extract_grid(AUTOMATION/"production-assets"/"bird-animals-sheet.png",["owl","parrot","flamingo","penguin","peacock","toucan"]); animals={**farm,**wild,**ocean,**birds}
    lines=asyncio.run(make_voices()); events,tracks,total=timeline(lines); shared.frame_for=frame_for; shared.render(WORK,OUTPUT,total,events,tracks,SPEC,animals); validate(total,events,animals); write_metadata(total); print(json.dumps({"id":SPEC["id"],"status":"completed","duration_seconds":total}),flush=True)


if __name__=="__main__": main()
