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
WORK = ROOT / "safari-shadow-work"
BACKGROUND = ROOT / "safari-shadow-background.png"
SHEET = ROOT / "safari-shadow-animal-sheet.png"
SHEET2 = ROOT / "safari-shadow-animal-sheet-2.png"
SILENT = WORK / "safari-shadow-silent.mp4"
OUTPUT = ROOT / "safari-shadow-guess-the-animal.mp4"
CONTACT = ROOT / "safari-shadow-contact-sheet.png"
W, H, FPS, DURATION = 1280, 720, 24, 130.2
VOICE = "en-AU-NatashaNeural"
RATE = "-8%"

LINES = [
    ("intro", 0.20, "Guess the safari shadow!"),
    ("round1", 3.30, "Round one. Rhino, elephant, or hippo. Which shadow matches?"),
    ("answer1", 16.158, "It's the elephant! Elephants use their trunks to drink water."),
    ("round2", 22.30, "Round two. Giraffe, lion, or zebra. Which shadow matches?"),
    ("answer2", 35.134, "It's the zebra! Every zebra has its own stripe pattern."),
    ("round3", 41.40, "Round three. Elephant, hippo, or rhino. Which shadow matches?"),
    ("answer3", 54.378, "It's the rhino! Rhinos love cooling off in mud."),
    ("round4", 60.10, "Round four. Giraffe, zebra, or lion. Which shadow matches?"),
    ("answer4", 72.982, "It's the giraffe! Giraffes are the tallest animals on land."),
    ("round5", 79.30, "Round five. Rhino, hippo, or elephant. Which shadow matches?"),
    ("answer5", 92.278, "It's the hippo! Hippos spend much of the day in water."),
    ("round6", 98.10, "Final round. Lion, giraffe, or zebra. Which shadow matches?"),
    ("answer6", 111.054, "It's the lion! A lion's roar can travel a very long way."),
    ("score", 117.25, "Amazing! How many of the six animals did you guess correctly?"),
    ("subscribe", 123.35, "Please like and subscribe for more fun puzzles. See you next time!"),
]

ROUNDS = [
    {"start": 3.20, "reveal": 15.908, "end": 22.10, "answer": "elephant", "choices": ["rhino", "elephant", "hippo"], "num": "ROUND 1", "fact": "Elephants use their trunks to drink water."},
    {"start": 22.10, "reveal": 34.884, "end": 41.20, "answer": "zebra", "choices": ["giraffe", "lion", "zebra"], "num": "ROUND 2", "fact": "Every zebra has its own pattern of stripes."},
    {"start": 41.20, "reveal": 54.128, "end": 59.90, "answer": "rhino", "choices": ["elephant", "hippo", "rhino"], "num": "ROUND 3", "fact": "Rhinos love cooling off in mud."},
    {"start": 59.90, "reveal": 72.732, "end": 79.10, "answer": "giraffe", "choices": ["giraffe", "zebra", "lion"], "num": "ROUND 4", "fact": "Giraffes are the tallest animals on land."},
    {"start": 79.10, "reveal": 92.028, "end": 97.90, "answer": "hippo", "choices": ["rhino", "hippo", "elephant"], "num": "ROUND 5", "fact": "Hippos spend much of the day in water."},
    {"start": 97.90, "reveal": 110.804, "end": 117.05, "answer": "lion", "choices": ["lion", "giraffe", "zebra"], "num": "ROUND 6", "fact": "A lion's roar can travel a very long way."},
]

COLORS = {
    "navy": (20, 58, 92, 255),
    "red": (237, 78, 73, 255),
    "yellow": (255, 191, 48, 255),
    "cream": (255, 253, 232, 246),
    "teal": (32, 164, 159, 255),
    "green": (61, 173, 91, 255),
}


