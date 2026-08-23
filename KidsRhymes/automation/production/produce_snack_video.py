"""Render a polished 1080p Tiny Tales animal-food guessing game."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
from pathlib import Path
import struct
import subprocess
import wave

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


HERE = Path(__file__).resolve().parent
AUTOMATION = HERE.parent
PROJECT = AUTOMATION.parent
ASSET = AUTOMATION / "production-assets" / "snack-suspects-sheet.png"
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
W, H = 1920, 1080
ART_FPS, VIDEO_FPS = 10, 30
VOICE = "en-US-AnaNeural"
VOICE_RATE = "-4%"
VOICE_PITCH = "+10Hz"

ANIMALS = [["rabbit", "panda", "monkey"], ["mouse", "giraffe", "squirrel"]]
ROUNDS = [
    {
        "animal": "rabbit", "snack": "crunchy carrots", "choices": ["mouse", "rabbit", "monkey"],
        "question": "Who ate the crunchy carrots? Was it the mouse, rabbit, or monkey?",
        "answer": "It was the rabbit!",
        "fact": "Rabbits enjoy leafy plants and vegetables. Carrots are a tasty treat, not an everyday meal.",
    },
    {
        "animal": "panda", "snack": "fresh bamboo", "choices": ["panda", "giraffe", "squirrel"],
        "question": "Who munched the fresh bamboo? Was it the panda, giraffe, or squirrel?",
        "answer": "It was the panda!",
        "fact": "Giant pandas spend many hours each day eating bamboo leaves and stems.",
    },
    {
        "animal": "monkey", "snack": "yellow banana", "choices": ["rabbit", "mouse", "monkey"],
        "question": "Who peeled the yellow banana? Was it the rabbit, mouse, or monkey?",
        "answer": "It was the monkey!",
        "fact": "Many monkeys eat fruit, but they also enjoy leaves, seeds, and insects.",
    },
    {
        "animal": "mouse", "snack": "little cheese wedge", "choices": ["squirrel", "mouse", "panda"],
        "question": "Who nibbled the little cheese wedge? Was it the squirrel, mouse, or panda?",
        "answer": "It was the mouse!",
        "fact": "Cartoon mice love cheese, but real mice usually choose grains, seeds, and fruit.",
    },
    {
        "animal": "giraffe", "snack": "tall green leaves", "choices": ["monkey", "giraffe", "rabbit"],
        "question": "Who reached the tall green leaves? Was it the monkey, giraffe, or rabbit?",
        "answer": "It was the giraffe!",
        "fact": "A giraffe uses its long neck and tongue to reach leaves high in the trees.",
    },
    {
        "animal": "squirrel", "snack": "shiny brown acorn", "choices": ["panda", "squirrel", "mouse"],
        "question": "Who carried away the shiny brown acorn? Was it the panda, squirrel, or mouse?",
        "answer": "It was the squirrel!",
        "fact": "Squirrels hide nuts and seeds in many places so they can find food later.",
    },
]

PALETTES = [
    ((124, 211, 246), (255, 231, 139), (255, 110, 98)),
    ((148, 224, 177), (255, 225, 146), (55, 151, 133)),
    ((190, 170, 241), (255, 213, 149), (111, 81, 181)),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = ["arialbd.ttf" if bold else "arial.ttf", "calibrib.ttf" if bold else "calibri.ttf"]
    for name in candidates:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F24, F30, F38, F48, F62, F78 = (font(s, True) for s in (24, 30, 38, 48, 62, 78))


def centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, face: ImageFont.ImageFont, fill: tuple[int, ...], stroke: int = 0) -> None:
    draw.text(xy, text, anchor="mm", font=face, fill=fill, stroke_width=stroke, stroke_fill=(255, 255, 255, 255))


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.ImageFont, width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        proposed = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), proposed, font=face)[2] > width:
            lines.append(current)
            current = word
        else:
            current = proposed
    if current:
        lines.append(current)
    return lines


def gradient_background(index: int, t: float) -> Image.Image:
    top, bottom, accent = PALETTES[index % len(PALETTES)]
    image = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(H):
        mix = y / (H - 1)
        colour = tuple(round(top[c] * (1 - mix) + bottom[c] * mix) for c in range(3))
        draw.line((0, y, W, y), fill=colour)
    for i in range(22):
        x = (i * 227 + int(t * 24)) % (W + 100) - 50
        y = 125 + (i * 149 + int(t * 17)) % 780
        radius = 9 + (i % 4) * 5
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=accent + (34,))
    return image.convert("RGBA")


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], outline=(255, 190, 52, 255), fill=(255, 254, 239, 247), radius=34, width=6) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def extract_animals() -> dict[str, Image.Image]:
    source = Image.open(ASSET).convert("RGB")
    result = {}
    for row, names in enumerate(ANIMALS):
        for col, name in enumerate(names):
            x1, x2 = round(col * source.width / 3), round((col + 1) * source.width / 3)
            y1, y2 = round(row * source.height / 2), round((row + 1) * source.height / 2)
            crop = source.crop((x1, y1, x2, y2))
            # Remove only the near-white studio border, retaining soft character edges.
            mask = Image.new("L", crop.size)
            pixels, alpha = crop.load(), mask.load()
            for y in range(crop.height):
                for x in range(crop.width):
                    r, g, b = pixels[x, y]
                    distance = 255 - min(r, g, b)
                    alpha[x, y] = max(0, min(255, int((distance - 2) * 8)))
            mask = mask.filter(ImageFilter.GaussianBlur(0.6))
            rgba = crop.convert("RGBA")
            rgba.putalpha(mask)
            bbox = mask.getbbox()
            if not bbox:
                raise RuntimeError(f"Could not isolate {name}")
            result[name] = rgba.crop(bbox)
    return result


def contain(frame: Image.Image, art: Image.Image, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    scale = min((x2 - x1) / art.width, (y2 - y1) / art.height)
    size = (max(1, round(art.width * scale)), max(1, round(art.height * scale)))
    resized = art.resize(size, Image.Resampling.LANCZOS)
    frame.alpha_composite(resized, (x1 + (x2 - x1 - size[0]) // 2, y1 + (y2 - y1 - size[1]) // 2))


def draw_snack(frame: Image.Image, name: str, centre=(960, 380), scale=1.0) -> None:
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    cx, cy = centre
    s = scale
    if "carrot" in name:
        d.polygon([(cx - 90*s, cy - 75*s), (cx + 92*s, cy), (cx - 90*s, cy + 75*s)], fill=(244, 116, 40, 255), outline=(187, 73, 24, 255))
        for dy in (-48, 0, 48): d.line((cx-35*s, cy+dy*s, cx+35*s, cy+dy*.45*s), fill=(255, 174, 75, 220), width=max(2, int(7*s)))
        for angle in (-.55, 0, .55):
            ex=cx-145*s; ey=cy+math.sin(angle)*100*s
            d.ellipse((ex-55*s,ey-25*s,ex+45*s,ey+25*s),fill=(63,171,83,255))
    elif "bamboo" in name:
        for offset, angle in [(-45,-.12),(20,.08),(72,-.05)]:
            x=cx+offset*s; d.rounded_rectangle((x-22*s,cy-135*s,x+22*s,cy+135*s),radius=int(18*s),fill=(86,177,79,255),outline=(41,126,55,255),width=max(2,int(5*s)))
            for yy in (-65,12,82): d.line((x-20*s,cy+yy*s,x+20*s,cy+yy*s),fill=(42,130,56,255),width=max(2,int(5*s)))
    elif "banana" in name:
        d.arc((cx-150*s,cy-135*s,cx+150*s,cy+135*s),20,160,fill=(255,209,48,255),width=max(10,int(70*s)))
        d.arc((cx-150*s,cy-135*s,cx+150*s,cy+135*s),22,158,fill=(255,235,94,255),width=max(4,int(42*s)))
    elif "cheese" in name:
        d.polygon([(cx-135*s,cy+95*s),(cx+135*s,cy+95*s),(cx+70*s,cy-115*s)],fill=(255,210,60,255),outline=(218,153,28,255))
        for ox,oy,r in [(-55,45,20),(45,50,15),(45,-20,18)]: d.ellipse(((cx+ox-r)*s+cx*(1-s),(cy+oy-r)*s+cy*(1-s),(cx+ox+r)*s+cx*(1-s),(cy+oy+r)*s+cy*(1-s)),fill=(224,161,35,255))
    elif "leaves" in name:
        d.line((cx,cy+135*s,cx,cy-100*s),fill=(72,133,57,255),width=max(4,int(14*s)))
        for ox,oy,flip in [(-75,-65,-1),(70,-25,1),(-65,25,-1),(55,70,1)]:
            d.ellipse((cx+ox*s-55*s,cy+oy*s-28*s,cx+ox*s+55*s,cy+oy*s+28*s),fill=(79,179,88,255),outline=(43,129,58,255),width=max(2,int(4*s)))
    else:
        d.ellipse((cx-95*s,cy-70*s,cx+95*s,cy+120*s),fill=(155,88,43,255),outline=(101,55,25,255),width=max(2,int(6*s)))
        d.polygon([(cx-115*s,cy-50*s),(cx,cy-135*s),(cx+115*s,cy-50*s)],fill=(103,66,38,255))
        d.line((cx,cy-130*s,cx+22*s,cy-165*s),fill=(81,55,32,255),width=max(2,int(10*s)))
    frame.alpha_composite(layer)


def header(frame: Image.Image, title_text: str, subtitle: str = "") -> None:
    d = ImageDraw.Draw(frame, "RGBA")
    panel(d, (235, 28, 1685, 151), radius=38, width=7)
    centered(d, (960, 76), title_text, F48, (28, 69, 99, 255))
    if subtitle:
        centered(d, (960, 126), subtitle, F24, (219, 75, 67, 255))


def intro_frame(t: float) -> Image.Image:
    frame = gradient_background(0, t)
    d = ImageDraw.Draw(frame, "RGBA")
    panel(d, (230, 205, 1690, 890), radius=55, width=9)
    centered(d, (960, 320), "WHO ATE THE SNACK?", F78, (226, 75, 67, 255), 2)
    centered(d, (960, 430), "6 ANIMAL FOOD CLUES", F48, (31, 93, 125, 255))
    draw_snack(frame, "yellow banana", (960, 655), .9)
    centered(d, (960, 835), "LOOK  •  GUESS  •  LEARN", F30, (47, 151, 105, 255))
    return frame.convert("RGB")


def round_frame(spec: dict, index: int, t: float, reveal: bool, animals: dict[str, Image.Image], fraction: float) -> Image.Image:
    frame = gradient_background(index, t)
    d = ImageDraw.Draw(frame, "RGBA")
    header(frame, "WHO ATE THE SNACK?", "LET'S CHECK THE NEXT ONE")
    if not reveal:
        panel(d, (660, 178, 1260, 535), fill=(255, 250, 221, 242), radius=45, width=7)
        draw_snack(frame, spec["snack"], (960, 350), .9)
        centered(d, (960, 490), spec["snack"].upper(), F30, (36, 81, 106, 255))
        panel(d, (680, 548, 1240, 588), fill=(255,255,255,225), outline=(255,255,255,225), radius=18, width=1)
        d.rounded_rectangle((686, 554, 686 + int(548 * (1 - fraction)), 582), radius=13, fill=(41, 164, 151, 255))
    else:
        panel(d, (560, 177, 1360, 540), fill=(238, 255, 234, 244), outline=(65, 171, 95, 255), radius=45, width=8)
        contain(frame, animals[spec["animal"]], (760, 190, 1160, 475))
        centered(d, (960, 492), f"IT WAS THE {spec['animal'].upper()}!", F38, (45, 148, 81, 255))

    boxes = [(115, 635, 605, 1015), (715, 635, 1205, 1015), (1315, 635, 1805, 1015)]
    for choice_index, (name, box) in enumerate(zip(spec["choices"], boxes)):
        correct = reveal and name == spec["animal"]
        outline = (61, 174, 91, 255) if correct else (255, 188, 50, 255)
        fill = (235, 255, 231, 247) if correct else (255, 254, 239, 244)
        panel(d, box, outline=outline, fill=fill, radius=35, width=10 if correct else 6)
        x1,y1,x2,y2=box
        contain(frame, animals[name], (x1+65,y1+15,x2-65,y2-75))
        d.ellipse((x1+18,y1+18,x1+78,y1+78),fill=(24,70,102,255))
        centered(d,(x1+48,y1+48),"ABC"[choice_index],F30,(255,255,255,255))
        centered(d,((x1+x2)//2,y2-36),name.upper(),F30,(43,149,80,255) if correct else (25,66,94,255))
    return frame.convert("RGB")


def fact_frame(spec: dict, index: int, t: float, animals: dict[str, Image.Image]) -> Image.Image:
    frame = gradient_background(index + 1, t)
    d = ImageDraw.Draw(frame, "RGBA")
    header(frame, "A TINY ANIMAL FACT", f"{spec['animal'].upper()} + {spec['snack'].upper()}")
    panel(d, (250, 205, 1670, 900), outline=(59, 166, 145, 255), radius=50, width=8)
    contain(frame, animals[spec["animal"]], (310, 260, 770, 815))
    draw_snack(frame, spec["snack"], (1410, 505), .68)
    lines = wrap_lines(d, spec["fact"], F38, 710)
    y = 390 - (len(lines)-1)*34
    for line in lines:
        centered(d, (1060, y), line, F38, (28, 69, 98, 255))
        y += 72
    return frame.convert("RGB")


def ending_frame(t: float, animals: dict[str, Image.Image]) -> Image.Image:
    frame = gradient_background(2, t)
    d = ImageDraw.Draw(frame, "RGBA")
    panel(d, (240, 175, 1680, 900), radius=52, width=9)
    centered(d, (960, 280), "AMAZING ANIMAL DETECTIVE!", F62, (223, 74, 67, 255), 2)
    centered(d, (960, 380), "HOW MANY DID YOU GUESS?", F48, (28, 70, 100, 255))
    for i, name in enumerate(["rabbit","panda","monkey","mouse","giraffe","squirrel"]):
        contain(frame, animals[name], (270+i*235,470,470+i*235,730))
    centered(d, (960, 800), "LIKE & SUBSCRIBE FOR MORE TINY TALES", F38, (46, 151, 102, 255))
    return frame.convert("RGB")


def speech_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_speech(work: Path) -> list[tuple[str, str]]:
    lines = [("intro", "Welcome to Who Ate the Snack! Look at each food clue, choose an animal, and get ready to learn.")]
    for i, spec in enumerate(ROUNDS, 1):
        lines.extend([(f"q{i}", spec["question"]), (f"a{i}", spec["answer"]), (f"f{i}", spec["fact"])])
    lines.append(("outro", "Amazing animal detective work! How many did you guess? Please like and subscribe for more Tiny Tales. See you next time!"))
    for key, text in lines:
        target = speech_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, VOICE, rate=VOICE_RATE, pitch=VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def duration(path: Path) -> float:
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    return float(json.loads(subprocess.check_output(command, text=True))["format"]["duration"])


def build_timeline(work: Path, lines: list[tuple[str, str]]) -> tuple[list[dict], list[tuple[str,float]], float]:
    durations = {key: duration(speech_path(work,key)) for key,_ in lines}
    events, voices = [], []
    cursor = .35
    def add(kind: str, length: float, **extra) -> dict:
        nonlocal cursor
        event={"kind":kind,"start":cursor,"end":cursor+length,**extra};events.append(event);cursor=event["end"];return event
    intro=add("intro",max(6.5,durations["intro"]+.8));voices.append(("intro",intro["start"]+.15))
    audits=[]
    for i,spec in enumerate(ROUNDS,1):
        question=add("question",durations[f"q{i}"],index=i,spec=spec);voices.append((f"q{i}",question["start"]))
        guess=add("guess",5.0,index=i,spec=spec)
        reveal=add("reveal",max(3.2,durations[f"a{i}"]+.55),index=i,spec=spec);voices.append((f"a{i}",reveal["start"]+.18))
        fact=add("fact",durations[f"f{i}"]+.75,index=i,spec=spec);voices.append((f"f{i}",fact["start"]+.12))
        audits.append(f"round{i}: question_end={question['end']:.3f} reveal={reveal['start']:.3f} response_window={reveal['start']-question['end']:.3f}")
    outro=add("outro",max(8.5,durations["outro"]+.85));voices.append(("outro",outro["start"]+.1))
    total=math.ceil(cursor*ART_FPS)/ART_FPS
    (work/"response-window-audit.txt").write_text("\n".join(audits)+"\n",encoding="utf-8")
    return events,voices,total


def frame_at(t: float, events: list[dict], animals: dict[str,Image.Image]) -> Image.Image:
    event=next((item for item in events if item["start"]<=t<item["end"]),events[-1])
    if event["kind"]=="intro": return intro_frame(t)
    if event["kind"]=="outro": return ending_frame(t,animals)
    if event["kind"]=="fact": return fact_frame(event["spec"],event["index"],t,animals)
    reveal=event["kind"]=="reveal"
    fraction=0 if reveal else max(0,min(1,(t-event["start"])/(event["end"]-event["start"])))
    return round_frame(event["spec"],event["index"],t,reveal,animals,fraction)


def make_audio_bed(work: Path, total: float, events: list[dict]) -> tuple[Path,Path]:
    sr=48000;n=int(total*sr);bed=work/"music-bed.wav";sfx=work/"answer-sfx.wav"
    chords=[(261.63,329.63,392.0),(293.66,369.99,440.0),(349.23,440.0,523.25),(329.63,392.0,493.88)]
    with wave.open(str(bed),"wb") as wf:
        wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(sr);block=bytearray()
        for i in range(n):
            t=i/sr;chord=chords[int(t/8)%len(chords)];beat=t%.5;pluck=math.exp(-7*beat)
            value=sum(math.sin(2*math.pi*f*t) for f in chord)/3*.018 + math.sin(2*math.pi*chord[1]*2*t)*pluck*.014
            fade=min(1,t/1.5,(total-t)/1.5);sample=int(max(-1,min(1,value*fade))*32767)
            block+=struct.pack("<hh",sample,sample)
            if len(block)>=131072:wf.writeframes(block);block.clear()
        if block:wf.writeframes(block)
    samples=[0.0]*n
    for event in events:
        if event["kind"]=="guess":
            for seconds_left in (4,3,2,1):
                start=event["end"]-seconds_left
                for j in range(int(.075*sr)):
                    tt=j/sr;samples[int(start*sr)+j]+=math.exp(-42*tt)*math.sin(2*math.pi*1050*tt)*.045
        if event["kind"]=="reveal":
            start=event["start"]
            for j in range(int(.75*sr)):
                tt=j/sr;samples[int(start*sr)+j]+=math.exp(-4.5*tt)*(math.sin(2*math.pi*659.25*tt)+.45*math.sin(2*math.pi*987.77*tt))*.075
    with wave.open(str(sfx),"wb") as wf:
        wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(sr)
        for offset in range(0,n,32768):
            data=bytearray()
            for value in samples[offset:offset+32768]:
                sample=int(max(-1,min(1,value))*32767);data+=struct.pack("<hh",sample,sample)
            wf.writeframes(data)
    return bed,sfx


def render(work: Path, output: Path, total: float, events: list[dict], voices: list[tuple[str,float]], animals: dict[str,Image.Image]) -> None:
    silent=work/"silent.mp4";frames=math.ceil(total*ART_FPS)
    command=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","medium","-crf","18","-profile:v","high","-level","4.1","-pix_fmt","yuv420p",str(silent)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    for number in range(frames):
        process.stdin.write(frame_at(number/ART_FPS,events,animals).tobytes())
        if number%(ART_FPS*15)==0:print(f"Rendered {number/ART_FPS:.0f}/{total:.0f}s",flush=True)
    process.stdin.close()
    if process.wait()!=0:raise RuntimeError("Silent video render failed")
    bed,sfx=make_audio_bed(work,total,events)
    inputs=["-i",str(silent),"-i",str(bed),"-i",str(sfx)];filters=["[1:a]volume=.68[bed]","[2:a]volume=1.0[sfx]"];labels=["[bed]","[sfx]"]
    for index,(key,start) in enumerate(voices,3):
        inputs.extend(["-i",str(speech_path(work,key))]);delay=round(start*1000)
        filters.append(f"[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.22[v{index}]");labels.append(f"[v{index}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    command=["ffmpeg","-y","-loglevel","error"]+inputs+["-filter_complex",";".join(filters),"-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t",f"{total:.3f}","-movflags","+faststart",str(output)]
    subprocess.run(command,check=True)


def quality_check(work: Path, output: Path, total: float, events: list[dict], animals: dict[str,Image.Image]) -> None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels","-of","json",str(output)],text=True))
    streams=probe["streams"];video=next((s for s in streams if s["codec_type"]=="video"),None);audio=next((s for s in streams if s["codec_type"]=="audio"),None)
    checks={
        "video_exists":output.exists() and output.stat().st_size>1_000_000,
        "duration_matches":abs(float(probe["format"]["duration"])-total)<.25,
        "video_h264_1080p":bool(video and video.get("codec_name")=="h264" and video.get("width")==W and video.get("height")==H and video.get("r_frame_rate")=="30/1"),
        "audio_aac_48k_stereo":bool(audio and audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2),
        "six_response_windows":len([e for e in events if e["kind"]=="guess"])==6,
    }
    report={"output":str(output),"duration_seconds":float(probe["format"]["duration"]),"size_bytes":int(probe["format"]["size"]),"checks":checks,"passed":all(checks.values())}
    (work/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    times=[1.5]
    for event in events:
        if event["kind"] in ("question","reveal","fact"):times.append(event["start"]+min(1.5,(event["end"]-event["start"])/2))
    times.append(total-1.5)
    contact=Image.new("RGB",(960,math.ceil(len(times)/4)*135),"white")
    for i,t in enumerate(times):
        image=frame_at(t,events,animals).resize((240,135),Image.Resampling.LANCZOS);d=ImageDraw.Draw(image);d.rectangle((0,0,56,19),fill="black");d.text((3,2),f"{t:.1f}s",font=font(12,True),fill="white")
        contact.paste(image,((i%4)*240,(i//4)*135))
    contact.save(work/"quality-contact-sheet.png")
    if not report["passed"]:raise RuntimeError(f"Quality gate failed: {report}")


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--episode",type=int,default=1);args=parser.parse_args()
    if args.episode!=1:raise RuntimeError("Only curated episode 1 is currently approved")
    if not ASSET.exists():raise FileNotFoundError(ASSET)
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True);work=WORK_ROOT/f"snack-episode-{args.episode:02d}";work.mkdir(parents=True,exist_ok=True)
    output=OUTPUT_DIR/f"who-ate-the-snack-episode-{args.episode:02d}.mp4"
    if output.exists():
        print(f"Completed output already exists; preserving without regeneration: {output}")
        return
    animals=extract_animals();lines=asyncio.run(make_speech(work));events,voices,total=build_timeline(work,lines);render(work,output,total,events,voices,animals);quality_check(work,output,total,events,animals)
    print(output)


if __name__=="__main__":main()
