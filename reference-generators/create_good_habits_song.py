import asyncio
import json
import math
import struct
import subprocess
import wave
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "good-habits-song-work"
OUTPUT = ROOT / "good-habits-every-day-song.mp4"
SILENT = WORK / "good-habits-silent.mp4"
CONTACT = ROOT / "good-habits-song-contact-sheet.png"
W, H, ART_FPS, VIDEO_FPS = 1280, 720, 8, 24
VOICE = "en-US-AnaNeural"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT = "C:/Windows/Fonts/arial.ttf"

BACKGROUNDS = {
    "bedroom": ROOT / "habit-bedroom.png",
    "bathroom": ROOT / "habit-bathroom.png",
    "kitchen": ROOT / "habit-kitchen.png",
    "playroom": ROOT / "habit-playroom.png",
}

SECTIONS = [
    {"id":"intro", "title":"THE HAPPY HABIT CLUB", "bg":"bedroom", "kind":"intro", "lines":[
        "Hello, Habit Heroes! Come and move with us.",
        "Small, happy choices can make every day shine.",
        "Watch, listen, and follow along!",
    ]},
    {"id":"bed", "title":"MAKE YOUR BED", "bg":"bedroom", "kind":"bed", "lines":[
        "Good morning, sunshine. Stretch up high!",
        "Pull up the blanket and smooth it nearby.",
        "Pillow in place, and everything neat.",
        "Our first happy habit is morning complete!",
    ]},
    {"id":"brush", "title":"BRUSH YOUR TEETH", "bg":"bathroom", "kind":"brush", "lines":[
        "Brush, brush, brush in a gentle way.",
        "Round every tooth at the start of the day.",
        "Front, back, top, and down below.",
        "A clean little smile is ready to glow!",
    ]},
    {"id":"chorus1", "title":"SING AND MOVE!", "bg":"bathroom", "kind":"chorus", "lines":[
        "Good habits, good habits, every day.",
        "Little steps help us learn and play.",
        "Brush and wash, be kind and say:",
        "I can make a happy day!",
    ]},
    {"id":"wash", "title":"WASH YOUR HANDS", "bg":"bathroom", "kind":"wash", "lines":[
        "Pump the soap and rub your palms.",
        "Backs and fingers, thumbs in your hands.",
        "Rinse them clean and dry them too.",
        "Healthy little hands are ready for you!",
    ]},
    {"id":"breakfast", "title":"EAT A HAPPY BREAKFAST", "bg":"kitchen", "kind":"breakfast", "lines":[
        "Fruit and toast give energy to play.",
        "Sip some water to start your day.",
        "Sit down calmly and take your time.",
        "A happy breakfast helps us shine!",
    ]},
    {"id":"chorus2", "title":"SING AND MOVE!", "bg":"kitchen", "kind":"chorus", "lines":[
        "Good habits, good habits, every day.",
        "Little steps help us learn and play.",
        "Brush and wash, be kind and say:",
        "I can make a happy day!",
    ]},
    {"id":"tidy", "title":"TIDY UP YOUR TOYS", "bg":"playroom", "kind":"tidy", "lines":[
        "Blocks in the basket, books on the shelf.",
        "I can tidy with a little help.",
        "Pick, place, sort, and smile.",
        "A tidy room feels good for a while!",
    ]},
    {"id":"kind", "title":"USE KIND WORDS", "bg":"playroom", "kind":"kind", "lines":[
        "Please and thank you are lovely to say.",
        "Take your turn when friends want to play.",
        "Share a toy and offer some care.",
        "Kindness grows whenever we share!",
    ]},
    {"id":"bedtime", "title":"CALM BEDTIME", "bg":"bedroom", "kind":"bedtime", "lines":[
        "Toys are resting. Pajamas are on.",
        "Brush once more when the day is done.",
        "Choose a small story, breathe slowly, and rest.",
        "A calm bedtime helps us feel our best!",
    ]},
    {"id":"chorus3", "title":"ONE MORE TIME!", "bg":"bedroom", "kind":"chorus", "lines":[
        "Good habits, good habits, every day.",
        "Little steps help us learn and play.",
        "Brush and wash, be kind and say:",
        "I can make a happy day!",
    ]},
    {"id":"outro", "title":"YOU'RE A HABIT HERO!", "bg":"playroom", "kind":"outro", "lines":[
        "Wonderful moving and singing, Habit Heroes!",
        "Try one happy habit today, and come back to sing with us again.",
        "Please like and subscribe for more songs and gentle adventures. See you next time!",
    ]},
]


