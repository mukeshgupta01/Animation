"""Render three local-only Tiny Tales Find My Home habitat-rescue adventures."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw

import produce_snack_video as base
import produce_animal_games as games
import produce_clue_detective_batch as shared


AUTOMATION = base.AUTOMATION
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
META_DIR = AUTOMATION.parent / "metadata"

EPISODES = [
    {
        "id": "ocean-find-my-home-01",
        "theme": "OCEAN",
        "sheet": AUTOMATION / "production-assets" / "ocean-animals-sheet.png",
        "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "clues": [
            {"answer": "OPEN OCEAN", "animal": "whale", "question": "Our whale needs room for a very long journey. Which home should we choose?", "choices": ["ROCKY SHORE", "OPEN OCEAN", "SEAGRASS MEADOW"], "reveal": "Open ocean! Many whales travel enormous distances through deep ocean water."},
            {"answer": "SEAGRASS MEADOW", "animal": "seahorse", "question": "Our seahorse needs plants it can hold with its curling tail. Where is home?", "choices": ["SEAGRASS MEADOW", "OPEN OCEAN", "SANDY BEACH"], "reveal": "Seagrass meadow! A seahorse can curl its tail around underwater plants."},
            {"answer": "ROCKY REEF", "animal": "octopus", "question": "Our octopus wants cracks and small spaces for a safe den. Which home fits?", "choices": ["OPEN OCEAN", "SANDY BEACH", "ROCKY REEF"], "reveal": "Rocky reef! An octopus can squeeze into a sheltered den between rocks."},
            {"answer": "ROCKY SHORE", "animal": "crab", "question": "Our crab needs a shore with pools, stones, and places to hide. Where should it go?", "choices": ["SEAGRASS MEADOW", "ROCKY SHORE", "OPEN OCEAN"], "reveal": "Rocky shore! Many crabs shelter beneath rocks and explore tidal pools."},
        ],
    },
    {
        "id": "wild-animal-find-my-home-01",
        "theme": "WILD ANIMAL",
        "sheet": AUTOMATION / "production-assets" / "jungle-animals-sheet.png",
        "names": ["lion", "tiger", "elephant", "zebra", "hippopotamus", "crocodile"],
        "clues": [
            {"answer": "GRASSLAND", "animal": "zebra", "question": "Our zebra needs wide open land with grass for the herd. Which home fits?", "choices": ["RAINFOREST", "GRASSLAND", "RIVER"], "reveal": "Grassland! Zebras graze together across open African grasslands."},
            {"answer": "FOREST", "animal": "tiger", "question": "Our tiger needs cover, shade, and space to move quietly. Where is home?", "choices": ["FOREST", "GRASSLAND", "ROCKY COAST"], "reveal": "Forest! Tigers live in several habitats, including forests with plenty of cover."},
            {"answer": "RIVER", "animal": "hippopotamus", "question": "Our hippopotamus needs deep water to stay cool during the day. Which home should we choose?", "choices": ["MOUNTAINS", "FOREST", "RIVER"], "reveal": "River! Hippopotamuses spend much of the day keeping cool in water."},
            {"answer": "GRASSLAND", "animal": "lion", "question": "Our lion needs open country where its family group can rest and watch the land. Where is home?", "choices": ["GRASSLAND", "ICY COAST", "RAINFOREST"], "reveal": "Grassland! Many lions live in savannas and open grasslands."},
        ],
    },
    {
        "id": "bird-find-my-home-01",
        "theme": "BIRD",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png",
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "clues": [
            {"answer": "WETLAND", "animal": "flamingo", "question": "Our flamingo needs shallow water where it can search for tiny food. Which home fits?", "choices": ["WOODLAND", "WETLAND", "ICY COAST"], "reveal": "Wetland! Flamingos feed in shallow lakes, lagoons, and other wetlands."},
            {"answer": "ICY COAST", "animal": "penguin", "question": "Our penguin needs a coast beside cold, food-rich water. Where should it go?", "choices": ["RAINFOREST", "WOODLAND", "ICY COAST"], "reveal": "Icy coast! Many penguins live near cold southern seas and swim to find food."},
            {"answer": "RAINFOREST", "animal": "toucan", "question": "Our toucan needs tall tropical trees with fruit on the branches. Which home fits?", "choices": ["RAINFOREST", "WETLAND", "GRASSLAND"], "reveal": "Rainforest! Toucans live in tropical forests and use their bills to reach fruit."},
            {"answer": "WOODLAND", "animal": "owl", "question": "Our owl needs trees for shelter, nesting, and quiet hunting. Where is home?", "choices": ["ICY COAST", "WOODLAND", "OPEN OCEAN"], "reveal": "Woodland! Many owl species use tree hollows or forest nesting places."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    lines = [("intro", f"Tiny Tales rescue team, we need your help! Four {spec['theme'].lower()} friends are searching for the right homes. Follow the map, listen to each need, and choose a habitat!")]
    for index, item in enumerate(spec["clues"], 1):
        options = ", ".join(item["choices"][:-1]) + f", or {item['choices'][-1]}"
        lines.append((f"q{index}", f"Next rescue. {item['question']} Is it {options}?"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "Every friend found a suitable home! You followed the clues and completed the habitat rescue map. See you on our next Tiny Tales mission!"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def habitat_palette(label: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    if any(word in label for word in ("OCEAN", "RIVER", "WETLAND", "SHORE")):
        return (198, 239, 250, 255), (49, 132, 174, 255)
    if any(word in label for word in ("FOREST", "RAINFOREST", "WOODLAND", "SEAGRASS")):
        return (211, 242, 210, 255), (55, 137, 78, 255)
    if any(word in label for word in ("GRASSLAND", "MEADOW")):
        return (239, 238, 180, 255), (115, 150, 54, 255)
    if "ICY" in label:
        return (226, 245, 252, 255), (104, 159, 190, 255)
    if any(word in label for word in ("ROCKY", "MOUNTAINS")):
        return (232, 224, 211, 255), (125, 103, 78, 255)
    return (250, 228, 190, 255), (199, 133, 55, 255)


def draw_habitat(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, selected: bool, faded: bool) -> None:
    fill, accent = habitat_palette(label)
    if faded:
        fill = tuple(min(255, value + 18) for value in fill[:3]) + (135,)
    outline = (45, 162, 91, 255) if selected else accent
    width = 13 if selected else 6
    draw.rounded_rectangle(box, radius=36, fill=fill, outline=outline, width=width)
    x1, y1, x2, y2 = box
    horizon = y1 + 125
    if any(word in label for word in ("OCEAN", "RIVER", "WETLAND", "SHORE")):
        for offset in range(0, 90, 25):
            draw.arc((x1 + 35, horizon + offset, x2 - 35, horizon + 55 + offset), 190, 350, fill=accent, width=6)
    elif any(word in label for word in ("FOREST", "RAINFOREST", "WOODLAND", "SEAGRASS")):
        for x in (x1 + 100, (x1 + x2) // 2, x2 - 100):
            draw.rectangle((x - 10, horizon + 35, x + 10, y2 - 50), fill=(123, 91, 57, 220))
            draw.ellipse((x - 55, horizon - 35, x + 55, horizon + 75), fill=accent)
    elif "ICY" in label:
        draw.polygon([(x1 + 60, y2 - 60), ((x1 + x2) // 2, horizon - 20), (x2 - 60, y2 - 60)], fill=accent)
    else:
        for x in range(x1 + 55, x2 - 40, 55):
            draw.line((x, y2 - 55, x + 12, horizon + 25), fill=accent, width=6)
    draw.text(((x1 + x2) // 2, y1 + 55), label, font=base.F30, fill=(29, 76, 106, 255), anchor="mm")


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(2, t); draw = ImageDraw.Draw(frame, "RGBA")
        base.panel(draw, (185, 145, 1735, 935), radius=55, width=9)
        base.centered(draw, (960, 300), spec["theme"], base.F62, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 425), "FIND MY HOME", base.F78, (224, 74, 67, 255), 2)
        base.centered(draw, (960, 555), "HABITAT RESCUE MAP", base.F48, (44, 151, 103, 255))
        draw.line((430, 700, 1490, 700), fill=(224, 74, 67, 210), width=14)
        for x in (430, 780, 1140, 1490):
            draw.ellipse((x - 35, 665, x + 35, 735), fill=(255, 247, 220, 255), outline=(29, 76, 106, 255), width=7)
        return frame.convert("RGB")
    if event["kind"] == "outro":
        return games.ending(t, animals)
    item = event["item"]; reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"] + 10, t).convert("RGBA"); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, f"{spec['theme']} HABITAT RESCUE", f"MAP STOP {event['index']} OF {len(spec['clues'])}")
    base.panel(draw, (125, 145, 1795, 430), radius=38, width=7)
    sprite = animals[item["animal"]].copy(); sprite.thumbnail((300, 220), Image.Resampling.LANCZOS)
    frame.alpha_composite(sprite, (250 - sprite.width // 2, 285 - sprite.height // 2))
    wording = item["reveal"] if reveal else item["question"]
    lines = base.wrap_lines(draw, wording, base.F38, 1230)
    y = 225 if len(lines) > 1 else 275
    for line in lines:
        base.centered(draw, (1110, y), line, base.F38, (46, 151, 84, 255) if reveal else (29, 76, 106, 255)); y += 52
    for index, label in enumerate(item["choices"]):
        x1 = 145 + index * 560
        draw_habitat(draw, (x1, 500, x1 + 510, 865), label, reveal and label == item["answer"], reveal and label != item["answer"])
    if event["kind"] == "think":
        base.centered(draw, (960, 940), "FOLLOW THE CLUE — POINT TO THE BEST HOME!", base.F30, (224, 74, 67, 255))
    return frame.convert("RGB")


def write_metadata(spec: dict, output: Path, total: float) -> None:
    title = f"{spec['theme'].title()} Find My Home | Habitat Rescue Adventure for Kids"
    doc = {"id": spec["id"], "title": title[:100], "description": f"Follow the Tiny Tales rescue map and help four {spec['theme'].lower()} friends find suitable homes. Listen to what each animal needs, choose from three habitats, and learn a memorable fact after every rescue.\n\nAn interactive adventure supporting habitat vocabulary, listening, observation, animal knowledge, and early reasoning for children ages 3 to 7.", "tags": ["animal habitats", "animals for kids", "interactive kids video", "preschool learning", "habitat game", "Tiny Tales", f"{spec['theme'].lower()} animals"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(output), "duration_seconds": total, "new_image_generation_calls": 0}
    META_DIR.mkdir(parents=True, exist_ok=True)
    (META_DIR / f"{spec['id']}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shared.frame_for = frame_for
    for spec in EPISODES:
        output = OUTPUT_DIR / f"{spec['id']}.mp4"; work = WORK_ROOT / spec["id"]; work.mkdir(parents=True, exist_ok=True)
        report = work / "quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):
            print(f"Preserving completed output: {output}", flush=True); continue
        animals = games.extract_grid(spec["sheet"], spec["names"])
        lines = asyncio.run(make_voices(work, spec)); events, tracks, total = shared.make_timeline(work, spec, lines)
        shared.render(work, output, total, events, tracks, spec, animals)
        shared.validate(work, output, total, events, spec, animals)
        report_doc = json.loads(report.read_text(encoding="utf-8")); report_doc["format"] = "find-my-home-habitat-rescue"; report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8")
        write_metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__":
    main()
