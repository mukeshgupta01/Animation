import asyncio
import math
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import edge_tts


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "ocean-odd-work"
BACKGROUND = ROOT / "ocean-odd-background.png"
SILENT = WORK / "ocean-odd-silent.mp4"
OUTPUT = ROOT / "ocean-odd-one-doesnt-belong.mp4"
W, H, FPS, DURATION = 1280, 720, 24, 74.0
VOICE, RATE = "en-AU-NatashaNeural", "-12%"

LINES = [
    ("intro", 0.30, "Three ocean puzzles are waiting. Which one doesn't belong? Let's begin!"),
    ("r1q", 4.70, "Round one. Five friends belong in the ocean, but one does not. Can you spot it?"),
    ("r1a", 17.00, "It's the cow! Cows live on land, while the others live in the ocean."),
    ("r2q", 24.00, "Round two. Which animal does not live in salty ocean water?"),
    ("r2a", 35.80, "It's the frog! Frogs usually live in fresh water or on land, not in the sea."),
    ("r3q", 42.50, "Final round. Four are fish, but one is a mammal. Which one doesn't belong?"),
    ("r3a", 54.50, "It's the dolphin! A dolphin is a mammal. It breathes air and feeds milk to its babies."),
    ("outro", 63.00, "Wonderful thinking! How many did you solve? Please like and subscribe for more fun puzzle videos. See you next time!"),
]


def get_font(size, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "calibrib.ttf" if bold else "calibri.ttf"]
    for name in names:
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F_TITLE = get_font(42, True)
F_HEAD = get_font(34, True)
F_LABEL = get_font(23, True)
F_SMALL = get_font(21, True)


def fit_text(draw, text, max_width, start=35, minimum=20):
    for size in range(start, minimum - 1, -1):
        f = get_font(size, True)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
    return get_font(minimum, True)


def ellipse(draw, box, fill, outline=(255, 255, 255, 255), width=3):
    draw.ellipse(box, fill=fill, outline=outline, width=width)


def fish(draw, cx, cy, s, color=(255, 150, 44, 255), stripes=False):
    ellipse(draw, (cx-42*s, cy-25*s, cx+39*s, cy+25*s), color, width=max(2, int(3*s)))
    draw.polygon([(cx-42*s, cy), (cx-70*s, cy-28*s), (cx-70*s, cy+28*s)], fill=color,
                 outline=(255,255,255,255))
    draw.polygon([(cx-4*s, cy-22*s), (cx+10*s, cy-42*s), (cx+18*s, cy-20*s)], fill=color)
    ellipse(draw, (cx+18*s, cy-9*s, cx+29*s, cy+2*s), (255,255,255,255), width=1)
    ellipse(draw, (cx+22*s, cy-5*s, cx+27*s, cy), (18,52,85,255), outline=None, width=0)
    if stripes:
        for dx in (-18, 2):
            draw.line((cx+dx*s, cy-20*s, cx+dx*s, cy+20*s), fill=(255,255,255,230), width=max(3,int(7*s)))


def crab(draw, cx, cy, s):
    c=(238,74,76,255)
    ellipse(draw,(cx-38*s,cy-22*s,cx+38*s,cy+26*s),c,width=3)
    for side in (-1,1):
        for dy in (-10,5,19):
            draw.line((cx+side*27*s,cy+dy*s,cx+side*58*s,cy+(dy+side*3)*s),fill=c,width=max(3,int(7*s)))
        ellipse(draw,(cx+side*48*s-14*s,cy-34*s,cx+side*48*s+14*s,cy-7*s),c,width=3)
    for ex in (-14,14):
        ellipse(draw,(cx+ex*s-6*s,cy-18*s,cx+ex*s+6*s,cy-6*s),(255,255,255,255),width=1)
        ellipse(draw,(cx+ex*s-2*s,cy-14*s,cx+ex*s+2*s,cy-10*s),(20,45,76,255),outline=None,width=0)


