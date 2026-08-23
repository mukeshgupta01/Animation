import asyncio
import json
import math
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "animal-parent-work"
BACKGROUND = ROOT / "footprint-trail-background.png"
BABY_SHEET_6 = ROOT / "baby-animals-sheet-6.png"
PARENT_SHEET_6 = ROOT / "parent-animals-sheet-6.png"
BABY_SHEET_4 = ROOT / "baby-animals-sheet-4.png"
PARENT_SHEET_4 = ROOT / "parent-animals-sheet-4.png"
SILENT = WORK / "animal-parent-silent.mp4"
OUTPUT = ROOT / "find-the-baby-animals-parent.mp4"
CONTACT = ROOT / "animal-parent-contact-sheet.png"
W, H, VIDEO_FPS, ART_FPS = 1280, 720, 24, 8
VOICE = "en-AU-NatashaNeural"
RATE = "-8%"

ROUNDS = [
    {"baby": "duckling", "answer": "duck", "choices": ["hen", "cow", "duck"],
     "question": "Look at this duckling. Hen, cow, or duck. Which one is its parent?",
     "answer_line": "The duck is the parent! A baby duck is called a duckling.", "fact": "A baby duck is called a duckling."},
    {"baby": "calf", "answer": "cow", "choices": ["cow", "horse", "sheep"],
     "question": "Here comes the next baby. This is a calf. Cow, horse, or sheep. Which one is its parent?",
     "answer_line": "The cow is the parent! A baby cow is called a calf.", "fact": "A baby cow is called a calf."},
    {"baby": "foal", "answer": "horse", "choices": ["cow", "horse", "kangaroo"],
     "question": "Let's meet another little one. Cow, horse, or kangaroo. Which one is the foal's parent?",
     "answer_line": "The horse is the parent! A baby horse is called a foal.", "fact": "A baby horse is called a foal."},
    {"baby": "chick", "answer": "hen", "choices": ["duck", "sheep", "hen"],
     "question": "Look who is next. Duck, sheep, or hen. Which one is the chick's parent?",
     "answer_line": "The hen is the parent! A young chicken is called a chick.", "fact": "A young chicken is called a chick."},
    {"baby": "lion cub", "answer": "lion", "choices": ["dog", "lion", "cat"],
     "question": "Here comes a new baby animal. Dog, lion, or cat. Which one is the cub's parent?",
     "answer_line": "The lion is the parent! A baby lion is called a cub.", "fact": "A baby lion is called a cub."},
    {"baby": "joey", "answer": "kangaroo", "choices": ["kangaroo", "horse", "lion"],
     "question": "Let's try another one. Kangaroo, horse, or lion. Which one is the joey's parent?",
     "answer_line": "The kangaroo is the parent! A baby kangaroo is called a joey.", "fact": "A baby kangaroo is called a joey."},
    {"baby": "puppy", "answer": "dog", "choices": ["cat", "cow", "dog"],
     "question": "Can you match this little one? Cat, cow, or dog. Which one is the puppy's parent?",
     "answer_line": "The dog is the parent! A baby dog is called a puppy.", "fact": "A baby dog is called a puppy."},
    {"baby": "kitten", "answer": "cat", "choices": ["cat", "dog", "lion"],
     "question": "Here comes our next baby. Cat, dog, or lion. Which one is the kitten's parent?",
     "answer_line": "The cat is the parent! A baby cat is called a kitten.", "fact": "A baby cat is called a kitten."},
    {"baby": "lamb", "answer": "sheep", "choices": ["cow", "sheep", "pig"],
     "question": "Take a look at this little one. Cow, sheep, or pig. Which one is the lamb's parent?",
     "answer_line": "The sheep is the parent! A baby sheep is called a lamb.", "fact": "A baby sheep is called a lamb."},
    {"baby": "piglet", "answer": "pig", "choices": ["sheep", "pig", "cow"],
     "question": "And here is our final baby. Sheep, pig, or cow. Which one is the piglet's parent?",
     "answer_line": "The pig is the parent! A baby pig is called a piglet.", "fact": "A baby pig is called a piglet."},
]

