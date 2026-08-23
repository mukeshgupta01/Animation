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
WORK = ROOT / "animal-homes-work"
BACKGROUND = ROOT / "footprint-trail-background.png"
SHEET = ROOT / "animal-homes-characters.png"
HOMES_SHEET = ROOT / "animal-homes-sheet.png"
SILENT = WORK / "animal-homes-silent.mp4"
OUTPUT = ROOT / "who-lives-here-animal-homes.mp4"
CONTACT = ROOT / "animal-homes-contact-sheet.png"
W, H, VIDEO_FPS, ART_FPS = 1280, 720, 24, 8
VOICE = "en-AU-NatashaNeural"
RATE = "-8%"

ROUNDS = [
    {"answer": "beaver", "home": "lodge", "choices": ["rabbit", "beaver", "frog"],
     "question": "Round one. Rabbit, beaver, or frog. Who lives here?",
     "answer_line": "The beaver lives here! Beavers build strong lodges from branches, mud, and plants.",
     "fact": "Beavers build lodges from branches, mud, and plants."},
    {"answer": "bee", "home": "hive", "choices": ["bird", "spider", "bee"],
     "question": "Round two. Bird, spider, or bee. Who lives here?",
     "answer_line": "The bee lives here! Bees work together in a hive and store honey inside.",
     "fact": "Bees live together and store honey inside."},
    {"answer": "spider", "home": "web", "choices": ["spider", "bee", "frog"],
     "question": "Round three. Spider, bee, or frog. Who lives here?",
     "answer_line": "The spider lives here! A spider spins silk to make its web.",
     "fact": "A spider spins strong silk to make its web."},
    {"answer": "rabbit", "home": "burrow", "choices": ["beaver", "bird", "rabbit"],
     "question": "Round four. Beaver, bird, or rabbit. Who lives here?",
     "answer_line": "The rabbit lives here! A rabbit's underground home is called a burrow.",
     "fact": "A rabbit's underground home is called a burrow."},
    {"answer": "bird", "home": "nest", "choices": ["rabbit", "bird", "bee"],
     "question": "Round five. Rabbit, bird, or bee. Who lives here?",
     "answer_line": "The bird lives here! Birds weave twigs and grass into safe, cozy nests.",
     "fact": "Birds weave twigs and grass into safe nests."},
    {"answer": "frog", "home": "pond", "choices": ["frog", "spider", "beaver"],
     "question": "Final round. Frog, spider, or beaver. Who lives here?",
     "answer_line": "The frog lives here! Ponds give frogs water, plants, and plenty of insects to eat.",
     "fact": "Ponds provide water, plants, and food for frogs."},
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
ANIMALS = None
HOMES = None
LINES = []
DURATION = 0.0


def fit_image(path):
    src = Image.open(path).convert("RGB")
    scale = max(W / src.width, H / src.height)
    res = src.resize((round(src.width * scale), round(src.height * scale)), Image.Resampling.LANCZOS)
    return res.crop(((res.width - W) // 2, (res.height - H) // 2,
                     (res.width - W) // 2 + W, (res.height - H) // 2 + H)).convert("RGBA")


def extract_animals():
    src = Image.open(SHEET).convert("RGB")
    names = [["beaver", "bee", "spider"], ["rabbit", "bird", "frog"]]
    result = {}
    for row in range(2):
        for col in range(3):
            x1, x2 = round(col * src.width / 3), round((col + 1) * src.width / 3)
            y1, y2 = round(row * src.height / 2), round((row + 1) * src.height / 2)
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


def extract_homes():
    src = Image.open(HOMES_SHEET).convert("RGBA")
    names = [["lodge", "hive", "web"], ["burrow", "nest", "pond"]]
    result = {}
    gutter = 8
    for row in range(2):
        for col in range(3):
            x1, x2 = round(col * src.width / 3) + gutter, round((col + 1) * src.width / 3) - gutter
            y1, y2 = round(row * src.height / 2) + gutter, round((row + 1) * src.height / 2) - gutter
            result[names[row][col]] = src.crop((x1, y1, x2, y2))
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
    centered(d, (640, 34), f"ROUND {spec['index']}", F18, COLORS["red"])
    centered(d, (640, 67), "WHO LIVES HERE?" if not revealed else "THIS HOME BELONGS TO...", F30, COLORS["navy"])
    cover(frame, (390, 105, 890, 443), fill=(255, 249, 220, 235), radius=34, width=5)
    if revealed:
        paste_contain(frame, HOMES[spec["home"]], (410, 122, 630, 390))
        paste_contain(frame, ANIMALS[spec["answer"]], (650, 122, 855, 390))
        cover(frame, (330, 388, 950, 452), fill=(239, 255, 235, 248), outline=COLORS["green"], radius=18, width=4)
        centered(d, (640, 405), spec["answer"].upper() + "!", F24, COLORS["green"])
        centered(d, (640, 435), spec["fact"], F18, COLORS["navy"])
    else:
        paste_contain(frame, HOMES[spec["home"]], (415, 120, 865, 405))
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
        paste_contain(frame, ANIMALS[name], (x1 + 45, y1 + 8, x2 - 18, y2 - 34))
        d.ellipse((x1 + 10, y1 + 10, x1 + 52, y1 + 52), fill=COLORS["navy"])
        centered(d, (x1 + 31, y1 + 31), "ABC"[i], F24, (255, 255, 255, 255))
        centered(d, ((x1 + x2) // 2, y2 - 18), name.upper(), F18, COLORS["green"] if correct else COLORS["navy"])


def frame_at(t):
    frame = BASE.copy(); frame.alpha_composite(Image.new("RGBA", frame.size, (255, 247, 205, 18)))
    d = ImageDraw.Draw(frame, "RGBA")
    if t < ROUNDS[0]["start"]:
        cover(frame, (165, 165, 1115, 545), radius=42, width=7)
        centered(d, (640, 250), "WHO LIVES", F42, COLORS["navy"], 1)
        centered(d, (640, 325), "HERE?", F54, COLORS["red"], 1)
        centered(d, (640, 410), "6 playful animal-home puzzles", F30, COLORS["teal"])
        centered(d, (640, 475), "Look closely and choose the animal!", F24, COLORS["navy"])
    else:
        spec = next((r for r in ROUNDS if r["start"] <= t < r["end"]), None)
        if spec:
            draw_round(frame, spec, t)
        elif t < ROUNDS[-1]["end"] + 6.2:
            cover(frame, (205, 155, 1075, 555), radius=40, width=7)
            centered(d, (640, 245), "AMAZING WORK!", F54, COLORS["red"], 1)
            centered(d, (640, 330), "HOW MANY DID YOU GUESS?", F42, COLORS["navy"])
            for i, name in enumerate(["beaver", "bee", "spider", "rabbit", "bird", "frog"]):
                paste_contain(frame, ANIMALS[name], (180 + i * 150, 385, 320 + i * 150, 525))
        else:
            cover(frame, (200, 140, 1080, 580), radius=42, width=7)
            centered(d, (640, 220), "LIKE & SUBSCRIBE", F54, COLORS["red"], 1)
            centered(d, (640, 290), "for more fun puzzles!", F30, COLORS["navy"])
            for i, name in enumerate(["beaver", "bee", "spider", "rabbit", "bird", "frog"]):
                paste_contain(frame, ANIMALS[name], (180 + i * 150, 330, 320 + i * 150, 510))
            centered(d, (640, 548), "SEE YOU NEXT TIME!", F24, COLORS["teal"])
    return frame.convert("RGB")


async def make_speech():
    WORK.mkdir(exist_ok=True)
    texts = [("intro", "Who lives here? Let's begin!")]
    for i, r in enumerate(ROUNDS, 1):
        texts += [(f"round{i}", r["question"]), (f"answer{i}", r["answer_line"])]
    texts += [("score", "Wonderful work! How many of the six animal homes did you guess correctly?"),
              ("subscribe", "Please like and subscribe for more fun puzzles. See you next time!")]
    for key, words in texts:
        path = WORK / f"animal-homes-voice-{key}.mp3"
        if not path.exists():
            print("Narration:", key, flush=True)
            await edge_tts.Communicate(words, VOICE, rate=RATE, volume="-2%").save(str(path))
    return texts


def duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(p.stdout)["format"]["duration"])


def build_timeline(texts):
    global LINES, DURATION
    durations = {key: duration(WORK / f"animal-homes-voice-{key}.mp3") for key, _ in texts}
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
    (WORK / "animal-homes-response-gap-audit.txt").write_text("\n".join(
        f"round{i}: question_end={qe:.3f} reveal={rv:.3f} quiet_gap={gap:.3f}" for i, qe, rv, gap in gaps), encoding="utf-8")
    report = []
    for i, (key, start, _) in enumerate(LINES):
        end = start + durations[key]
        next_start = LINES[i + 1][1] if i + 1 < len(LINES) else DURATION
        gap = next_start - end
        if gap < .18:
            raise RuntimeError(f"Narration overlap after {key}: {gap:.3f}s")
        report.append(f"{key}: start={start:.3f} duration={durations[key]:.3f} end={end:.3f} gap={gap:.3f}")
    (WORK / "animal-homes-timing-audit.txt").write_text("\n".join(report), encoding="utf-8")


def make_audio():
    sr = 24000; n = int(DURATION * sr)
    notes = [261.63, 329.63, 392.0, 349.23, 293.66, 349.23]
    bed = WORK / "animal-homes-bed.wav"; sfx = WORK / "animal-homes-sfx.wav"
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
    inputs = ["-i", str(SILENT), "-i", str(WORK / "animal-homes-bed.wav"), "-i", str(WORK / "animal-homes-sfx.wav")]
    filters = ["[1:a]volume=.50[bed]", "[2:a]volume=.90[sfx]"]; labels = ["[bed]", "[sfx]"]
    for idx, (key, start, _) in enumerate(LINES, 3):
        inputs += ["-i", str(WORK / f"animal-homes-voice-{key}.mp3")]
        delay = round(start * 1000); filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.18[v{idx}]"); labels.append(f"[v{idx}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93[aout]")
    subprocess.run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DURATION), "-movflags", "+faststart", str(OUTPUT)], check=True)


def make_contact_sheet():
    times = []
    for r in ROUNDS: times += [r["start"] + 2.5, r["reveal"] + 1]
    sheet = Image.new("RGB", (1280, 540), "white")
    for i, t in enumerate(times):
        im = frame_at(t).resize((320, 180), Image.Resampling.LANCZOS); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 72, 24), fill="black"); d.text((5, 3), f"{t:.1f}s", font=font(14, True), fill="white")
        sheet.paste(im, ((i % 4) * 320, (i // 4) * 180))
    sheet.save(CONTACT)


def main():
    global BASE, ANIMALS, HOMES
    WORK.mkdir(exist_ok=True); BASE = fit_image(BACKGROUND); ANIMALS = extract_animals(); HOMES = extract_homes()
    texts = asyncio.run(make_speech()); build_timeline(texts); make_audio(); render_silent(); mix_audio(); make_contact_sheet()
    print(OUTPUT)


if __name__ == "__main__":
    main()
