import asyncio
import math
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "ultimate-animal-work"
ANIMALS_IMAGE = ROOT / "hidden-animals-puzzle-corrected.png"
DINOSAURS_IMAGE = ROOT / "hidden-dinosaurs-puzzle.png"
SILENT = WORK / "ultimate-animal-silent.mp4"
OUTPUT = ROOT / "ultimate-3-round-animal-challenge.mp4"
W, H, FPS, DURATION = 1280, 720, 24, 76.0
VOICE, RATE = "en-AU-NatashaNeural", "-10%"

LINES = [
    ("hook", 0.30, "Three animal puzzles are waiting. Can you solve them all?"),
    ("round1", 4.80, "Round one. Can you find the owl hiding in the garden?"),
    ("answer1", 19.30, "There it is, inside the pink tree! You found the owl."),
    ("round2", 25.20, "Round two. Which animal does not belong with the garden animals?"),
    ("answer2", 38.20, "It is the T-Rex! It belongs in the prehistoric world."),
    ("round3a", 44.00, "Round three. Look carefully at these five animals."),
    ("round3b", 49.80, "One animal disappeared. Which one was it?"),
    ("answer3", 60.20, "The rabbit disappeared! Wonderful remembering."),
    ("ending", 65.20, "You completed all three puzzles! Please like and subscribe for more fun challenges. See you next time!"),
]


def font(size, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "calibrib.ttf" if bold else "calibri.ttf"]
    for name in names:
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F20, F25, F32, F44, F62 = font(20, True), font(25, True), font(32, True), font(44, True), font(62, True)
COLORS = [(238, 74, 79), (255, 165, 42), (45, 171, 106), (29, 157, 205), (156, 90, 210)]


def cover(path):
    return Image.open(path).convert("RGB").resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")


def crop_subject(src, nx, ny, half_w=0.105, half_h=0.17):
    sw, sh = src.size
    x1, y1 = int((nx-half_w)*sw), int((ny-half_h)*sh)
    x2, y2 = int((nx+half_w)*sw), int((ny+half_h)*sh)
    x1, y1, x2, y2 = max(0,x1), max(0,y1), min(sw,x2), min(sh,y2)
    return src.crop((x1,y1,x2,y2)).resize((194, 180), Image.Resampling.LANCZOS)


def title_bar(frame, left, right):
    d = ImageDraw.Draw(frame, "RGBA")
    d.rounded_rectangle((left, 12, right, 92), radius=24,
                        fill=(255,252,231,245), outline=(255,187,37,255), width=5)


