"""Render three local-only Tiny Tales Baby Animal Family Album adventures."""

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
        "id": "farm-baby-animal-family-album-01", "theme": "FARM",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png",
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "clues": [
            {"animal": "cow", "baby": "CALF", "choices": ["CALF", "CUB", "CHICK"], "question": "What do we call a young cow?", "reveal": "A young cow is a calf. A newborn calf can stand and begin walking surprisingly soon."},
            {"animal": "sheep", "baby": "LAMB", "choices": ["FOAL", "LAMB", "PIGLET"], "question": "What do we call a young sheep?", "reveal": "A young sheep is a lamb. Lambs recognise their mothers by sound and smell."},
            {"animal": "horse", "baby": "FOAL", "choices": ["KID", "CALF", "FOAL"], "question": "What do we call a young horse?", "reveal": "A young horse is a foal. Foals have long legs that help them keep up with the herd."},
            {"animal": "pig", "baby": "PIGLET", "choices": ["PIGLET", "OWLET", "LAMB"], "question": "What do we call a young pig?", "reveal": "A young pig is a piglet. Piglets use squeaks and grunts to communicate."},
        ],
    },
    {
        "id": "wild-baby-animal-family-album-01", "theme": "WILD ANIMAL",
        "sheet": AUTOMATION / "production-assets" / "jungle-animals-sheet.png",
        "names": ["lion", "tiger", "elephant", "zebra", "hippopotamus", "crocodile"],
        "clues": [
            {"animal": "lion", "baby": "CUB", "choices": ["FOAL", "CUB", "CALF"], "question": "What do we call a young lion?", "reveal": "A young lion is a cub. Lion cubs learn through play with other members of their pride."},
            {"animal": "elephant", "baby": "CALF", "choices": ["CALF", "HATCHLING", "LAMB"], "question": "What do we call a young elephant?", "reveal": "A young elephant is a calf. The herd helps protect and guide elephant calves."},
            {"animal": "zebra", "baby": "FOAL", "choices": ["CUB", "FOAL", "PIGLET"], "question": "What do we call a young zebra?", "reveal": "A young zebra is a foal. A mother zebra and her foal learn to recognise each other's stripe patterns."},
            {"animal": "crocodile", "baby": "HATCHLING", "choices": ["HATCHLING", "OWLET", "KID"], "question": "What do we call a young crocodile that has just left its egg?", "reveal": "A young crocodile is a hatchling. Hatchlings make calls that can alert their mother."},
        ],
    },
    {
        "id": "bird-baby-family-album-01", "theme": "BIRD",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png",
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "clues": [
            {"animal": "owl", "baby": "OWLET", "choices": ["OWLET", "PEACHICK", "FOAL"], "question": "What special word can we use for a young owl?", "reveal": "A young owl is an owlet. Owlets begin with soft down feathers before growing flight feathers."},
            {"animal": "peacock", "baby": "PEACHICK", "choices": ["CALF", "CHICK", "PEACHICK"], "question": "What special word can we use for a young peafowl?", "reveal": "A young peafowl is a peachick. The word peacock describes an adult male peafowl."},
            {"animal": "flamingo", "baby": "CHICK", "choices": ["CHICK", "CUB", "LAMB"], "question": "What do we call a young flamingo?", "reveal": "A young flamingo is a chick. Flamingo chicks begin with grey or white down, not bright pink feathers."},
            {"animal": "penguin", "baby": "CHICK", "choices": ["PIGLET", "OWLET", "CHICK"], "question": "What do we call a young penguin?", "reveal": "A young penguin is a chick. Soft down helps keep a penguin chick warm on land."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    lines = [("intro", f"Open the Tiny Tales {spec['theme'].lower()} Family Album! Meet four animal families, choose each baby's special name, and add the answer to our scrapbook.")]
    for index, item in enumerate(spec["clues"], 1):
        options = ", ".join(item["choices"][:-1]) + f", or {item['choices'][-1]}"
        lines.append((f"q{index}", f"Family page {index}. {item['question']} Is it {options}?"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "The family album is complete! You learned special names for animal babies and met four caring animal families. Which baby name will you remember?"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def album_page(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rotation: int = 0) -> None:
    draw.rounded_rectangle(box, radius=28, fill=(255, 252, 235, 255), outline=(181, 135, 78, 255), width=7)
    x1, y1, x2, y2 = box
    for y in range(y1 + 55, y2 - 30, 58):
        draw.line((x1 + 30, y, x2 - 30, y), fill=(226, 213, 180, 180), width=2)
    draw.line((x1 + 70, y1 + 20, x1 + 70, y2 - 20), fill=(224, 112, 105, 190), width=3)


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(2, t); draw = ImageDraw.Draw(frame, "RGBA")
        album_page(draw, (300, 130, 1620, 950)); draw.rounded_rectangle((905, 130, 1015, 950), radius=35, fill=(196, 145, 80, 255))
        base.centered(draw, (960, 300), spec["theme"], base.F62, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 445), "BABY ANIMAL", base.F78, (224, 74, 67, 255), 2)
        base.centered(draw, (960, 565), "FAMILY ALBUM", base.F78, (44, 151, 103, 255), 2)
        base.centered(draw, (960, 760), "MEET  •  NAME  •  DISCOVER", base.F38, (29, 76, 106, 255))
        return frame.convert("RGB")
    if event["kind"] == "outro": return games.ending(t, animals)
    item = event["item"]; reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"] + 30, t).convert("RGBA"); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, f"{spec['theme']} FAMILY ALBUM", f"PAGE {event['index']} OF {len(spec['clues'])}")
    album_page(draw, (120, 145, 1800, 900)); draw.rounded_rectangle((925, 145, 995, 900), radius=22, fill=(194, 143, 79, 255))
    base.centered(draw, (520, 220), f"ADULT {item['animal'].upper()}", base.F38, (29, 76, 106, 255))
    adult = animals[item["animal"]].copy(); adult.thumbnail((570, 480), Image.Resampling.LANCZOS); frame.alpha_composite(adult, (520 - adult.width // 2, 525 - adult.height // 2))
    base.centered(draw, (1390, 220), "BABY NAME", base.F38, (224, 74, 67, 255))
    baby = animals[item["animal"]].copy(); baby.thumbnail((300, 255), Image.Resampling.LANCZOS); frame.alpha_composite(baby, (1390 - baby.width // 2, 420 - baby.height // 2))
    if reveal:
        draw.rounded_rectangle((1090, 575, 1690, 700), radius=38, fill=(218, 244, 221, 255), outline=(44, 151, 103, 255), width=9)
        base.centered(draw, (1390, 638), item["baby"], base.F62, (46, 151, 84, 255), 2)
        lines = base.wrap_lines(draw, item["reveal"], base.F30, 710); y = 770
        for line in lines: base.centered(draw, (1390, y), line, base.F30, (29, 76, 106, 255)); y += 40
    else:
        for index, choice in enumerate(item["choices"]):
            y = 575 + index * 95
            draw.rounded_rectangle((1100, y, 1680, y + 72), radius=28, fill=(255, 255, 255, 235), outline=(49, 132, 174, 255), width=5)
            base.centered(draw, (1390, y + 36), choice, base.F38, (29, 76, 106, 255))
        if event["kind"] == "think": base.centered(draw, (960, 955), "POINT TO THE BABY'S SPECIAL NAME!", base.F30, (224, 74, 67, 255))
    return frame.convert("RGB")


def write_metadata(spec: dict, output: Path, total: float) -> None:
    title_theme = "Wild" if spec["theme"] == "WILD ANIMAL" else spec["theme"].title()
    title = f"{title_theme} Baby Animal Family Album | Learn Baby Names for Kids"
    doc = {"id": spec["id"], "title": title[:100], "description": f"Open a Tiny Tales {spec['theme'].lower()} family scrapbook. Meet four adult animals, choose each baby's special name, and learn a gentle family fact after every reveal.\n\nAn interactive vocabulary adventure supporting listening, animal-family knowledge, word learning, observation, and early reasoning for children ages 3 to 7.", "tags": ["baby animals", "animal families", "baby animal names", "preschool vocabulary", "animals for kids", "Tiny Tales", f"{spec['theme'].lower()} animals"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(output), "duration_seconds": total, "new_image_generation_calls": 0}
    META_DIR.mkdir(parents=True, exist_ok=True); (META_DIR / f"{spec['id']}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True); shared.frame_for = frame_for
    for spec in EPISODES:
        output = OUTPUT_DIR / f"{spec['id']}.mp4"; work = WORK_ROOT / spec["id"]; work.mkdir(parents=True, exist_ok=True); report = work / "quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {output}", flush=True); continue
        animals = games.extract_grid(spec["sheet"], spec["names"]); lines = asyncio.run(make_voices(work, spec)); events, tracks, total = shared.make_timeline(work, spec, lines)
        shared.render(work, output, total, events, tracks, spec, animals); shared.validate(work, output, total, events, spec, animals)
        report_doc = json.loads(report.read_text(encoding="utf-8")); report_doc["format"] = "baby-animal-family-album"; report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8"); write_metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__": main()
