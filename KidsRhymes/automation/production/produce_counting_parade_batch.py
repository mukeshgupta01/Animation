"""Render three local-only Tiny Tales Animal Counting Parade adventures."""

from __future__ import annotations

import asyncio
import json
import math
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
        "id": "ocean-animal-counting-parade-01", "theme": "OCEAN",
        "sheet": AUTOMATION / "production-assets" / "ocean-animals-sheet.png",
        "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "clues": [
            {"animal": "whale", "count": 1, "question": "A giant visitor is swimming past. How many whales can you count?", "reveal": "One whale! Whales breathe air through blowholes."},
            {"animal": "sea turtle", "count": 3, "question": "The turtle parade is crossing the blue water. How many sea turtles can you count?", "reveal": "Three sea turtles! Sea turtles paddle with strong flippers."},
            {"animal": "crab", "count": 4, "question": "Some sideways walkers have reached the shore. How many crabs can you count?", "reveal": "Four crabs! Crabs have ten jointed limbs, including their claws."},
            {"animal": "dolphin", "count": 2, "question": "Two playful shapes are gliding together. How many dolphins can you count?", "reveal": "Two dolphins! Dolphins communicate with clicks and whistles."},
        ],
    },
    {
        "id": "farm-animal-counting-parade-01", "theme": "FARM",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png",
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "clues": [
            {"animal": "horse", "count": 2, "question": "The paddock gate is open for the parade. How many horses can you count?", "reveal": "Two horses! Horses can rest while standing or lying down."},
            {"animal": "chicken", "count": 4, "question": "The feathered friends are looking for seeds. How many chickens can you count?", "reveal": "Four chickens! Chickens use many different calls to communicate."},
            {"animal": "pig", "count": 1, "question": "A curious snout is exploring the farmyard. How many pigs can you count?", "reveal": "One pig! A pig has an excellent sense of smell."},
            {"animal": "sheep", "count": 3, "question": "The woolly parade is walking across the grass. How many sheep can you count?", "reveal": "Three sheep! Wool helps sheep stay warm in cool weather."},
        ],
    },
    {
        "id": "bird-counting-parade-01", "theme": "COLOURFUL BIRD",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png",
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "clues": [
            {"animal": "flamingo", "count": 3, "question": "The pink birds are standing in shallow water. How many flamingos can you count?", "reveal": "Three flamingos! Pigments in their food help colour their feathers pink."},
            {"animal": "owl", "count": 1, "question": "A quiet bird is watching from the tree. How many owls can you count?", "reveal": "One owl! An owl can turn its head far around to look behind."},
            {"animal": "penguin", "count": 4, "question": "The waddling parade has reached the icy coast. How many penguins can you count?", "reveal": "Four penguins! Penguins use their wings like flippers underwater."},
            {"animal": "toucan", "count": 2, "question": "Two colourful bills are peeking through the leaves. How many toucans can you count?", "reveal": "Two toucans! A toucan's large bill helps it reach fruit."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    lines = [("intro", f"Welcome to the {spec['theme'].lower()} Animal Counting Parade! Look carefully, count each group one time, and show the number with your fingers.")]
    for index, item in enumerate(spec["clues"], 1):
        lines.append((f"q{index}", f"The next group is here. {item['question']}"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "The counting parade is complete! You looked carefully, counted each animal, and matched every group to a number. Fantastic counting!"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def animal_positions(count: int) -> list[tuple[int, int]]:
    layouts = {
        1: [(960, 555)],
        2: [(680, 555), (1240, 555)],
        3: [(580, 600), (960, 440), (1340, 600)],
        4: [(650, 430), (1270, 430), (650, 700), (1270, 700)],
    }
    return layouts[count]


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(4, t); draw = ImageDraw.Draw(frame, "RGBA")
        base.panel(draw, (185, 145, 1735, 935), radius=55, width=9)
        base.centered(draw, (960, 285), spec["theme"], base.F62, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 410), "ANIMAL COUNTING PARADE", base.F78, (224, 74, 67, 255), 2)
        for index in range(1, 5):
            x = 500 + (index - 1) * 305
            draw.ellipse((x - 78, 625, x + 78, 781), fill=(255, 247, 220, 255), outline=(44, 151, 103, 255), width=8)
            draw.text((x, 703), str(index), font=base.F78, fill=(29, 76, 106, 255), anchor="mm")
        return frame.convert("RGB")
    if event["kind"] == "outro":
        return games.ending(t, animals)
    item = event["item"]; reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"] + 18, t).convert("RGBA"); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, f"{spec['theme']} COUNTING PARADE", f"COUNT {event['index']} OF {len(spec['clues'])}")
    base.panel(draw, (145, 145, 1775, 880), radius=48, width=8)
    heading = f"THE ANSWER IS {item['count']}!" if reveal else f"HOW MANY {item['animal'].upper()}{'' if item['count'] == 1 else 'S'}?"
    base.centered(draw, (960, 225), heading, base.F62, (46, 151, 84, 255) if reveal else (224, 74, 67, 255), 2)
    source = animals[item["animal"]]
    size = (430, 330) if item["count"] <= 2 else (330, 250)
    for index, (x, y) in enumerate(animal_positions(item["count"])):
        sprite = source.copy(); sprite.thumbnail(size, Image.Resampling.LANCZOS)
        bounce = round(-12 * abs(math.sin(t * 2.8 + index))) if event["kind"] == "think" else 0
        frame.alpha_composite(sprite, (x - sprite.width // 2, y - sprite.height // 2 + bounce))
        if reveal:
            draw.ellipse((x - 30, y + sprite.height // 2 - 10, x + 30, y + sprite.height // 2 + 50), fill=(44, 151, 103, 255))
            draw.text((x, y + sprite.height // 2 + 20), str(index + 1), font=base.F30, fill=(255, 255, 255, 255), anchor="mm")
    if reveal:
        lines = base.wrap_lines(draw, item["reveal"], base.F30, 1400)
        y = 825 - (len(lines) - 1) * 20
        for line in lines:
            base.centered(draw, (960, y), line, base.F30, (29, 76, 106, 255)); y += 42
    elif event["kind"] == "think":
        base.centered(draw, (960, 830), "COUNT ONCE — THEN SHOW THE NUMBER WITH YOUR FINGERS!", base.F30, (29, 76, 106, 255))
    return frame.convert("RGB")


def write_metadata(spec: dict, output: Path, total: float) -> None:
    title = f"{spec['theme'].title()} Animal Counting Parade | Count 1 to 4 for Kids"
    doc = {"id": spec["id"], "title": title[:100], "description": f"Join four playful {spec['theme'].lower()} counting groups. Look carefully, count each animal once, show the number with your fingers, and discover a fact after every answer.\n\nA gentle Tiny Tales activity supporting one-to-one counting, numeral recognition, listening, attention, and animal vocabulary for children ages 3 to 7.", "tags": ["counting for kids", "count 1 to 4", "animal counting", "preschool math", "numbers for kids", "Tiny Tales", f"{spec['theme'].lower()} animals"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(output), "duration_seconds": total, "new_image_generation_calls": 0}
    META_DIR.mkdir(parents=True, exist_ok=True)
    (META_DIR / f"{spec['id']}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True); shared.frame_for = frame_for
    for spec in EPISODES:
        output = OUTPUT_DIR / f"{spec['id']}.mp4"; work = WORK_ROOT / spec["id"]; work.mkdir(parents=True, exist_ok=True)
        report = work / "quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):
            print(f"Preserving completed output: {output}", flush=True); continue
        animals = games.extract_grid(spec["sheet"], spec["names"])
        lines = asyncio.run(make_voices(work, spec)); events, tracks, total = shared.make_timeline(work, spec, lines)
        shared.render(work, output, total, events, tracks, spec, animals); shared.validate(work, output, total, events, spec, animals)
        report_doc = json.loads(report.read_text(encoding="utf-8")); report_doc["format"] = "animal-counting-parade"; report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8")
        write_metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__":
    main()
