"""Render three visually distinct Tiny Tales picture-size comparison adventures."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw

import produce_animal_games as games
import produce_clue_detective_batch as shared
import produce_snack_video as base


AUTOMATION = base.AUTOMATION
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
META_DIR = AUTOMATION.parent / "metadata"

EPISODES = [
    {
        "id": "ocean-bubble-size-station-01", "theme": "OCEAN", "mode": "bubbles",
        "title": "Ocean Bubble Size Station | Big and Small for Kids",
        "sheet": AUTOMATION / "production-assets" / "ocean-animals-sheet.png",
        "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "clues": [
            {"question": "Look at these three pictures. Which picture is the biggest?", "choices": ["dolphin", "sea turtle", "whale"], "scales": [0.68, 0.48, 1.0], "answer": "whale", "reveal": "The whale picture is the biggest. Biggest means it takes up the most space."},
            {"question": "Which picture is the smallest this time?", "choices": ["octopus", "seahorse", "crab"], "scales": [0.88, 0.36, 0.58], "answer": "seahorse", "reveal": "The seahorse picture is the smallest. Smallest means it takes up the least space."},
            {"question": "Which picture is between the biggest and smallest?", "choices": ["sea turtle", "dolphin", "crab"], "scales": [0.72, 1.0, 0.43], "answer": "sea turtle", "reveal": "The sea turtle is in the middle: bigger than the crab picture and smaller than the dolphin picture."},
            {"question": "One last bubble check. Which picture is biggest?", "choices": ["whale", "octopus", "dolphin"], "scales": [1.0, 0.55, 0.73], "answer": "whale", "reveal": "The whale picture is biggest. You compared all three before choosing."},
        ],
    },
    {
        "id": "farm-barn-height-lineup-01", "theme": "FARM", "mode": "ruler",
        "title": "Farm Barn Height Lineup | Tall and Short for Kids",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png",
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "clues": [
            {"question": "Compare the picture heights. Which one is tallest?", "choices": ["horse", "sheep", "chicken"], "scales": [1.0, 0.66, 0.42], "answer": "horse", "reveal": "The horse picture is tallest. Its top reaches highest on the barn ruler."},
            {"question": "Which picture is shortest in this lineup?", "choices": ["pig", "cow", "goat"], "scales": [0.48, 1.0, 0.72], "answer": "pig", "reveal": "The pig picture is shortest. Its top is lowest on the ruler."},
            {"question": "Which picture has the middle height?", "choices": ["chicken", "sheep", "horse"], "scales": [0.4, 0.68, 1.0], "answer": "sheep", "reveal": "The sheep picture has the middle height: taller than the chicken and shorter than the horse."},
            {"question": "Which farm picture reaches highest now?", "choices": ["cow", "goat", "pig"], "scales": [1.0, 0.7, 0.52], "answer": "cow", "reveal": "The cow picture reaches highest. Looking at the tops helped you compare."},
        ],
    },
    {
        "id": "bird-feather-measuring-studio-01", "theme": "BIRD", "mode": "feathers",
        "title": "Bird Feather Measuring Studio | Long and Short for Kids",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png",
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "clues": [
            {"question": "Compare the picture strips. Which bird has the longest strip?", "choices": ["owl", "flamingo", "penguin"], "scales": [0.54, 1.0, 0.72], "answer": "flamingo", "reveal": "The flamingo has the longest picture strip. It stretches farthest along the measuring tape."},
            {"question": "Which bird has the shortest picture strip?", "choices": ["peacock", "toucan", "owl"], "scales": [1.0, 0.43, 0.7], "answer": "toucan", "reveal": "The toucan has the shortest picture strip. Its strip ends first."},
            {"question": "Which strip ends in the middle?", "choices": ["penguin", "parrot", "peacock"], "scales": [0.42, 0.7, 1.0], "answer": "parrot", "reveal": "The parrot strip ends in the middle: longer than penguin's and shorter than peacock's."},
            {"question": "Final measurement. Which strip is longest?", "choices": ["owl", "toucan", "flamingo"], "scales": [0.65, 0.48, 1.0], "answer": "flamingo", "reveal": "The flamingo strip is longest. You checked where every strip ended."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    intros = {
        "bubbles": "Dive into the Ocean Bubble Size Station! Compare three picture bubbles, then choose the biggest, smallest, or middle-sized picture.",
        "ruler": "Welcome to the Farm Barn Height Lineup! Compare where each picture reaches, then choose the tallest, shortest, or middle height.",
        "feathers": "Step into the Bird Feather Measuring Studio! Compare where each colourful picture strip ends, then choose the longest, shortest, or middle length.",
    }
    lines = [("intro", intros[spec["mode"]])]
    for index, item in enumerate(spec["clues"], 1):
        options = ", ".join(item["choices"][:-1]) + f", or {item['choices'][-1]}"
        lines.append((f"q{index}", f"{item['question']} Is it {options}?"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "Brilliant comparing! You looked for bigger and smaller, taller and shorter, and longer and shorter. See you for another Tiny Tales adventure!"))
    for key, wording in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(wording, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def scene_background(spec: dict, t: float) -> Image.Image:
    frame = base.gradient_background({"bubbles": 5, "ruler": 12, "feathers": 18}[spec["mode"]], t).convert("RGBA")
    draw = ImageDraw.Draw(frame, "RGBA")
    if spec["mode"] == "bubbles":
        draw.rectangle((0, 650, 1920, 1080), fill=(30, 139, 170, 90))
        for x, y, r in [(100, 210, 26), (1770, 290, 38), (250, 820, 18), (1660, 760, 24)]:
            draw.ellipse((x-r, y-r, x+r, y+r), outline=(255, 255, 255, 150), width=5)
    elif spec["mode"] == "ruler":
        draw.rectangle((0, 705, 1920, 1080), fill=(119, 188, 92, 150))
        draw.polygon([(120, 705), (120, 270), (470, 100), (820, 270), (820, 705)], fill=(196, 73, 57, 170))
        for x in range(50, 1900, 170): draw.rectangle((x, 640, x+110, 760), fill=(250, 244, 210, 220), outline=(151, 103, 65, 255), width=5)
    else:
        draw.rectangle((0, 680, 1920, 1080), fill=(255, 247, 218, 180))
        for x in range(110, 1810, 100):
            length = 28 if x % 200 else 48
            draw.line((x, 895, x, 895-length), fill=(29, 76, 106, 230), width=4)
        draw.line((100, 895, 1820, 895), fill=(29, 76, 106, 240), width=8)
    return frame


def intro_frame(spec: dict, t: float) -> Image.Image:
    frame = scene_background(spec, t); draw = ImageDraw.Draw(frame, "RGBA")
    titles = {"bubbles": ("OCEAN BUBBLE", "SIZE STATION"), "ruler": ("FARM BARN", "HEIGHT LINEUP"), "feathers": ("BIRD FEATHER", "MEASURING STUDIO")}
    first, second = titles[spec["mode"]]
    base.panel(draw, (230, 150, 1690, 810), radius=55, width=9)
    base.centered(draw, (960, 325), first, base.F78, (224, 74, 67, 255), 2)
    base.centered(draw, (960, 455), second, base.F78, (29, 76, 106, 255), 2)
    base.centered(draw, (960, 650), "LOOK - COMPARE - CHOOSE", base.F38, (44, 151, 103, 255))
    return frame.convert("RGB")


def choice_cards(frame: Image.Image, item: dict, reveal: bool, mode: str) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    animals = frame.info["animals"]
    positions = [420, 960, 1500]
    for index, (name, scale, x) in enumerate(zip(item["choices"], item["scales"], positions)):
        selected = reveal and name == item["answer"]
        if mode == "bubbles":
            radius = int(180 * scale + 70); box = (x-radius, 520-radius, x+radius, 520+radius)
            draw.ellipse(box, fill=(240, 253, 255, 230), outline=(44, 151, 190, 255) if not selected else (46, 174, 92, 255), width=12 if selected else 7)
        elif mode == "ruler":
            height = int(370 * scale + 80); box = (x-210, 770-height, x+210, 790)
            draw.rounded_rectangle(box, radius=34, fill=(255, 250, 225, 235), outline=(46, 174, 92, 255) if selected else (160, 108, 62, 255), width=12 if selected else 7)
            for y in range(760, 300, -70): draw.line((x-205, y, x-175, y), fill=(119, 79, 48, 180), width=4)
        else:
            width = int(360 * scale + 170); box = (x-width//2, 380, x+width//2, 770)
            draw.rounded_rectangle(box, radius=70, fill=(255, 245, 210, 235), outline=(46, 174, 92, 255) if selected else (159, 105, 180, 255), width=12 if selected else 7)
            draw.line((box[0]+25, 730, box[2]-25, 730), fill=(224, 74, 67, 220), width=12)
        sprite = animals[name].copy(); max_side = int(245 * (0.58 + 0.42 * scale)); sprite.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        frame.alpha_composite(sprite, (x-sprite.width//2, 535-sprite.height//2))
        base.centered(draw, (x, 830), name.upper(), base.F38, (29, 76, 106, 255))
        if selected: base.centered(draw, (x, 925), "YES!", base.F38, (46, 151, 84, 255), 2)


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro": return intro_frame(spec, t)
    if event["kind"] == "outro": return games.ending(t, animals)
    item = event["item"]; reveal = event["kind"] == "reveal"
    frame = scene_background(spec, t); frame.info["animals"] = animals; draw = ImageDraw.Draw(frame, "RGBA")
    labels = {"bubbles": "BUBBLE SIZE", "ruler": "BARN HEIGHT", "feathers": "STRIP LENGTH"}
    base.header(frame, labels[spec["mode"]], f"COMPARE {event['index']} OF 4")
    base.panel(draw, (150, 145, 1770, 335), radius=35, width=6)
    wording = item["reveal"] if reveal else item["question"]
    lines = base.wrap_lines(draw, wording, base.F48, 1480); y = 205 if len(lines) > 1 else 240
    for line in lines:
        base.centered(draw, (960, y), line, base.F48, (46, 151, 84, 255) if reveal else (29, 76, 106, 255)); y += 58
    choice_cards(frame, item, reveal, spec["mode"])
    if event["kind"] == "think": base.centered(draw, (960, 995), "TAKE A CAREFUL LOOK!", base.F30, (224, 74, 67, 255))
    return frame.convert("RGB")


def write_metadata(spec: dict, output: Path, total: float) -> None:
    descriptions = {
        "bubbles": "Compare playful ocean-animal picture bubbles and find the biggest, smallest, and middle-sized pictures.",
        "ruler": "Line up friendly farm-animal pictures beside a barn ruler and compare tall, short, and middle heights.",
        "feathers": "Visit a colourful bird measuring studio and compare long, short, and middle picture strips.",
    }
    doc = {"id": spec["id"], "title": spec["title"], "description": f"{descriptions[spec['mode']]} Each puzzle includes a six-second thinking window and a clear visual answer.\n\nA Tiny Tales early-maths adventure supporting comparison words, visual attention, listening, and reasoning for children ages 3 to 7.", "tags": ["big and small", "size comparison", "early maths", "preschool learning", "animals for kids", "Tiny Tales", f"{spec['theme'].lower()} animals"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(output), "duration_seconds": total, "new_image_generation_calls": 0}
    META_DIR.mkdir(parents=True, exist_ok=True); (META_DIR / f"{spec['id']}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True); shared.frame_for = frame_for
    for spec in EPISODES:
        output = OUTPUT_DIR / f"{spec['id']}.mp4"; work = WORK_ROOT / spec["id"]; work.mkdir(parents=True, exist_ok=True); report = work / "quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):
            print(f"Preserving completed output: {output}", flush=True); continue
        animals = games.extract_grid(spec["sheet"], spec["names"]); lines = asyncio.run(make_voices(work, spec)); events, tracks, total = shared.make_timeline(work, spec, lines)
        shared.render(work, output, total, events, tracks, spec, animals); shared.validate(work, output, total, events, spec, animals)
        report_doc = json.loads(report.read_text(encoding="utf-8")); report_doc["format"] = f"picture-size-{spec['mode']}"; report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8"); write_metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__": main()