def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def remove_connected_magenta(im):
    """Remove only magenta-like pixels connected to the canvas edge.

    This preserves coral clothing and warm skin that color-distance keying can
    incorrectly erase.
    """
    im = im.convert("RGBA")
    px = im.load(); w, h = im.size
    keyish = bytearray(w*h)
    for y in range(h):
        for x in range(w):
            r,g,b,_ = px[x,y]
            if r > 175 and b > 115 and g < 125 and ((r+b)//2-g) > 75:
                keyish[y*w+x] = 1
    seen = bytearray(w*h); stack=[]
    for x in range(w):
        if keyish[x]: stack.append(x)
        j=(h-1)*w+x
        if keyish[j]: stack.append(j)
    for y in range(h):
        j=y*w
        if keyish[j]: stack.append(j)
        j=y*w+w-1
        if keyish[j]: stack.append(j)
    while stack:
        j=stack.pop()
        if seen[j] or not keyish[j]: continue
        seen[j]=1; x=j%w; y=j//w
        if x: stack.append(j-1)
        if x<w-1: stack.append(j+1)
        if y: stack.append(j-w)
        if y<h-1: stack.append(j+w)
    mask=Image.new("L",(w,h),255); mp=mask.load()
    for y in range(h):
        for x in range(w):
            if seen[y*w+x]: mp[x,y]=0
    # A tiny blur gives antialiased edges without changing interior colors.
    mask=mask.filter(ImageFilter.GaussianBlur(.55))
    im.putalpha(mask)
    return im


BG={k:Image.open(v).convert("RGB").resize((W,H),Image.Resampling.LANCZOS) for k,v in BACKGROUNDS.items()}
KIDS=remove_connected_magenta(Image.open(ROOT/"habit-kids-magenta.png"))


def crop_alpha(im, box):
    part=im.crop(box); bb=part.getchannel("A").getbbox()
    return part.crop(bb) if bb else part


GIRL=crop_alpha(KIDS,(0,0,KIDS.width//2+30,KIDS.height))
BOY=crop_alpha(KIDS,(KIDS.width//2-30,0,KIDS.width,KIDS.height))

LINES=[]
VOICE_DUR={}
DURATION=0


def smooth(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)


def paste_scaled(frame, sprite, center, height, angle=0, flip=False, opacity=255):
    ratio=height/sprite.height
    im=sprite.resize((max(1,int(sprite.width*ratio)),int(height)),Image.Resampling.LANCZOS)
    if flip: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if angle: im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    if opacity<255:
        im.putalpha(im.getchannel("A").point(lambda p:p*opacity//255))
    frame.alpha_composite(im,(int(center[0]-im.width/2),int(center[1]-im.height/2)))


def rounded_panel(d, box, fill, outline, width=4, radius=24):
    d.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)


def centered_text(d, text, y, fnt, fill, max_width=1180):
    # Reduce font only if a lyric is unusually long.
    while d.textbbox((0,0),text,font=fnt)[2] > max_width and getattr(fnt,"size",20)>22:
        fnt=font(fnt.size-2, fnt.path.endswith("arialbd.ttf") if hasattr(fnt,"path") else True)
    bb=d.textbbox((0,0),text,font=fnt)
    d.text(((W-(bb[2]-bb[0]))/2,y),text,font=fnt,fill=fill)


def current_section(t):
    for sec in SECTIONS:
        if sec["start"]<=t<sec["end"]: return sec
    return SECTIONS[-1]


def current_lyric(t):
    active=[ln for ln in LINES if ln[1]<=t<ln[2]]
    return active[0][3] if active else ""


def draw_header(frame, sec, lyric):
    d=ImageDraw.Draw(frame)
    rounded_panel(d,(205,20,1075,92),(255,252,236,246),(255,171,55,255),5,26)
    centered_text(d,sec["title"],34,font(36), (38,72,96),820)
    if lyric:
        rounded_panel(d,(70,615,1210,694),(255,252,238,247),(59,165,214,255),4,24)
        centered_text(d,lyric,635,font(31),(35,65,88),1080)


def draw_music_notes(d,t):
    colors=[(255,93,87,220),(255,190,55,220),(64,173,214,220),(102,193,108,220)]
    for i in range(12):
        x=(75+i*109+int(t*26))%W
        y=125+(i*57+int(t*48))%420
        r=5+2*math.sin(t*3+i)
        d.ellipse((x-r,y-r,x+r,y+r),fill=colors[i%4])
        d.line((x+r,y,x+r,y-18),fill=colors[i%4],width=4)


def draw_bubbles(d,t):
    for i in range(24):
        x=80+(i*83)%1120+18*math.sin(t+i)
        y=590-((i*47+int(t*65))%480)
        r=7+(i%5)*3
        d.ellipse((x-r,y-r,x+r,y+r),fill=(210,245,255,80),outline=(80,188,225,170),width=3)


def draw_blocks(d,t,active):
    colors=[(255,97,82),(255,199,65),(54,151,215),(79,185,101)]
    for i in range(9):
        p=smooth(min(1,max(0,(t-active-i*.18)/1.2)))
        sx=180+(i%5)*210; sy=565-(i%2)*55
        ex=180+(i%3)*45; ey=500-(i//3)*38
        x=sx+(ex-sx)*p; y=sy+(ey-sy)*p
        d.rounded_rectangle((x-20,y-20,x+20,y+20),radius=6,fill=colors[i%4],outline=(255,255,255,190),width=2)


def draw_hearts(d,t):
    for i in range(10):
        a=t*1.3+i*.7; x=640+260*math.sin(a); y=300+115*math.sin(a*1.7)
        s=8+4*math.sin(t*2+i)
        c=(255,104,118,205)
        d.ellipse((x-s,y-s,x,y),fill=c); d.ellipse((x,y-s,x+s,y),fill=c)
        d.polygon([(x-s,y-s/3),(x+s,y-s/3),(x,y+s*1.3)],fill=c)


def frame_at(t):
    sec=current_section(t); local=t-sec["start"]
    frame=BG[sec["bg"]].convert("RGBA")
    d=ImageDraw.Draw(frame,"RGBA")
    kind=sec["kind"]
    # Keep evening cozy and bright rather than dark.
    if kind=="bedtime":
        d.rectangle((0,0,W,H),fill=(87,109,173,48))
        for i in range(18):
            x=60+(i*79)%1160; y=110+(i*53)%370; r=3+2*math.sin(t*2+i)
            d.ellipse((x-r,y-r,x+r,y+r),fill=(255,231,125,200))
    dance=kind in ("intro","chorus","outro")
    bob=12*math.sin(local*3.2)
    girl_x=430+25*math.sin(local*1.5); boy_x=850-25*math.sin(local*1.5)
    angle=4*math.sin(local*2.4) if dance else 2*math.sin(local*1.7)
    paste_scaled(frame,GIRL,(girl_x,420+bob),440,angle)
    paste_scaled(frame,BOY,(boy_x,420-bob),440,-angle)
    d=ImageDraw.Draw(frame,"RGBA")
    if dance: draw_music_notes(d,t)
    if kind=="bed":
        for i in range(12):
            a=i*math.pi/6+t*.5; x=245+130*math.cos(a); y=355+80*math.sin(a)
            d.ellipse((x-5,y-5,x+5,y+5),fill=(255,215,57,210))
    elif kind=="brush":
        for cx,sgn in [(430,1),(850,-1)]:
            y=350+10*math.sin(local*5)
            d.rounded_rectangle((cx-35,y-7,cx+35,y+7),radius=7,fill=(44,146,214),outline="white",width=2)
            x0,x1=sorted((cx+sgn*25,cx+sgn*50))
            d.rectangle((x0,y-12,x1,y+12),fill=(255,219,75))
    elif kind=="wash": draw_bubbles(d,t)
    elif kind=="breakfast":
        fruits=[((255,85,75),"apple"),((255,190,45),"banana"),((94,183,92),"pear")]
        for i,(c,_) in enumerate(fruits):
            x=505+i*135+18*math.sin(local*2+i); y=250+20*math.sin(local*2.5+i)
            d.ellipse((x-28,y-28,x+28,y+28),fill=c+(230,),outline=(255,255,255,190),width=3)
    elif kind=="tidy": draw_blocks(d,local,2.0)
    elif kind=="kind": draw_hearts(d,t)
    elif kind=="bedtime":
        d.pieslice((965,115,1090,240),60,300,fill=(255,231,132,235))
        d.ellipse((1000,125,1080,205),fill=(110,145,202,180))
    lyric=current_lyric(t)
    draw_header(frame,sec,lyric)
    if kind=="outro" and local>sec["subscribe_local"]:
        dd=ImageDraw.Draw(frame)
        rounded_panel(dd,(345,505,935,590),(255,247,224,245),(255,91,83,255),5,25)
        centered_text(dd,"LIKE & SUBSCRIBE",526,font(38),(220,65,58),540)
    return frame.convert("RGB")


def speech_path(key): return WORK/f"good-habits-{key}.mp3"


async def make_speech():
    WORK.mkdir(exist_ok=True)
    items=[]
    for sec in SECTIONS:
        for i,text in enumerate(sec["lines"]): items.append((f"{sec['id']}-{i}",text,sec["id"]))
    for key,text,_ in items:
        path=speech_path(key)
        if not path.exists():
            print("Rhyme:",key,flush=True)
            await edge_tts.Communicate(text,VOICE,rate="+2%",pitch="+5Hz",volume="-2%").save(str(path))
    return items


def duration(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)],capture_output=True,text=True,check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def build_timeline(items):
    global LINES,DURATION
    durs={key:duration(speech_path(key)) for key,_,_ in items}
    text_by={key:text for key,text,_ in items}; cursor=.35; LINES=[]
    for sec in SECTIONS:
        sec["start"]=cursor
        for i,text in enumerate(sec["lines"]):
            key=f"{sec['id']}-{i}"; start=cursor; end=start+durs[key]
            LINES.append((key,start,end,text,sec["id"])); cursor=end+.22
            if sec["id"]=="outro" and i==2: sec["subscribe_local"]=start-sec["start"]
        cursor+=1.0 if sec["kind"]=="chorus" else .7
        sec["end"]=cursor
    DURATION=math.ceil((cursor+.6)*ART_FPS)/ART_FPS
    report=[]
    for i,(key,s,e,_,sid) in enumerate(LINES):
        nxt=LINES[i+1][1] if i+1<len(LINES) else DURATION
        report.append(f"{key} [{sid}]: start={s:.3f} end={e:.3f} gap={nxt-e:.3f}")
    (WORK/"good-habits-voice-timing.txt").write_text("\n".join(report),encoding="utf-8")


def make_music():
    sr=24000; n=int(DURATION*sr); path=WORK/"good-habits-original-music.wav"
    bpm=96; beat=60/bpm; chords=[(261.63,329.63,392.0),(293.66,369.99,440.0),(349.23,440.0,523.25),(392.0,493.88,587.33)]
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr);block=bytearray()
        for i in range(n):
            t=i/sr; ch=chords[int(t/(beat*4))%4]; pos=t%beat
            pluck=math.exp(-5.5*pos/beat); melody=ch[int(t/beat)%3]
            v=.012*sum(math.sin(2*math.pi*f*t) for f in ch)
            v+=.020*pluck*math.sin(2*math.pi*melody*2*t)
            # Gentle kick and clap establish a follow-along pulse.
            v+=.018*math.exp(-18*pos)*math.sin(2*math.pi*(70-25*pos)*t)
            if int(t/beat)%2==1: v+=.006*math.exp(-24*pos)*math.sin(2*math.pi*1200*t)
            block+=struct.pack("<h",max(-32767,min(32767,int(v*32767))))
            if len(block)>=sr*4: wf.writeframes(block);block.clear()
        if block:wf.writeframes(block)
    return path


def render():
    total=math.ceil(DURATION*ART_FPS)
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",str(SILENT)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(total):
        if i%(ART_FPS*10)==0:print(f"Rendered {i//ART_FPS}/{math.ceil(DURATION)} seconds",flush=True)
        p.stdin.write(frame_at(i/ART_FPS).tobytes())
    p.stdin.close()
    if p.wait()!=0:raise RuntimeError("render failed")


def mix(music):
    inputs=["-i",str(SILENT),"-i",str(music)];filters=["[1:a]volume=.72[m]"];labels=["[m]"]
    for idx,(key,start,_,_,_) in enumerate(LINES,2):
        inputs += ["-i",str(speech_path(key))];delay=round(start*1000)
        filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.18[v{idx}]");labels.append(f"[v{idx}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=.88[a]")
    cmd=["ffmpeg","-y"]+inputs+["-filter_complex",";".join(filters),"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-ar","24000","-ac","1","-t",f"{DURATION:.3f}","-movflags","+faststart",str(OUTPUT)]
    subprocess.run(cmd,check=True)


def contact_sheet():
    times=[]
    for sec in SECTIONS: times += [sec["start"]+1.5,(sec["start"]+sec["end"])/2]
    tw,th,cols=320,180,4;rows=math.ceil(len(times)/cols)
    sh=Image.new("RGB",(tw*cols,th*rows),"white")
    for i,t in enumerate(times):
        im=frame_at(min(t,DURATION-.1)).resize((tw,th),Image.Resampling.LANCZOS);d=ImageDraw.Draw(im)
        d.rectangle((0,0,70,24),fill="black");d.text((5,3),f"{t:.1f}s",font=font(14),fill="white")
        sh.paste(im,((i%cols)*tw,(i//cols)*th))
    sh.save(CONTACT)


async def main():
    items=await make_speech();build_timeline(items);music=make_music();render();mix(music);contact_sheet();print(OUTPUT)


if __name__=="__main__":asyncio.run(main())
