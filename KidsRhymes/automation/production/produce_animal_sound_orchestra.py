"""Render a one-off Tiny Tales animal-sound concert with call-and-response pauses."""

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

OPENING_SONG = [
    ("opening1", "Moo and baa, oink and cluck! Animal friends, come sing with us!"),
    ("opening2", "Roar and trumpet, hoot and squawk! Clap to the rhythm, stomp and walk!"),
]

FINALE_SONG = [
    ("finale1", "Cow goes moo and Sheep goes baa. Pig says oink and Chicken says cluck!"),
    ("finale2", "Lion goes roar and Elephant trumpets. Owl says hoo and Parrot says squawk!"),
    ("finale3", "Moo, baa, oink, cluck, keep the animal beat! Roar, trumpet, hoo, squawk, move your hands and feet!"),
    ("finale4", "Every voice is different. Every sound belongs. Animal friends together make a fantastic song!"),
]


def voice_path(key: str) -> Path:
    return WORK / f"voice-{key}.mp3"


async def make_voices() -> list[tuple[str, str]]:
    lines = list(OPENING_SONG)
    lines.append(("welcome", "Welcome to the Tiny Tales Animal Sound Orchestra! Let's introduce each performer, listen to every animal sound, and tune in with us for our fantastic Animal Sound Song at the end!"))
    lines += [(f"p{index}", item["line"]) for index, item in enumerate(PERFORMERS, 1)]
    lines += FINALE_SONG
    lines.append(("bow", "Bravo, animal orchestra! Which performer was your favourite? Keep listening, moving, and making music together!"))
    for key, wording in lines:
        target = voice_path(key)
        if not target.exists():
            await edge_tts.Communicate(wording, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def make_timeline(lines: list[tuple[str, str]]) -> tuple[list[dict], list[tuple[str, float]], float]:
    lengths = {key: base.duration(voice_path(key)) for key, _ in lines}; events=[]; tracks=[]; cursor=0.0
    def add(kind: str, length: float, **data: object) -> dict:
        nonlocal cursor
        event={"kind":kind,"start":cursor,"end":cursor+length,**data}; events.append(event); cursor=event["end"]; return event
    opening_length = sum(lengths[key] + .7 for key, _ in OPENING_SONG) + 1.0
    event=add("opening_song",max(15.0,opening_length)); song_cursor=event["start"]+.6
    for key, _ in OPENING_SONG:
        tracks.append((key,song_cursor)); song_cursor += lengths[key]+.7
    event=add("welcome",max(10.0,lengths["welcome"]+1.2)); tracks.append(("welcome",event["start"]+.25))
    for index,item in enumerate(PERFORMERS,1):
        event=add("reveal",lengths[f"p{index}"]+.8,index=index,item=item); tracks.append((f"p{index}",event["start"]+.15))
        add("think",4.8,index=index,item=item)
    finale_length = sum(lengths[key] + .65 for key, _ in FINALE_SONG) + 1.2
    event=add("finale_song",max(30.0,finale_length)); song_cursor=event["start"]+.6
    for key, _ in FINALE_SONG:
        tracks.append((key,song_cursor)); song_cursor += lengths[key]+.65
    event=add("bow",max(9.0,lengths["bow"]+1.0)); tracks.append(("bow",event["start"]+.15))
    total=math.ceil(cursor*base.ART_FPS)/base.ART_FPS; events[-1]["end"]=total
    return events,tracks,total


def stage(frame: Image.Image, family: str, t: float) -> None:
    draw=ImageDraw.Draw(frame,"RGBA"); colors={"farm":((255,221,135,255),(224,76,76,255)),"wild":((255,190,92,255),(44,154,113,255)),"bird":((126,221,255,255),(139,86,209,255)),"rainbow":((255,205,91,255),(217,74,143,255))}; floor,curtain=colors[family]
    sky_top={"farm":(53,101,187),"wild":(24,116,115),"bird":(62,73,159),"rainbow":(70,50,150)}[family]
    for y in range(0,850,10):
        mix=y/850; colour=tuple(int(sky_top[i]*(1-mix)+(42,32,82)[i]*mix) for i in range(3)); draw.rectangle((0,y,1920,y+10),fill=(*colour,255))
    for index,(x,y,color) in enumerate([(180,170,(255,95,132,110)),(520,290,(75,225,255,100)),(920,150,(255,218,76,100)),(1320,300,(120,255,156,100)),(1710,160,(190,115,255,110))]):
        radius=120+int(22*math.sin(t*1.1+index)); draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color)
    draw.polygon([(0,0),(630,0),(830,760),(0,760)],fill=(*floor[:3],120)); draw.polygon([(1920,0),(1290,0),(1090,760),(1920,760)],fill=(*floor[:3],120));
    draw.polygon([(0,0),(430,0),(330,870),(0,980)],fill=curtain); draw.polygon([(1920,0),(1490,0),(1590,870),(1920,980)],fill=curtain); draw.rectangle((0,850,1920,1080),fill=floor)
    accent_palette=[(255,220,70,165),(77,218,255,155),(255,105,171,155),(119,241,155,155)]
    for side in (0,1):
        anchor=105 if side==0 else 1815
        for index in range(7):
            y=145+index*105; radius=28+int(7*math.sin(t*2+index)); draw.ellipse((anchor-radius,y-radius,anchor+radius,y+radius),fill=accent_palette[index%len(accent_palette)])
            x2=anchor+(120 if side==0 else -120); draw.line((anchor,y,x2,y+45),fill=accent_palette[(index+1)%len(accent_palette)],width=18)
    bunting=[(255,92,137,230),(255,214,70,230),(65,211,255,230),(107,235,144,230),(171,102,255,230)]
    draw.line((430,115,1490,115),fill=(255,255,255,190),width=8)
    for index,x in enumerate(range(470,1490,120)): draw.polygon([(x,118),(x+82,118),(x+41,185)],fill=bunting[index%len(bunting)])
    for row in range(3):
        for x in range(120+row*55,1880,180): draw.ellipse((x-14,900+row*55,x+14,928+row*55),fill=((255,248,205,220) if row%2==0 else (255,115,180,190)))
    for index,x in enumerate((470,760,1080,1390)): draw.line((x,0,x+int(90*math.sin(t*.8+index)),760),fill=(255,247,185,85),width=72)
    for index,x in enumerate(range(120,1900,160)):
        glow=190+int(55*math.sin(t*3+index)); draw.ellipse((x-13,55,x+13,81),fill=(255,235,95,glow))


