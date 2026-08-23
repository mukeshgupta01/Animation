"""Produce the original 3D-look Animal Action Alphabet A-Z."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import wave

import edge_tts
from PIL import Image, ImageDraw, ImageFilter

import produce_snack_video as base
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
OUTPUT = AUTOMATION / "production-output" / "animal-action-alphabet-a-to-z-01.mp4"
WORK = AUTOMATION / "production-work" / "animal-action-alphabet-a-to-z-01"
META = AUTOMATION.parent / "metadata" / "animal-action-alphabet-a-to-z-01.json"
ASSETS = AUTOMATION / "production-assets"
VOICE = select_voice_profile("maisie-uk")
ART_FPS, VIDEO_FPS = 10, 30

SHEETS = {
    "af": ASSETS / "animal-action-3d-a-f.png",
    "gl": ASSETS / "animal-action-3d-g-l.png",
    "mr": ASSETS / "animal-action-3d-m-r.png",
    "sx": ASSETS / "animal-action-3d-s-x.png",
    "yz": ASSETS / "animal-action-3d-y-z.png",
}
BACKGROUNDS = {
    "meadow": ASSETS / "animal-action-meadow-stage.png",
    "jungle": ASSETS / "animal-action-jungle-stage.png",
    "ocean": ASSETS / "animal-action-ocean-stage.png",
    "sunset": ASSETS / "animal-action-sunset-stage.png",
    "finale": ASSETS / "animal-action-finale-stage.png",
}

# letter, animal, action, instruction, sprite group/index, environment, movement
ANIMALS = [
    ("A", "Alligator", "AMBLE", "Amble low and slow", "af", 0, "meadow", "travel"),
    ("B", "Bear", "BOUNCE", "Bounce up and down", "af", 1, "meadow", "bounce"),
    ("C", "Cat", "CREEP", "Creep softly like a cat", "af", 2, "meadow", "creep"),
    ("D", "Dog", "DANCE", "Dance with happy paws", "af", 3, "meadow", "dance"),
    ("E", "Elephant", "STOMP", "Stomp gently and strong", "af", 4, "meadow", "stomp"),
    ("F", "Frog", "JUMP", "Jump like a frog", "af", 5, "meadow", "jump"),
    ("G", "Giraffe", "GROW TALL", "Stretch and grow tall", "gl", 0, "jungle", "grow"),
    ("H", "Horse", "GALLOP", "Gallop on the spot", "gl", 1, "jungle", "gallop"),
    ("I", "Iguana", "INCH", "Inch along very slowly", "gl", 2, "jungle", "inch"),
    ("J", "Jaguar", "JOG", "Jog with light feet", "gl", 3, "jungle", "jog"),
    ("K", "Kangaroo", "JUMP", "Jump like a kangaroo", "gl", 4, "jungle", "jump"),
    ("L", "Lion", "LEAP", "Leap across the grass", "gl", 5, "jungle", "leap"),
    ("M", "Monkey", "MARCH", "March with swinging arms", "mr", 0, "jungle", "march"),
    ("N", "Narwhal", "NOD", "Nod your head gently", "mr", 1, "ocean", "nod"),
    ("O", "Owl", "OPEN WINGS", "Open your arms like wings", "mr", 2, "finale", "wings"),
    ("P", "Penguin", "WADDLE", "Waddle side to side", "mr", 3, "ocean", "waddle"),
    ("Q", "Quokka", "QUICK STEPS", "Take quick tiny steps", "mr", 4, "sunset", "quick"),
    ("R", "Rabbit", "REACH", "Reach your paws up high", "mr", 5, "meadow", "reach"),
    ("S", "Seal", "SWAY", "Sway from side to side", "sx", 0, "ocean", "sway"),
    ("T", "Tiger", "TIPTOE", "Tiptoe like a tiger", "sx", 1, "jungle", "tiptoe"),
    ("U", "Urchin", "UNFURL", "Unfurl all your fingers", "sx", 2, "ocean", "unfurl"),
    ("V", "Vulture", "FLAP", "Flap your wide wings", "sx", 3, "sunset", "flap"),
    ("W", "Whale", "WAVE", "Wave both arms slowly", "sx", 4, "ocean", "wave"),
    ("X", "X-ray Tetra", "MAKE AN X", "Make a big X with your arms", "sx", 5, "ocean", "xmove"),
    ("Y", "Yak", "YAWN", "Stretch into a giant yawn", "yz", 0, "sunset", "yawn"),
    ("Z", "Zebra", "ZIGZAG", "Zigzag from side to side", "yz", 1, "finale", "zigzag"),
]


def voice_path(name: str) -> Path:
    return WORK / f"voice-{name}.mp3"


async def make_voices() -> None:
    lines = [("intro", "Welcome to the Animal Action Alphabet! Make a safe movement space. We will meet every letter from A to Z."),
             ("outro", "Amazing animal actions! You moved from A all the way to Z. Which animal move was your favourite?")]
    for letter, animal, action, instruction, *_ in ANIMALS:
        lines.append((letter.lower(), f"{letter}. {animal}. {instruction}. Ready, go!"))
    tasks = []
    for name, text in lines:
        target = voice_path(name)
        if target.exists():
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(target)],
                capture_output=True,
                text=True,
            )
            if probe.returncode != 0 or not probe.stdout.strip():
                target.unlink()
        if not target.exists():
            tasks.append(edge_tts.Communicate(text, VOICE["voice"], rate=VOICE["rate"], pitch=VOICE["pitch"], volume="-1%").save(str(target)))
    if tasks:
        await asyncio.gather(*tasks)


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], text=True).strip())


def timeline() -> tuple[list[dict], list[tuple[Path, float]], float]:
    events = [{"kind": "title", "start": 0.0, "end": 4.8}]
    voices: list[tuple[Path, float]] = []
    cursor = 4.8
    intro = voice_path("intro")
    events.append({"kind": "intro", "start": cursor, "end": cursor + duration(intro) + .4})
    voices.append((intro, cursor)); cursor = events[-1]["end"] + .25
    for index, item in enumerate(ANIMALS):
        path = voice_path(item[0].lower())
        spoken = duration(path)
        events.append({"kind": "call", "start": cursor, "end": cursor + spoken + .15, "index": index})
        voices.append((path, cursor)); cursor += spoken + .15
        events.append({"kind": "action", "start": cursor, "end": cursor + 4.8, "index": index, "activity": True})
        cursor += 5.02
    outro = voice_path("outro")
    events.append({"kind": "outro", "start": cursor, "end": cursor + duration(outro) + .5})
    voices.append((outro, cursor)); cursor = events[-1]["end"]
    events.append({"kind": "end", "start": cursor, "end": cursor + 4.5})
    return events, voices, cursor + 4.5


def split_sheet(path: Path, columns: int, rows: int) -> list[Image.Image]:
    sheet = Image.open(path).convert("RGBA")
    result = []
    for row in range(rows):
        for col in range(columns):
            cell = sheet.crop((col * sheet.width // columns, row * sheet.height // rows, (col + 1) * sheet.width // columns, (row + 1) * sheet.height // rows))
            bbox = cell.getchannel("A").getbbox()
            if not bbox:
                raise RuntimeError(f"Empty animal cell {row},{col} in {path}")
            result.append(cell.crop(bbox))
    return result


def fit_background(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max((base.W + 160) / image.width, (base.H + 100) / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def load_assets() -> dict:
    required = [*SHEETS.values(), *BACKGROUNDS.values()]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Animal Action Alphabet assets: {missing}")
    sprites = {}
    for key in ("af", "gl", "mr", "sx"):
        sprites[key] = split_sheet(SHEETS[key], 3, 2)
    sprites["yz"] = split_sheet(SHEETS["yz"], 2, 1)
    return {"sprites": sprites, "backgrounds": {key: fit_background(path) for key, path in BACKGROUNDS.items()}}


def camera(source: Image.Image, t: float, seed: float) -> Image.Image:
    max_x, max_y = max(0, source.width - base.W), max(0, source.height - base.H)
    x = round(max_x * (.5 + .45 * math.sin(t * .11 + seed)))
    y = round(max_y * (.48 + .35 * math.sin(t * .08 + seed * .7)))
    return source.crop((x, y, x + base.W, y + base.H)).convert("RGBA")


def place(frame: Image.Image, image: Image.Image, center: tuple[float, float], height: float, tilt: float = 0.0) -> None:
    ratio = height / image.height
    item = image.resize((max(1, round(image.width * ratio)), max(1, round(height))), Image.Resampling.LANCZOS)
    if tilt:
        item = item.rotate(tilt, Image.Resampling.BICUBIC, expand=True)
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0)); shadow = ImageDraw.Draw(layer, "RGBA")
    width = max(90, round(item.width * .58)); cx, cy = center
    shadow.ellipse((cx - width / 2, cy - 14, cx + width / 2, cy + 18), fill=(35, 30, 38, 72))
    frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(8)))
    frame.alpha_composite(item, (round(cx - item.width / 2), round(cy - item.height)))


def movement(kind: str, p: float, t: float) -> tuple[float, float, float, float]:
    cycle = 2 * math.pi * p * 4
    x, y, scale, tilt = 1170.0, 950.0, 1.0, 0.0
    if kind in {"travel", "creep", "inch", "gallop", "jog", "leap", "quick", "tiptoe", "zigzag", "xmove"}:
        x = 880 + 500 * p
    if kind in {"bounce", "jump", "leap", "gallop"}: y -= abs(math.sin(cycle)) * (145 if kind in {"jump", "leap"} else 70)
    if kind in {"stomp", "march", "jog", "quick", "tiptoe"}: y -= abs(math.sin(cycle * (1.5 if kind == "quick" else 1))) * (42 if kind != "tiptoe" else 18)
    if kind in {"dance", "sway", "waddle", "flap", "wave", "nod", "yawn"}: tilt = math.sin(cycle) * (10 if kind in {"dance", "waddle", "sway"} else 6)
    if kind in {"grow", "reach", "wings", "unfurl", "yawn"}: scale = 1 + .14 * abs(math.sin(math.pi * p * 2))
    if kind == "creep": y += 55; scale = .9
    if kind == "inch": x = 890 + 360 * p + 24 * math.sin(cycle); scale = .9
    if kind == "nod": y += 8 * math.sin(cycle); tilt = 6 * math.sin(cycle)
    if kind == "xmove": y -= 130 * abs(math.sin(cycle / 2)); x += 100 * math.sin(cycle / 2)
    if kind == "zigzag": x = 1130 + 230 * math.sin(cycle / 2)
    return x, y, scale, tilt


def current_animal(event: dict) -> tuple | None:
    if "index" in event:
        return ANIMALS[event["index"]]
    return None


def frame_for(event: dict, t: float, assets: dict) -> Image.Image:
    item = current_animal(event)
    env = item[6] if item else "finale"
    frame = camera(assets["backgrounds"][env], t, float(ord(item[0])) if item else 7.0)
    draw = ImageDraw.Draw(frame, "RGBA")
    if event["kind"] == "title":
        frame.alpha_composite(Image.new("RGBA", frame.size, (20, 35, 78, 48)))
        base.panel(draw, (250, 150, 1670, 650), radius=58, fill=(255, 250, 232, 238), outline=(255, 175, 51, 255), width=8)
        base.centered(draw, (960, 270), "ANIMAL ACTION", base.F62, (40, 104, 155, 255), 2)
        base.centered(draw, (960, 400), "ALPHABET", base.font(96, True), (225, 72, 79, 255), 2)
        base.centered(draw, (960, 535), "MOVE FROM A TO Z!", base.F48, (62, 137, 92, 255), 2)
        return frame.convert("RGB")
    if event["kind"] in {"intro", "outro", "end"}:
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, letter in enumerate(letters):
            angle = 2 * math.pi * i / 26 + t * .12
            x = 960 + 700 * math.cos(angle); y = 555 + 360 * math.sin(angle)
            draw.ellipse((x - 34, y - 34, x + 34, y + 34), fill=((54 + i * 17) % 180 + 55, (120 + i * 23) % 150 + 60, (180 + i * 13) % 70 + 150, 235), outline=(255, 255, 255, 245), width=3)
            base.centered(draw, (x, y - 1), letter, base.font(30, True), (255, 255, 255, 255))
        base.panel(draw, (420, 340, 1500, 760), radius=48, fill=(255, 250, 235, 235), outline=(255, 179, 48, 255), width=7)
        headline = "READY TO MOVE?" if event["kind"] == "intro" else "A TO Z - AMAZING!"
        base.centered(draw, (960, 465), headline, base.F62, (48, 105, 148, 255), 2)
        base.centered(draw, (960, 590), "26 ANIMALS • 26 ACTIONS", base.F48, (218, 74, 82, 255), 2)
        return frame.convert("RGB")

    letter, animal, action, instruction, group, sprite_index, _, motion = item
    progress = max(0.0, min(1.0, (t - event["start"]) / (event["end"] - event["start"])))
    active_progress = progress if event["kind"] == "action" else .15
    x, y, scale, tilt = movement(motion, active_progress, t)
    image = assets["sprites"][group][sprite_index]
    base_height = 650 if letter not in {"G", "W", "Y"} else 720
    place(frame, image, (x, y), base_height * scale, tilt)
    # Action trails make movement visibly different even with single rendered poses.
    for i in range(9):
        phase = t * 2.2 + i * .8 + ord(letter)
        px = 980 + 520 * math.cos(phase); py = 580 + 300 * math.sin(phase * 1.3)
        radius = 7 + i % 4
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=((65 + i * 28) % 210, (130 + i * 17) % 190, 230, 130))
    base.panel(draw, (75, 80, 675, 925), radius=50, fill=(255, 250, 235, 238), outline=(255, 178, 48, 255), width=7)
    base.centered(draw, (375, 270), letter, base.font(235, True), (222, 70, 80, 255), 4)
    base.centered(draw, (375, 505), animal.upper(), base.F48 if len(animal) < 9 else base.F38, (43, 92, 132, 255), 2)
    base.centered(draw, (375, 615), action, base.F48 if len(action) < 10 else base.F38, (60, 142, 95, 255), 2)
    if event["kind"] == "action":
        base.centered(draw, (375, 715), "YOUR TURN!", base.F38, (224, 112, 34, 255), 2)
        count = min(5, int(progress * 5) + 1)
        for i in range(5):
            cx = 215 + i * 80
            draw.ellipse((cx - 25, 790 - 25, cx + 25, 790 + 25), fill=(255, 168, 42, 255) if i < count else (205, 214, 215, 255), outline=(255, 255, 255, 255), width=3)
    else:
        base.centered(draw, (375, 745), instruction.upper(), base.font(28, True), (74, 80, 88, 255), 2)
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "animal-action-music.wav"
    if target.exists(): return target
    rate = 48000; count = round(total * rate); rng = random.Random(2608)
    notes = (261.63, 329.63, 392.0, 440.0, 523.25)
    with wave.open(str(target), "wb") as handle:
        handle.setnchannels(2); handle.setsampwidth(2); handle.setframerate(rate); block = bytearray()
        for i in range(count):
            t = i / rate; beat = t % .5; eighth = t % .25; note = notes[int(t / 2) % len(notes)]
            kick = math.sin(2 * math.pi * (75 - 25 * min(1, beat / .15)) * beat) * math.exp(-24 * beat) * .095
            clap = (rng.random() * 2 - 1) * math.exp(-34 * ((t + .25) % .5)) * .018
            bass = math.sin(2 * math.pi * note / 2 * t) * .022
            bell = math.sin(2 * math.pi * notes[int(t / .25) % len(notes)] * t) * math.exp(-13 * eighth) * .025
            fade = min(1, t / 1.2, (total - t) / 1.5); sample = round(max(-1, min(1, (kick + clap + bass + bell) * fade)) * 32767)
            block += struct.pack("<hh", sample, sample)
            if len(block) >= 131072: handle.writeframes(block); block.clear()
        if block: handle.writeframes(block)
    return target


def render(events: list[dict], voices: list[tuple[Path, float]], total: float, assets: dict) -> None:
    silent = WORK / "silent.mp4"
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{base.W}x{base.H}", "-r", str(ART_FPS), "-i", "-", "-an", "-vf", f"fps={VIDEO_FPS}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-profile:v", "high", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    assert process.stdin is not None
    for number in range(math.ceil(total * ART_FPS)):
        t = number / ART_FPS
        event = next((value for value in events if value["start"] <= t < value["end"]), events[-1])
        process.stdin.write(frame_for(event, t, assets).tobytes())
        if number % (ART_FPS * 15) == 0: print(f"Rendered {t:.0f}/{total:.0f}s", flush=True)
    process.stdin.close()
    if process.wait() != 0: raise RuntimeError("Animal Action Alphabet silent render failed")
    bed = make_music(total); inputs = ["-i", str(silent), "-i", str(bed)]; filters = ["[1:a]volume=.70[bed]"]; labels = ["[bed]"]
    for stream, (voice, start) in enumerate(voices, 2):
        inputs += ["-i", str(voice)]; delay = round(start * 1000)
        filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.24[v{stream}]"); labels.append(f"[v{stream}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUTPUT)], check=True)


def quality(events: list[dict], total: float, assets: dict) -> None:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(OUTPUT)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video"); audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    gaps = [{"letter": ANIMALS[e["index"]][0], "quiet_gap_seconds": e["end"] - e["start"]} for e in events if e.get("activity")]
    (WORK / "activity-gap-audit.json").write_text(json.dumps(gaps, indent=2) + "\n", encoding="utf-8")
    checks = {"size": OUTPUT.stat().st_size > 3_000_000, "duration": 190 <= float(probe["format"]["duration"]) <= 360 and abs(float(probe["format"]["duration"]) - total) < .3, "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H, "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2, "twenty_six_letters": len(ANIMALS) == 26 and len({x[0] for x in ANIMALS}) == 26, "twenty_six_response_gaps": len(gaps) == 26 and all(g["quiet_gap_seconds"] >= 4.5 for g in gaps), "twenty_six_sprites": sum(len(v) for v in assets["sprites"].values()) == 26, "five_world_stages": len(assets["backgrounds"]) == 5, "voice_rotation": VOICE["name"] == "maisie-uk"}
    report = {"format": "3d-animal-action-alphabet-parade", "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]), "voice_profile": VOICE["name"], "new_image_generation_calls": 11, "rejected_image_variants": 1, "true_rigged_3d_animation": False, "visual_method": "original 3D-rendered animal sprites with code-driven action motion, tracking cameras and five world stages", "checks": checks, "passed": all(checks.values())}
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    action_events = [e for e in events if e.get("activity")]
    contact = Image.new("RGB", (1568, 504), "white")
    for i, event in enumerate(action_events):
        t = event["start"] + 2.2; image = frame_for(event, t, assets).resize((224, 126), Image.Resampling.LANCZOS)
        contact.paste(image, ((i % 7) * 224, (i // 7) * 126))
    contact.save(WORK / "quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Animal Action Alphabet quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc = {"id": "animal-action-alphabet-a-to-z-01", "title": "Animal Action Alphabet A-Z | Move and Learn with 26 Animals", "description": "Move through the whole alphabet with 26 lively animal friends. Children amble, bounce, creep, dance, stomp, jump, stretch, gallop, waddle, flap, zigzag and try many more safe actions from A to Z.\n\nAn original Tiny Tales 3D-look alphabet-and-movement parade supporting letter recognition, animal vocabulary, listening and active play for children ages 3 to 7.", "tags": ["animal alphabet", "ABC for kids", "movement for kids", "animals A to Z", "preschool learning", "brain break for kids", "Tiny Tales"], "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": False, "output": str(OUTPUT), "duration_seconds": total, "voice_profile": VOICE["name"], "format_family": "3d-animal-action-alphabet-parade", "visual_system": "3d-animal-world-stage-portals", "interaction_style": "letter-callout-and-whole-body-movement", "new_image_generation_calls": 11, "rejected_image_variants": 1, "true_rigged_3d_animation": False}
    META.parent.mkdir(parents=True, exist_ok=True); META.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True); OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() and (WORK / "quality-report.json").exists() and json.loads((WORK / "quality-report.json").read_text(encoding="utf-8")).get("passed"):
        print(f"Completed output already exists; preserving without regeneration: {OUTPUT}"); return
    asyncio.run(make_voices()); events, voices, total = timeline(); assets = load_assets(); render(events, voices, total, assets); quality(events, total, assets); write_metadata(total)
    print(json.dumps({"id": "animal-action-alphabet-a-to-z-01", "duration_seconds": total, "status": "completed"}, indent=2))


if __name__ == "__main__":
    main()