def octopus(draw,cx,cy,s):
    c=(176,92,215,255)
    ellipse(draw,(cx-35*s,cy-39*s,cx+35*s,cy+20*s),c,width=3)
    for i in range(6):
        x=cx+(i-2.5)*13*s
        draw.arc((x-15*s,cy+4*s,x+20*s,cy+55*s),0,180,fill=c,width=max(4,int(8*s)))
    for ex in (-13,13):
        ellipse(draw,(cx+ex*s-7*s,cy-13*s,cx+ex*s+7*s,cy+1*s),(255,255,255,255),width=1)
        ellipse(draw,(cx+ex*s-2*s,cy-9*s,cx+ex*s+2*s,cy-5*s),(20,45,76,255),outline=None,width=0)


def turtle(draw,cx,cy,s):
    c=(72,178,102,255)
    ellipse(draw,(cx-42*s,cy-28*s,cx+35*s,cy+28*s),c,width=3)
    ellipse(draw,(cx+30*s,cy-13*s,cx+55*s,cy+12*s),(111,202,107,255),width=2)
    for dx,dy in [(-30,-25),(-28,22),(20,-23),(18,22)]:
        ellipse(draw,(cx+(dx-10)*s,cy+(dy-7)*s,cx+(dx+10)*s,cy+(dy+7)*s),(111,202,107,255),width=2)
    draw.arc((cx-28*s,cy-18*s,cx+22*s,cy+20*s),10,170,fill=(255,224,89,255),width=max(2,int(4*s)))


def seahorse(draw,cx,cy,s):
    c=(255,188,54,255)
    ellipse(draw,(cx-18*s,cy-43*s,cx+25*s,cy-4*s),c,width=3)
    draw.polygon([(cx+18*s,cy-34*s),(cx+48*s,cy-25*s),(cx+19*s,cy-14*s)],fill=c)
    draw.arc((cx-27*s,cy-11*s,cx+19*s,cy+58*s),260,110,fill=c,width=max(5,int(12*s)))
    draw.arc((cx-6*s,cy+29*s,cx+34*s,cy+64*s),20,330,fill=c,width=max(3,int(7*s)))
    ellipse(draw,(cx+5*s,cy-31*s,cx+13*s,cy-23*s),(18,52,85,255),outline=None,width=0)


def cow(draw,cx,cy,s):
    base=(250,247,232,255)
    ellipse(draw,(cx-46*s,cy-29*s,cx+44*s,cy+29*s),base,width=3)
    ellipse(draw,(cx+26*s,cy-38*s,cx+62*s,cy+3*s),base,width=3)
    for dx in (-28,22):
        draw.line((cx+dx*s,cy+21*s,cx+dx*s,cy+52*s),fill=(75,55,52,255),width=max(3,int(7*s)))
    ellipse(draw,(cx-24*s,cy-20*s,cx+1*s,cy+4*s),(64,52,58,255),outline=None,width=0)
    ellipse(draw,(cx+18*s,cy+1*s,cx+39*s,cy+23*s),(64,52,58,255),outline=None,width=0)
    ellipse(draw,(cx+48*s,cy-27*s,cx+55*s,cy-20*s),(25,45,67,255),outline=None,width=0)
    draw.polygon([(cx+31*s,cy-35*s),(cx+22*s,cy-52*s),(cx+38*s,cy-39*s)],fill=(255,213,112,255))
    draw.polygon([(cx+54*s,cy-35*s),(cx+65*s,cy-51*s),(cx+62*s,cy-34*s)],fill=(255,213,112,255))