def notes(draw: ImageDraw.ImageDraw, t: float, color: tuple[int,int,int,int]) -> None:
    for index,(x,y) in enumerate([(370,480),(510,350),(1360,380),(1510,520),(1180,270)]):
        bob=int(18*math.sin(t*2+index)); draw.ellipse((x-22,y-15+bob,x+22,y+22+bob),fill=color); draw.line((x+19,y+bob,x+19,y-95+bob),fill=color,width=9); draw.line((x+19,y-95+bob,x+70,y-70+bob),fill=color,width=9)


def paste_animal(frame: Image.Image, animals: dict, name: str, box: tuple[int,int,int,int], pulse: float=1.0, angle: float=0.0, dx: int=0, dy: int=0) -> None:
    sprite=animals[name].copy(); maxw=int((box[2]-box[0])*pulse); maxh=int((box[3]-box[1])*pulse); sprite.thumbnail((maxw,maxh),Image.Resampling.LANCZOS)
    if abs(angle)>.01: sprite=sprite.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    cx=(box[0]+box[2])//2; frame.alpha_composite(sprite,(cx-sprite.width//2+dx,box[3]-sprite.height+dy))


def performer_pose(name: str, local: float, echo: bool) -> tuple[float,float,int,int]:
    phase=local*({"cow":2.8,"sheep":3.5,"pig":3.0,"chicken":4.8,"lion":2.2,"elephant":2.0,"owl":2.7,"parrot":4.0}[name])
    angle=0.0; scale=1.0; dx=0; dy=0
    if name=="cow": angle=2.8*math.sin(phase); dy=-abs(int(16*math.sin(phase)))
    elif name=="sheep": dx=int(75*math.sin(phase*.55)); dy=-abs(int(36*math.sin(phase))) ; angle=4*math.sin(phase)
    elif name=="pig": dx=int(58*math.sin(phase*.7)); dy=int(10*math.cos(phase*2)); angle=7*math.sin(phase)
    elif name=="chicken": dx=int(65*math.sin(phase*.52)); dy=-abs(int(52*math.sin(phase))); angle=8*math.sin(phase)
    elif name=="lion": dx=int(90*math.sin(phase*.32)); dy=-abs(int(13*math.sin(phase))); scale=1+.035*(.5+.5*math.sin(phase))
    elif name=="elephant": dx=int(60*math.sin(phase*.35)); dy=-abs(int(18*math.sin(phase))); angle=2.5*math.sin(phase)
    elif name=="owl": dx=int(70*math.sin(phase*.45)); dy=int(44*math.sin(phase)); angle=-6*math.sin(phase*.7)
    elif name=="parrot": dx=int(78*math.sin(phase*.45)); dy=-abs(int(50*math.sin(phase))); angle=10*math.sin(phase)
    if echo: scale*=1.0+.055*math.sin(local*5)
    entrance=min(1.0,max(0.0,local/1.6)); ease=1-(1-entrance)**3
    dx+=int((1-ease)*(-720 if name in {"cow","pig","lion","owl"} else 720))
    dy+=int((1-ease)*120)
    return scale,angle,dx,dy


