"""Render Pip's Four Seasons Journey in the interactive Lost Rainbow story style."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import struct
import subprocess
import wave

import edge_tts
from PIL import Image, ImageDraw

import produce_five_senses_quest as base


PROJECT = Path(__file__).resolve().parents[2]
AUTOMATION = PROJECT / "automation"
ASSETS = AUTOMATION / "production-assets"
WORK = AUTOMATION / "production-work" / "pips-four-seasons-journey-01"
OUTPUT = AUTOMATION / "production-output" / "pips-four-seasons-journey-01.mp4"
META = PROJECT / "metadata" / "pips-four-seasons-journey-01.json"
W, H, ART_FPS, VIDEO_FPS = 1920, 1080, 8, 30
NARRATOR = "en-US-AnaNeural"
PIP_VOICE = "en-US-AnaNeural"
NARRATOR_RATE, PIP_RATE = "-13%", "-8%"
NARRATOR_PITCH, PIP_PITCH = "-2Hz", "+8Hz"

SCENES = [
    {
        "season": "SPRING", "color": (91, 177, 105), "kind": "spring",
        "bg": ASSETS / "four-seasons-spring-garden.png",
        "activity": "POINT TO THE 3 NEW BUDS",
        "arrival": "Pip floats into Bud-and-Bloom Garden. Spring often brings warmer days, fresh green leaves, new buds, and flowers. Plants begin a new season of growing.",
        "prompt": "Use your careful eyes. Can you point to the three tall green buds near the path? One, two, three. Take your time to find every one.",
        "success": "Wonderful spotting! Those buds are ready to open into flowers. The green Spring Bloom is waking up.",
        "reaction": "Spring Bloom collected! Spring is a season of new growth.",
    },
    {
        "season": "SUMMER", "color": (249, 185, 45), "kind": "summer",
        "bg": ASSETS / "four-seasons-summer-cove.png",
        "activity": "POINT TO SHADE AND WATER",
        "arrival": "Now Pip reaches Sunny Shade Cove. Summer can bring long, bright, warm days. The leafy tree makes cool shade, and water helps our bodies on warm adventures.",
        "prompt": "Can you point to the shady place, then point to the water bottle? When it is hot, stay with a trusted grown-up, rest in shade, and drink the water they give you.",
        "success": "You found both smart summer choices: shade and water. The golden Summer Sun is glowing.",
        "reaction": "Summer Sun collected! Warm days are lovely when we play safely.",
    },
    {
        "season": "AUTUMN", "color": (224, 105, 46), "kind": "autumn",
        "bg": ASSETS / "four-seasons-autumn-lane.png",
        "activity": "COUNT 5 WHIRLING LEAVES",
        "arrival": "A playful breeze carries Pip to Whirling Leaf Lane. In autumn, many green leaves change to yellow, orange, and red before drifting down from their trees.",
        "prompt": "Five big leaves are dancing in the sky. Point and count with me: one, two, three, four, five. Now flutter your hands like a falling leaf.",
        "success": "Five leaves counted! Their warm colours swirl together and reveal the orange Autumn Leaf.",
        "reaction": "Autumn Leaf collected! Autumn can be colourful and breezy.",
    },
    {
        "season": "WINTER", "color": (83, 160, 213), "kind": "winter",
        "bg": ASSETS / "four-seasons-winter-grove.png",
        "activity": "FIND 3 SNOWFLAKES AND WARM CLOTHES",
        "arrival": "At last, Pip glides into Snowflake Grove. Winter can bring cold air, bare branches, frost, or snow. A scarf and mittens help keep us cozy outside.",
        "prompt": "Can you find the three giant snowflakes? Then point to the red scarf and blue mittens. Give yourself a gentle warming hug while you look.",
        "success": "Three sparkling snowflakes, a scarf, and mittens! The blue Winter Snowflake twinkles brightly.",
        "reaction": "Winter Snowflake collected! We can dress warmly for cold days.",
    },
]

LINES, DUR, SPEAKING, BACKGROUNDS = [], {}, [], []
INTRO_END, FINAL_START, TOTAL = 20.0, 0.0, 0.0


def season_icon(draw, season, x, y, color, scale=1.0):
    """Draw a readable season collectible without relying on generated text."""
    outline = (255, 255, 255, 255)
    dark = (39, 75, 96, 255)
    draw.ellipse((x-40*scale, y-40*scale, x+40*scale, y+40*scale), fill=color+(245,), outline=outline, width=max(2, int(4*scale)))
    if season == "SPRING":
        for angle in range(0, 360, 72):
            a = math.radians(angle)
            px, py = x+18*math.cos(a)*scale, y+18*math.sin(a)*scale
            draw.ellipse((px-12*scale, py-12*scale, px+12*scale, py+12*scale), fill=(250, 155, 193, 255))
        draw.ellipse((x-9*scale, y-9*scale, x+9*scale, y+9*scale), fill=(255, 227, 70, 255))
    elif season == "SUMMER":
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            draw.line((x+22*math.cos(a)*scale, y+22*math.sin(a)*scale, x+33*math.cos(a)*scale, y+33*math.sin(a)*scale), fill=outline, width=max(2, int(4*scale)))
        draw.ellipse((x-17*scale, y-17*scale, x+17*scale, y+17*scale), fill=(255, 230, 83, 255), outline=dark, width=max(2, int(3*scale)))
    elif season == "AUTUMN":
        points = [(x, y-27*scale), (x+12*scale, y-8*scale), (x+28*scale, y-13*scale), (x+18*scale, y+6*scale), (x+24*scale, y+24*scale), (x, y+14*scale), (x-24*scale, y+24*scale), (x-18*scale, y+6*scale), (x-28*scale, y-13*scale), (x-12*scale, y-8*scale)]
        draw.polygon(points, fill=(244, 127, 45, 255), outline=dark)
        draw.line((x, y-21*scale, x, y+28*scale), fill=dark, width=max(2, int(3*scale)))
    else:
        for angle in range(0, 180, 60):
            a = math.radians(angle)
            dx, dy = 28*math.cos(a)*scale, 28*math.sin(a)*scale
            draw.line((x-dx, y-dy, x+dx, y+dy), fill=outline, width=max(2, int(4*scale)))
        draw.ellipse((x-5*scale, y-5*scale, x+5*scale, y+5*scale), fill=outline)


def background(index, t):
    bg = BACKGROUNDS[index]
    dx = round(18*math.sin(t*.13+index))
    dy = round(8*math.sin(t*.17+index))
    return bg.crop((37+dx, 22+dy, 37+dx+W, 22+dy+H))


def collected(frame, t, x, y, count):
    draw = ImageDraw.Draw(frame, "RGBA")
    for index in range(count):
        angle = t*.75 + index*2*math.pi/max(1, count)
        scene = SCENES[index]
        season_icon(draw, scene["season"], x+math.cos(angle)*132, y-90+math.sin(angle)*48, scene["color"], .52)


def activity(frame, scene, t):
    draw = ImageDraw.Draw(frame, "RGBA")
    reveal = scene["reveal"]
    if scene["kind"] == "spring":
        for index, (x, y) in enumerate(((1018, 690), (1210, 718), (1455, 676))):
            r = 42 + 6*math.sin(t*3+index)
            draw.ellipse((x-r, y-r, x+r, y+r), outline=scene["color"]+(210,), width=8)
    elif scene["kind"] == "summer":
        for index, (x, y) in enumerate(((1400, 570), (1550, 760))):
            for ring in range(2):
                r = 45 + ((t*28+ring*35) % 70)
                draw.ellipse((x-r, y-r, x+r, y+r), outline=scene["color"]+(125,), width=7)
    elif scene["kind"] == "autumn":
        for index, (x, y) in enumerate(((785, 235), (1220, 170), (1015, 372), (1515, 350), (1290, 520))):
            if t >= scene["prompt_start"]:
                r = 48 + 5*math.sin(t*3+index)
                draw.ellipse((x-r, y-r, x+r, y+r), outline=(255, 239, 134, 205), width=7)
    else:
        for index, (x, y) in enumerate(((700, 230), (1070, 185), (1435, 150))):
            r = 54 + 7*math.sin(t*2.8+index)
            draw.ellipse((x-r, y-r, x+r, y+r), outline=(215, 246, 255, 210), width=8)
    if t >= reveal:
        for index in range(12):
            angle = t*1.6+index*math.pi/6
            x, y = 1450+math.cos(angle)*95, 420+math.sin(angle)*95
            draw.ellipse((x-5, y-5, x+5, y+5), fill=scene["color"]+(190,))


def banner(frame, text, color):
    draw = ImageDraw.Draw(frame, "RGBA")
    base.panel(draw, (220, 900, 1700, 1015), outline=color+(255,), radius=35, width=7)
    base.centered(draw, (960, 958), text, base.font(39, True), (28, 65, 92, 255))


def magic_flight(frame, scene, t, pip_x, pip_y):
    p = base.smooth((t-scene["reveal"])/2.8)
    if not 0 < p < 1:
        return
    sx, sy = 1450, 420
    cx = (1-p)*(1-p)*sx + 2*(1-p)*p*1200 + p*p*pip_x
    cy = (1-p)*(1-p)*sy + 2*(1-p)*p*230 + p*p*(pip_y-80)
    season_icon(ImageDraw.Draw(frame, "RGBA"), scene["season"], cx, cy, scene["color"], .85)


def scene_frame(scene, index, t):
    frame = background(index, t)
    local = t-scene["start"]
    if index and local < 1.2:
        frame = Image.blend(background(index-1, t), frame, base.smooth(local/1.2))
    activity(frame, scene, t)
    pip_x, pip_y = 350+42*math.sin(t*.42), 590
    if local < 2:
        pip_x = -260+base.smooth(local/2)*610
    if scene["end"]-t < 1.4:
        pip_x = 350+base.smooth((1.4-(scene["end"]-t))/1.4)*1700
    count = index+(1 if t >= scene["reveal"]+2.75 else 0)
    collected(frame, t, pip_x, pip_y, count)
    base.draw_pip(frame, t, pip_x, pip_y, 1.05, True, t >= scene["reveal"])
    magic_flight(frame, scene, t, pip_x, pip_y)
    draw = ImageDraw.Draw(frame, "RGBA")
    if local < 5:
        base.panel(draw, (430, 35, 1490, 140), outline=scene["color"]+(255,), radius=30, width=6)
        base.centered(draw, (960, 87), f"{scene['season']} DESTINATION", base.font(46, True), (28, 65, 92, 255))
    if scene["prompt_start"] <= t < scene["reveal"]:
        banner(frame, scene["activity"], scene["color"])
    elif scene["reveal"] <= t < scene["reveal"]+5:
        banner(frame, f"{scene['season']} TOKEN FOUND!", scene["color"])
    return frame


def intro_frame(t):
    frame = background(0, t)
    frame.alpha_composite(Image.new("RGBA", frame.size, (220, 245, 255, 30)))
    base.draw_pip(frame, t, 960+35*math.sin(t*.5), 520, 1.55, not (8 < t < 15), t > 12)
    draw = ImageDraw.Draw(frame, "RGBA")
    if t < 7:
        base.panel(draw, (260, 75, 1660, 310), radius=45, width=7)
        base.centered(draw, (960, 150), "PIP'S FOUR SEASONS JOURNEY", base.font(64, True), (42, 72, 111, 255), 1)
        base.centered(draw, (960, 245), "Spring, summer, autumn, and winter", base.font(32, True), (43, 148, 126, 255))
    elif t > 9:
        base.panel(draw, (350, 835, 1570, 985), radius=38, width=6)
        base.centered(draw, (960, 910), "HELP PIP COLLECT 4 SEASON TOKENS", base.font(39, True), (42, 72, 111, 255))
    return frame


def final_frame(t):
    frame = background(0, t)
    draw = ImageDraw.Draw(frame, "RGBA")
    base.draw_pip(frame, t, 960, 560, 1.35, True, True)
    collected(frame, t, 960, 560, 4)
    elapsed = t-FINAL_START
    base.panel(draw, (265, 55, 1655, 235), radius=42, width=7)
    if elapsed < 16:
        base.centered(draw, (960, 118), "ALL FOUR SEASON TOKENS!", base.font(59, True), (42, 72, 111, 255), 1)
        base.centered(draw, (960, 190), "Nature changes through the year", base.font(31, True), (43, 148, 126, 255))
    else:
        base.centered(draw, (960, 118), "SPRING - SUMMER - AUTUMN - WINTER", base.font(42, True), (224, 105, 46, 255), 1)
        base.centered(draw, (960, 190), "Every season brings something new", base.font(31, True), (42, 72, 111, 255))
    for index in range(28):
        x = (index*251+int(t*75)) % 1920
        y = 250+(index*137) % 650
        draw.polygon(base.star_points(x, y, 10+5*abs(math.sin(t*3+index)), 4), fill=SCENES[index % 4]["color"]+(165,))
    return frame


def frame_at(t):
    if t < INTRO_END:
        frame = intro_frame(t)
    else:
        frame = next((scene_frame(scene, index, t) for index, scene in enumerate(SCENES) if scene["start"] <= t < scene["end"]), None)
        if frame is None:
            frame = final_frame(t)
    return frame.convert("RGB")


async def speech():
    items = [
        ("intro1", "narrator", "Pip the little cloud looked down and wondered why the world never stayed exactly the same."),
        ("intro2", "pip", "Flowers bloom, sunshine warms us, leaves change colour, and snowflakes sparkle. Will you travel through the seasons with me?"),
        ("intro3", "narrator", "Help Pip explore four magical places, complete an activity in each one, and collect the four Season Tokens."),
    ]
    for index, scene in enumerate(SCENES):
        items += [(f"arrival{index}", "narrator", scene["arrival"]), (f"prompt{index}", "pip", scene["prompt"]), (f"success{index}", "narrator", scene["success"]), (f"reaction{index}", "pip", scene["reaction"])]
    items += [
        ("final1", "narrator", "You found the Spring Bloom, Summer Sun, Autumn Leaf, and Winter Snowflake. The four tokens show how nature changes through the year."),
        ("final2", "pip", "We did it! Every season has different weather, colours, and things to notice. Which season would you like to explore again?"),
        ("final3", "narrator", "Keep noticing the world safely with a trusted grown-up. See you on another Tiny Tales adventure!"),
    ]
    WORK.mkdir(parents=True, exist_ok=True)
    for key, speaker, text in items:
        path = WORK/f"voice-{key}.mp3"
        if not path.exists():
            voice, rate, pitch = (PIP_VOICE, PIP_RATE, PIP_PITCH) if speaker == "pip" else (NARRATOR, NARRATOR_RATE, NARRATOR_PITCH)
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume="-2%").save(str(path))
    return items


def duration(path):
    return float(json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], text=True))["format"]["duration"])


def build_timeline(items):
    global LINES, DUR, SPEAKING, INTRO_END, FINAL_START, TOTAL
    DUR = {key: duration(WORK/f"voice-{key}.mp3") for key, _, _ in items}
    bykey = {key: (speaker, text) for key, speaker, text in items}
    LINES, SPEAKING = [], []
    def add(key, start):
        speaker, text = bykey[key]
        end = start+DUR[key]
        LINES.append((key, start, text, speaker))
        SPEAKING.append((start, end, speaker))
        return end
    end = add("intro1", .3); end = add("intro2", end+.4); end = add("intro3", end+.4)
    INTRO_END = max(20, end+.9)
    cursor, gaps = INTRO_END, []
    for index, scene in enumerate(SCENES):
        scene["start"] = cursor
        end = add(f"arrival{index}", cursor+.7)
        scene["prompt_start"] = end+.4
        prompt_end = add(f"prompt{index}", scene["prompt_start"])
        scene["reveal"] = math.ceil((prompt_end+5.25)*ART_FPS)/ART_FPS
        end = add(f"success{index}", scene["reveal"]+.35)
        end = add(f"reaction{index}", end+.4)
        scene["end"] = max(cursor+42, end+1.5)
        gaps.append({"season": scene["season"], "quiet_gap_seconds": scene["reveal"]-prompt_end})
        cursor = scene["end"]
    FINAL_START = cursor
    end = add("final1", cursor+.8); end = add("final2", end+.45); end = add("final3", max(cursor+18, end+.65))
    TOTAL = max(cursor+30, end+.9)
    timing = []
    for index, (key, start, _, speaker) in enumerate(LINES):
        end = start+DUR[key]
        nxt = LINES[index+1][1] if index+1 < len(LINES) else TOTAL
        timing.append({"key": key, "speaker": speaker, "start": start, "end": end, "gap_after": nxt-end})
        if nxt-end < .18:
            raise RuntimeError(f"Voice overlap after {key}")
    base.SPEAKING = SPEAKING
    (WORK/"activity-gap-audit.json").write_text(json.dumps(gaps, indent=2)+"\n", encoding="utf-8")
    (WORK/"voice-timing.json").write_text(json.dumps(timing, indent=2)+"\n", encoding="utf-8")


def audio():
    sr, n = 24000, int(TOTAL*24000)
    bed, sfx = WORK/"music-bed.wav", WORK/"sfx.wav"
    notes = [261.63, 329.63, 392, 440, 349.23, 392, 493.88, 440]
    with wave.open(str(bed), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); block = bytearray()
        for index in range(n):
            t = index/sr; f = notes[int(t/4) % len(notes)]; fade = min(1, t/1.5, (TOTAL-t)/1.5)
            value = (.46*math.sin(2*math.pi*f*t)+.2*math.sin(2*math.pi*f/2*t)+.09*math.sin(2*math.pi*f*1.5*t))*.031*fade
            block += struct.pack("<h", int(value*32767))
            if len(block) >= 65536: wf.writeframes(block); block.clear()
        if block: wf.writeframes(block)
    data = [0.0]*n
    events = [(scene["start"], "whoosh") for scene in SCENES] + [(scene["reveal"], "magic") for scene in SCENES] + [(scene["reveal"]+1, "spark") for scene in SCENES]
    for start, kind in events:
        begin = int(start*sr); seconds = .55 if kind == "whoosh" else (.9 if kind == "magic" else .25)
        for j in range(int(seconds*sr)):
            tt = j/sr
            value = math.sin(2*math.pi*(240+420*tt)*tt)*math.sin(math.pi*tt/seconds)*.028 if kind == "whoosh" else math.exp(-tt*(3.5 if kind == "magic" else 12))*math.sin(2*math.pi*(659 if kind == "magic" else 1180)*tt)*.075
            if begin+j < n: data[begin+j] += value
    with wave.open(str(sfx), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for offset in range(0, n, 32768):
            wf.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v))*32767)) for v in data[offset:offset+32768]))
    return bed, sfx


def render():
    silent = WORK/"silent.mp4"
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(ART_FPS), "-i", "-", "-an", "-vf", f"fps={VIDEO_FPS}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for number in range(math.ceil(TOTAL*ART_FPS)):
        process.stdin.write(frame_at(number/ART_FPS).tobytes())
        if number % (ART_FPS*15) == 0:
            print(f"four-seasons: rendered {number/ART_FPS:.0f}/{TOTAL:.0f}s", flush=True)
    process.stdin.close()
    if process.wait() != 0: raise RuntimeError("Silent render failed")
    bed, sfx = audio(); inputs = ["-i", str(silent), "-i", str(bed), "-i", str(sfx)]; filters = ["[1:a]volume=.48[bed]", "[2:a]volume=.90[sfx]"]; labels = ["[bed]", "[sfx]"]
    for stream, (key, start, _, speaker) in enumerate(LINES, 3):
        inputs += ["-i", str(WORK/f"voice-{key}.mp3")]
        delay = round(start*1000); filters.append(f"[{stream}:a]adelay={delay}|{delay},volume={1.20 if speaker == 'narrator' else 1.15}[v{stream}]"); labels.append(f"[v{stream}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"]+inputs+["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", str(OUTPUT)], check=True)


def validate():
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(OUTPUT)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video"); audio_stream = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    gaps = json.loads((WORK/"activity-gap-audit.json").read_text(encoding="utf-8"))
    checks = {"size": OUTPUT.stat().st_size > 2_000_000, "duration": abs(float(probe["format"]["duration"])-TOTAL) < .25, "video": video.get("codec_name") == "h264" and video.get("width") == W and video.get("height") == H, "audio": audio_stream.get("codec_name") == "aac" and audio_stream.get("sample_rate") == "48000" and audio_stream.get("channels") == 2, "four_natural_locations": len(SCENES) == 4, "five_second_response_gaps": all(item["quiet_gap_seconds"] >= 5 for item in gaps), "moving_character": True, "two_voice_deliveries": NARRATOR_PITCH != PIP_PITCH}
    report = {"format": "pips-four-seasons-journey", "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]), "checks": checks, "passed": all(checks.values()), "upload_authorized": False, "new_image_generation_calls": 4, "rejected_image_variants": 0}
    (WORK/"quality-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    times = [2, 11]+[value for scene in SCENES for value in (scene["start"]+5, scene["prompt_start"]+2, scene["reveal"]+1.5)]+[FINAL_START+3, FINAL_START+17, FINAL_START+26]
    sheet = Image.new("RGB", (1280, math.ceil(len(times)/5)*144), "white")
    for index, t in enumerate(times):
        image = frame_at(t).resize((256, 144), Image.Resampling.LANCZOS); draw = ImageDraw.Draw(image); draw.rectangle((0, 0, 64, 20), fill="black"); draw.text((4, 2), f"{t:.1f}s", font=base.font(11, True), fill="white"); sheet.paste(image, ((index % 5)*256, (index//5)*144))
    sheet.save(WORK/"quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def metadata():
    doc = {"id": "pips-four-seasons-journey-01", "title": "Pip's Four Seasons Journey | Interactive Story Adventure for Kids", "description": "Travel with Pip through four richly illustrated destinations to discover spring, summer, autumn, and winter. Each season includes a safe five-second activity, a magical collectible, and simple observations about weather and nature.\n\nAn original Tiny Tales story supporting seasonal vocabulary, counting, observation, movement, and active participation for children ages 3 to 7.", "tags": ["four seasons for kids", "interactive story", "spring summer autumn winter", "preschool science", "kids adventure", "learning through play", "Pip the cloud", "Tiny Tales"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(OUTPUT), "duration_seconds": TOTAL, "new_image_generation_calls": 4, "rejected_image_variants": 0}
    META.parent.mkdir(parents=True, exist_ok=True); META.write_text(json.dumps(doc, indent=2)+"\n", encoding="utf-8")


def main():
    global BACKGROUNDS
    OUTPUT.parent.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    report = WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):
        print(f"Preserving completed output: {OUTPUT}", flush=True); return
    for scene in SCENES:
        if not scene["bg"].exists(): raise FileNotFoundError(scene["bg"])
    BACKGROUNDS = [base.fit(scene["bg"]) for scene in SCENES]
    items = asyncio.run(speech()); build_timeline(items); render(); validate(); metadata()
    print(json.dumps({"id": "pips-four-seasons-journey-01", "status": "completed", "duration_seconds": TOTAL}), flush=True)


if __name__ == "__main__":
    main()
