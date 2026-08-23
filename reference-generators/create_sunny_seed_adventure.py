import asyncio
import json
import math
import random
import struct
import subprocess
import wave
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "sunny-seed-work"
OUTPUT = ROOT / "help-sunny-the-seed-grow.mp4"
SILENT = WORK / "sunny-seed-silent.mp4"
CONTACT = ROOT / "sunny-seed-motion-contact-sheet.png"
BG_PATH = ROOT / "sunny-garden-background.png"
GROWTH_PATH = ROOT / "sunny-growth-sheet.png"
FRIENDS_PATH = ROOT / "sunny-friends-sheet.png"
W, H, VIDEO_FPS, ART_FPS = 1280, 720, 24, 8

VOICE = "en-US-AnaNeural"
NARRATOR_RATE, SUNNY_RATE = "-13%", "-8%"
NARRATOR_PITCH, SUNNY_PITCH = "-2Hz", "+8Hz"
VOICE_CUT = "child-v1"

FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT = "C:/Windows/Fonts/arial.ttf"

STEPS = [
    {
        "title": "FIND A SUNNY SPOT",
        "prompt": "Point to the big, soft patch of soil. Can you show Sunny where to land?",
        "arrival": "Sunny floats over a cheerful garden. There is plenty of room, but a little seed needs just the right place to begin.",
        "success": "You found it! Sunny lands gently in the soft soil.",
        "reaction": "This spot feels warm and cozy!",
        "kind": "land",
    },
    {
        "title": "PAT THE SOIL GENTLY",
        "prompt": "Pretend to pat the soil three gentle times. Pat... pat... pat.",
        "arrival": "Now Sunny needs a small blanket of earth. Not too heavy, and not too deep.",
        "success": "Perfectly gentle! The soft earth tucks Sunny in safely.",
        "reaction": "Snug as a seed can be!",
        "kind": "soil",
    },
    {
        "title": "MAKE LITTLE RAINDROPS",
        "prompt": "Tap your knees softly like falling rain. Keep tapping while the raindrops come down.",
        "arrival": "A seed cannot wake without water. The clouds are ready, but they need your help to make a gentle shower.",
        "success": "Pitter-patter! The water sinks into the soil, and Sunny's tiny root begins to wiggle.",
        "reaction": "I can feel my root waking up!",
        "kind": "rain",
    },
    {
        "title": "BRING OUT THE SUNSHINE",
        "prompt": "Make a big sunshine circle with your arms. Hold it high and help the garden glow.",
        "arrival": "The rain has passed. Sunny is ready for warm light to reach down through the earth.",
        "success": "Here comes the sunshine! A tiny green sprout pushes up to say hello.",
        "reaction": "Hello, bright blue sky!",
        "kind": "sun",
    },
    {
        "title": "STRETCH AND GROW",
        "prompt": "Crouch down small, then slowly stretch up tall like Sunny. Keep growing... nice and slowly.",
        "arrival": "Sunny has two little leaves, but there is still a long way to grow.",
        "success": "Look at that strong stem! More leaves unfold as Sunny reaches higher and higher.",
        "reaction": "I'm almost as tall as the flowers!",
        "kind": "grow",
    },
    {
        "title": "OPEN THE GOLDEN PETALS",
        "prompt": "Bring your hands together like a flower bud. Now slowly open them into wide, golden petals.",
        "arrival": "At the very top is a sleepy flower bud. One last gentle movement will help it bloom.",
        "success": "The petals open! Sunny has become a beautiful golden sunflower.",
        "reaction": "We grew together! Thank you, wonderful garden helper!",
        "kind": "bloom",
    },
]

