import asyncio
import math
import os
import struct
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "hidden-dinosaurs-work"
PUZZLE = ROOT / "hidden-dinosaurs-puzzle.png"
SILENT = WORK / "hidden-dinosaurs-silent.mp4"
OUTPUT = ROOT / "find-5-hidden-dinosaurs.mp4"
W, H, FPS, DURATION = 1280, 720, 24, 121.0

VOICE = "en-AU-NatashaNeural"
RATE = "-10%"

LINES = [
    ("hello", 0.45, "Hello, kids! Are you ready for a fun dinosaur challenge?"),
    ("five", 6.45, "There are five sneaky dinosaurs hiding somewhere in this prehistoric picture."),
    ("timer", 12.65, "Can you find all five before the timer runs out?"),
    ("careful", 17.30, "Look very carefully... because these dinosaurs are really good at hiding!"),
    ("ready", 23.80, "Ready?"),
    ("starts", 25.70, "Your time starts... now!"),
    ("clue1", 34.00, "Clue one... look behind the big ferns on the left."),
    ("clue2", 40.50, "Clue two... search near the rocks at the lower left."),
    ("clue3", 47.00, "Clue three... look among the plants beside the river."),
    ("clue4", 53.50, "Clue four... check between the tall trees on the right."),
    ("clue5", 59.80, "Clue five... look high near the rocky ledge."),
    ("timesup", 69.30, "Time's up! How many dinosaurs did you find?"),
    ("trex", 74.50, "The T-Rex hid behind the ferns on the left. That was clue one."),
    ("triceratops", 81.00, "The triceratops hid near the lower-left rocks. That was clue two."),
    ("stegosaurus", 87.90, "The stegosaurus hid among the riverbank plants. That was clue three."),
    ("brachiosaurus", 94.30, "The brachiosaurus peeked between the tall trees on the right. That was clue four."),
    ("pterodactyl", 101.60, "The pterodactyl hid high on the rocky ledge. That was clue five. Great searching!"),
    ("subscribe", 110.20, "Did you enjoy the dinosaur challenge? Please like and subscribe for more fun videos like this. See you next time!"),
]


def font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for item in candidates:
        if item.exists():
            return ImageFont.truetype(str(item), size)
    return ImageFont.load_default()


F_SMALL = font(25, True)
F_MED = font(40, True)
F_BIG = font(62, True)
F_HUGE = font(100, True)


def rounded_label(canvas, text, y, size="big", accent=(245, 72, 77), number_five=False, alpha=238):
    draw = ImageDraw.Draw(canvas, "RGBA")
    chosen = {"small": F_SMALL, "med": F_MED, "big": F_BIG, "huge": F_HUGE}[size]
    bbox = draw.textbbox((0, 0), text, font=chosen, stroke_width=2)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 30, 17
    x = (W - tw) // 2
    box = (x-pad_x, y-pad_y, x+tw+pad_x, y+th+pad_y)
    draw.rounded_rectangle(box, radius=25, fill=(255, 252, 230, alpha), outline=(255, 196, 55, 255), width=5)
    draw.text((x+3, y+4), text, font=chosen, fill=(12, 43, 83, 100), stroke_width=2, stroke_fill=(255,255,255,60))
    draw.text((x, y), text, font=chosen, fill=(14, 48, 91, 255), stroke_width=2, stroke_fill=(255,255,255,230))
    if number_five:
        # A playful red ring makes the 5 especially prominent without covering the puzzle.
        pos = text.find("5")
        if pos >= 0:
            pre = draw.textlength(text[:pos], font=chosen)
            five_w = draw.textlength("5", font=chosen)
            cx = int(x + pre + five_w/2)
            cy = int(y + th/2)
            draw.ellipse((cx-39, cy-47, cx+39, cy+47), outline=(231,45,54,255), width=6)