def center_text(d, text, y, f, fill=(15,48,89,255), stroke=0):
    d.text((W//2, y), text, anchor="mm", font=f, fill=fill,
           stroke_width=stroke, stroke_fill=(255,255,255,255))


def timer(draw, remaining, total, cx=1215, cy=52):
    r = 40 if remaining > 3 else 47
    draw.ellipse((cx-r,cy-r,cx+r,cy+r), fill=(255,252,231,248), outline=(255,187,37,255), width=5)
    draw.arc((cx-r+7,cy-r+7,cx+r-7,cy+r-7), -90, -90+360*remaining/total,
             fill=(31,158,164,255), width=6)
    txt = str(max(0, math.ceil(remaining)))
    f = font(31 if remaining > 3 else 37, True)
    draw.text((cx,cy-2), txt, anchor="mm", font=f, fill=(15,48,89,255))


def card_canvas(animal_src, dino_src, missing=False, reveal=None):
    bg = Image.new("RGBA", (W,H), (168,231,244,255))
    d = ImageDraw.Draw(bg, "RGBA")
    for y in range(H):
        c = int(244 - 30*y/H)
        d.line((0,y,W,y), fill=(157,220+c//8,247,255))
    d.ellipse((-120,510,400,900), fill=(99,190,100,255))
    d.ellipse((870,500,1400,900), fill=(85,177,92,255))
    animals = [
        crop_subject(animal_src, .145,.14),
        crop_subject(animal_src, .756,.46),
        crop_subject(animal_src, .145,.70),
        crop_subject(animal_src, .430,.916),
        crop_subject(animal_src, .707,.916),
    ]
    if reveal == "odd":
        animals = [animals[0], animals[1], crop_subject(dino_src,.198,.43), animals[3], animals[4]]
    xs = [55, 300, 545, 790, 1035]
    for i,(x,img) in enumerate(zip(xs,animals)):
        border = COLORS[i]
        d.rounded_rectangle((x,220,x+190,485), radius=28, fill=(255,252,231,250), outline=border+(255,), width=6)
        if missing and i == 2:
            d.rounded_rectangle((x+8,228,x+182,400), radius=20, fill=(241,248,249,255))
            d.text((x+95,315), "?", anchor="mm", font=font(90,True), fill=(45,171,106,255))
        else:
            mask = Image.new("L", (194,180), 0)
            md = ImageDraw.Draw(mask); md.rounded_rectangle((0,0,193,179), radius=18, fill=255)
            bg.paste(img, (x-2,228), mask)
        d.text((x+95,445), str(i+1), anchor="mm", font=F32, fill=border+(255,))
    if reveal == "odd":
        x=xs[2]; d.rounded_rectangle((x-8,212,x+198,493), radius=31, outline=(238,74,79,255), width=10)
        d.rounded_rectangle((430,530,850,600), radius=22, fill=(255,252,231,245), outline=(238,74,79,255), width=5)
        center_text(d, "T-REX • PREHISTORIC ANIMAL", 565, F25, (238,74,79,255))
    if reveal == "rabbit":
        x=xs[2]; d.rounded_rectangle((x-8,212,x+198,493), radius=31, outline=(45,171,106,255), width=10)
        d.rounded_rectangle((480,530,800,600), radius=22, fill=(255,252,231,245), outline=(45,171,106,255), width=5)
        center_text(d, "THE RABBIT!", 565, F32, (45,171,106,255))
    return bg


def render_video():
    garden = cover(ANIMALS_IMAGE)
    animal_src = Image.open(ANIMALS_IMAGE).convert("RGB")
    dino_src = Image.open(DINOSAURS_IMAGE).convert("RGB")
    cards_odd = card_canvas(animal_src,dino_src,reveal="odd")
    cards_odd_plain = card_canvas(animal_src,dino_src)
    cards_all = card_canvas(animal_src,dino_src)
    cards_missing = card_canvas(animal_src,dino_src,missing=True)
    cards_rabbit = card_canvas(animal_src,dino_src,reveal="rabbit")

    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-an","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(SILENT)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(int(DURATION*FPS)):
        t=n/FPS
        if t < 24.9:
            frame=garden.copy()
        elif t < 43.8:
            frame=(cards_odd if t>=38.0 else cards_odd_plain).copy()
        elif t < 49.6:
            frame=cards_all.copy()
        elif t < 60.0:
            frame=cards_missing.copy()
        elif t < 65.0:
            frame=cards_rabbit.copy()
        else:
            frame=garden.copy().filter(ImageFilter.GaussianBlur(5))
        d=ImageDraw.Draw(frame,"RGBA")

        if t < 4.6:
            d.rounded_rectangle((150,205,1130,505),radius=42,fill=(255,252,231,245),outline=(255,187,37,255),width=7)
            center_text(d,"3 ANIMAL PUZZLES!",290,F62,(238,74,79,255),2)
            center_text(d,"Can you solve them all?",395,F44)
            center_text(d,"Round 1 starts right away",462,F25,(31,158,164,255))
        elif t < 19.0:
            title_bar(frame,250,1030); center_text(d,"ROUND 1 • FIND THE OWL",52,F32)
            if 9.0 <= t < 19.0: timer(d,19.0-t,10)
        elif t < 24.9:
            title_bar(frame,300,980); center_text(d,"YOU FOUND THE OWL!",52,F32,(255,152,38,255))
            x,y=int(.756*W),int(.46*H); rr=int(52+5*math.sin((t-19)*5))
            d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=(255,255,255,255),width=10)
            d.ellipse((x-rr+5,y-rr+5,x+rr-5,y+rr-5),outline=(255,152,38,255),width=6)
        elif t < 38.0:
            title_bar(frame,175,1105); center_text(d,"ROUND 2 • WHICH ONE DOESN'T BELONG?",52,F32)
            if 29.0 <= t < 38.0: timer(d,38.0-t,9)
        elif t < 43.8:
            title_bar(frame,300,980); center_text(d,"THE T-REX!",52,F44,(238,74,79,255))
        elif t < 49.6:
            title_bar(frame,230,1050); center_text(d,"ROUND 3 • REMEMBER THEM!",52,F32)
            d.rounded_rectangle((365,520,915,590),radius=22,fill=(255,252,231,240))
            center_text(d,"Look at all five animals",555,F25)
        elif t < 60.0:
            title_bar(frame,245,1035); center_text(d,"WHICH ANIMAL DISAPPEARED?",52,F32)
            if 50.0 <= t < 60.0: timer(d,60.0-t,10)
        elif t < 65.0:
            title_bar(frame,320,960); center_text(d,"THE RABBIT!",52,F44,(45,171,106,255))
        else:
            d.rounded_rectangle((180,185,1100,535),radius=42,fill=(255,252,231,246),outline=(255,187,37,255),width=7)
            center_text(d,"3 PUZZLES COMPLETE!",270,F62,(45,171,106,255),2)
            center_text(d,"LIKE & SUBSCRIBE",385,F44,(238,74,79,255))
            center_text(d,"For more fun challenges",465,F25,(31,158,164,255))

        proc.stdin.write(frame.convert("RGB").tobytes())
        if n%(FPS*10)==0: print(f"Rendered {n/FPS:.0f}/{DURATION:.0f} seconds",flush=True)
    proc.stdin.close()
    if proc.wait()!=0: raise RuntimeError("video render failed")


async def make_speech():
    WORK.mkdir(exist_ok=True)
    for key,_,text in LINES:
        p=WORK/f"voice-{key}.mp3"
        if not p.exists():
            print("Narration:",key,flush=True)
            await edge_tts.Communicate(text,VOICE,rate=RATE,volume="-2%").save(str(p))


def make_bed():
    sr=44100; path=WORK/"gentle-bed.wav"
    notes=[261.63,329.63,392.0,349.23,293.66,392.0]
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        buf=bytearray()
        for i in range(int(DURATION*sr)):
            t=i/sr; note=notes[int(t/4)%len(notes)]
            v=(.55*math.sin(2*math.pi*note*t)+.22*math.sin(2*math.pi*note/2*t))*.045
            fade=min(1,t/1.5,(DURATION-t)/1.5); buf+=struct.pack("<h",int(v*fade*32767))
            if len(buf)>=65536: wf.writeframes(buf); buf.clear()
        if buf: wf.writeframes(buf)


def make_sfx():
    sr=44100; data=[0.0]*int(DURATION*sr)
    events=[(4.6,"chime"),(19.0,"chime"),(24.9,"chime"),(38.0,"chime"),(43.8,"chime"),(60.0,"chime")]
    for x in [16,17,18,35,36,37,57,58,59]: events.append((x,"tick"))
    for start,kind in events:
        n0=int(start*sr); dur=.8 if kind=="chime" else .08
        for j in range(int(dur*sr)):
            tt=j/sr
            v=(math.exp(-tt*4)*(math.sin(2*math.pi*659.25*tt)+.5*math.sin(2*math.pi*987.77*tt))*.11
               if kind=="chime" else math.exp(-tt*35)*math.sin(2*math.pi*1200*tt)*.09)
            if n0+j<len(data): data[n0+j]+=v
    with wave.open(str(WORK/"sfx.wav"),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for start in range(0,len(data),32768):
            wf.writeframes(b"".join(struct.pack("<h",int(max(-1,min(1,v))*32767)) for v in data[start:start+32768]))


def mix_audio():
    inputs=["-i",str(SILENT),"-i",str(WORK/"gentle-bed.wav"),"-i",str(WORK/"sfx.wav")]
    filters=["[1:a]volume=.55[bed]","[2:a]volume=.9[sfx]"]; labels=["[bed]","[sfx]"]
    for idx,(key,start,_) in enumerate(LINES,start=3):
        inputs += ["-i",str(WORK/f"voice-{key}.mp3")]; delay=int(start*1000)
        filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.25[v{idx}]"); labels.append(f"[v{idx}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.95[aout]")
    cmd=["ffmpeg","-y"]+inputs+["-filter_complex",";".join(filters),"-map","0:v:0","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-t",str(DURATION),"-movflags","+faststart",str(OUTPUT)]
    subprocess.run(cmd,check=True)


def main():
    WORK.mkdir(exist_ok=True)
    asyncio.run(make_speech()); make_bed(); make_sfx(); render_video(); mix_audio(); print(OUTPUT)


if __name__=="__main__": main()