INTRO_TEXT = [
    ("intro0", "narrator", "Hello, little gardeners! Welcome to Sunny's growing adventure. Are you ready to help a tiny seed grow?"),
    ("intro1", "narrator", "On a breezy morning, a tiny seed named Sunny sailed across the sky, looking for a garden to call home."),
    ("intro2", "sunny", "Hello! I may be small, but one day I hope to become a tall, golden sunflower."),
    ("intro3", "narrator", "Sunny will need soil, rain, sunshine, and your gentle movements. Let's help this little seed grow!"),
]

FINAL_TEXT = [
    ("final1", "narrator", "Sunny's garden is buzzing with new friends. You helped a tiny seed grow all the way into a sunflower!"),
    ("final2", "sunny", "Whenever you see a flower, remember that wonderful things can begin very small."),
    ("subscribe2", "narrator", "Before you go, please tap like and subscribe for more gentle children's adventures with us. See you next time!"),
]

BG = Image.open(BG_PATH).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
SHEET = Image.open(GROWTH_PATH).convert("RGBA")
FRIENDS = Image.open(FRIENDS_PATH).convert("RGBA")


def alpha_crop(im, box):
    part = im.crop(box)
    bbox = part.getchannel("A").getbbox()
    return part.crop(bbox) if bbox else part


