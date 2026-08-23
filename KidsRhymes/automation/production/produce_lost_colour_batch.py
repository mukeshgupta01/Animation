"""Render three local-only Tiny Tales Lost Colour Rescue adventures."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import subprocess

import edge_tts
from PIL import Image, ImageDraw, ImageFilter, ImageOps

import produce_snack_video as base
import produce_animal_games as games


AUTOMATION = base.AUTOMATION
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
META_DIR = AUTOMATION.parent / "metadata"

EPISODES = [
    {
        "id": "ocean-lost-colour-rescue-01",
        "world": "OCEAN",
        "sheet": AUTOMATION / "production-assets" / "ocean-animals-sheet.png",
        "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "missions": [
            {"animal": "whale", "answer": "BLUE", "choices": [("PINK", "#F48FB1"), ("BLUE", "#4B9FE1"), ("YELLOW", "#F5C84C")], "fact": "Whales breathe air through blowholes on top of their heads."},
            {"animal": "crab", "answer": "RED", "choices": [("GREEN", "#62B66E"), ("PURPLE", "#9C72CF"), ("RED", "#E85D5D")], "fact": "Crabs usually move sideways using their jointed legs."},
            {"animal": "seahorse", "answer": "YELLOW", "choices": [("YELLOW", "#F5C84C"), ("BLUE", "#4B9FE1"), ("PINK", "#F48FB1")], "fact": "A seahorse swims upright and curls its tail around sea plants."},
            {"animal": "octopus", "answer": "ORANGE", "choices": [("PURPLE", "#9C72CF"), ("ORANGE", "#F39A4A"), ("GREEN", "#62B66E")], "fact": "An octopus can change colour and texture to communicate or hide."},
        ],
    },
    {
        "id": "farm-lost-colour-rescue-01",
        "world": "FARM",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png",
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "missions": [
            {"animal": "pig", "answer": "PINK", "choices": [("BLUE", "#4B9FE1"), ("PINK", "#F48FB1"), ("GREEN", "#62B66E")], "fact": "A pig uses its strong sensitive snout to explore and find food."},
            {"animal": "chicken", "answer": "RED", "choices": [("RED", "#E85D5D"), ("PURPLE", "#9C72CF"), ("BLUE", "#4B9FE1")], "fact": "Chickens communicate with many different calls and sounds."},
            {"animal": "sheep", "answer": "WHITE", "choices": [("YELLOW", "#F5C84C"), ("BROWN", "#9B6B43"), ("WHITE", "#F7F5ED")], "fact": "A sheep's wool helps keep it warm in cool weather."},
            {"animal": "cow", "answer": "BLACK & WHITE", "choices": [("BLACK & WHITE", "#444444"), ("ORANGE", "#F39A4A"), ("PINK", "#F48FB1")], "fact": "Cows use their long tongues to pull grass into their mouths."},
        ],
    },
    {
        "id": "bird-lost-colour-rescue-01",
        "world": "COLOURFUL BIRD",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png",
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "missions": [
            {"animal": "flamingo", "answer": "PINK", "choices": [("PINK", "#F48FB1"), ("GREEN", "#62B66E"), ("BLUE", "#4B9FE1")], "fact": "Flamingos get their pink colour from pigments in their food."},
            {"animal": "peacock", "answer": "BLUE & GREEN", "choices": [("ORANGE", "#F39A4A"), ("BLUE & GREEN", "#3BA9A0"), ("PINK", "#F48FB1")], "fact": "A peacock can fan long colourful feathers into a huge display."},
            {"animal": "penguin", "answer": "BLACK & WHITE", "choices": [("PURPLE", "#9C72CF"), ("YELLOW", "#F5C84C"), ("BLACK & WHITE", "#444444")], "fact": "Penguins use their wings like flippers to fly through water."},
            {"animal": "parrot", "answer": "RED & GREEN", "choices": [("RED & GREEN", "#D85C59"), ("BLUE", "#4B9FE1"), ("WHITE", "#F7F5ED")], "fact": "Parrots use strong curved beaks to crack seeds and climb."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    lines = [("intro", f"Oh no! The colours have floated away from our {spec['world'].lower()} friends. Join the Lost Colour Rescue and help bring every friend back to bright, happy colour!")]
    for index, mission in enumerate(spec["missions"], 1):
        choices = ", ".join(name.lower() for name, _ in mission["choices"][:-1]) + f", or {mission['choices'][-1][0].lower()}"
        lines.append((f"q{index}", f"Our {mission['animal']} has lost its storybook colour. Which colour should we choose: {choices}?"))
        lines.append((f"a{index}", f"You found {mission['answer'].lower()}! Colour restored! {mission['fact']}"))
    lines.append(("outro", "Every colour is back! You made careful choices and rescued all our animal friends. See you on the next Tiny Tales adventure!"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def timeline(work: Path, spec: dict, lines: list[tuple[str, str]]) -> tuple[list[dict], list[tuple[str, float]], float]:
    lengths = {key: base.duration(voice_path(work, key)) for key, _ in lines}
    events: list[dict] = []
    tracks: list[tuple[str, float]] = []
    cursor = 0.3

    def add(kind: str, length: float, **data: object) -> dict:
        nonlocal cursor
        event = {"kind": kind, "start": cursor, "end": cursor + length, **data}
        events.append(event); cursor = event["end"]
        return event

    event = add("intro", max(8.0, lengths["intro"] + 0.8)); tracks.append(("intro", event["start"] + 0.1))
    for index, mission in enumerate(spec["missions"], 1):
        event = add("question", lengths[f"q{index}"] + 0.4, index=index, mission=mission); tracks.append((f"q{index}", event["start"] + 0.1))
        add("think", 6.0, index=index, mission=mission)
        event = add("reveal", lengths[f"a{index}"] + 1.0, index=index, mission=mission); tracks.append((f"a{index}", event["start"] + 0.15))
    event = add("outro", max(8.0, lengths["outro"] + 0.8)); tracks.append(("outro", event["start"] + 0.1))
    return events, tracks, math.ceil(cursor * base.ART_FPS) / base.ART_FPS


def faded(sprite: Image.Image) -> Image.Image:
    alpha = sprite.getchannel("A")
    gray = ImageOps.grayscale(sprite.convert("RGB")).convert("RGBA")
    gray.putalpha(alpha.point(lambda value: int(value * 0.72)))
    return gray


def place_sprite(frame: Image.Image, sprite: Image.Image, center: tuple[int, int], box: tuple[int, int]) -> None:
    image = sprite.copy()
    image.thumbnail(box, Image.Resampling.LANCZOS)
    x = center[0] - image.width // 2; y = center[1] - image.height // 2
    shadow = Image.new("RGBA", frame.size)
    mask = Image.new("L", image.size, 0); mask.paste(image.getchannel("A"))
    blur = mask.filter(ImageFilter.GaussianBlur(18))
    shadow.paste((30, 52, 67, 95), (x + 12, y + 20), blur)
    frame.alpha_composite(shadow); frame.alpha_composite(image, (x, y))


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(1, t); draw = ImageDraw.Draw(frame, "RGBA")
        base.panel(draw, (190, 150, 1730, 930), radius=55, width=9)
        base.centered(draw, (960, 310), spec["world"], base.F62, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 430), "LOST COLOUR RESCUE", base.F78, (224, 74, 67, 255), 2)
        base.centered(draw, (960, 650), "LOOK  •  CHOOSE  •  RESTORE", base.F38, (44, 151, 103, 255))
        return frame.convert("RGB")
    if event["kind"] == "outro":
        return games.ending(t, animals)
    mission = event["mission"]
    reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"] + 6, t).convert("RGBA"); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, f"{spec['world']} LOST COLOUR RESCUE", f"RESCUE {event['index']} OF {len(spec['missions'])}")
    base.panel(draw, (125, 145, 900, 815), radius=40, width=7)
    base.panel(draw, (965, 145, 1795, 815), radius=40, width=7)
    base.centered(draw, (510, 220), f"HELP THE {mission['animal'].upper()}!", base.F48, (29, 76, 106, 255))
    sprite = animals[mission["animal"]] if reveal else faded(animals[mission["animal"]])
    place_sprite(frame, sprite, (510, 525), (600, 500))
    if reveal:
        base.centered(draw, (1380, 230), f"{mission['answer']} RESTORED!", base.F48, (46, 151, 84, 255))
        fact_lines = base.wrap_lines(draw, mission["fact"], base.F38, 680)
        y = 430
        for line in fact_lines:
            base.centered(draw, (1380, y), line, base.F38, (29, 76, 106, 255)); y += 54
    else:
        base.centered(draw, (1380, 225), "CHOOSE A COLOUR", base.F48, (224, 74, 67, 255))
        for index, (name, colour) in enumerate(mission["choices"]):
            y = 350 + index * 145
            draw.rounded_rectangle((1060, y - 50, 1700, y + 50), radius=30, fill=(255, 255, 255, 238), outline=colour, width=10)
            draw.ellipse((1100, y - 30, 1160, y + 30), fill=colour, outline=(30, 60, 80, 255), width=3)
            draw.text((1210, y), name, font=base.F38, fill=(29, 76, 106, 255), anchor="lm")
        if event["kind"] == "think":
            base.centered(draw, (960, 915), "POINT TO YOUR CHOICE — YOU HAVE SIX SECONDS!", base.F30, (224, 74, 67, 255))
    return frame.convert("RGB")


def render(work: Path, output: Path, total: float, events: list[dict], tracks: list[tuple[str, float]], spec: dict, animals: dict[str, Image.Image]) -> None:
    silent = work / "silent.mp4"
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{base.W}x{base.H}", "-r", str(base.ART_FPS), "-i", "-", "-an", "-vf", f"fps={base.VIDEO_FPS}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for number in range(math.ceil(total * base.ART_FPS)):
        event = next((item for item in events if item["start"] <= number / base.ART_FPS < item["end"]), events[-1])
        process.stdin.write(frame_for(event, number / base.ART_FPS, spec, animals).tobytes())
        if number % (base.ART_FPS * 15) == 0:
            print(f"{spec['id']}: rendered {number / base.ART_FPS:.0f}/{total:.0f}s", flush=True)
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("Video render failed")
    bed, sfx = base.make_audio_bed(work, total, events)
    inputs = ["-i", str(silent), "-i", str(bed), "-i", str(sfx)]
    filters = ["[1:a]volume=.68[bed]", "[2:a]volume=1.0[sfx]"]
    labels = ["[bed]", "[sfx]"]
    for stream, (key, start) in enumerate(tracks, 3):
        inputs += ["-i", str(voice_path(work, key))]; delay = round(start * 1000)
        filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.22[v{stream}]"); labels.append(f"[v{stream}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(output)], check=True)


def validate(work: Path, output: Path, total: float, events: list[dict], spec: dict, animals: dict[str, Image.Image]) -> None:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(output)], text=True))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    checks = {"size": output.stat().st_size > 1_000_000, "duration": abs(float(probe["format"]["duration"]) - total) < 0.25, "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H, "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2}
    report = {"format": "lost-colour-rescue", "output": str(output), "duration_seconds": float(probe["format"]["duration"]), "checks": checks, "passed": all(checks.values()), "upload_authorized": False}
    (work / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    samples = [events[0]] + [event for event in events if event["kind"] in ("think", "reveal")] + [events[-1]]
    sheet = Image.new("RGB", (960, math.ceil(len(samples) / 4) * 135), "white")
    for index, event in enumerate(samples):
        sample = frame_for(event, event["start"] + min(1, (event["end"] - event["start"]) / 2), spec, animals).resize((240, 135), Image.Resampling.LANCZOS)
        sheet.paste(sample, ((index % 4) * 240, (index // 4) * 135))
    sheet.save(work / "quality-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(f"Quality gate failed: {report}")


def metadata(spec: dict, output: Path, total: float) -> None:
    title = f"{spec['world'].title()} Lost Colour Rescue | Interactive Animal Adventure"
    doc = {"id": spec["id"], "title": title[:100], "description": f"The colours have floated away! Join four playful {spec['world'].lower()} rescue missions, choose the missing storybook colour, and discover a memorable animal fact after every reveal.\n\nAn interactive Tiny Tales adventure supporting colour words, listening, observation, animal vocabulary, and decision-making for children ages 3 to 7.", "tags": ["colours for kids", "animal adventure", "interactive kids video", "preschool learning", "animal facts", "Tiny Tales", f"{spec['world'].lower()} animals"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(output), "duration_seconds": total, "new_image_generation_calls": 0}
    META_DIR.mkdir(parents=True, exist_ok=True)
    (META_DIR / f"{spec['id']}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for spec in EPISODES:
        output = OUTPUT_DIR / f"{spec['id']}.mp4"; work = WORK_ROOT / spec["id"]; work.mkdir(parents=True, exist_ok=True)
        report = work / "quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):
            print(f"Preserving completed output: {output}", flush=True); continue
        animals = games.extract_grid(spec["sheet"], spec["names"])
        lines = asyncio.run(make_voices(work, spec)); events, tracks, total = timeline(work, spec, lines)
        render(work, output, total, events, tracks, spec, animals); validate(work, output, total, events, spec, animals); metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__":
    main()
