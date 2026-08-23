"""Render a connected Tiny Tales seed-to-flower farm story."""

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
WORK=AUTOMATION/"production-work"/"tiny-seed-big-farm-adventure-01"
OUTPUT=OUTPUT_DIR/"tiny-seed-big-farm-adventure-01.mp4"
META=AUTOMATION.parent/"metadata"/"tiny-seed-big-farm-adventure-01.json"
SPEC={"id":"tiny-seed-big-farm-adventure-01"}

STAGES=[
    {"scene":"seed","animal":"chicken","heading":"A TINY SEED","label":"A young plant waits inside","line":"Chicken found a tiny sunflower seed beside the garden. Inside its protective coat was a very young plant and stored food to help it begin growing. The seed was small, but it held a big possibility."},
    {"scene":"plant","animal":"pig","heading":"INTO THE SOIL","label":"Soil holds water and air","line":"Pig helped make a small hole and the seed settled into loose soil. Soil can hold water and air around a seed. The garden team covered it gently, without packing the soil too tightly."},
    {"scene":"water","animal":"cow","heading":"ADD WATER","label":"The seed absorbs moisture","line":"Cow brought water for the dry garden bed. The seed absorbed moisture, its coat softened, and growing could begin. A seed needs the right amount of water, warmth, and air to germinate."},
    {"scene":"roots","animal":"goat","heading":"ROOTS GROW DOWN","label":"Germination begins","line":"The first little root pushed downward into the soil. Roots anchor a plant and absorb water and minerals. Wiggle your fingers down like roots exploring the earth."},
    {"scene":"sprout","animal":"sheep","heading":"A SHOOT GROWS UP","label":"The sprout reaches for light","line":"Next, a pale shoot curved upward and broke through the soil. It became greener in the light. Curl small like a seed, then slowly rise like the new sprout."},
    {"scene":"leaves","animal":"horse","heading":"LEAVES CATCH LIGHT","label":"The plant makes food","line":"The stem grew taller and opened broad green leaves. Leaves use light, water, and carbon dioxide from the air to make sugars for the plant. Stretch your arms out like leaves catching sunlight."},
    {"scene":"flower","animal":"chicken","heading":"FLOWER, THEN NEW SEEDS","label":"The life cycle continues","line":"At last, a bright sunflower opened. Pollinators can help flowers make seeds, and mature sunflower heads hold many new seeds. Some may feed animals, and some may grow into brand-new plants."},
]


def voice_path(key: str) -> Path: return WORK/f"voice-{key}.mp3"


async def make_voices() -> list[tuple[str,str]]:
    lines=[("intro","Come to the Tiny Tales farm garden for the big adventure of one tiny seed. Farm friends will help it settle into soil, grow roots and leaves, open a flower, and make new seeds.")]
    lines += [(f"s{index}",item["line"]) for index,item in enumerate(STAGES,1)]
    lines.append(("outro","The tiny seed became a sunflower and made seeds for a new beginning. Seed, roots, sprout, stem, leaves, flower, and new seeds form a plant life cycle. What would you like to grow?"))
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
    for index,item in enumerate(STAGES,1):
        event=add("reveal",lengths[f"s{index}"]+1,index=index,item=item); tracks.append((f"s{index}",event["start"]+.15))
        if item["scene"] in {"roots","sprout","leaves"}: add("think",5.0,index=index,item=item)
    event=add("outro",max(10.0,lengths["outro"]+1)); tracks.append(("outro",event["start"]+.15)); return events,tracks,math.ceil(cursor*base.ART_FPS)/base.ART_FPS