def make_base():
    src = Image.open(PUZZLE).convert("RGB")
    # Edge-to-edge full screen. Preserve the complete horizontal puzzle so no
    # hiding place is cropped; only expand it vertically to the 16:9 canvas.
    sharp = src.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    d = ImageDraw.Draw(sharp, "RGBA")
    d.rounded_rectangle((270, 12, 1000, 96), radius=26,
                        fill=(255,252,231,242), outline=(255,189,40,255), width=5)
    d.text((635, 54), "FIND THE 5 HIDDEN DINOSAURS!", anchor="mm", font=font(37, True),
           fill=(14,48,91,255), stroke_width=1, stroke_fill=(255,255,255,255))
    return sharp, 0, H


def timer(draw, remaining, pulse=1.0):
    cx, cy = 1208, 52
    r = int(39 * pulse)
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(255,252,231,245), outline=(255,185,37,255), width=5)
    draw.arc((cx-r+8, cy-r+8, cx+r-8, cy+r-8), -90, -90 + 360*remaining/40.0, fill=(35,170,158,255), width=6)
    txt = str(max(0, math.ceil(remaining)))
    f = font(int(32*pulse), True)
    bb = draw.textbbox((0,0), txt, font=f)
    draw.text((cx-(bb[2]-bb[0])/2, cy-(bb[3]-bb[1])/2-2), txt, font=f, fill=(16,52,90,255))


def clue_card(frame, heading, body, top=False):
    d = ImageDraw.Draw(frame, "RGBA")
    y1, y2 = (8, 86) if top else (630, 706)
    x1, x2 = (280, 990) if top else (135, 1145)
    d.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=(255,252,231,242), outline=(255,189,40,255), width=4)
    d.text((x1+25, y1+13), heading, font=F_SMALL, fill=(233,71,69,255))
    # The wider intro heading needs its own text column; challenge headings are short.
    body_x = x1 + (390 if not top else 185)
    d.text((body_x, y1+12), body, font=font(25, True), fill=(16,52,90,255))


ANIMALS = [
    ("1  T-REX", (0.198, 0.430), (233, 63, 72), "Behind the ferns on the left"),
    ("2  TRICERATOPS", (0.135, 0.735), (255, 152, 40), "Near the lower-left rocks"),
    ("3  STEGOSAURUS", (0.420, 0.790), (66, 172, 73), "Among the riverbank plants"),
    ("4  BRACHIOSAURUS", (0.815, 0.500), (25, 155, 220), "Between the tall trees"),
    ("5  PTERODACTYL", (0.835, 0.115), (155, 88, 210), "High on the rocky ledge"),
]