def font(size, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "calibrib.ttf" if bold else "calibri.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F18 = font(18, True)
F26 = font(26, True)
F32 = font(32, True)
F42 = font(42, True)
F56 = font(56, True)


def fit_background():
    src = Image.open(BACKGROUND).convert("RGB")
    scale = max(W / src.width, H / src.height)
    resized = src.resize((round(src.width * scale), round(src.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - W) // 2
    top = (resized.height - H) // 2
    return resized.crop((left, top, left + W, top + H)).convert("RGBA")


def extract_animals():
    sheet = Image.open(SHEET).convert("RGB")
    boxes = {
        "elephant": (10, 190, 570, 930),
        # Exclude the distant tail tuft: its very thin connecting line does not
        # survive silhouette conversion cleanly at video size.
        "giraffe": (620, 20, 990, 930),
        "lion": (1010, 190, 1525, 930),
    }
    animals = {}
    for name, box in boxes.items():
        crop = sheet.crop(box)
        pixels = crop.load()
        mask = Image.new("L", crop.size, 0)
        mp = mask.load()
        for y in range(crop.height):
            for x in range(crop.width):
                r, g, b = pixels[x, y]
                # Keep colored/grey animal pixels and softly reject the warm-white studio background.
                distance = max(0, 250 - min(r, g, b))
                alpha = max(0, min(255, int((distance - 5) * 8.0)))
                mp[x, y] = alpha
        mask = mask.filter(ImageFilter.GaussianBlur(0.65))
        rgba = crop.convert("RGBA")
        rgba.putalpha(mask)
        bbox = mask.getbbox()
        if not bbox:
            raise RuntimeError(f"Could not isolate {name}")
        animals[name] = rgba.crop(bbox)
    sheet2 = Image.open(SHEET2).convert("RGB")
    boxes2 = {
        "zebra": (15, 105, 450, 920),
        "hippo": (520, 190, 975, 920),
        "rhino": (1005, 120, 1515, 920),
    }
    for name, box in boxes2.items():
        crop = sheet2.crop(box)
        pixels = crop.load()
        mask = Image.new("L", crop.size, 0)
        mp = mask.load()
        for y in range(crop.height):
            for x in range(crop.width):
                r, g, b = pixels[x, y]
                distance = max(0, 250 - min(r, g, b))
                mp[x, y] = max(0, min(255, int((distance - 5) * 8.0)))
        mask = mask.filter(ImageFilter.GaussianBlur(0.65))
        rgba = crop.convert("RGBA")
        rgba.putalpha(mask)
        bbox = mask.getbbox()
        if not bbox:
            raise RuntimeError(f"Could not isolate {name}")
        animals[name] = rgba.crop(bbox)
    return animals


BASE = None
ANIMALS = None


def cover(frame, box, fill=COLORS["cream"], outline=COLORS["yellow"], radius=24, width=4):
    ImageDraw.Draw(frame, "RGBA").rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered_text(draw, xy, text, fnt, fill, stroke=0):
    draw.text(xy, text, anchor="mm", font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(255, 255, 255, 255))


def paste_contain(frame, art, box, silhouette=False):
    x1, y1, x2, y2 = box
    max_w, max_h = x2 - x1, y2 - y1
    scale = min(max_w / art.width, max_h / art.height)
    size = (max(1, round(art.width * scale)), max(1, round(art.height * scale)))
    resized = art.resize(size, Image.Resampling.LANCZOS)
    if silhouette:
        alpha = resized.getchannel("A")
        solid = Image.new("RGBA", resized.size, (30, 48, 61, 255))
        solid.putalpha(alpha)
        resized = solid
    px = x1 + (max_w - size[0]) // 2
    py = y1 + (max_h - size[1]) // 2
    frame.alpha_composite(resized, (px, py))


def draw_header(frame, small, main):
    d = ImageDraw.Draw(frame, "RGBA")
    cover(frame, (215, 14, 1065, 104), fill=(255, 253, 232, 242), radius=26)
    centered_text(d, (640, 38), small, F18, COLORS["red"])
    centered_text(d, (640, 74), main, F32, COLORS["navy"])


def draw_round(frame, spec, t):
    d = ImageDraw.Draw(frame, "RGBA")
    revealed = t >= spec["reveal"]
    draw_header(frame, spec["num"], "WHOSE SHADOW IS THIS?" if not revealed else "THE ANSWER IS...")

    # Central stage is entirely above the choices, so neither the answer nor its label is covered.
    cover(frame, (430, 115, 850, 455), fill=(255, 253, 239, 238), outline=(255, 191, 48, 255), radius=35, width=5)
    paste_contain(frame, ANIMALS[spec["answer"]], (500, 135, 780, 435), silhouette=not revealed)

    if not revealed:
        elapsed = max(0.0, t - spec["start"])
        total = spec["reveal"] - spec["start"]
        frac = max(0.0, min(1.0, elapsed / total))
        cover(frame, (490, 422, 790, 448), fill=(255, 255, 255, 220), outline=(255, 255, 255, 220), radius=13, width=1)
        d.rounded_rectangle((494, 426, 494 + int(292 * (1 - frac)), 444), radius=9, fill=COLORS["teal"])
    else:
        answer = spec["answer"].upper()
        cover(frame, (350, 397, 930, 457), fill=(240, 255, 236, 246), outline=COLORS["green"], radius=18, width=4)
        centered_text(d, (640, 414), answer + "!", F26, COLORS["green"])
        centered_text(d, (640, 441), spec["fact"], F18, COLORS["navy"])

    positions = [(100, 475, 430, 690), (475, 475, 805, 690), (850, 475, 1180, 690)]
    letters = ["A", "B", "C"]
    for i, (name, box) in enumerate(zip(spec["choices"], positions)):
        is_answer = name == spec["answer"]
        outline = COLORS["green"] if revealed and is_answer else COLORS["yellow"]
        width = 7 if revealed and is_answer else 4
        fill = (238, 255, 232, 248) if revealed and is_answer else (255, 253, 232, 244)
        cover(frame, box, fill=fill, outline=outline, radius=24, width=width)
        x1, y1, x2, y2 = box
        paste_contain(frame, ANIMALS[name], (x1 + 45, y1 + 10, x2 - 16, y2 - 35))
        d.ellipse((x1 + 10, y1 + 10, x1 + 52, y1 + 52), fill=COLORS["navy"])
        centered_text(d, (x1 + 31, y1 + 31), letters[i], F26, (255, 255, 255, 255))
        centered_text(d, ((x1 + x2) // 2, y2 - 20), name.upper(), F18,
                      COLORS["green"] if revealed and is_answer else COLORS["navy"])


def frame_at(t):
    frame = BASE.copy()
    frame.alpha_composite(Image.new("RGBA", frame.size, (255, 247, 205, 25)))
    d = ImageDraw.Draw(frame, "RGBA")
    # A translucent wash keeps every card readable while retaining the bright landscape.

    if t < 3.40:
        cover(frame, (170, 178, 1110, 530), fill=(255, 253, 232, 244), radius=42, width=7)
        centered_text(d, (640, 245), "GUESS THE ANIMAL SHADOW", F42, COLORS["navy"], 1)
        centered_text(d, (640, 315), "SAFARI CHALLENGE", F56, COLORS["red"], 1)
        centered_text(d, (640, 405), "6 bright and playful rounds!", F32, COLORS["teal"])
        centered_text(d, (640, 472), "Let's begin!", F26, COLORS["navy"])
    else:
        active = next((r for r in ROUNDS if r["start"] <= t < r["end"]), None)
        if active:
            draw_round(frame, active, t)
        elif 117.05 <= t < 123.15:
            cover(frame, (220, 155, 1060, 555), fill=(255, 253, 232, 246), radius=40, width=7)
            centered_text(d, (640, 245), "AMAZING WORK!", F56, COLORS["red"], 1)
            centered_text(d, (640, 335), "HOW MANY DID YOU GUESS?", F42, COLORS["navy"])
            for i, name in enumerate(["elephant", "zebra", "rhino", "giraffe", "hippo", "lion"]):
                paste_contain(frame, ANIMALS[name], (185 + i * 150, 385, 325 + i * 150, 525))
        else:
            cover(frame, (205, 140, 1075, 580), fill=(255, 253, 232, 246), radius=42, width=7)
            centered_text(d, (640, 220), "LIKE & SUBSCRIBE", F56, COLORS["red"], 1)
            centered_text(d, (640, 292), "for more fun puzzles!", F32, COLORS["navy"])
            for i, name in enumerate(["elephant", "zebra", "rhino", "giraffe", "hippo", "lion"]):
                paste_contain(frame, ANIMALS[name], (180 + i * 150, 330, 325 + i * 150, 520))
            centered_text(d, (640, 548), "SEE YOU NEXT TIME!", F26, COLORS["teal"])
    return frame.convert("RGB")


async def make_speech():
    WORK.mkdir(exist_ok=True)
    for key, _, words in LINES:
        path = WORK / f"safari-shadow-voice-{key}.mp3"
        if not path.exists():
            print("Narration:", key, flush=True)
            await edge_tts.Communicate(words, VOICE, rate=RATE, volume="-2%").save(str(path))


def probe_duration(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(result.stdout)["format"]["duration"])


def audit_voice_timing():
    report = []
    for i, (key, start, _) in enumerate(LINES):
        dur = probe_duration(WORK / f"safari-shadow-voice-{key}.mp3")
        end = start + dur
        next_start = LINES[i + 1][1] if i + 1 < len(LINES) else DURATION
        gap = next_start - end
        report.append((key, start, dur, end, gap))
        if gap < 0.18:
            raise RuntimeError(f"Narration overlap: {key} ends {end:.2f}, next begins {next_start:.2f}")
    (WORK / "safari-shadow-timing-audit.txt").write_text(
        "\n".join(f"{k}: start={s:.2f} duration={d:.3f} end={e:.3f} gap={g:.3f}" for k, s, d, e, g in report), encoding="utf-8")
    line_map = {key: (start, probe_duration(WORK / f"safari-shadow-voice-{key}.mp3")) for key, start, _ in LINES}
    gaps = []
    for i, spec in enumerate(ROUNDS, start=1):
        start, dur = line_map[f"round{i}"]
        quiet = spec["reveal"] - (start + dur)
        gaps.append((i, start + dur, spec["reveal"], quiet))
        if not 4.90 <= quiet <= 5.10:
            raise RuntimeError(f"Round {i} quiet response gap is {quiet:.3f}s, expected about 5s")
    (WORK / "safari-shadow-response-gap-audit.txt").write_text(
        "\n".join(f"round{i}: question_end={end:.3f} reveal={reveal:.3f} quiet_gap={gap:.3f}" for i, end, reveal, gap in gaps), encoding="utf-8")


def make_audio_bed():
    sr = 44100
    bed = WORK / "safari-shadow-gentle-bed.wav"
    sfx = WORK / "safari-shadow-sfx.wav"
    notes = [261.63, 329.63, 392.00, 349.23, 293.66, 349.23, 440.00, 392.00]
    with wave.open(str(bed), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        block = bytearray()
        for i in range(int(DURATION * sr)):
            t = i / sr
            n = notes[int(t / 4.0) % len(notes)]
            fade = min(1.0, t / 1.5, (DURATION - t) / 1.5)
            v = (0.48 * math.sin(2 * math.pi * n * t) + 0.22 * math.sin(2 * math.pi * n / 2 * t)) * 0.038 * fade
            block += struct.pack("<h", int(max(-1, min(1, v)) * 32767))
            if len(block) >= 65536:
                wf.writeframes(block); block.clear()
        if block: wf.writeframes(block)

    reveal_times = [spec["reveal"] for spec in ROUNDS]
    events = [(reveal, "chime") for reveal in reveal_times]
    # Three soft thinking ticks at the end of each round; there is no spoken or displayed countdown.
    for reveal in reveal_times:
        for delta in [5.0, 4.0, 3.0, 2.0, 1.0]:
            events.append((reveal - delta, "tick"))
    data = [0.0] * int(DURATION * sr)
    for start, kind in events:
        n0 = int(start * sr)
        dur = 0.75 if kind == "chime" else 0.07
        for j in range(int(dur * sr)):
            tt = j / sr
            if kind == "chime":
                v = math.exp(-tt * 4.3) * (math.sin(2 * math.pi * 659.25 * tt) + 0.48 * math.sin(2 * math.pi * 987.77 * tt)) * 0.10
            else:
                v = math.exp(-tt * 38) * math.sin(2 * math.pi * 1050 * tt) * 0.055
            if n0 + j < len(data): data[n0 + j] += v
    with wave.open(str(sfx), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for start in range(0, len(data), 32768):
            wf.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in data[start:start + 32768]))


def render_silent():
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(SILENT)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = round(DURATION * FPS)
    for n in range(total):
        proc.stdin.write(frame_at(n / FPS).tobytes())
        if n % (FPS * 10) == 0:
            print(f"Rendered {n / FPS:.0f}/{DURATION:.0f} seconds", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("Silent video render failed")


def mix_audio():
    inputs = ["-i", str(SILENT), "-i", str(WORK / "safari-shadow-gentle-bed.wav"), "-i", str(WORK / "safari-shadow-sfx.wav")]
    filters = ["[1:a]volume=0.52[bed]", "[2:a]volume=0.85[sfx]"]
    labels = ["[bed]", "[sfx]"]
    for idx, (key, start, _) in enumerate(LINES, start=3):
        inputs += ["-i", str(WORK / f"safari-shadow-voice-{key}.mp3")]
        delay = round(start * 1000)
        filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.18[v{idx}]")
        labels.append(f"[v{idx}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.93[aout]")
    subprocess.run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DURATION), "-movflags", "+faststart", str(OUTPUT)], check=True)


def make_contact_sheet():
    times = [6.0, 17.0, 24.0, 36.0, 43.0, 55.0, 61.0, 74.0, 80.0, 92.0, 99.0, 111.0]
    thumbs = []
    for t in times:
        im = frame_at(t).resize((320, 180), Image.Resampling.LANCZOS)
        dd = ImageDraw.Draw(im)
        dd.rectangle((0, 0, 70, 25), fill=(0, 0, 0))
        dd.text((6, 4), f"{t:.1f}s", font=font(14, True), fill="white")
        thumbs.append(im)
    sheet = Image.new("RGB", (1280, 540), "white")
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % 4) * 320, (i // 4) * 180))
    sheet.save(CONTACT)


def main():
    global BASE, ANIMALS
    WORK.mkdir(exist_ok=True)
    BASE = fit_background()
    ANIMALS = extract_animals()
    asyncio.run(make_speech())
    audit_voice_timing()
    make_audio_bed()
    render_silent()
    mix_audio()
    make_contact_sheet()
    print(OUTPUT)


if __name__ == "__main__":
    main()