def frog(draw,cx,cy,s):
    c=(104,199,76,255)
    ellipse(draw,(cx-40*s,cy-20*s,cx+40*s,cy+35*s),c,width=3)
    for ex in (-22,22):
        ellipse(draw,(cx+ex*s-13*s,cy-39*s,cx+ex*s+13*s,cy-12*s),c,width=2)
        ellipse(draw,(cx+ex*s-5*s,cy-32*s,cx+ex*s+5*s,cy-22*s),(255,255,255,255),width=1)
        ellipse(draw,(cx+ex*s-2*s,cy-29*s,cx+ex*s+2*s,cy-25*s),(20,50,70,255),outline=None,width=0)
    draw.arc((cx-18*s,cy-5*s,cx+18*s,cy+18*s),10,170,fill=(20,90,65,255),width=max(2,int(3*s)))


def dolphin(draw,cx,cy,s):
    c=(62,158,211,255)
    ellipse(draw,(cx-52*s,cy-21*s,cx+39*s,cy+22*s),c,width=3)
    draw.polygon([(cx-50*s,cy),(cx-78*s,cy-27*s),(cx-70*s,cy+7*s),(cx-82*s,cy+30*s)],fill=c)
    draw.polygon([(cx-5*s,cy-18*s),(cx+10*s,cy-43*s),(cx+18*s,cy-14*s)],fill=c)
    draw.polygon([(cx+27*s,cy-5*s),(cx+66*s,cy+3*s),(cx+31*s,cy+12*s)],fill=c)
    ellipse(draw,(cx+17*s,cy-10*s,cx+24*s,cy-3*s),(20,45,70,255),outline=None,width=0)


def shark(draw,cx,cy,s):
    fish(draw,cx,cy,s,(96,135,158,255))
    draw.polygon([(cx-5*s,cy-20*s),(cx+8*s,cy-52*s),(cx+21*s,cy-18*s)],fill=(96,135,158,255))


def whale(draw,cx,cy,s):
    c=(74,125,193,255)
    ellipse(draw,(cx-53*s,cy-27*s,cx+43*s,cy+27*s),c,width=3)
    draw.polygon([(cx-48*s,cy),(cx-78*s,cy-29*s),(cx-67*s,cy+2*s),(cx-81*s,cy+29*s)],fill=c)
    ellipse(draw,(cx+20*s,cy-10*s,cx+27*s,cy-3*s),(20,45,70,255),outline=None,width=0)
    draw.arc((cx+18*s,cy-4*s,cx+42*s,cy+12*s),5,160,fill=(255,255,255,230),width=max(2,int(3*s)))


DRAWERS = {"FISH": fish, "CRAB": crab, "TURTLE": turtle, "OCTOPUS": octopus,
           "SEAHORSE": seahorse, "COW": cow, "FROG": frog, "DOLPHIN": dolphin,
           "SHARK": shark, "WHALE": whale}

ROUNDS = [
    ["FISH", "CRAB", "TURTLE", "COW", "OCTOPUS", "SEAHORSE"],
    ["TURTLE", "DOLPHIN", "FROG", "WHALE", "FISH", "OCTOPUS"],
    ["FISH", "SHARK", "FISH", "DOLPHIN", "FISH", "FISH"],
]
ANSWERS = [3, 2, 3]
COLORS = [(238,74,76,255), (72,178,102,255), (62,158,211,255)]