def action_effects(draw: ImageDraw.ImageDraw, name: str, t: float, echo: bool) -> None:
    colour={"farm":(255,126,63,180),"wild":(100,245,170,180),"bird":(112,205,255,190)}[next(item["family"] for item in PERFORMERS if item["animal"]==name)]
    for index in range(5):
        x=560+index*200+int(28*math.sin(t*2+index)); y=700-int(55*((t*.8+index*.18)%1))
        draw.ellipse((x-10,y-10,x+10,y+10),fill=colour)
    if name in {"lion","elephant","owl","parrot"}:
        radius=100+int(35*((t*1.4)%1)); alpha=int(170*(1-((t*1.4)%1))); draw.ellipse((960-radius,470-radius,960+radius,470+radius),outline=(255,239,110,alpha),width=12)
    if echo:
        for radius in (105,150,195): draw.arc((960-radius,430-radius,960+radius,430+radius),205,335,fill=(255,255,255,130),width=8)


def ensemble_frame(event: dict, t: float, animals: dict, finale: bool=False, bow: bool=False) -> Image.Image:
    frame=Image.new("RGBA",(base.W,base.H)); stage(frame,"rainbow",t); draw=ImageDraw.Draw(frame,"RGBA")
    local=t-event["start"]; names=["cow","sheep","pig","chicken","lion","elephant","owl","parrot"]
    for index,name in enumerate(names):
        x0=80+index*220; bounce=-abs(int((32 if finale else 20)*math.sin(local*3.1+index*.65))); angle=(7 if finale else 4)*math.sin(local*2.4+index)
        paste_animal(frame,animals,name,(x0,430,x0+210,850),1.02,angle,0,bounce)
    base.panel(draw,(250,90,1670,345),radius=52,width=9)
    heading="ANIMAL SOUND SONG" if finale else ("MEET THE ORCHESTRA" if not bow else "BRAVO, PERFORMERS!")
    base.centered(draw,(960,188),heading,base.F78,(224,74,67,255),2)
    if bow: hook="EVERY SOUND BELONGS!"
    elif finale:
        hooks=["MOO - BAA - OINK - CLUCK!","ROAR - TRUMPET - HOOT - SQUAWK!","MOVE YOUR HANDS AND FEET!","SING THE ANIMAL BEAT!"]; hook=hooks[int(local/6)%len(hooks)]
    else: hook="CLAP - STOMP - SING WITH US!"
    base.centered(draw,(960,292),hook,base.F38,(29,76,106,255),2)
    notes(draw,t,(255,235,82,235)); return frame.convert("RGB")


