"""Render three local-only Tiny Tales Amazing Animal Tools Lab adventures."""

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
        "id": "ocean-amazing-animal-tools-01", "theme": "OCEAN",
        "sheet": AUTOMATION / "production-assets" / "ocean-animals-sheet.png",
        "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "clues": [
            {"tool": "PROTECTIVE SHELL", "answer": "sea turtle", "choices": ["dolphin", "sea turtle", "octopus"], "question": "Which ocean friend carries this strong protective covering on its back?", "reveal": "The sea turtle! Its shell is part of its skeleton and protects its body."},
            {"tool": "EIGHT FLEXIBLE ARMS", "answer": "octopus", "choices": ["crab", "octopus", "whale"], "question": "Which ocean friend uses eight flexible arms with rows of suckers?", "reveal": "The octopus! Its arms can explore, hold objects, and taste what they touch."},
            {"tool": "CURLING TAIL", "answer": "seahorse", "choices": ["seahorse", "dolphin", "crab"], "question": "Which ocean friend curls this tail around seagrass to hold on?", "reveal": "The seahorse! Its grasping tail helps it stay anchored among underwater plants."},
            {"tool": "BLOWHOLE", "answer": "whale", "choices": ["sea turtle", "whale", "octopus"], "question": "Which ocean friend breathes air through this opening on top of its head?", "reveal": "The whale! A blowhole lets a whale breathe quickly when it reaches the surface."},
        ],
    },
    {
        "id": "farm-amazing-animal-tools-01", "theme": "FARM",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png",
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "clues": [
            {"tool": "WARM WOOL", "answer": "sheep", "choices": ["pig", "sheep", "horse"], "question": "Which farm friend grows this thick covering that helps keep its body warm?", "reveal": "The sheep! Its wool traps air and provides insulation in cool weather."},
            {"tool": "SENSITIVE SNOUT", "answer": "pig", "choices": ["cow", "goat", "pig"], "question": "Which farm friend uses this strong nose to smell and explore the ground?", "reveal": "The pig! Its snout is sensitive and supported by strong muscles and bone."},
            {"tool": "WIDE-VIEW PUPILS", "answer": "goat", "choices": ["goat", "chicken", "horse"], "question": "Which farm friend has horizontal pupils that help it see a wide area?", "reveal": "The goat! Horizontal pupils give grazing animals a broad view of their surroundings."},
            {"tool": "FEATHER COAT", "answer": "chicken", "choices": ["sheep", "chicken", "cow"], "question": "Which farm friend wears overlapping feathers that help cover and protect its body?", "reveal": "The chicken! Feathers help with warmth, protection, and communication displays."},
        ],
    },
    {
        "id": "bird-amazing-animal-tools-01", "theme": "BIRD",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png",
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "clues": [
            {"tool": "LARGE LIGHT BILL", "answer": "toucan", "choices": ["parrot", "toucan", "owl"], "question": "Which bird uses this enormous but surprisingly light bill to reach food?", "reveal": "The toucan! Its bill contains a lightweight network with many air spaces."},
            {"tool": "SWIMMING FLIPPERS", "answer": "penguin", "choices": ["penguin", "flamingo", "peacock"], "question": "Which bird has wings shaped like flippers for powerful underwater swimming?", "reveal": "The penguin! Stiff flipper-like wings help it steer and speed through water."},
            {"tool": "GIANT FEATHER FAN", "answer": "peacock", "choices": ["toucan", "owl", "peacock"], "question": "Which bird can spread long colourful feathers into this enormous display?", "reveal": "The peacock! Long upper-tail feathers form the famous fan-shaped display."},
            {"tool": "FORWARD-FACING EYES", "answer": "owl", "choices": ["flamingo", "owl", "parrot"], "question": "Which bird has large forward-facing eyes that help judge distance?", "reveal": "The owl! Forward-facing eyes provide overlapping views that support depth perception."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    lines = [("intro", f"Welcome to the {spec['theme'].lower()} Amazing Animal Tools Lab! Examine each special body feature, choose its animal owner, and discover how the tool works.")]
    for index, item in enumerate(spec["clues"], 1):
        options = ", ".join(item["choices"][:-1]) + f", or {item['choices'][-1]}"
        lines.append((f"q{index}", f"Tool number {index}: {item['tool'].lower()}. {item['question']} Is it {options}?"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "The Animal Tools Lab is complete! You examined shells, feathers, tails, eyes, and more. Every animal body has fascinating ways to survive and move!"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def draw_tool_icon(draw: ImageDraw.ImageDraw, tool: str, center: tuple[int, int], t: float) -> None:
    x, y = center; accent = (224, 74, 67, 255); blue = (49, 132, 174, 255)
    if "SHELL" in tool:
        draw.ellipse((x - 170, y - 120, x + 170, y + 120), fill=(238, 187, 96, 255), outline=accent, width=10)
        for radius in (45, 85, 125): draw.arc((x - radius, y - radius, x + radius, y + radius), 15, 340, fill=accent, width=7)
    elif "ARMS" in tool or "FAN" in tool or "FEATHER" in tool:
        for index in range(8):
            angle = index * math.pi / 7 - math.pi / 2
            x2 = x + round(math.cos(angle) * 180); y2 = y + round(math.sin(angle) * 180)
            draw.line((x, y, x2, y2), fill=(91 + index * 15, 105, 190 - index * 10, 255), width=30)
            draw.ellipse((x2 - 24, y2 - 24, x2 + 24, y2 + 24), fill=accent)
    elif "TAIL" in tool:
        points = []
        for step in range(80):
            angle = step * 0.23; radius = 3.0 * step
            points.append((x + round(math.cos(angle) * radius), y + round(math.sin(angle) * radius)))
        draw.line(points, fill=accent, width=18, joint="curve")
    elif "BLOWHOLE" in tool:
        draw.ellipse((x - 85, y + 40, x + 85, y + 120), fill=(70, 92, 105, 255))
        for offset in (-70, 0, 70): draw.arc((x - 110 + offset, y - 150, x + 110 + offset, y + 70), 205, 335, fill=blue, width=15)
    elif "WOOL" in tool:
        for dx, dy in ((-100, 10), (-45, -55), (30, -65), (100, 0), (45, 65), (-45, 70)):
            draw.ellipse((x + dx - 70, y + dy - 70, x + dx + 70, y + dy + 70), fill=(250, 247, 231, 255), outline=(170, 150, 125, 255), width=6)
    elif "SNOUT" in tool or "BILL" in tool:
        draw.ellipse((x - 175, y - 90, x + 175, y + 90), fill=(241, 151, 113, 255), outline=accent, width=9)
        draw.ellipse((x + 60, y - 24, x + 95, y + 24), fill=(80, 60, 55, 255))
    elif "EYES" in tool or "PUPILS" in tool:
        for dx in (-90, 90):
            draw.ellipse((x + dx - 75, y - 90, x + dx + 75, y + 90), fill=(252, 245, 205, 255), outline=blue, width=8)
            draw.ellipse((x + dx - 20, y - 65, x + dx + 20, y + 65), fill=(35, 45, 55, 255))
    else:
        draw.ellipse((x - 150, y - 150, x + 150, y + 150), fill=(210, 235, 245, 255), outline=blue, width=10)


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(0, t); draw = ImageDraw.Draw(frame, "RGBA")
        base.panel(draw, (185, 145, 1735, 935), radius=55, width=9)
        base.centered(draw, (960, 290), spec["theme"], base.F62, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 415), "AMAZING ANIMAL TOOLS", base.F78, (224, 74, 67, 255), 2)
        base.centered(draw, (960, 560), "LOOK  •  TEST  •  DISCOVER", base.F38, (44, 151, 103, 255))
        draw.rounded_rectangle((570, 675, 1350, 805), radius=45, fill=(220, 241, 248, 255), outline=(49, 132, 174, 255), width=8)
        base.centered(draw, (960, 740), "BODY FEATURE LAB", base.F48, (29, 76, 106, 255))
        return frame.convert("RGB")
    if event["kind"] == "outro": return games.ending(t, animals)
    item = event["item"]; reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"] + 22, t).convert("RGBA"); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, f"{spec['theme']} ANIMAL TOOLS LAB", f"TOOL {event['index']} OF {len(spec['clues'])}")
    base.panel(draw, (130, 145, 780, 865), radius=42, width=8); base.panel(draw, (830, 145, 1790, 865), radius=42, width=8)
    base.centered(draw, (455, 225), item["tool"], base.F38, (224, 74, 67, 255)); draw_tool_icon(draw, item["tool"], (455, 520), t)
    if reveal:
        base.centered(draw, (1310, 220), f"IT BELONGS TO THE {item['answer'].upper()}!", base.F38, (46, 151, 84, 255))
        sprite = animals[item["answer"]].copy(); sprite.thumbnail((480, 370), Image.Resampling.LANCZOS); frame.alpha_composite(sprite, (1310 - sprite.width // 2, 480 - sprite.height // 2))
        lines = base.wrap_lines(draw, item["reveal"], base.F30, 800); y = 745
        for line in lines: base.centered(draw, (1310, y), line, base.F30, (29, 76, 106, 255)); y += 42
    else:
        base.centered(draw, (1310, 220), "WHO USES THIS TOOL?", base.F38, (29, 76, 106, 255))
        for index, name in enumerate(item["choices"]):
            x = 1010 + index * 300; sprite = animals[name].copy(); sprite.thumbnail((230, 220), Image.Resampling.LANCZOS)
            draw.rounded_rectangle((x - 130, 340, x + 130, 690), radius=34, fill=(255, 255, 255, 235), outline=(49, 132, 174, 255), width=6)
            frame.alpha_composite(sprite, (x - sprite.width // 2, 485 - sprite.height // 2)); draw.text((x, 630), name.upper(), font=base.F30, fill=(29, 76, 106, 255), anchor="mm")
        if event["kind"] == "think": base.centered(draw, (1310, 795), "INSPECT — THEN POINT TO THE OWNER!", base.F30, (224, 74, 67, 255))
    return frame.convert("RGB")


def write_metadata(spec: dict, output: Path, total: float) -> None:
    title = f"{spec['theme'].title()} Amazing Animal Tools | Body Features for Kids"
    doc = {"id": spec["id"], "title": title[:100], "description": f"Enter the Tiny Tales Amazing Animal Tools Lab. Examine four special {spec['theme'].lower()} body features, choose each animal owner, and discover how shells, tails, feathers, eyes, and other tools work.\n\nAn interactive science adventure supporting observation, body-part vocabulary, animal knowledge, listening, and early reasoning for children ages 3 to 7.", "tags": ["animal body parts", "animal adaptations", "science for kids", "preschool learning", "animal facts", "Tiny Tales", f"{spec['theme'].lower()} animals"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(output), "duration_seconds": total, "new_image_generation_calls": 0}
    META_DIR.mkdir(parents=True, exist_ok=True); (META_DIR / f"{spec['id']}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True); shared.frame_for = frame_for
    for spec in EPISODES:
        output = OUTPUT_DIR / f"{spec['id']}.mp4"; work = WORK_ROOT / spec["id"]; work.mkdir(parents=True, exist_ok=True); report = work / "quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"): print(f"Preserving completed output: {output}", flush=True); continue
        animals = games.extract_grid(spec["sheet"], spec["names"]); lines = asyncio.run(make_voices(work, spec)); events, tracks, total = shared.make_timeline(work, spec, lines)
        shared.render(work, output, total, events, tracks, spec, animals); shared.validate(work, output, total, events, spec, animals)
        report_doc = json.loads(report.read_text(encoding="utf-8")); report_doc["format"] = "amazing-animal-tools-lab"; report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8"); write_metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__": main()