def reveal(frame, index, t, puzzle_y, puzzle_h):
    name, (sx, sy), color, desc = ANIMALS[index]
    x = int(sx * W)
    y = int(puzzle_y + sy * puzzle_h)
    d = ImageDraw.Draw(frame, "RGBA")
    rr = int(48 + 5*math.sin(t*5))
    d.ellipse((x-rr, y-rr, x+rr, y+rr), outline=(255,255,255,255), width=9)
    d.ellipse((x-rr+5, y-rr+5, x+rr-5, y+rr-5), outline=color+(255,), width=6)
    d.rounded_rectangle((315, 8, 965, 86), radius=24, fill=(255,252,231,245), outline=color+(255,), width=5)
    bb = d.textbbox((0,0), name, font=F_MED)
    d.text(((W-(bb[2]-bb[0]))/2, 13), name, font=F_MED, fill=color+(255,), stroke_width=1, stroke_fill=(255,255,255,255))
    d.text((W//2, 68), desc, anchor="mm", font=font(20, True), fill=(18,51,86,255))


def render_video():
    base, py, ph = make_base()
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(SILENT)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int(DURATION * FPS)
    for n in range(total):
        t = n / FPS
        frame = base.copy()
        d = ImageDraw.Draw(frame, "RGBA")

        if 0.35 <= t < 3.05:
            rounded_label(frame, "HELLO KIDS!", 292, "big")
            d.text((W//2+245, 330), "\u263a", anchor="mm", font=F_BIG, fill=(255,184,45,255))
        elif 3.05 <= t < 6.35:
            rounded_label(frame, "ARE YOU READY?", 292, "big")
        elif 6.35 <= t < 12.55:
            rounded_label(frame, "FIND 5 HIDDEN DINOSAURS!", 276, "big", number_five=True)
        elif 12.55 <= t < 17.15:
            rounded_label(frame, "CAN YOU FIND ALL 5?", 292, "big", number_five=True)
            # Neutral timer icon animation, kept over the banner rather than any hiding place.
            a = (t-12.55)*3.2
            cx, cy, rr = 1040, 365, int(36+4*math.sin(a))
            d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr), fill=(255,252,231,235), outline=(255,185,37,255), width=5)
            d.line((cx,cy,cx,cy-21), fill=(25,154,154,255), width=5)
            d.line((cx,cy,cx+15,cy+10), fill=(25,154,154,255), width=5)
        elif 17.15 <= t < 23.40:
            # Decorative magnifier travels only across the title/banner area.
            x = int(390 + ((t-17.15)/6.25)*480)
            y = py + 50
            d.ellipse((x-34,y-34,x+34,y+34), outline=(255,255,255,230), width=8)
            d.ellipse((x-34,y-34,x+34,y+34), outline=(31,159,168,210), width=4)
            d.line((x+25,y+25,x+58,y+58), fill=(31,159,168,230), width=10)
            clue_card(frame, "LOOK CAREFULLY", "These dinosaurs are good at hiding!")
        elif 23.40 <= t < 25.65:
            rounded_label(frame, "READY?", 292, "huge")
        elif 28.45 <= t < 30.05:
            rounded_label(frame, "GO!", 278, "huge")

        challenge_start = 29.0
        if challenge_start <= t < 69.0:
            remaining = 69.0 - t
            pulse = 1.16 if remaining <= 5 else 1.0
            timer(d, remaining, pulse)
            if 34.0 <= t < 39.2:
                clue_card(frame, "CLUE 1", "Look behind the big ferns on the left.", top=True)
            elif 40.5 <= t < 45.7:
                clue_card(frame, "CLUE 2", "Search near the lower-left rocks.", top=True)
            elif 47.0 <= t < 52.2:
                clue_card(frame, "CLUE 3", "Look among the plants beside the river.", top=True)
            elif 53.5 <= t < 58.7:
                clue_card(frame, "CLUE 4", "Check between the tall trees on the right.", top=True)
            elif 59.8 <= t < 64.0:
                clue_card(frame, "CLUE 5", "Look high near the rocky ledge.", top=True)
            elif remaining <= 5:
                clue_card(frame, "LAST 5 SECONDS", "Keep looking carefully!", top=True)

        if 69.0 <= t < 74.3:
            rounded_label(frame, "TIME'S UP!", 268, "big")
            d.rounded_rectangle((300, 385, 980, 442), radius=19, fill=(255,252,231,235))
            d.text((W//2, 413), "How many dinosaurs did you find?", anchor="mm", font=font(29, True), fill=(17,50,88,255))

        reveal_times = [(74.45,80.9), (80.9,87.8), (87.8,94.2), (94.2,101.55), (101.55,110.0)]
        for i, (a,b) in enumerate(reveal_times):
            if a <= t < b:
                reveal(frame, i, t-a, py, ph)
                break

        if 110.0 <= t < DURATION:
            d.rounded_rectangle((235, 232, 1045, 492), radius=38,
                                fill=(255,252,231,244), outline=(255,189,40,255), width=7)
            d.text((W//2, 285), "LIKE & SUBSCRIBE!", anchor="mm", font=F_BIG,
                   fill=(233,63,72,255), stroke_width=2, stroke_fill=(255,255,255,255))
            d.text((W//2, 375), "For more dinosaur challenges", anchor="mm", font=F_MED,
                   fill=(16,52,90,255))
            d.text((W//2, 445), "See you next time!", anchor="mm", font=font(28, True),
                   fill=(31,155,158,255))

        proc.stdin.write(frame.convert("RGB").tobytes())
        if n % (FPS*10) == 0:
            print(f"Rendered {n/FPS:.0f}/{DURATION:.0f} seconds", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg video render failed")


async def make_speech():
    for key, _, text in LINES:
        path = WORK / f"voice-{key}.mp3"
        if not path.exists():
            print("Narration:", key, flush=True)
            await edge_tts.Communicate(text, VOICE, rate=RATE, volume="-2%").save(str(path))


def make_bed():
    sr = 44100
    path = WORK / "gentle-bed.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        chunk = bytearray()
        notes = [261.63, 329.63, 392.00, 329.63, 293.66, 349.23, 392.00, 349.23]
        for i in range(int(DURATION*sr)):
            t = i/sr
            note = notes[int(t/4) % len(notes)]
            pad = 0.45*math.sin(2*math.pi*note*t) + 0.25*math.sin(2*math.pi*(note/2)*t)
            sparkle = 0.0
            phase = t % 4.0
            if phase < 0.8:
                sparkle = math.exp(-phase*5)*math.sin(2*math.pi*note*2*t)*0.35
            fade = min(1.0, t/2.0, (DURATION-t)/2.0)
            sample = int(max(-1,min(1,(pad+sparkle)*0.055*fade))*32767)
            chunk += struct.pack("<h", sample)
            if len(chunk) >= 65536:
                wf.writeframes(chunk); chunk.clear()
        if chunk: wf.writeframes(chunk)


def make_sfx():
    sr = 44100
    events = [(28.8, "chime"), (34.0, "chime"), (40.5, "chime"),
              (47.0, "chime"), (53.5, "chime"), (59.8, "chime")]
    # Final five seconds: soft ticks only, with no spoken countdown.
    for tick in [64.0, 65.0, 66.0, 67.0, 68.0]:
        events.append((tick, "tick"))
    path = WORK / "sfx.wav"
    data = [0.0] * int(DURATION*sr)
    for start, kind in events:
        n0 = int(start*sr)
        dur = 0.9 if kind == "chime" else 0.08
        for j in range(int(dur*sr)):
            tt = j/sr
            if kind == "chime":
                val = math.exp(-tt*4.0)*(math.sin(2*math.pi*659.25*tt)+0.55*math.sin(2*math.pi*987.77*tt))*0.12
            else:
                val = math.exp(-tt*35)*math.sin(2*math.pi*1200*tt)*0.09
            if n0+j < len(data): data[n0+j] += val
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for start in range(0,len(data),32768):
            wf.writeframes(b"".join(struct.pack("<h", int(max(-1,min(1,v))*32767)) for v in data[start:start+32768]))


def mix_audio():
    inputs = ["-i", str(SILENT), "-i", str(WORK/"gentle-bed.wav"), "-i", str(WORK/"sfx.wav")]
    filters = ["[1:a]volume=0.55[bed]", "[2:a]volume=0.9[sfx]"]
    labels = ["[bed]", "[sfx]"]
    for idx, (key, start, _) in enumerate(LINES, start=3):
        inputs += ["-i", str(WORK/f"voice-{key}.mp3")]
        delay = int(start*1000)
        filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.25[v{idx}]")
        labels.append(f"[v{idx}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.95[aout]")
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DURATION), "-movflags", "+faststart", str(OUTPUT)]
    subprocess.run(cmd, check=True)


def main():
    WORK.mkdir(exist_ok=True)
    asyncio.run(make_speech())
    make_bed()
    make_sfx()
    render_video()
    mix_audio()
    print(OUTPUT)


if __name__ == "__main__":
    main()