COLORS = {
    "navy": (20, 58, 92, 255), "red": (235, 76, 72, 255),
    "yellow": (255, 190, 44, 255), "cream": (255, 253, 232, 246),
    "teal": (31, 160, 154, 255), "green": (58, 169, 87, 255),
    "track": (104, 67, 38, 230),
}


def font(size, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "calibrib.ttf" if bold else "calibri.ttf"]
    for name in names:
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F18, F24, F30, F42, F54 = font(18, True), font(24, True), font(30, True), font(42, True), font(54, True)
BASE = None
BABIES = None
PARENTS = None
LINES = []
DURATION = 0.0


def fit_image(path):
    src = Image.open(path).convert("RGB")
    scale = max(W / src.width, H / src.height)
    res = src.resize((round(src.width * scale), round(src.height * scale)), Image.Resampling.LANCZOS)
    return res.crop(((res.width - W) // 2, (res.height - H) // 2,
                     (res.width - W) // 2 + W, (res.height - H) // 2 + H)).convert("RGBA")


def isolate_grid(path, names):
    src = Image.open(path).convert("RGB")
    rows, cols = len(names), len(names[0])
    result = {}
    for row in range(rows):
        for col in range(cols):
            x1, x2 = round(col * src.width / cols), round((col + 1) * src.width / cols)
            y1, y2 = round(row * src.height / rows), round((row + 1) * src.height / rows)
            crop = src.crop((x1, y1, x2, y2))
            mask = Image.new("L", crop.size, 0)
            cp, mp = crop.load(), mask.load()
            for y in range(crop.height):
                for x in range(crop.width):
                    r, g, b = cp[x, y]
                    distance = 255 - min(r, g, b)
                    mp[x, y] = max(0, min(255, int((distance - 4) * 7.0)))
            mask = mask.filter(ImageFilter.GaussianBlur(0.55))
            rgba = crop.convert("RGBA"); rgba.putalpha(mask)
            bbox = mask.getbbox()
            if not bbox:
                raise RuntimeError(f"Could not isolate {names[row][col]}")
            result[names[row][col]] = rgba.crop(bbox)
    return result


def extract_babies():
    result = isolate_grid(BABY_SHEET_6, [["duckling", "calf", "foal"], ["chick", "lion cub", "joey"]])
    result.update(isolate_grid(BABY_SHEET_4, [["puppy", "kitten"], ["lamb", "piglet"]]))
    return result


def extract_parents():
    result = isolate_grid(PARENT_SHEET_6, [["duck", "cow", "horse"], ["hen", "lion", "kangaroo"]])
    result.update(isolate_grid(PARENT_SHEET_4, [["dog", "cat"], ["sheep", "pig"]]))
    return result


def cover(frame, box, fill=COLORS["cream"], outline=COLORS["yellow"], radius=24, width=4):
    ImageDraw.Draw(frame, "RGBA").rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw, xy, text, fnt, fill, stroke=0):
    draw.text(xy, text, anchor="mm", font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(255, 255, 255, 255))


def paste_contain(frame, art, box):
    x1, y1, x2, y2 = box
    scale = min((x2 - x1) / art.width, (y2 - y1) / art.height)
    size = (max(1, round(art.width * scale)), max(1, round(art.height * scale)))
    res = art.resize(size, Image.Resampling.LANCZOS)
    frame.alpha_composite(res, (x1 + (x2 - x1 - size[0]) // 2, y1 + (y2 - y1 - size[1]) // 2))


def footprint_stamp(animal, size=180):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im, "RGBA")
    c = COLORS["track"]
    if animal == "duck":
        d.polygon([(90, 132), (78, 80), (35, 38), (70, 91), (70, 24), (91, 88), (114, 30), (106, 92), (151, 55), (109, 105)], fill=c)
        d.ellipse((78, 111, 105, 146), fill=c)
    elif animal == "rabbit":
        d.ellipse((38, 18, 78, 105), fill=c); d.ellipse((102, 18, 142, 105), fill=c)
        d.ellipse((55, 112, 82, 154), fill=c); d.ellipse((98, 112, 125, 154), fill=c)
    elif animal == "bear":
        d.ellipse((48, 72, 132, 158), fill=c)
        for x, y, r in [(38, 64, 17), (64, 43, 18), (91, 36, 18), (118, 44, 18), (143, 64, 17)]:
            d.ellipse((x-r, y-r, x+r, y+r), fill=c)
    elif animal == "horse":
        d.ellipse((35, 20, 145, 165), fill=c); d.ellipse((57, 42, 123, 142), fill=(0, 0, 0, 0))
        d.rectangle((57, 20, 123, 72), fill=(0, 0, 0, 0))
    elif animal == "elephant":
        d.ellipse((26, 24, 154, 160), fill=c)
        for x in [48, 70, 92, 114, 136]:
            d.ellipse((x-10, 23, x+10, 48), fill=(127, 85, 48, 220))
    elif animal == "lion":
        d.ellipse((50, 82, 130, 158), fill=c)
        d.polygon([(58, 111), (77, 92), (91, 118), (104, 92), (123, 111), (122, 142), (58, 142)], fill=c)
        for x, y in [(52, 61), (78, 42), (105, 42), (131, 61)]:
            d.ellipse((x-17, y-17, x+17, y+17), fill=c)
    return im


STAMPS = {}


def draw_tracks(frame, animal):
    positions = [(560, 140, -8, .62), (666, 232, 7, .72), (548, 328, -5, .82)]
    for x, y, angle, scale in positions:
        stamp = STAMPS[animal].resize((round(180 * scale), round(180 * scale)), Image.Resampling.LANCZOS).rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        frame.alpha_composite(stamp, (round(x - stamp.width / 2), round(y - stamp.height / 2)))


def draw_round(frame, spec, t):
    d = ImageDraw.Draw(frame, "RGBA"); revealed = t >= spec["reveal"]
    cover(frame, (220, 12, 1060, 94), radius=25)
    centered(d, (640, 34), "BABY ANIMAL", F18, COLORS["red"])
    centered(d, (640, 67), "FIND ITS PARENT!" if not revealed else "THE PARENT IS...", F30, COLORS["navy"])
    cover(frame, (390, 105, 890, 443), fill=(255, 249, 220, 235), radius=34, width=5)
    if revealed:
        paste_contain(frame, BABIES[spec["baby"]], (410, 122, 630, 390))
        paste_contain(frame, PARENTS[spec["answer"]], (650, 122, 855, 390))
        cover(frame, (330, 388, 950, 452), fill=(239, 255, 235, 248), outline=COLORS["green"], radius=18, width=4)
        centered(d, (640, 405), spec["answer"].upper() + "!", F24, COLORS["green"])
        centered(d, (640, 435), spec["fact"], F18, COLORS["navy"])
    else:
        paste_contain(frame, BABIES[spec["baby"]], (500, 120, 780, 395))
        total = max(.1, spec["reveal"] - spec["start"])
        frac = max(0, min(1, (t - spec["start"]) / total))
        cover(frame, (485, 412, 795, 439), fill=(255, 255, 255, 220), outline=(255, 255, 255, 220), radius=13, width=1)
        d.rounded_rectangle((489, 416, 489 + int(302 * (1 - frac)), 435), radius=9, fill=COLORS["teal"])

    boxes = [(85, 470, 435, 697), (465, 470, 815, 697), (845, 470, 1195, 697)]
    for i, (name, box) in enumerate(zip(spec["choices"], boxes)):
        correct = revealed and name == spec["answer"]
        cover(frame, box, fill=(238, 255, 232, 248) if correct else (255, 253, 232, 244),
              outline=COLORS["green"] if correct else COLORS["yellow"], radius=24, width=7 if correct else 4)
        x1, y1, x2, y2 = box
        paste_contain(frame, PARENTS[name], (x1 + 45, y1 + 8, x2 - 18, y2 - 34))
        d.ellipse((x1 + 10, y1 + 10, x1 + 52, y1 + 52), fill=COLORS["navy"])
        centered(d, (x1 + 31, y1 + 31), "ABC"[i], F24, (255, 255, 255, 255))
        centered(d, ((x1 + x2) // 2, y2 - 18), name.upper(), F18, COLORS["green"] if correct else COLORS["navy"])


def frame_at(t):
    frame = BASE.copy(); frame.alpha_composite(Image.new("RGBA", frame.size, (255, 247, 205, 18)))
    d = ImageDraw.Draw(frame, "RGBA")
    if t < ROUNDS[0]["start"]:
        cover(frame, (165, 165, 1115, 545), radius=42, width=7)
        centered(d, (640, 250), "FIND THE BABY'S", F42, COLORS["navy"], 1)
        centered(d, (640, 325), "PARENT!", F54, COLORS["red"], 1)
        centered(d, (640, 410), "10 playful animal matching puzzles", F30, COLORS["teal"])
        centered(d, (640, 475), "Look closely and choose the parent!", F24, COLORS["navy"])
    else:
        spec = next((r for r in ROUNDS if r["start"] <= t < r["end"]), None)
        if spec:
            draw_round(frame, spec, t)
        elif t < ROUNDS[-1]["end"] + 7.0:
            cover(frame, (205, 155, 1075, 555), radius=40, width=7)
            centered(d, (640, 245), "AMAZING WORK!", F54, COLORS["red"], 1)
            centered(d, (640, 330), "HOW MANY DID YOU GUESS?", F42, COLORS["navy"])
            for i, name in enumerate([r["baby"] for r in ROUNDS]):
                col, row = i % 5, i // 5
                paste_contain(frame, BABIES[name], (260 + col * 155, 370 + row * 78, 385 + col * 155, 445 + row * 78))
        else:
            cover(frame, (200, 140, 1080, 580), radius=42, width=7)
            centered(d, (640, 220), "LIKE & SUBSCRIBE", F54, COLORS["red"], 1)
            centered(d, (640, 290), "for more fun puzzles!", F30, COLORS["navy"])
            for i, name in enumerate([r["answer"] for r in ROUNDS]):
                col, row = i % 5, i // 5
                paste_contain(frame, PARENTS[name], (260 + col * 155, 330 + row * 93, 385 + col * 155, 420 + row * 93))
            centered(d, (640, 548), "SEE YOU NEXT TIME!", F24, COLORS["teal"])
    return frame.convert("RGB")


async def make_speech():
    WORK.mkdir(exist_ok=True)
    texts = [("intro", "Can you find each baby animal's parent? Let's begin!")]
    for i, r in enumerate(ROUNDS, 1):
        texts += [(f"round{i}", r["question"]), (f"answer{i}", r["answer_line"])]
    texts += [("score", "Wonderful work! How many of the ten animal parents did you match correctly?"),
              ("subscribe", "Please like and subscribe for more fun puzzles. See you next time!")]
    for key, words in texts:
        path = WORK / f"animal-parent-voice-{key}.mp3"
        if not path.exists():
            print("Narration:", key, flush=True)
            await edge_tts.Communicate(words, VOICE, rate=RATE, volume="-2%").save(str(path))
    return texts


def duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(p.stdout)["format"]["duration"])


def build_timeline(texts):
    global LINES, DURATION
    durations = {key: duration(WORK / f"animal-parent-voice-{key}.mp3") for key, _ in texts}
    LINES = [("intro", .20, dict(texts)["intro"])]
    cursor = max(3.2, .20 + durations["intro"] + .35)
    gaps = []
    for i, r in enumerate(ROUNDS, 1):
        r["index"] = i; r["start"] = cursor
        qstart = cursor + .10; qend = qstart + durations[f"round{i}"]
        reveal = round((qend + 5.0) * ART_FPS) / ART_FPS
        r["reveal"] = reveal
        astart = reveal + .25; aend = astart + durations[f"answer{i}"]
        r["end"] = max(astart + durations[f"answer{i}"] + .45, reveal + 5.8)
        LINES += [(f"round{i}", qstart, r["question"]), (f"answer{i}", astart, r["answer_line"])]
        gaps.append((i, qend, reveal, reveal - qend))
        cursor = r["end"] + .10
    score_start = cursor + .10
    subscribe_start = max(score_start + durations["score"] + .40, ROUNDS[-1]["end"] + 6.25)
    LINES += [("score", score_start, dict(texts)["score"]), ("subscribe", subscribe_start, dict(texts)["subscribe"])]
    DURATION = subscribe_start + durations["subscribe"] + .75
    (WORK / "animal-parent-response-gap-audit.txt").write_text("\n".join(
        f"round{i}: question_end={qe:.3f} reveal={rv:.3f} quiet_gap={gap:.3f}" for i, qe, rv, gap in gaps), encoding="utf-8")
    report = []
    for i, (key, start, _) in enumerate(LINES):
        end = start + durations[key]
        next_start = LINES[i + 1][1] if i + 1 < len(LINES) else DURATION
        gap = next_start - end
        if gap < .18:
            raise RuntimeError(f"Narration overlap after {key}: {gap:.3f}s")
        report.append(f"{key}: start={start:.3f} duration={durations[key]:.3f} end={end:.3f} gap={gap:.3f}")
    (WORK / "animal-parent-timing-audit.txt").write_text("\n".join(report), encoding="utf-8")


def make_audio():
    sr = 24000; n = int(DURATION * sr)
    notes = [261.63, 329.63, 392.0, 349.23, 293.66, 349.23]
    bed = WORK / "animal-parent-bed.wav"; sfx = WORK / "animal-parent-sfx.wav"
    with wave.open(str(bed), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        block = bytearray()
        for i in range(n):
            t = i / sr; f = notes[int(t / 4) % len(notes)]; fade = min(1, t / 1.5, (DURATION - t) / 1.5)
            v = (.48 * math.sin(2 * math.pi * f * t) + .2 * math.sin(2 * math.pi * f / 2 * t)) * .034 * fade
            block += struct.pack("<h", int(v * 32767))
            if len(block) >= 65536: wf.writeframes(block); block.clear()
        if block: wf.writeframes(block)
    data = [0.0] * n
    for r in ROUNDS:
        events = [(r["reveal"], "chime")] + [(r["reveal"] - x, "tick") for x in [5, 4, 3, 2, 1]]
        for start, kind in events:
            n0 = int(start * sr); length = int((.65 if kind == "chime" else .07) * sr)
            for j in range(length):
                tt = j / sr
                v = math.exp(-tt * (4.5 if kind == "chime" else 38)) * math.sin(2 * math.pi * (659 if kind == "chime" else 1020) * tt) * (.09 if kind == "chime" else .05)
                if n0 + j < n: data[n0 + j] += v
    with wave.open(str(sfx), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for k in range(0, n, 32768):
            wf.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in data[k:k+32768]))


def render_silent():
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(ART_FPS), "-i", "-",
           "-an", "-vf", f"fps={VIDEO_FPS}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", str(SILENT)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = math.ceil(DURATION * ART_FPS)
    for n in range(total):
        p.stdin.write(frame_at(n / ART_FPS).tobytes())
        if n % (ART_FPS * 10) == 0: print(f"Rendered {n/ART_FPS:.0f}/{DURATION:.0f} seconds", flush=True)
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError("Video render failed")


def mix_audio():
    inputs = ["-i", str(SILENT), "-i", str(WORK / "animal-parent-bed.wav"), "-i", str(WORK / "animal-parent-sfx.wav")]
    filters = ["[1:a]volume=.50[bed]", "[2:a]volume=.90[sfx]"]; labels = ["[bed]", "[sfx]"]
    for idx, (key, start, _) in enumerate(LINES, 3):
        inputs += ["-i", str(WORK / f"animal-parent-voice-{key}.mp3")]
        delay = round(start * 1000); filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.18[v{idx}]"); labels.append(f"[v{idx}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93[aout]")
    subprocess.run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DURATION), "-movflags", "+faststart", str(OUTPUT)], check=True)


def make_contact_sheet():
    times = []
    for r in ROUNDS: times += [r["start"] + 2.5, r["reveal"] + 1]
    sheet = Image.new("RGB", (1280, 576), "white")
    for i, t in enumerate(times):
        im = frame_at(t).resize((256, 144), Image.Resampling.LANCZOS); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 64, 22), fill="black"); d.text((5, 3), f"{t:.1f}s", font=font(12, True), fill="white")
        sheet.paste(im, ((i % 5) * 256, (i // 5) * 144))
    sheet.save(CONTACT)


def main():
    global BASE, BABIES, PARENTS
    WORK.mkdir(exist_ok=True); BASE = fit_image(BACKGROUND); BABIES = extract_babies(); PARENTS = extract_parents()
    texts = asyncio.run(make_speech()); build_timeline(texts); make_audio(); render_silent(); mix_audio(); make_contact_sheet()
    print(OUTPUT)


if __name__ == "__main__":
    main()