def card(draw, x, y, w, h, name, index, round_no, reveal=False):
    answer = index == ANSWERS[round_no]
    fill=(255,253,235,244)
    outline=COLORS[round_no] if reveal and answer else (255,255,255,245)
    width=8 if reveal and answer else 4
    draw.rounded_rectangle((x,y,x+w,y+h),radius=25,fill=fill,outline=outline,width=width)
    cx,cy=x+w//2,y+70
    func=DRAWERS[name]
    if name == "FISH":
        shades=[(255,151,49,255),(244,92,120,255),(64,182,205,255),(247,194,61,255)]
        func(draw,cx,cy,0.72,shades[index%4],round_no==2)
    else:
        func(draw,cx,cy,0.72)
    label=chr(65+index)
    ellipse(draw,(x+12,y+12,x+48,y+48),(22,65,100,255),outline=(255,255,255,255),width=2)
    draw.text((x+30,y+29),label,anchor="mm",font=F_SMALL,fill=(255,255,255,255))
    draw.text((x+w//2,y+h-25),name,anchor="mm",font=F_LABEL,fill=(17,52,86,255))
    if reveal and answer:
        draw.rounded_rectangle((x+w-72,y+10,x+w-12,y+48),radius=17,fill=COLORS[round_no])
        draw.text((x+w-42,y+29),"YES!",anchor="mm",font=get_font(16,True),fill=(255,255,255,255))


def header(draw, round_no, question, final=False):
    draw.rounded_rectangle((95,16,1185,104),radius=28,fill=(255,253,235,244),outline=(255,194,48,255),width=5)
    heading = "FINAL ROUND" if final else f"ROUND {round_no+1}"
    draw.text((125,39),heading,font=F_HEAD,fill=COLORS[round_no])
    f=fit_text(draw,question,760,31,22)
    draw.text((1170,58),question,anchor="rm",font=f,fill=(17,52,86,255))


def round_frame(base, round_no, question, reveal=False):
    im=base.copy(); d=ImageDraw.Draw(im,"RGBA")
    header(d,round_no,question,round_no==2)
    positions=[(145,135),(455,135),(765,135),(145,385),(455,385),(765,385)]
    for i,(x,y) in enumerate(positions):
        card(d,x,y,270,205,ROUNDS[round_no][i],i,round_no,reveal)
    return im


def render_video():
    bg=Image.open(BACKGROUND).convert("RGB").resize((W,H),Image.Resampling.LANCZOS).convert("RGBA")
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(SILENT)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(int(DURATION*FPS)):
        t=n/FPS
        if t < 4.60:
            frame=bg.copy(); d=ImageDraw.Draw(frame,"RGBA")
            d.rounded_rectangle((185,190,1095,510),radius=42,fill=(255,253,235,244),outline=(255,194,48,255),width=7)
            d.text((W//2,265),"WHICH ONE",anchor="mm",font=get_font(69,True),fill=(238,74,76,255))
            d.text((W//2,345),"DOESN'T BELONG?",anchor="mm",font=get_font(65,True),fill=(17,52,86,255))
            d.text((W//2,435),"3 OCEAN PUZZLES",anchor="mm",font=F_HEAD,fill=(62,158,211,255))
        elif t < 17.0:
            frame=round_frame(bg,0,"Which friend does not belong in the ocean?")
        elif t < 23.8:
            frame=round_frame(bg,0,"The COW lives on land!",True)
        elif t < 35.8:
            frame=round_frame(bg,1,"Who does not live in salty ocean water?")
        elif t < 42.3:
            frame=round_frame(bg,1,"The FROG prefers fresh water or land!",True)
        elif t < 54.5:
            frame=round_frame(bg,2,"Four are fish. Which one is a mammal?")
        elif t < 62.8:
            frame=round_frame(bg,2,"The DOLPHIN is a mammal!",True)
        else:
            frame=bg.copy(); d=ImageDraw.Draw(frame,"RGBA")
            d.rounded_rectangle((190,180,1090,540),radius=44,fill=(255,253,235,245),outline=(255,194,48,255),width=7)
            d.text((W//2,250),"WONDERFUL THINKING!",anchor="mm",font=get_font(48,True),fill=(238,74,76,255))
            d.text((W//2,325),"How many did you solve?",anchor="mm",font=F_HEAD,fill=(17,52,86,255))
            d.rounded_rectangle((355,380,925,465),radius=32,fill=(62,158,211,255))
            d.text((W//2,421),"LIKE & SUBSCRIBE",anchor="mm",font=get_font(39,True),fill=(255,255,255,255))
            d.text((W//2,500),"For more fun puzzles!",anchor="mm",font=F_LABEL,fill=(36,139,112,255))
        proc.stdin.write(frame.convert("RGB").tobytes())
        if n%(FPS*10)==0: print(f"Rendered {t:.0f}/{DURATION:.0f} seconds",flush=True)
    proc.stdin.close()
    if proc.wait()!=0: raise RuntimeError("video render failed")


async def make_speech():
    for key,_,text in LINES:
        p=WORK/f"voice-{key}.mp3"
        if not p.exists():
            print("Narration:",key,flush=True)
            await edge_tts.Communicate(text,VOICE,rate=RATE,volume="-2%").save(str(p))


def make_bed():
    sr=44100; p=WORK/"ocean-bed.wav"
    notes=[261.63,329.63,392.00,329.63,293.66,349.23,440.00,349.23]
    with wave.open(str(p),"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr)
        chunk=bytearray()
        for i in range(int(DURATION*sr)):
            t=i/sr; note=notes[int(t/4)%len(notes)]
            pad=.42*math.sin(2*math.pi*note*t)+.20*math.sin(2*math.pi*(note/2)*t)
            sparkle=math.exp(-(t%4)*4)*math.sin(2*math.pi*note*2*t)*.22 if t%4<1 else 0
            fade=min(1,t/2,(DURATION-t)/2)
            v=int(max(-1,min(1,(pad+sparkle)*.045*fade))*32767)
            chunk+=struct.pack("<h",v)
            if len(chunk)>65536: wf.writeframes(chunk);chunk.clear()
        if chunk: wf.writeframes(chunk)


def make_sfx():
    sr=44100; data=[0.0]*int(DURATION*sr)
    events=[]
    for start in (13.0,14.0,15.0,32.0,33.0,34.0,51.0,52.0,53.0): events.append((start,"tick"))
    for start in (17.0,35.8,54.5): events.append((start,"chime"))
    for start,kind in events:
        n0=int(start*sr); dur=.75 if kind=="chime" else .07
        for j in range(int(dur*sr)):
            tt=j/sr
            v=(math.exp(-tt*4)*(math.sin(2*math.pi*659.25*tt)+.45*math.sin(2*math.pi*987.77*tt))*.10 if kind=="chime" else math.exp(-tt*40)*math.sin(2*math.pi*1050*tt)*.055)
            if n0+j<len(data):data[n0+j]+=v
    with wave.open(str(WORK/"ocean-sfx.wav"),"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr)
        for i in range(0,len(data),32768): wf.writeframes(b"".join(struct.pack("<h",int(max(-1,min(1,v))*32767)) for v in data[i:i+32768]))


def speech_durations():
    result=[]
    for key,start,_ in LINES:
        p=WORK/f"voice-{key}.mp3"
        raw=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(p)],text=True).strip()
        result.append((key,start,float(raw),start+float(raw)))
    for i,item in enumerate(result[:-1]):
        if item[3] > result[i+1][1]-0.08:
            raise RuntimeError(f"Narration overlap: {item[0]} ends {item[3]:.2f}, next begins {result[i+1][1]:.2f}")
    print("Narration timings:",result,flush=True)


def mix_audio():
    inputs=["-i",str(SILENT),"-i",str(WORK/"ocean-bed.wav"),"-i",str(WORK/"ocean-sfx.wav")]
    filters=["[1:a]volume=0.48[bed]","[2:a]volume=0.9[sfx]"];labels=["[bed]","[sfx]"]
    for idx,(key,start,_) in enumerate(LINES,start=3):
        inputs += ["-i",str(WORK/f"voice-{key}.mp3")]
        delay=int(start*1000);filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.28[v{idx}]");labels.append(f"[v{idx}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.95[aout]")
    cmd=["ffmpeg","-y"]+inputs+["-filter_complex",";".join(filters),"-map","0:v:0","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-t",str(DURATION),"-movflags","+faststart",str(OUTPUT)]
    subprocess.run(cmd,check=True)


def main():
    WORK.mkdir(exist_ok=True)
    asyncio.run(make_speech());speech_durations();make_bed();make_sfx();render_video();mix_audio()
    print(OUTPUT)


if __name__=="__main__": main()