SW = SHEET.width
STAGE_RANGES = [(0, 230), (230, 465), (465, 750), (750, 1060), (1060, 1370), (1370, SW)]
STAGES = [alpha_crop(SHEET, (x0, 0, x1, SHEET.height)) for x0, x1 in STAGE_RANGES]
BEE = alpha_crop(FRIENDS, (0, 0, FRIENDS.width // 2, FRIENDS.height))
BUTTERFLY = alpha_crop(FRIENDS, (FRIENDS.width // 2, 0, FRIENDS.width, FRIENDS.height))

LINES = []
SPEAKING = []
VOICE_DUR = {}
INTRO_END = 0
FINAL_START = 0
DURATION = 0


def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def paste_scaled(frame, sprite, center, height, angle=0, opacity=255):
    ratio = height / sprite.height
    size = (max(1, int(sprite.width * ratio)), max(1, int(height)))
    im = sprite.resize(size, Image.Resampling.LANCZOS)
    if angle:
        im = im.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    if opacity < 255:
        a = im.getchannel("A").point(lambda p: p * opacity // 255)
        im.putalpha(a)
    x = int(center[0] - im.width / 2)
    y = int(center[1] - im.height / 2)
    frame.alpha_composite(im, (x, y))


def panel(frame, title, subtitle=None, color=(245, 176, 45)):
    d = ImageDraw.Draw(frame)
    y0, y1 = 26, 104
    d.rounded_rectangle((210, y0, 1070, y1), radius=26, fill=(255, 252, 235, 246), outline=color, width=5)
    f = font(38)
    bb = d.textbbox((0, 0), title, font=f)
    d.text(((W - (bb[2] - bb[0])) / 2, 38), title, font=f, fill=(42, 72, 92))
    if subtitle:
        d.rounded_rectangle((280, 614, 1000, 686), radius=24, fill=(255, 252, 235, 244), outline=color, width=4)
        sf = font(30)
        bb = d.textbbox((0, 0), subtitle, font=sf)
        d.text(((W - (bb[2] - bb[0])) / 2, 632), subtitle, font=sf, fill=(42, 72, 92))


def speaking_at(t, speaker):
    return any(s <= t <= e and sp == speaker for s, e, sp in SPEAKING)


def add_sparkles(frame, t, center, color=(255, 210, 60), count=12, radius=120):
    d = ImageDraw.Draw(frame)
    for i in range(count):
        a = i * 2 * math.pi / count + t * (0.45 + (i % 3) * .08)
        rr = radius * (.55 + .35 * math.sin(t * 2 + i) ** 2)
        x = center[0] + math.cos(a) * rr
        y = center[1] + math.sin(a) * rr * .55
        r = 3 + 3 * (0.5 + 0.5 * math.sin(t * 5 + i))
        d.ellipse((x-r, y-r, x+r, y+r), fill=color + (220,))


def seed_position(t):
    if t < 4:
        p = smooth(t / 4)
        return (200 + 420 * p, -70 + 400 * p)
    return (620 + 12 * math.sin(t * 1.2), 330 + 8 * math.sin(t * 1.7))


def intro_frame(t):
    frame = BG.convert("RGBA")
    d = ImageDraw.Draw(frame)
    # Decorative wind curls make the seed's flight visibly animated.
    for i in range(3):
        x = 120 + i * 245 + 35 * math.sin(t * 1.4 + i)
        y = 175 + i * 44
        d.arc((x, y, x + 120, y + 45), 15, 330, fill=(255, 255, 255, 180), width=4)
    x, y = seed_position(t)
    paste_scaled(frame, STAGES[0], (x, y), 190, angle=8 * math.sin(t * 2))
    if t < 8:
        panel(frame, "HELP SUNNY GROW!", "A GENTLE GARDEN ADVENTURE")
    else:
        panel(frame, "A TINY SEED WITH A BIG DREAM")
    return frame


def stage_for_step(index, local, step):
    if index == 0:
        return 0
    if index == 1:
        return 0 if local < step["reveal_local"] + 1.0 else 1
    if index == 2:
        return 0 if local < step["reveal_local"] else 1
    if index == 3:
        return 1 if local < step["reveal_local"] else 2
    if index == 4:
        if local < step["reveal_local"]: return 2
        p = local - step["reveal_local"]
        return 2 if p < 1.1 else (3 if p < 2.4 else 4)
    return 4 if local < step["reveal_local"] else 5


def draw_weather(frame, kind, local, step):
    d = ImageDraw.Draw(frame)
    active = step["prompt_local"] <= local <= step["reveal_local"] + 3.5
    if kind == "rain" and active:
        # Soft, colorful rain; never darken the scene.
        for i in range(55):
            x = (i * 89 + int(local * 150)) % (W + 80) - 40
            y = (i * 47 + int(local * 260)) % 520 + 80
            d.line((x, y, x - 8, y + 20), fill=(76, 168, 235, 170), width=4)
        d.rounded_rectangle((445, 120, 835, 205), radius=40, fill=(244, 249, 255, 235), outline=(170, 218, 243), width=4)
    if kind == "sun" and active:
        pulse = 1 + .08 * math.sin(local * 3)
        cx, cy, rr = 1030, 155, int(56 * pulse)
        for i in range(16):
            a = i * math.pi / 8 + local * .08
            d.line((cx + math.cos(a) * 72, cy + math.sin(a) * 72,
                    cx + math.cos(a) * 98, cy + math.sin(a) * 98), fill=(255, 206, 45, 190), width=7)
        d.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=(255, 222, 62, 245), outline=(255, 187, 35), width=5)


def step_frame(index, t):
    step = STEPS[index]
    local = t - step["start"]
    frame = BG.convert("RGBA")
    draw_weather(frame, step["kind"], local, step)
    d = ImageDraw.Draw(frame)
    prompt_active = step["prompt_local"] <= local < step["reveal_local"]
    revealed = local >= step["reveal_local"]
    title = step["title"]
    subtitle = title if prompt_active else ("WONDERFUL!" if revealed else None)
    panel(frame, f"STEP {index + 1}: {title}", subtitle)

    base_x, ground_y = 640, 565
    stage = stage_for_step(index, local, step)
    if index == 0:
        if revealed:
            p = smooth(min(1, (local - step["reveal_local"]) / 1.3))
            x = 270 + (base_x - 270) * p
            y = 260 + (ground_y - 80 - 260) * p + math.sin(p * math.pi) * -90
        else:
            x = 270 + 12 * math.sin(local * 1.8)
            y = 280 + 8 * math.sin(local * 2.1)
        paste_scaled(frame, STAGES[0], (x, y), 175, angle=6 * math.sin(local * 2))
        if prompt_active:
            for j, (px, py) in enumerate([(430, 520), (640, 520), (850, 520)]):
                pulse = 8 * math.sin(local * 3 + j)
                d.ellipse((px-46-pulse, py-22-pulse/2, px+46+pulse, py+22+pulse/2), outline=(255, 216, 74, 230), width=7)
    else:
        # Scale and sway the painted character without distorting it.
        heights = [155, 185, 185, 335, 455, 520]
        h = heights[stage]
        if index == 4 and revealed:
            h *= .82 + .18 * smooth(min(1, (local-step["reveal_local"]) / 3))
        angle = 2.0 * math.sin(t * 1.1) if stage >= 2 else 4 * math.sin(t * 1.7)
        cy = ground_y - h / 2
        if stage <= 1:
            cy = 520
        paste_scaled(frame, STAGES[stage], (base_x, cy), h, angle=angle)

    if step["kind"] == "soil" and prompt_active:
        for beat in range(3):
            q = local - step["prompt_local"] - beat * 1.5
            if 0 <= q <= .7:
                for k in range(10):
                    a = k * .63
                    rr = 20 + 65 * q
                    x = base_x + math.cos(a) * rr
                    y = 545 + math.sin(a) * rr * .25
                    d.ellipse((x-6, y-4, x+6, y+4), fill=(148, 84, 35, int(220*(1-q/.7))))
    if step["kind"] == "grow" and revealed:
        add_sparkles(frame, t, (base_x, 340), (107, 210, 87), 16, 175)
    if step["kind"] == "bloom" and revealed:
        add_sparkles(frame, t, (base_x, 265), (255, 205, 42), 18, 220)
        p = smooth(min(1, (local - step["reveal_local"]) / 2.5))
        bx = -100 + p * 400 + 25 * math.sin(t * 1.6)
        by = 260 + 40 * math.sin(t * 2.1)
        fx = W + 100 - p * 380 + 30 * math.sin(t * 1.3)
        fy = 225 + 55 * math.sin(t * 1.7 + 1)
        paste_scaled(frame, BEE, (bx, by), 135, angle=4*math.sin(t*3))
        paste_scaled(frame, BUTTERFLY, (fx, fy), 170, angle=3*math.sin(t*2))
    return frame


def final_frame(t):
    local = t - FINAL_START
    frame = BG.convert("RGBA")
    h = 530 + 10 * math.sin(local * 1.2)
    paste_scaled(frame, STAGES[5], (640, 565-h/2), h, angle=1.8*math.sin(local*.9))
    # Friends loop around Sunny along visibly changing paths.
    bx = 250 + 90 * math.sin(local * .9)
    by = 260 + 55 * math.sin(local * 1.7)
    fx = 1030 + 110 * math.sin(local * .65 + 2)
    fy = 230 + 75 * math.sin(local * 1.35 + 1)
    paste_scaled(frame, BEE, (bx, by), 145, angle=5*math.sin(local*3))
    paste_scaled(frame, BUTTERFLY, (fx, fy), 185, angle=4*math.sin(local*2.4))
    add_sparkles(frame, t, (640, 265), (255, 209, 48), 14, 230)
    subscribe_at = next((start - FINAL_START for key, start, _, _ in LINES if key == "subscribe2"), 20)
    if local < 10:
        panel(frame, "SUNNY GREW WITH YOUR HELP!", "FROM A TINY SEED TO A GOLDEN FLOWER")
    elif local >= subscribe_at:
        panel(frame, "LIKE & SUBSCRIBE", "FOR MORE GENTLE ADVENTURES")
    else:
        panel(frame, "WONDERFUL THINGS CAN START SMALL")
    return frame


def frame_at(t):
    if t < INTRO_END:
        return intro_frame(t).convert("RGB")
    for i, step in enumerate(STEPS):
        if step["start"] <= t < step["end"]:
            return step_frame(i, t).convert("RGB")
    return final_frame(t).convert("RGB")


def speech_path(key):
    return WORK / f"sunny-seed-{VOICE_CUT}-{key}.mp3"


async def make_speech():
    WORK.mkdir(exist_ok=True)
    items = list(INTRO_TEXT)
    for i, s in enumerate(STEPS):
        items += [
            (f"arrival{i}", "narrator", s["arrival"]),
            (f"prompt{i}", "sunny", s["prompt"]),
            (f"success{i}", "narrator", s["success"]),
            (f"reaction{i}", "sunny", s["reaction"]),
        ]
    items += FINAL_TEXT
    for key, speaker, text in items:
        path = speech_path(key)
        if not path.exists():
            rate = SUNNY_RATE if speaker == "sunny" else NARRATOR_RATE
            pitch = SUNNY_PITCH if speaker == "sunny" else NARRATOR_PITCH
            print("Narration:", key, flush=True)
            await edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, volume="-2%").save(str(path))
    return items


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def build_timeline(items):
    global LINES, SPEAKING, VOICE_DUR, INTRO_END, FINAL_START, DURATION
    VOICE_DUR = {key: probe_duration(speech_path(key)) for key, _, _ in items}
    bykey = {key: (speaker, text) for key, speaker, text in items}
    LINES, SPEAKING = [], []

    def add(key, start):
        speaker, text = bykey[key]
        end = start + VOICE_DUR[key]
        LINES.append((key, start, text, speaker))
        SPEAKING.append((start, end, speaker))
        return end

    cursor = add("intro0", .3) + .45
    cursor = add("intro1", cursor) + .35
    cursor = add("intro2", cursor) + .35
    cursor = add("intro3", cursor) + 1.45
    INTRO_END = cursor

    response = []
    for i, s in enumerate(STEPS):
        s["start"] = cursor
        end = add(f"arrival{i}", cursor + .65)
        prompt_start = end + .35
        prompt_end = add(f"prompt{i}", prompt_start)
        reveal = round((prompt_end + 5.0) * ART_FPS) / ART_FPS
        success_start = reveal + .3
        success_end = add(f"success{i}", success_start)
        reaction_end = add(f"reaction{i}", success_end + .35)
        s["prompt_local"] = prompt_start - s["start"]
        s["reveal_local"] = reveal - s["start"]
        s["end"] = reaction_end + 1.85
        cursor = s["end"]
        response.append((s["title"], prompt_end, reveal, reveal-prompt_end))

    FINAL_START = cursor
    cursor = add("final1", cursor + .65) + .4
    cursor = add("final2", cursor) + .6
    cursor = add("subscribe2", cursor) + .8
    DURATION = math.ceil(cursor * ART_FPS) / ART_FPS

    (WORK / "sunny-seed-activity-gap-audit.txt").write_text("\n".join(f"{name}: prompt_end={pe:.3f} reveal={rv:.3f} quiet_gap={gap:.3f}" for name, pe, rv, gap in response), encoding="utf-8")
    report = []
    for i, (key, start, _, speaker) in enumerate(LINES):
        end = start + VOICE_DUR[key]
        nxt = LINES[i+1][1] if i+1 < len(LINES) else DURATION
        report.append(f"{key} ({speaker}): start={start:.3f} duration={VOICE_DUR[key]:.3f} end={end:.3f} gap={nxt-end:.3f}")
    (WORK / "sunny-seed-voice-timing.txt").write_text("\n".join(report), encoding="utf-8")


def make_audio_beds():
    sr = 24000
    n = int(DURATION * sr)
    music_path = WORK / "sunny-seed-music.wav"
    sfx_path = WORK / "sunny-seed-sfx.wav"
    with wave.open(str(music_path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        block = bytearray()
        notes = [261.63, 329.63, 392.0, 329.63, 293.66, 349.23, 440.0, 349.23]
        for i in range(n):
            t = i / sr
            f = notes[int(t / 2.0) % len(notes)]
            env = .55 + .45 * math.sin(math.pi * ((t % 2.0) / 2.0))
            val = int(380 * env * (math.sin(2*math.pi*f*t) + .28*math.sin(2*math.pi*(f/2)*t)))
            block += struct.pack("<h", val)
            if len(block) >= sr * 4:
                wf.writeframes(block); block.clear()
        if block: wf.writeframes(block)

    events = []
    for s in STEPS:
        events.append((s["start"] + s["reveal_local"], 660, .75, .12))
        if s["kind"] == "soil":
            for k in range(3): events.append((s["start"] + s["prompt_local"] + .7 + 1.5*k, 170, .18, .05))
    events += [(FINAL_START + 1.0, 523, 1.4, .09), (FINAL_START + 1.3, 659, 1.2, .08), (FINAL_START + 1.6, 784, 1.0, .07)]
    with wave.open(str(sfx_path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        block = bytearray()
        for i in range(n):
            t = i / sr
            v = 0.0
            for start, freq, dur, amp in events:
                q = t - start
                if 0 <= q < dur:
                    env = math.sin(math.pi*q/dur) * math.exp(-1.7*q)
                    v += amp * env * math.sin(2*math.pi*freq*q)
            block += struct.pack("<h", max(-32767, min(32767, int(v*32767))))
            if len(block) >= sr * 4:
                wf.writeframes(block); block.clear()
        if block: wf.writeframes(block)
    return music_path, sfx_path


def render_video():
    total = math.ceil(DURATION * ART_FPS)
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(ART_FPS), "-i", "-",
           "-an", "-vf", f"fps={VIDEO_FPS}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(SILENT)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(total):
        if i % (ART_FPS*10) == 0: print(f"Rendered {i//ART_FPS}/{math.ceil(DURATION)} seconds", flush=True)
        p.stdin.write(frame_at(i/ART_FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError("silent render failed")


def mix_audio(music, sfx):
    inputs = ["-i", str(SILENT), "-i", str(music), "-i", str(sfx)]
    filters = ["[1:a]volume=0.30[m]", "[2:a]volume=0.72[s]"]
    labels = ["[m]", "[s]"]
    for idx, (key, start, _, speaker) in enumerate(LINES, 3):
        inputs += ["-i", str(speech_path(key))]
        delay = round(start * 1000)
        vol = 1.18 if speaker == "narrator" else 1.14
        filters.append(f"[{idx}:a]adelay={delay}|{delay},volume={vol}[v{idx}]")
        labels.append(f"[v{idx}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.88[a]")
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[a]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-ar", "24000", "-ac", "1", "-r", str(VIDEO_FPS),
           "-t", f"{DURATION:.3f}", "-movflags", "+faststart", str(OUTPUT)]
    subprocess.run(cmd, check=True)


def make_contact_sheet():
    times = [2, 10]
    for s in STEPS:
        times += [s["start"]+2.5, s["start"]+s["prompt_local"]+1.5, s["start"]+s["reveal_local"]+1.5]
    times += [FINAL_START+2, FINAL_START+12, DURATION-4]
    thumb_w, thumb_h = 320, 180
    cols = 4
    rows = math.ceil(len(times)/cols)
    sheet = Image.new("RGB", (cols*thumb_w, rows*thumb_h), "white")
    for i, t in enumerate(times):
        im = frame_at(min(t, DURATION-.1)).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 66, 24), fill=(0, 0, 0))
        d.text((5, 3), f"{t:.1f}s", font=font(14), fill="white")
        sheet.paste(im, ((i%cols)*thumb_w, (i//cols)*thumb_h))
    sheet.save(CONTACT)


async def main():
    items = await make_speech()
    build_timeline(items)
    music, sfx = make_audio_beds()
    render_video()
    mix_audio(music, sfx)
    make_contact_sheet()
    print(OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
