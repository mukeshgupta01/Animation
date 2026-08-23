import asyncio
import json
import math
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import edge_tts


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "farm-disappeared-work"
SHEET = ROOT / "farm-disappeared-animal-cards.png"
SILENT = WORK / "farm-disappeared-silent.mp4"
OUTPUT = ROOT / "farm-disappeared-what-disappeared.mp4"
W, H, FPS, RENDER_FPS, DURATION = 1280, 720, 24, 12, 70.0

VOICE = "en-AU-NatashaNeural"
RATE = "-10%"

LINES = [
    ("hook", 0.35, "Watch carefully! Which farm animal will disappear?"),
    ("round1", 5.80, "Round one. Remember these three animals."),
    ("ask1", 11.20, "What disappeared?"),
    ("answer1", 16.00, "It was the pig! Great job!"),
    ("round2", 20.10, "Round two. This time, remember four animals."),
    ("ask2", 26.00, "Which animal disappeared?"),
    ("answer2", 31.10, "It was the sheep! Well spotted!"),
    ("round3", 35.40, "Final round. Look carefully at all five animals."),
    ("ask3", 42.00, "One is missing. Which animal disappeared?"),
    ("answer3", 48.30, "It was the horse! Amazing remembering!"),
    ("score", 53.20, "How many did you get right? You did a wonderful job!"),
    ("subscribe", 59.00, "If you enjoyed this game, please like and subscribe for more fun challenges. See you next time!"),
]

ANIMALS = {
    "cow": ((24, 24, 499, 499), (94, 181, 230)),
    "pig": ((525, 24, 1001, 499), (255, 210, 93)),
    "sheep": ((1028, 24, 1504, 499), (137, 221, 192)),
    "chicken": ((24, 526, 499, 998), (255, 185, 139)),
    "horse": ((525, 526, 1001, 998), (195, 165, 230)),
    "duck": ((1028, 526, 1504, 998), (112, 193, 236)),
}


def get_font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for item in candidates:
        if item.exists():
            return ImageFont.truetype(str(item), size)
    return ImageFont.load_default()


F_TITLE = get_font(48, True)
F_HEADING = get_font(43, True)
F_LABEL = get_font(25, True)
F_BODY = get_font(30, True)
F_SMALL = get_font(23, True)


def draw_centered(draw, xy, text, font, fill, stroke=0, stroke_fill=(255, 255, 255, 255)):
    draw.text(xy, text, anchor="mm", font=font, fill=fill,
              stroke_width=stroke, stroke_fill=stroke_fill)


def make_background():
    bg = Image.new("RGBA", (W, H), (211, 244, 255, 255))
    d = ImageDraw.Draw(bg, "RGBA")
    # Sunny sky and rolling green pasture keep the scene bright without visual clutter.
    d.ellipse((1040, -85, 1295, 170), fill=(255, 224, 94, 245))
    d.ellipse((-180, 430, 740, 850), fill=(151, 220, 104, 255))
    d.ellipse((420, 420, 1500, 850), fill=(119, 207, 99, 255))
    d.rectangle((0, 590, W, H), fill=(107, 195, 84, 255))
    # Small barn silhouette at the far edge, safely behind the cards.
    d.polygon([(35, 475), (135, 390), (235, 475)], fill=(241, 91, 79, 180))
    d.rectangle((55, 475, 215, 590), fill=(242, 111, 91, 180))
    d.rectangle((116, 520, 158, 590), fill=(124, 73, 62, 170))
    d.rounded_rectangle((24, 18, 1256, 112), radius=30,
                        fill=(255, 253, 235, 246), outline=(255, 191, 57, 255), width=6)
    return bg


def prepare_cards():
    sheet = Image.open(SHEET).convert("RGB")
    cards = {}
    for name, (crop, _) in ANIMALS.items():
        card = sheet.crop(crop)
        card = ImageEnhance.Color(card).enhance(1.03)
        cards[name] = card.convert("RGBA")
    return cards


def card_layout(names):
    count = len(names)
    widths = {3: 315, 4: 260, 5: 212}
    card_w = widths[count]
    card_h = card_w
    gap = {3: 36, 4: 30, 5: 22}[count]
    total = count * card_w + (count - 1) * gap
    x0 = (W - total) // 2
    return [(x0 + i * (card_w + gap), 180, card_w, card_h) for i in range(count)]