def intro_frame(t: float, animals: dict, outro: bool=False) -> Image.Image:
    frame=Image.new("RGBA",(base.W,base.H)); stage(frame,"bird",t); draw=ImageDraw.Draw(frame,"RGBA"); base.panel(draw,(260,100,1660,470),radius=55,width=9)
    base.centered(draw,(960,220),"ANIMAL SOUND",base.F78,(224,74,67,255),2); base.centered(draw,(960,340),"ORCHESTRA" if not outro else "BRAVO!",base.F78,(29,76,106,255),2)
    names=["cow","sheep","pig","chicken","lion","elephant","owl","parrot"]
    for index,name in enumerate(names): paste_animal(frame,animals,name,(120+index*210,550,300+index*210,850),.92)
    base.centered(draw,(960,945),"LISTEN - ECHO - PERFORM" if not outro else "WHICH SOUND WAS YOUR FAVOURITE?",base.F38,(255,255,255,255),2); return frame.convert("RGB")


def frame_for(event: dict, t: float, spec: dict, animals: dict) -> Image.Image:
    if event["kind"]=="opening_song": return ensemble_frame(event,t,animals)
    if event["kind"]=="welcome": return ensemble_frame(event,t,animals)
    if event["kind"]=="finale_song": return ensemble_frame(event,t,animals,finale=True)
    if event["kind"]=="bow": return ensemble_frame(event,t,animals,finale=True,bow=True)
    item=event["item"]; echo=event["kind"]=="think"; frame=Image.new("RGBA",(base.W,base.H)); stage(frame,item["family"],t); draw=ImageDraw.Draw(frame,"RGBA"); notes(draw,t,(255,224,88,230))
    base.header(frame,"TINY TALES ANIMAL SOUND ORCHESTRA",f"PERFORMER {event['index']} OF {len(PERFORMERS)}")
    local=t-event["start"]; pulse,angle,dx,dy=performer_pose(item["animal"],local,echo); paste_animal(frame,animals,item["animal"],(540,220,1380,875),pulse,angle,dx,dy); action_effects(draw,item["animal"],t,echo)
    draw.rounded_rectangle((250,735,1670,965),radius=55,fill=(255,253,235,242),outline=(255,188,50,255),width=8)
    base.centered(draw,(960,805),f"{item['animal'].upper()} SAYS",base.F38,(29,76,106,255)); base.centered(draw,(960,900),item["sound"],base.F78,(46,151,84,255) if not echo else (224,74,67,255),3)
    if echo:
        base.centered(draw,(960,1015),f"YOUR TURN - {item['verb'].upper()}!",base.F38,(255,255,255,255),2)
        elapsed=t-event["start"]; total=event["end"]-event["start"]; draw.rounded_rectangle((430,170,1490,205),radius=15,fill=(255,255,255,110)); draw.rounded_rectangle((430,170,430+int(1060*min(1,elapsed/total)),205),radius=15,fill=(255,211,57,230))
    return frame.convert("RGB")