def paste(frame: Image.Image,animals: dict,name: str,box: tuple[int,int,int,int]) -> None:
    sprite=animals[name].copy(); sprite.thumbnail((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS); frame.alpha_composite(sprite,((box[0]+box[2]-sprite.width)//2,box[3]-sprite.height))


def leaf(draw: ImageDraw.ImageDraw,x: int,y: int,left: bool,scale: float=1.0) -> None:
    w=int(105*scale); h=int(48*scale); x1=x-w if left else x; x2=x if left else x+w; draw.ellipse((x1,y-h,x2,y+h),fill=(74,174,78,255),outline=(39,126,59,255),width=max(4,int(7*scale))); draw.line((x,y,x1 if left else x2,y),fill=(39,126,59,255),width=max(3,int(5*scale)))


def plant(draw: ImageDraw.ImageDraw,stage: str,t: float) -> None:
    cx=930; soil=705; seed_y=555 if stage=="seed" else soil+60; draw.ellipse((cx-45,seed_y,cx+45,seed_y+45),fill=(126,80,42,255),outline=(81,52,31,255),width=6)
    if stage in {"roots","sprout","leaves","flower"}:
        root_bottom=930 if stage!="roots" else 875; draw.line((cx,soil+85,cx,root_bottom),fill=(237,226,185,255),width=14)
        for dx,dy in [(-110,95),(100,145),(-75,205),(85,245)]: draw.line((cx,soil+115,cx+dx,soil+dy),fill=(237,226,185,255),width=9)
    if stage in {"sprout","leaves","flower"}:
        top={"sprout":590,"leaves":360,"flower":280}[stage]; draw.line((cx,soil+70,cx,top),fill=(48,145,68,255),width=20)
        if stage=="sprout": leaf(draw,cx,610,True,.6); leaf(draw,cx,575,False,.6)
        else:
            leaf(draw,cx,580,True,.9); leaf(draw,cx,510,False,1.0); leaf(draw,cx,435,True,1.0); leaf(draw,cx,380,False,.85)
        if stage=="leaves": draw.ellipse((cx-58,top-65,cx+58,top+45),fill=(87,164,70,255),outline=(45,121,57,255),width=7)
        if stage=="flower":
            for index in range(12):
                angle=index*math.pi/6; px=cx+int(math.cos(angle)*92); py=top+int(math.sin(angle)*92); draw.ellipse((px-48,py-28,px+48,py+28),fill=(255,205,45,255),outline=(229,153,29,255),width=5)
            draw.ellipse((cx-70,top-70,cx+70,top+70),fill=(117,72,36,255),outline=(81,49,26,255),width=8)


def water_drops(draw: ImageDraw.ImageDraw,t: float) -> None:
    for index,x in enumerate(range(740,1130,75)):
        y=300+int((t*130+index*70)%300); draw.ellipse((x-13,y-25,x+13,y+20),fill=(70,181,233,230)); draw.polygon([(x,y-48),(x-14,y-16),(x+14,y-16)],fill=(70,181,233,230))


def garden_frame(event: dict,t: float,animals: dict) -> Image.Image:
    item=event["item"]; scene=item["scene"]; action=event["kind"]=="think"; palettes={"seed":(147,219,247),"plant":(167,224,246),"water":(120,189,218),"roots":(173,221,243),"sprout":(143,218,247),"leaves":(127,207,244),"flower":(255,203,135)}; frame=Image.new("RGBA",(base.W,base.H),palettes[scene]+(255,)); draw=ImageDraw.Draw(frame,"RGBA")
    if scene!="water": draw.ellipse((1570,180,1780,390),fill=(255,219,67,255))
    else:
        for x,y,r in [(450,270,150),(690,220,180),(930,270,145),(1160,240,165)]: draw.ellipse((x-r,y-r,x+r,y+r),fill=(102,126,145,235))
        water_drops(draw,t)
    draw.rectangle((0,705,1920,1080),fill=(113,75,43,255)); draw.rectangle((0,675,1920,725),fill=(96,177,80,255))
    for x in range(100,1850,220): draw.ellipse((x-28,645,x+28,705),fill=(70,159,70,255))
    if scene=="plant": draw.ellipse((860,735,1000,800),fill=(76,48,30,255)); draw.polygon([(835,740),(930,660),(1025,740)],fill=(113,75,43,255))
    plant(draw,scene,t)
    paste(frame,animals,item["animal"],(1280,430,1800,940)); base.header(frame,item["heading"],f"STAGE {event['index']} OF {len(STAGES)} - {item['label'].upper()}")
    draw.rounded_rectangle((165,830,670,955),radius=38,fill=(255,255,242,238),outline=(255,188,50,255),width=7); base.centered(draw,(417,892),scene.upper(),base.F48,(29,76,106,255))
    if action:
        prompts={"roots":"FINGERS DOWN LIKE ROOTS","sprout":"CURL SMALL - THEN RISE","leaves":"STRETCH ARMS LIKE LEAVES"}; draw.rounded_rectangle((260,975,1660,1060),radius=28,fill=(39,79,111,245)); base.centered(draw,(960,1018),prompts[scene],base.F38,(255,255,255,255)); elapsed=t-event["start"]; total=event["end"]-event["start"]; draw.rounded_rectangle((430,165,1490,195),radius=14,fill=(255,255,255,130)); draw.rounded_rectangle((430,165,430+int(1060*min(1,elapsed/total)),195),radius=14,fill=(255,198,50,240))
    return frame.convert("RGB")


def lifecycle_frame(t: float,animals: dict,outro: bool=False) -> Image.Image:
    frame=base.gradient_background(16 if outro else 6,t).convert("RGBA"); draw=ImageDraw.Draw(frame,"RGBA"); base.panel(draw,(180,105,1740,960),radius=60,width=9); base.centered(draw,(960,220),"THE TINY SEED'S",base.F78,(224,74,67,255),2); base.centered(draw,(960,335),"BIG FARM ADVENTURE" if not outro else "LIFE CYCLE COMPLETE!",base.F62,(29,76,106,255),2)
    labels=["SEED","ROOTS","SPROUT","LEAVES","FLOWER","NEW SEEDS"]
    for index,label in enumerate(labels):
        x=300+index*265; draw.ellipse((x-100,500,x+100,700),fill=(242,255,232,255),outline=(46,151,84,255),width=7); base.centered(draw,(x,600),label,base.F24,(29,76,106,255));
        if index<len(labels)-1: draw.line((x+105,600,x+155,600),fill=(224,74,67,220),width=12)
    paste(frame,animals,"chicken",(800,680,1120,900)); base.centered(draw,(960,885),"PLANT - WATER - GROW - BLOOM" if not outro else "ONE FLOWER CAN BEGIN MANY NEW JOURNEYS",base.F38,(46,151,84,255)); return frame.convert("RGB")


def frame_for(event: dict,t: float,spec: dict,animals: dict) -> Image.Image:
    if event["kind"]=="intro": return lifecycle_frame(t,animals)
    if event["kind"]=="outro": return lifecycle_frame(t,animals,True)
    return garden_frame(event,t,animals)


def validate(total: float,events: list[dict],animals: dict) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio"); checks={"size":OUTPUT.stat().st_size>1_000_000,"duration":abs(float(probe["format"]["duration"])-total)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,"audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"seven_growth_stages":len([e for e in events if e["kind"]=="reveal"])==7,"three_movement_windows":len([e for e in events if e["kind"]=="think"])==3}
    report={"format":"tiny-seed-growth-story","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values()),"upload_authorized":False}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[events[0]]+[e for e in events if e["kind"] in {"reveal","think"}]+[events[-1]]; contact=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for index,event in enumerate(samples): contact.paste(frame_for(event,event["start"]+min(1,(event["end"]-event["start"])/2),SPEC,animals).resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    contact.save(WORK/"quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc={"id":SPEC["id"],"title":"The Tiny Seed's Big Farm Adventure | Plant Life Cycle for Kids","description":"Follow one tiny sunflower seed as farm friends plant it, add water, watch roots grow down and a shoot grow up, open leaves, bloom, and make new seeds. Seven changing scenes introduce germination and the plant life cycle with three gentle movement moments.\n\nA Tiny Tales science story supporting nature vocabulary, sequencing, observation, and whole-body learning for children ages 3 to 7.","tags":["plant life cycle","seed to flower","plants for kids","germination","science for kids","farm story","Tiny Tales","preschool learning"],"category_id":"27","made_for_kids":True,"privacy":"private","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"new_image_generation_calls":0}; META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True); report=WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {OUTPUT}",flush=True); return
    animals=games.extract_grid(AUTOMATION/"production-assets"/"farm-animals-sheet.png",["cow","pig","sheep","horse","chicken","goat"]); lines=asyncio.run(make_voices()); events,tracks,total=timeline(lines); shared.frame_for=frame_for; shared.render(WORK,OUTPUT,total,events,tracks,SPEC,animals); validate(total,events,animals); write_metadata(total); print(json.dumps({"id":SPEC["id"],"status":"completed","duration_seconds":total}),flush=True)


if __name__=="__main__": main()