def paste_round(frame, cards, names, missing=None, reveal=None, pulse=0.0):
    d = ImageDraw.Draw(frame, "RGBA")
    layout = card_layout(names)
    for name, (x, y, cw, ch) in zip(names, layout):
        colour = ANIMALS[name][1]
        if name == missing:
            d.rounded_rectangle((x, y, x + cw, y + ch), radius=27,
                                fill=(255, 253, 238, 238), outline=colour + (255,), width=6)
            draw_centered(d, (x + cw // 2, y + ch // 2 - 4), "?", get_font(int(cw * .40), True),
                          (43, 91, 121, 255))
            continue
        img = cards[name].resize((cw, ch), Image.Resampling.LANCZOS)
        mask = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=27, fill=255)
        frame.paste(img, (x, y), mask)
        width = 9 if name == reveal else 5
        outline = (255, 211, 65, 255) if name == reveal else colour + (255,)
        if name == reveal:
            pad = int(5 + 3 * math.sin(pulse * 5))
            d.rounded_rectangle((x - pad, y - pad, x + cw + pad, y + ch + pad),
                                radius=31, outline=(255, 255, 255, 255), width=5)
        d.rounded_rectangle((x, y, x + cw, y + ch), radius=27, outline=outline, width=width)
        label_y = y + ch + 13
        label_w = min(cw - 14, 155)
        d.rounded_rectangle((x + cw // 2 - label_w // 2, label_y,
                             x + cw // 2 + label_w // 2, label_y + 42), radius=15,
                            fill=(255, 253, 238, 245), outline=colour + (255,), width=3)
        draw_centered(d, (x + cw // 2, label_y + 21), name.upper(), F_LABEL,
                      (23, 60, 88, 255))


def bottom_prompt(frame, text, colour=(22, 64, 95, 255)):
    d = ImageDraw.Draw(frame, "RGBA")
    d.rounded_rectangle((170, 625, 1110, 698), radius=25,
                        fill=(255, 253, 238, 246), outline=(255, 191, 57, 255), width=5)
    draw_centered(d, (W // 2, 661), text, F_BODY, colour)


def title(frame, top, sub=None, accent=(232, 72, 76, 255)):
    d = ImageDraw.Draw(frame, "RGBA")
    draw_centered(d, (W // 2, 57), top, F_HEADING, accent,
                  stroke=2, stroke_fill=(255, 255, 255, 255))
    if sub:
        draw_centered(d, (W // 2, 94), sub, F_SMALL, (19, 60, 91, 255))


def blink_transition(frame, amount):
    # A soft cream flash signals the memory change without startling children.
    alpha = int(205 * math.sin(math.pi * max(0.0, min(1.0, amount))))
    ImageDraw.Draw(frame, "RGBA").rectangle((0, 125, W, 615), fill=(255, 250, 220, alpha))


def render_video():
    base = make_background()
    cards = prepare_cards()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(RENDER_FPS), "-i", "-", "-an", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags",
           "+faststart", "-r", str(FPS), str(SILENT)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(int(DURATION * RENDER_FPS)):
        t = n / RENDER_FPS
        frame = base.copy()

        if t < 5.70:
            title(frame, "WHAT DISAPPEARED?", "A farm-animal memory game")
            paste_round(frame, cards, ["cow", "pig", "duck"])
            bottom_prompt(frame, "WATCH CAREFULLY!")
        elif t < 10.90:
            title(frame, "ROUND 1", "Remember these 3 animals")
            paste_round(frame, cards, ["cow", "pig", "duck"])
            bottom_prompt(frame, "LOOK... AND REMEMBER")
        elif t < 11.15:
            title(frame, "ROUND 1", "Something is changing...")
            paste_round(frame, cards, ["cow", "pig", "duck"])
            blink_transition(frame, (t - 10.90) / .25)
        elif t < 15.90:
            title(frame, "WHAT DISAPPEARED?", "Think carefully")
            paste_round(frame, cards, ["cow", "pig", "duck"], missing="pig")
            bottom_prompt(frame, "WHICH ANIMAL IS MISSING?")
        elif t < 20.00:
            title(frame, "THE PIG!", "Great job!")
            paste_round(frame, cards, ["cow", "pig", "duck"], reveal="pig", pulse=t - 15.9)
            bottom_prompt(frame, "THE PIG DISAPPEARED", (224, 77, 86, 255))
        elif t < 25.75:
            title(frame, "ROUND 2", "Remember these 4 animals")
            paste_round(frame, cards, ["cow", "sheep", "chicken", "horse"])
            bottom_prompt(frame, "LOOK... AND REMEMBER")
        elif t < 25.98:
            title(frame, "ROUND 2", "Something is changing...")
            paste_round(frame, cards, ["cow", "sheep", "chicken", "horse"])
            blink_transition(frame, (t - 25.75) / .23)
        elif t < 31.00:
            title(frame, "WHAT DISAPPEARED?", "This one is trickier")
            paste_round(frame, cards, ["cow", "sheep", "chicken", "horse"], missing="sheep")
            bottom_prompt(frame, "WHICH ANIMAL IS MISSING?")
        elif t < 35.30:
            title(frame, "THE SHEEP!", "Well spotted!")
            paste_round(frame, cards, ["cow", "sheep", "chicken", "horse"], reveal="sheep", pulse=t - 31.0)
            bottom_prompt(frame, "THE SHEEP DISAPPEARED", (58, 145, 109, 255))
        elif t < 41.75:
            title(frame, "FINAL ROUND", "Remember all 5 animals")
            paste_round(frame, cards, ["cow", "pig", "sheep", "chicken", "horse"])
            bottom_prompt(frame, "LOOK VERY CAREFULLY")
        elif t < 41.98:
            title(frame, "FINAL ROUND", "Something is changing...")
            paste_round(frame, cards, ["cow", "pig", "sheep", "chicken", "horse"])
            blink_transition(frame, (t - 41.75) / .23)
        elif t < 48.20:
            title(frame, "WHAT DISAPPEARED?", "The hardest round")
            paste_round(frame, cards, ["cow", "pig", "sheep", "chicken", "horse"], missing="horse")
            bottom_prompt(frame, "WHICH ANIMAL IS MISSING?")
        elif t < 53.00:
            title(frame, "THE HORSE!", "Amazing remembering!")
            paste_round(frame, cards, ["cow", "pig", "sheep", "chicken", "horse"], reveal="horse", pulse=t - 48.2)
            bottom_prompt(frame, "THE HORSE DISAPPEARED", (116, 77, 173, 255))
        elif t < 59.00:
            d = ImageDraw.Draw(frame, "RGBA")
            title(frame, "FANTASTIC WORK!", "How many did you get right?")
            d.rounded_rectangle((245, 205, 1035, 540), radius=45,
                                fill=(255, 253, 238, 246), outline=(255, 191, 57, 255), width=7)
            draw_centered(d, (W // 2, 315), "1   2   3", get_font(94, True), (232, 72, 76, 255))
            draw_centered(d, (W // 2, 425), "Every try makes your memory stronger!", F_BODY,
                          (21, 72, 101, 255))
        else:
            d = ImageDraw.Draw(frame, "RGBA")
            title(frame, "LIKE & SUBSCRIBE!", "For more fun children's challenges")
            d.rounded_rectangle((230, 205, 1050, 550), radius=45,
                                fill=(255, 253, 238, 246), outline=(255, 191, 57, 255), width=7)
            draw_centered(d, (W // 2, 300), "THANKS FOR PLAYING!", F_TITLE,
                          (232, 72, 76, 255), stroke=2)
            # Simple heart and play symbols are drawn with Unicode-safe text glyphs.
            draw_centered(d, (W // 2, 397), "LIKE   +   SUBSCRIBE", F_HEADING, (21, 89, 124, 255))
            draw_centered(d, (W // 2, 485), "See you next time!", F_BODY, (53, 155, 111, 255))

        proc.stdin.write(frame.convert("RGB").tobytes())
        if n % (RENDER_FPS * 10) == 0:
            print(f"Rendered {n / FPS:.0f}/{DURATION:.0f} seconds", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("Video rendering failed")


async def make_speech():
    for key, _, words in LINES:
        target = WORK / f"voice-{key}.mp3"
        if not target.exists():
            print("Narration:", key, flush=True)
            await edge_tts.Communicate(words, VOICE, rate=RATE, volume="-2%").save(str(target))


def duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    return float(json.loads(subprocess.check_output(cmd, text=True))["format"]["duration"])


def audit_voice_timing():
    report = []
    for i, (key, start, _) in enumerate(LINES):
        seconds = duration(WORK / f"voice-{key}.mp3")
        end = start + seconds
        next_start = LINES[i + 1][1] if i + 1 < len(LINES) else DURATION
        gap = next_start - end
        report.append((key, start, seconds, end, gap))
        if gap < 0.15:
            raise RuntimeError(f"Narration overlap or insufficient pause after {key}: {gap:.3f}s")
    audit = WORK / "farm-disappeared-voice-timing.txt"
    audit.write_text("\n".join(
        f"{k:10s} start={s:6.2f} duration={d:5.2f} end={e:6.2f} gap={g:5.2f}"
        for k, s, d, e, g in report
    ) + "\n", encoding="utf-8")
    print(audit.read_text(encoding="utf-8"), flush=True)


def make_audio_assets():
    sr = 44100
    # Quiet musical bed.
    bed = WORK / "gentle-bed.wav"
    with wave.open(str(bed), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        data = bytearray()
        notes = [261.63, 329.63, 392.00, 349.23, 293.66, 349.23, 440.00, 392.00]
        for i in range(int(DURATION * sr)):
            t = i / sr
            note = notes[int(t / 4) % len(notes)]
            wave_value = .50 * math.sin(2 * math.pi * note * t) + .22 * math.sin(2 * math.pi * note / 2 * t)
            fade = min(1.0, t / 1.5, (DURATION - t) / 1.5)
            sample = int(max(-1, min(1, wave_value * .047 * fade)) * 32767)
            data += struct.pack("<h", sample)
            if len(data) >= 65536:
                wf.writeframes(data); data.clear()
        if data:
            wf.writeframes(data)

    # Chimes signal answers; soft ticks provide thinking time without a spoken countdown.
    events = [(15.90, "chime"), (31.00, "chime"), (48.20, "chime"), (59.00, "chime")]
    for t in [13.7, 14.6, 15.5, 29.0, 29.8, 30.6, 47.0, 47.6]:
        events.append((t, "tick"))
    samples = [0.0] * int(DURATION * sr)
    for start, kind in events:
        length = .75 if kind == "chime" else .065
        for j in range(int(length * sr)):
            tt = j / sr
            if kind == "chime":
                value = math.exp(-tt * 4.5) * (math.sin(2 * math.pi * 659.25 * tt) +
                                               .48 * math.sin(2 * math.pi * 987.77 * tt)) * .10
            else:
                value = math.exp(-tt * 45) * math.sin(2 * math.pi * 1150 * tt) * .07
            at = int(start * sr) + j
            if at < len(samples):
                samples[at] += value
    sfx = WORK / "gentle-sfx.wav"
    with wave.open(str(sfx), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for start in range(0, len(samples), 32768):
            wf.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767))
                                    for v in samples[start:start + 32768]))


def mix_audio():
    inputs = ["-i", str(SILENT), "-i", str(WORK / "gentle-bed.wav"),
              "-i", str(WORK / "gentle-sfx.wav")]
    filters = ["[1:a]volume=0.52[bed]", "[2:a]volume=0.95[sfx]"]
    labels = ["[bed]", "[sfx]"]
    for idx, (key, start, _) in enumerate(LINES, start=3):
        inputs += ["-i", str(WORK / f"voice-{key}.mp3")]
        delay = int(start * 1000)
        filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.30[v{idx}]")
        labels.append(f"[v{idx}]")
    filters.append("".join(labels) +
                   f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.95[aout]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + inputs + [
        "-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DURATION),
        "-movflags", "+faststart", str(OUTPUT)]
    subprocess.run(cmd, check=True)


def export_audit_frames():
    times = [2.0, 7.0, 12.5, 16.5, 23.0, 28.5, 33.0, 39.0, 45.5, 50.5, 56.0, 63.0]
    for index, at in enumerate(times, 1):
        out = WORK / f"audit-{index:02d}-{at:04.1f}s.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(at), "-i", str(OUTPUT),
                        "-frames:v", "1", str(out)], check=True)


def main():
    WORK.mkdir(exist_ok=True)
    asyncio.run(make_speech())
    audit_voice_timing()
    make_audio_assets()
    render_video()
    mix_audio()
    export_audit_frames()
    print(OUTPUT)


if __name__ == "__main__":
    main()
