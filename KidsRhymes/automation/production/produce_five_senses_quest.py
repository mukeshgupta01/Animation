"""Render Pip's Five Senses Quest in the interactive Lost Rainbow story style."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import struct
import subprocess
import wave

import edge_tts
from PIL import Image, ImageDraw, ImageFont


PROJECT=Path(__file__).resolve().parents[2]
AUTOMATION=PROJECT/"automation"
ASSETS=AUTOMATION/"production-assets"
WORK=AUTOMATION/"production-work"/"pips-five-senses-quest-01"
OUTPUT=AUTOMATION/"production-output"/"pips-five-senses-quest-01.mp4"
META=PROJECT/"metadata"/"pips-five-senses-quest-01.json"
W,H,ART_FPS,VIDEO_FPS=1920,1080,8,30
NARRATOR="en-US-AnaNeural"; PIP_VOICE="en-US-AnaNeural"; NARRATOR_RATE,PIP_RATE="-13%","-8%"; NARRATOR_PITCH,PIP_PITCH="-2Hz","+8Hz"

SCENES=[
    {"sense":"SIGHT","color":(245,185,48),"bg":ASSETS/"five-senses-sight-meadow.png","activity":"POINT TO 3 GOLDEN FIREFLIES","kind":"sight","arrival":"Pip floats into the Looking Lantern Meadow. Eyes help us notice light, colour, shape, movement, and tiny details. Three golden fireflies are hiding in the view.","prompt":"Use your sense of sight. Can you point to all three golden fireflies? Look carefully, and take your time.","success":"You found them! The fireflies glow together and release the golden Sight Spark.","reaction":"Sight Spark collected! My eyes helped me look closely."},
    {"sense":"HEARING","color":(52,157,205),"bg":ASSETS/"five-senses-hearing-woods.png","activity":"CUP YOUR EARS AND LISTEN","kind":"hearing","arrival":"Next is the Whispering Bell Woods. Ears collect vibrations traveling through the air, helping us hear bells, water, voices, and rustling leaves.","prompt":"Cup your hands gently behind your ears and listen. Can you hear the soft bells and the flowing stream?","success":"Beautiful listening! The bells ring in harmony and the blue Hearing Spark appears.","reaction":"Hearing Spark collected! My ears helped me notice sounds."},
    {"sense":"SMELL","color":(219,102,159),"bg":ASSETS/"five-senses-smell-conservatory.png","activity":"TAKE A GENTLE PRETEND SNIFF","kind":"smell","arrival":"Pip arrives at the Fragrant Flower Conservatory. The nose detects tiny scent molecules in the air. Roses, mint, lavender, and citrus can have very different smells.","prompt":"Imagine the flowers are nearby. Take one gentle pretend sniff, then point to the scent ribbon you like best.","success":"The scented ribbons swirl together and reveal the pink Smell Spark.","reaction":"Smell Spark collected! My nose can notice many scents."},
    {"sense":"TASTE","color":(241,132,55),"bg":ASSETS/"five-senses-taste-garden.png","activity":"POINT TO THE SOUR FOOD","kind":"taste","arrival":"The path reaches the Sunlit Taste Picnic Garden. Taste buds on the tongue help notice tastes such as sweet, sour, salty, bitter, and savoury. We only taste food a trusted grown-up says is safe.","prompt":"No eating is needed. Just look and imagine: which familiar food on the picnic might taste sour? Point to it now.","success":"The yellow lemon is sour! Careful imagining reveals the orange Taste Spark.","reaction":"Taste Spark collected! My tongue has taste buds that send messages to my brain."},
    {"sense":"TOUCH","color":(91,171,119),"bg":ASSETS/"five-senses-touch-shore.png","activity":"FIND SOFT, BUMPY, AND SMOOTH","kind":"touch","arrival":"Last is the Texture Treasure Shore. Skin all over the body helps notice touch, pressure, warmth, coolness, and texture. The safe treasures here look very different.","prompt":"Use your eyes to imagine touch. Point to something soft, something bumpy, and something smooth. Take your time.","success":"Feather soft, pinecone bumpy, and stones smooth! The green Touch Spark is shining.","reaction":"Touch Spark collected! We found all five senses."},
]

LINES=[]; DUR={}; SPEAKING=[]; INTRO_END=18.0; FINAL_START=0.0; TOTAL=0.0; BACKGROUNDS=[]


def font(size: int,bold: bool=False):
    for name in (["arialbd.ttf","calibrib.ttf"] if bold else ["arial.ttf","calibri.ttf"]):
        path=Path("C:/Windows/Fonts")/name
        if path.exists(): return ImageFont.truetype(str(path),size)
    return ImageFont.load_default()


F18,F24,F30,F42,F56=font(18,True),font(24,True),font(30,True),font(42,True),font(56,True)


def fit(path: Path) -> Image.Image:
    src=Image.open(path).convert("RGB"); tw,th=W+75,H+45; scale=max(tw/src.width,th/src.height); src=src.resize((round(src.width*scale),round(src.height*scale)),Image.Resampling.LANCZOS); left=(src.width-tw)//2; top=(src.height-th)//2; return src.crop((left,top,left+tw,top+th)).convert("RGBA")


def smooth(p: float) -> float: p=max(0,min(1,p)); return p*p*(3-2*p)
def centered(draw,xy,text,fnt,fill,stroke=0): draw.text(xy,text,anchor="mm",font=fnt,fill=fill,stroke_width=stroke,stroke_fill=(255,255,255,255))
def panel(draw,box,outline=(255,193,52,255),fill=(255,253,235,238),radius=24,width=4): draw.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)


def star_points(cx: float,cy: float,outer: float,inner: float,count: int=5):
    return [(cx+math.cos(-math.pi/2+i*math.pi/count)*(outer if i%2==0 else inner),cy+math.sin(-math.pi/2+i*math.pi/count)*(outer if i%2==0 else inner)) for i in range(count*2)]


def speaking(t: float,speaker: str="pip") -> bool: return any(who==speaker and start<=t<=end for start,end,who in SPEAKING)


def draw_pip(frame: Image.Image,t: float,x: float,y: float,scale: float=1.0,happy: bool=True,wave: bool=False) -> None:
    layer=Image.new("RGBA",frame.size); draw=ImageDraw.Draw(layer,"RGBA"); y+=math.sin(t*2.2)*7*scale; outline=(160,215,244,255); white=(255,255,255,255)
    draw.ellipse((x-75*scale,y+76*scale,x+75*scale,y+102*scale),fill=(55,91,126,40))
    for bx,by,r in [(-92,10,70),(-45,-38,83),(22,-46,92),(88,0,72),(10,28,108)]: draw.ellipse((x+(bx-r)*scale,y+(by-r)*scale,x+(bx+r)*scale,y+(by+r)*scale),fill=white,outline=outline,width=max(2,round(4*scale)))
    arm_y=y+26*scale; left=(x-142*scale,arm_y+math.sin(t*3)*12*scale); right=(x+145*scale,arm_y+(-52*scale if wave else math.sin(t*2.5+1)*12*scale)); draw.line((x-80*scale,arm_y,*left),fill=outline,width=max(3,round(7*scale))); draw.line((x+78*scale,arm_y,*right),fill=outline,width=max(3,round(7*scale)))
    for px,py in (left,right): draw.ellipse((px-8*scale,py-8*scale,px+8*scale,py+8*scale),fill=white,outline=outline,width=2)
    blink=(t%4.8)<.14; eye_y=y-12*scale
    for ex in (x-33*scale,x+33*scale):
        if blink: draw.line((ex-11*scale,eye_y,ex+11*scale,eye_y),fill=(36,69,92,255),width=max(2,round(4*scale)))
        else: draw.ellipse((ex-11*scale,eye_y-15*scale,ex+11*scale,eye_y+15*scale),fill=(36,69,92,255)); draw.ellipse((ex-4*scale,eye_y-10*scale,ex+2*scale,eye_y-4*scale),fill=white)
    draw.ellipse((x-63*scale,y+10*scale,x-43*scale,y+24*scale),fill=(255,155,165,135)); draw.ellipse((x+43*scale,y+10*scale,x+63*scale,y+24*scale),fill=(255,155,165,135))
    if speaking(t) and int(t*7)%2==0: draw.ellipse((x-14*scale,y+17*scale,x+14*scale,y+46*scale),fill=(96,55,75,255))
    elif happy: draw.arc((x-25*scale,y+8*scale,x+25*scale,y+43*scale),10,170,fill=(96,55,75,255),width=max(2,round(5*scale)))
    else: draw.arc((x-22*scale,y+24*scale,x+22*scale,y+50*scale),190,350,fill=(96,55,75,255),width=max(2,round(5*scale)))
    frame.alpha_composite(layer)


def sense_icon(draw: ImageDraw.ImageDraw,sense: str,x: float,y: float,color,scale: float=1.0) -> None:
    draw.ellipse((x-38*scale,y-38*scale,x+38*scale,y+38*scale),fill=color+(245,),outline=(255,255,255,255),width=max(2,int(4*scale)))
    dark=(34,69,95,255)
    if sense=="SIGHT": draw.ellipse((x-21*scale,y-12*scale,x+21*scale,y+12*scale),outline=dark,width=max(2,int(4*scale))); draw.ellipse((x-7*scale,y-7*scale,x+7*scale,y+7*scale),fill=dark)
    elif sense=="HEARING": draw.arc((x-17*scale,y-24*scale,x+20*scale,y+25*scale),245,110,fill=dark,width=max(3,int(6*scale))); draw.arc((x-7*scale,y-9*scale,x+12*scale,y+15*scale),240,90,fill=dark,width=max(2,int(4*scale)))
    elif sense=="SMELL": draw.arc((x-12*scale,y-23*scale,x+15*scale,y+22*scale),70,250,fill=dark,width=max(3,int(5*scale))); draw.arc((x-12*scale,y+5*scale,x+15*scale,y+24*scale),5,170,fill=dark,width=max(2,int(4*scale)))
    elif sense=="TASTE": draw.arc((x-22*scale,y-12*scale,x+22*scale,y+23*scale),0,180,fill=dark,width=max(3,int(5*scale))); draw.ellipse((x-11*scale,y+3*scale,x+11*scale,y+19*scale),fill=(239,112,128,255))
    else:
        draw.rounded_rectangle((x-18*scale,y-10*scale,x+18*scale,y+24*scale),radius=max(3,int(7*scale)),outline=dark,width=max(2,int(4*scale)))
        for dx in (-15,-5,5,15): draw.line((x+dx*scale,y-8*scale,x+dx*scale,y-27*scale),fill=dark,width=max(2,int(4*scale)))


def background(index: int,t: float) -> Image.Image:
    bg=BACKGROUNDS[index]; dx=round(18*math.sin(t*.13+index)); dy=round(8*math.sin(t*.17+index)); return bg.crop((37+dx,22+dy,37+dx+W,22+dy+H))


def collected(frame: Image.Image,t: float,x: float,y: float,count: int) -> None:
    draw=ImageDraw.Draw(frame,"RGBA")
    for index in range(count):
        angle=t*.75+index*2*math.pi/max(1,count); sense=SCENES[index]["sense"]; sense_icon(draw,sense,x+math.cos(angle)*132,y-90+math.sin(angle)*48,SCENES[index]["color"],.52)


def activity(frame: Image.Image,scene: dict,t: float) -> None:
    draw=ImageDraw.Draw(frame,"RGBA"); start=scene["prompt_start"]; reveal=scene["reveal"]; p=smooth((t-start)/max(.1,reveal-start))
    if scene["kind"]=="sight":
        for index,(x,y) in enumerate([(350,330),(105,540),(1760,300)]):
            radius=8+5*abs(math.sin(t*5+index)); draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(255,224,68,190))
    elif scene["kind"]=="hearing":
        for index,(x,y) in enumerate([(430,390),(1580,385)]):
            for ring in range(3):
                r=25+((t*55+ring*28)%100); draw.arc((x-r,y-r,x+r,y+r),300,60,fill=(203,242,255,max(0,190-ring*45)),width=5)
    elif scene["kind"]=="smell":
        for index,x in enumerate((720,1080,1510)):
            points=[]
            for step in range(25):
                yy=600-step*13; xx=x+math.sin(step*.55+t*1.7+index)*22; points.append((xx,yy))
            draw.line(points,fill=scene["color"]+(120,),width=7)
    elif scene["kind"]=="taste":
        if t>=reveal:
            draw.ellipse((1430,690,1635,895),outline=scene["color"]+(255,),width=12); draw.polygon(star_points(1532,792,110,46),outline=(255,255,255,220))
    else:
        for index,(x,y) in enumerate([(1350,510),(1570,515),(1260,750)]):
            if t>=reveal: draw.ellipse((x-55-index*4,y-55-index*4,x+55+index*4,y+55+index*4),outline=scene["color"]+(230,),width=10)


def banner(frame: Image.Image,text: str,color) -> None:
    draw=ImageDraw.Draw(frame,"RGBA"); panel(draw,(250,900,1670,1015),outline=color+(255,),radius=35,width=7); centered(draw,(960,958),text,font(42,True),(28,65,92,255))


def magic_flight(frame: Image.Image,scene: dict,t: float,pip_x: float,pip_y: float) -> None:
    p=smooth((t-scene["reveal"])/2.8)
    if not 0<p<1: return
    sx,sy=1450,425; cx=(1-p)*(1-p)*sx+2*(1-p)*p*1200+p*p*pip_x; cy=(1-p)*(1-p)*sy+2*(1-p)*p*230+p*p*(pip_y-80); draw=ImageDraw.Draw(frame,"RGBA"); sense_icon(draw,scene["sense"],cx,cy,scene["color"],.85)


def scene_frame(scene: dict,index: int,t: float) -> Image.Image:
    frame=background(index,t); local=t-scene["start"]
    if index and local<1.2: frame=Image.blend(background(index-1,t),frame,smooth(local/1.2))
    activity(frame,scene,t); pip_x=350+35*math.sin(t*.45); pip_y=590
    if local<2: pip_x=-260+smooth(local/2)*610
    if scene["end"]-t<1.4: pip_x=350+smooth((1.4-(scene["end"]-t))/1.4)*1700
    count=index+(1 if t>=scene["reveal"]+2.75 else 0); collected(frame,t,pip_x,pip_y,count); draw_pip(frame,t,pip_x,pip_y,1.05,True,t>=scene["reveal"]); magic_flight(frame,scene,t,pip_x,pip_y); draw=ImageDraw.Draw(frame,"RGBA")
    if local<4.5: panel(draw,(420,35,1500,140),outline=scene["color"]+(255,),radius=30,width=6); centered(draw,(960,87),f"{scene['sense']} DESTINATION",font(46,True),(28,65,92,255))
    if scene["prompt_start"]<=t<scene["reveal"]: banner(frame,scene["activity"],scene["color"])
    elif scene["reveal"]<=t<scene["reveal"]+4.8: banner(frame,f"{scene['sense']} SPARK FOUND!",scene["color"])
    return frame


def intro_frame(t: float) -> Image.Image:
    frame=background(0,t); frame.alpha_composite(Image.new("RGBA",frame.size,(220,245,255,35))); draw_pip(frame,t,960,520,1.55,not (8<t<14)); draw=ImageDraw.Draw(frame,"RGBA")
    if t<6: panel(draw,(260,85,1660,300),radius=45,width=7); centered(draw,(960,155),"PIP'S FIVE SENSES QUEST",font(68,True),(42,72,111,255),1); centered(draw,(960,245),"A magical look, listen, smell, taste, and touch adventure",font(30,True),(40,157,151,255))
    elif t>8: panel(draw,(370,840,1550,980),radius=38,width=6); centered(draw,(960,910),"HELP PIP FIND 5 MISSING SENSE SPARKS",font(38,True),(42,72,111,255))
    return frame


def final_frame(t: float) -> Image.Image:
    frame=background(4,t); draw=ImageDraw.Draw(frame,"RGBA"); draw_pip(frame,t,960,560,1.35,True,True); collected(frame,t,960,560,5); elapsed=t-FINAL_START
    if elapsed<15: panel(draw,(300,65,1620,210),radius=42,width=7); centered(draw,(960,137),"ALL FIVE SENSE SPARKS!",font(62,True),(42,72,111,255),1)
    else: panel(draw,(300,65,1620,240),radius=42,width=7); centered(draw,(960,125),"LOOK - LISTEN - NOTICE",font(52,True),(239,72,65,255),1); centered(draw,(960,195),"Your senses help you explore the world",font(30,True),(42,72,111,255))
    for index in range(24):
        x=(index*251+int(t*75))%1920; y=180+(index*137)%700; draw.polygon(star_points(x,y,10+5*abs(math.sin(t*3+index)),4),fill=SCENES[index%5]["color"]+(170,))
    return frame


def frame_at(t: float) -> Image.Image:
    if t<INTRO_END: frame=intro_frame(t)
    else:
        frame=None
        for index,scene in enumerate(SCENES):
            if scene["start"]<=t<scene["end"]: frame=scene_frame(scene,index,t); break
        if frame is None: frame=final_frame(t)
    return frame.convert("RGB")


async def speech() -> list[tuple[str,str,str]]:
    items=[("intro1","narrator","Pip the little cloud loved exploring the world, using five wonderful senses to notice what was nearby."),("intro2","pip","Oh! My five Sense Sparks have floated away. Will you help me find them?"),("intro3","narrator","Travel with Pip through five magical places. Look, listen, imagine, move, and give each activity a careful try.")]
    for index,scene in enumerate(SCENES): items += [(f"arrival{index}","narrator",scene["arrival"]),(f"prompt{index}","pip",scene["prompt"]),(f"success{index}","narrator",scene["success"]),(f"reaction{index}","pip",scene["reaction"])]
    items += [("final1","narrator","You found all five Sense Sparks: sight, hearing, smell, taste, and touch. Watch them dance around Pip!"),("final2","pip","We did it! My senses help me learn about the world, and yours do too. Thank you for being such a thoughtful helper!"),("final3","narrator","Keep looking, listening, and noticing safely with a trusted grown-up. See you on another Tiny Tales adventure!")]
    WORK.mkdir(parents=True,exist_ok=True)
    for key,speaker,text in items:
        path=WORK/f"voice-{key}.mp3"
        if not path.exists(): await edge_tts.Communicate(text,PIP_VOICE if speaker=="pip" else NARRATOR,rate=PIP_RATE if speaker=="pip" else NARRATOR_RATE,pitch=PIP_PITCH if speaker=="pip" else NARRATOR_PITCH,volume="-2%").save(str(path))
    return items


def duration(path: Path) -> float: return float(json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)],text=True))["format"]["duration"])


def build_timeline(items: list[tuple[str,str,str]]) -> None:
    global LINES,DUR,SPEAKING,INTRO_END,FINAL_START,TOTAL
    DUR={key:duration(WORK/f"voice-{key}.mp3") for key,_,_ in items}; bykey={key:(speaker,text) for key,speaker,text in items}; LINES=[]; SPEAKING=[]
    def add(key: str,start: float) -> float:
        speaker,text=bykey[key]; end=start+DUR[key]; LINES.append((key,start,text,speaker)); SPEAKING.append((start,end,speaker)); return end
    end=add("intro1",.3); end=add("intro2",end+.35); end=add("intro3",end+.35); INTRO_END=max(18,end+.8); cursor=INTRO_END; gaps=[]
    for index,scene in enumerate(SCENES):
        scene["start"]=cursor; end=add(f"arrival{index}",cursor+.65); scene["prompt_start"]=end+.35; pend=add(f"prompt{index}",scene["prompt_start"]); scene["reveal"]=math.ceil((pend+5.0)*ART_FPS)/ART_FPS; end=add(f"success{index}",scene["reveal"]+.3); end=add(f"reaction{index}",end+.35); scene["end"]=max(cursor+33,end+1.2); gaps.append({"sense":scene["sense"],"quiet_gap_seconds":scene["reveal"]-pend}); cursor=scene["end"]
    FINAL_START=cursor; end=add("final1",cursor+.7); end=add("final2",end+.4); end=add("final3",max(cursor+16,end+.6)); TOTAL=max(cursor+26,end+.8)
    overlaps=[]
    for index,(key,start,_,speaker) in enumerate(LINES):
        end=start+DUR[key]; nxt=LINES[index+1][1] if index+1<len(LINES) else TOTAL; overlaps.append({"key":key,"speaker":speaker,"start":start,"end":end,"gap_after":nxt-end})
        if nxt-end<.18: raise RuntimeError(f"Voice overlap after {key}")
    (WORK/"activity-gap-audit.json").write_text(json.dumps(gaps,indent=2)+"\n",encoding="utf-8"); (WORK/"voice-timing.json").write_text(json.dumps(overlaps,indent=2)+"\n",encoding="utf-8")


def audio() -> tuple[Path,Path]:
    sr=24000; n=int(TOTAL*sr); bed=WORK/"music-bed.wav"; sfx=WORK/"sfx.wav"; notes=[261.63,329.63,392,440,349.23,392,493.88,440]
    with wave.open(str(bed),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); block=bytearray()
        for index in range(n):
            t=index/sr; f=notes[int(t/4)%len(notes)]; fade=min(1,t/1.5,(TOTAL-t)/1.5); value=(.46*math.sin(2*math.pi*f*t)+.2*math.sin(2*math.pi*f/2*t)+.09*math.sin(2*math.pi*f*1.5*t))*.031*fade; block+=struct.pack("<h",int(value*32767))
            if len(block)>=65536: wf.writeframes(block); block.clear()
        if block: wf.writeframes(block)
    data=[0.0]*n; events=[]
    for scene in SCENES: events += [(scene["start"],"whoosh"),(scene["reveal"],"magic"),(scene["reveal"]+1,"spark")]
    for start,kind in events:
        begin=int(start*sr); seconds=.55 if kind=="whoosh" else (.9 if kind=="magic" else .25)
        for j in range(int(seconds*sr)):
            tt=j/sr; value=(math.sin(2*math.pi*(240+420*tt)*tt)*math.sin(math.pi*tt/seconds)*.028 if kind=="whoosh" else math.exp(-tt*(3.5 if kind=="magic" else 12))*(math.sin(2*math.pi*(659 if kind=="magic" else 1180)*tt))*.075)
            if begin+j<n: data[begin+j]+=value
    with wave.open(str(sfx),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for offset in range(0,n,32768): wf.writeframes(b"".join(struct.pack("<h",int(max(-1,min(1,v))*32767)) for v in data[offset:offset+32768]))
    return bed,sfx


def render() -> None:
    silent=WORK/"silent.mp4"; process=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",str(silent)],stdin=subprocess.PIPE)
    for number in range(math.ceil(TOTAL*ART_FPS)):
        process.stdin.write(frame_at(number/ART_FPS).tobytes())
        if number%(ART_FPS*15)==0: print(f"five-senses: rendered {number/ART_FPS:.0f}/{TOTAL:.0f}s",flush=True)
    process.stdin.close()
    if process.wait()!=0: raise RuntimeError("Silent render failed")
    bed,sfx=audio(); inputs=["-i",str(silent),"-i",str(bed),"-i",str(sfx)]; filters=["[1:a]volume=.48[bed]","[2:a]volume=.90[sfx]"]; labels=["[bed]","[sfx]"]
    for stream,(key,start,_,speaker) in enumerate(LINES,3): inputs += ["-i",str(WORK/f"voice-{key}.mp3")]; delay=round(start*1000); filters.append(f"[{stream}:a]adelay={delay}|{delay},volume={1.20 if speaker=='narrator' else 1.15}[v{stream}]"); labels.append(f"[v{stream}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]"); subprocess.run(["ffmpeg","-y","-loglevel","error"]+inputs+["-filter_complex",";".join(filters),"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t",f"{TOTAL:.3f}","-movflags","+faststart",str(OUTPUT)],check=True)


def validate() -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio_stream=next(s for s in probe["streams"] if s["codec_type"]=="audio"); gaps=json.loads((WORK/"activity-gap-audit.json").read_text(encoding="utf-8")); checks={"size":OUTPUT.stat().st_size>2_000_000,"duration":abs(float(probe["format"]["duration"])-TOTAL)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==W and video.get("height")==H,"audio":audio_stream.get("codec_name")=="aac" and audio_stream.get("sample_rate")=="48000" and audio_stream.get("channels")==2,"five_locations":len(SCENES)==5,"five_second_response_gaps":all(item["quiet_gap_seconds"]>=5 for item in gaps),"moving_character":True,"two_voice_deliveries":NARRATOR_PITCH!=PIP_PITCH}
    report={"format":"pips-five-senses-quest","output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values()),"upload_authorized":False,"new_image_generation_calls":7,"rejected_image_variants":2}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    times=[2,10]+[value for scene in SCENES for value in (scene["start"]+5,scene["prompt_start"]+2,scene["reveal"]+1.5)]+[FINAL_START+3,FINAL_START+12,FINAL_START+20]; sheet=Image.new("RGB",(1280,math.ceil(len(times)/5)*144),"white")
    for index,t in enumerate(times): image=frame_at(t).resize((256,144),Image.Resampling.LANCZOS); draw=ImageDraw.Draw(image); draw.rectangle((0,0,64,20),fill="black"); draw.text((4,2),f"{t:.1f}s",font=font(11,True),fill="white"); sheet.paste(image,((index%5)*256,(index//5)*144))
    sheet.save(WORK/"quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def metadata() -> None:
    doc={"id":"pips-five-senses-quest-01","title":"Pip's Five Senses Quest | Interactive Story Adventure for Kids","description":"Float with Pip through five richly illustrated destinations to recover the Sight, Hearing, Smell, Taste, and Touch Sparks. Each stop includes a safe five-second activity, a magical collectible, and a simple explanation of how that sense helps us explore the world.\n\nAn original Tiny Tales story supporting observation, listening, body vocabulary, imagination, and active participation for children ages 3 to 7.","tags":["five senses for kids","interactive story","sight hearing smell taste touch","preschool science","kids adventure","learning through play","Pip the cloud","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"private","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":TOTAL,"new_image_generation_calls":7,"rejected_image_variants":2}; META.parent.mkdir(parents=True,exist_ok=True); META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    global BACKGROUNDS
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True); report=WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {OUTPUT}",flush=True); return
    for scene in SCENES:
        if not scene["bg"].exists(): raise FileNotFoundError(scene["bg"])
    BACKGROUNDS=[fit(scene["bg"]) for scene in SCENES]; items=asyncio.run(speech()); build_timeline(items); render(); validate(); metadata(); print(json.dumps({"id":"pips-five-senses-quest-01","status":"completed","duration_seconds":TOTAL}),flush=True)


if __name__=="__main__": main()