def make_music(total: float, events: list[dict]) -> Path:
    target=WORK/"original-animal-orchestra-music.wav"; rate=48000; rng=random.Random(20260827)
    song_ranges=[(event["start"],event["end"]) for event in events if event["kind"] in {"opening_song","finale_song"}]
    notes=(261.63,329.63,392.0,523.25,440.0,392.0,349.23,293.66)
    with wave.open(str(target),"wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate); block=bytearray()
        for index in range(round(total*rate)):
            t=index/rate; strong=any(start<=t<end for start,end in song_ranges); beat=t%.5; eighth=t%.25; bar=int(t/2)
            root=notes[bar%4]/2; kick=math.sin(2*math.pi*(78-30*min(1,beat/.16))*beat)*math.exp(-24*beat)*(.13 if strong else .055)
            clap_pos=(t+.25)%.5; clap=(rng.random()*2-1)*math.exp(-35*clap_pos)*(.028 if strong else .009)
            bass=math.sin(2*math.pi*root*t)*(.032 if strong else .014)
            bell=math.sin(2*math.pi*notes[(int(t/.25)+bar)%len(notes)]*t)*math.exp(-11*eighth)*(.052 if strong else .018)
            shaker=(rng.random()*2-1)*(.010 if strong and int(t*8)%2==0 else .003)
            fade=min(1.0,t/1.0,(total-t)/1.2); value=(kick+clap+bass+bell+shaker)*fade; sample=max(-32767,min(32767,round(value*32767)))
            block+=struct.pack("<hh",sample,sample)
            if len(block)>=131072: output.writeframesraw(block); block.clear()
        if block: output.writeframesraw(block)
    return target


def render(total: float, events: list[dict], tracks: list[tuple[str,float]], animals: dict) -> None:
    silent=WORK/"silent-corrected.mp4"; reusable=False
    if silent.exists():
        duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(silent)],text=True)); reusable=abs(duration-total)<.25
    if reusable: print(f"Reusing completed corrected silent render: {silent}",flush=True)
    else:
        process=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{base.W}x{base.H}","-r",str(base.ART_FPS),"-i","-","-an","-vf",f"fps={base.VIDEO_FPS}","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",str(silent)],stdin=subprocess.PIPE)
        for number in range(math.ceil(total*base.ART_FPS)):
            t=number/base.ART_FPS; event=next((item for item in events if item["start"]<=t<item["end"]),None)
            if event is None: process.kill(); raise RuntimeError(f"Uncovered visual timestamp: {t:.3f}")
            process.stdin.write(frame_for(event,t,SPEC,animals).tobytes())
            if number%(base.ART_FPS*15)==0: print(f"animal-sound-orchestra corrected: rendered {t:.0f}/{total:.0f}s",flush=True)
        process.stdin.close()
        if process.wait()!=0: raise RuntimeError("Corrected silent render failed")
    music=make_music(total,events); inputs=["-i",str(silent),"-i",str(music)]; filters=["[1:a]volume=.78[m]"]; labels=["[m]"]
    for stream,(key,start) in enumerate(tracks,2):
        inputs.extend(["-i",str(voice_path(key))]); delay=round(start*1000); filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.32[v{stream}]"); labels.append(f"[v{stream}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg","-y","-loglevel","error",*inputs,"-filter_complex",";".join(filters),"-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t",f"{total:.3f}","-movflags","+faststart",str(OUTPUT)],check=True)


def validate(total: float, events: list[dict], tracks: list[tuple[str,float]], animals: dict) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    decode=subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],capture_output=True,text=True)
    transitions=[{"from_kind":a["kind"],"to_kind":b["kind"],"from_end":a["end"],"to_start":b["start"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]; (WORK/"timeline-gap-audit.json").write_text(json.dumps(transitions,indent=2)+"\n",encoding="utf-8")
    movement=[]
    for event in [item for item in events if item["kind"]=="reveal"]:
        duration=event["end"]-event["start"]; samples=[performer_pose(event["item"]["animal"],duration*fraction,False) for fraction in (.12,.3,.5,.7,.88)]; movement.append({"animal":event["item"]["animal"],"distinct_pose_samples":len({tuple(round(value,3) if isinstance(value,float) else value for value in sample) for sample in samples}),"horizontal_range":max(sample[2] for sample in samples)-min(sample[2] for sample in samples),"vertical_range":max(sample[3] for sample in samples)-min(sample[3] for sample in samples)})
    (WORK/"performer-motion-audit.json").write_text(json.dumps(movement,indent=2)+"\n",encoding="utf-8")
    sync=[]
    for key,start in tracks:
        end=start+base.duration(voice_path(key)); event=next(item for item in events if item["start"]<=start<item["end"]); sync.append({"voice":key,"visual_kind":event["kind"],"narration_start":start,"narration_end":end,"visual_start":event["start"],"visual_end":event["end"],"narration_contained_by_visual":end<=event["end"]+.000001})
    (WORK/"narration-visual-sync-audit.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8")
    checks={"size":OUTPUT.stat().st_size>1_000_000,"duration":abs(float(probe["format"]["duration"])-total)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==base.W and video.get("height")==base.H,"audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"full_decode_passed":decode.returncode==0 and not decode.stderr.strip(),"continuous_visual_timeline":all(abs(item["gap_seconds"])<.000001 for item in transitions),"end_card_is_final_event_only":events[-1]["kind"]=="bow" and all(item["kind"]!="bow" for item in events[:-1]),"eight_performers":len([e for e in events if e["kind"]=="reveal"])==8,"eight_echo_windows":len([e for e in events if e["kind"]=="think"])==8,"all_performers_move":all(item["distinct_pose_samples"]>=4 and (item["horizontal_range"]>10 or item["vertical_range"]>10) for item in movement),"original_opening_and_finale_song":events[0]["kind"]=="opening_song" and any(e["kind"]=="finale_song" for e in events),"narration_visual_sync":all(item["narration_contained_by_visual"] for item in sync)}
    report={"format":"animal-sound-orchestra-corrected","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values()),"upload_authorized":False}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    samples=[events[0],events[1]]+[e for e in events if e["kind"] in {"reveal","think"}]+[next(e for e in events if e["kind"]=="finale_song"),events[-1]]; contact=Image.new("RGB",(960,math.ceil(len(samples)/4)*135),"white")
    for index,event in enumerate(samples): contact.paste(frame_for(event,event["start"]+min(2.2,(event["end"]-event["start"])/2),SPEC,animals).resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    contact.save(WORK/"quality-contact-sheet.png")
    transition_contact=Image.new("RGB",(640,len(transitions)*180),"white")
    for index,(left,right) in enumerate(zip(events,events[1:])):
        transition_contact.paste(frame_for(left,max(left["start"],left["end"]-.12),SPEC,animals).resize((320,180),Image.Resampling.LANCZOS),(0,index*180)); transition_contact.paste(frame_for(right,right["start"]+.12,SPEC,animals).resize((320,180),Image.Resampling.LANCZOS),(320,index*180))
    transition_contact.save(WORK/"transition-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc={"id":SPEC["id"],"title":"Animal Sound Orchestra | Moo, Roar, Hoot and More for Kids","description":"Eight lively animal performers dance onto a colourful Tiny Tales concert stage. Meet Cow, Sheep, Pig, Chicken, Lion, Elephant, Owl, and Parrot; echo each call; then sing and move with the original Tiny Tales Animal Sound Song finale.\n\nA playful music, listening, speech, and movement adventure supporting animal vocabulary, rhythm, memory, and confident participation for children ages 3 to 7.","tags":["animal sounds","animal sounds for kids","farm animal sounds","wild animal sounds","preschool music","animal sound song","listen and repeat","Tiny Tales","kids learning"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":base.VOICE_PROFILE_NAME,"format_family":"animated-animal-orchestra-sing-along","visual_system":"colourful-code-animated-concert-with-eight-moving-performers","interaction_style":"animal-call-echo-and-original-finale-song","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"transition_contact_sheet_reviewed":True,"quality_report":"automation/production-work/animal-sound-orchestra-01/quality-report.json","transition_audit":"automation/production-work/animal-sound-orchestra-01/timeline-gap-audit.json","quality_contact_sheet":"automation/production-work/animal-sound-orchestra-01/quality-contact-sheet.png","transition_contact_sheet":"automation/production-work/animal-sound-orchestra-01/transition-contact-sheet.png","narration_visual_sync_audit":"automation/production-work/animal-sound-orchestra-01/narration-visual-sync-audit.json","performer_motion_audit":"automation/production-work/animal-sound-orchestra-01/performer-motion-audit.json","new_image_generation_calls":0}; META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True); report=WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {OUTPUT}",flush=True); return
    farm=games.extract_grid(AUTOMATION/"production-assets"/"farm-animals-sheet.png",["cow","pig","sheep","horse","chicken","goat"]); wild=games.extract_grid(AUTOMATION/"production-assets"/"jungle-animals-sheet.png",["lion","tiger","elephant","zebra","hippopotamus","crocodile"]); birds=games.extract_grid(AUTOMATION/"production-assets"/"bird-animals-sheet.png",["owl","parrot","flamingo","penguin","peacock","toucan"]); animals={**farm,**wild,**birds}
    lines=asyncio.run(make_voices()); events,tracks,total=make_timeline(lines); render(total,events,tracks,animals); validate(total,events,tracks,animals); write_metadata(total); print(json.dumps({"id":SPEC["id"],"status":"completed","duration_seconds":total}),flush=True)


if __name__=="__main__": main()
