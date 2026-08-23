"""Render three local-only Tiny Tales Move Like an Animal activity adventures."""

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
        "id": "ocean-move-like-an-animal-01", "theme": "OCEAN",
        "sheet": AUTOMATION / "production-assets" / "ocean-animals-sheet.png",
        "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "clues": [
            {"animal": "dolphin", "action": "GLIDE", "motion": "glide", "question": "Stand tall and glide your arms smoothly like a dolphin moving through water. Ready to glide?", "reveal": "Wonderful gliding! A dolphin's streamlined body helps it move efficiently through water."},
            {"animal": "sea turtle", "action": "PADDLE", "motion": "paddle", "question": "Stretch your arms wide and paddle slowly like a sea turtle. Can you make four strong paddles?", "reveal": "Powerful paddling! Sea turtles use strong front flippers to travel through the ocean."},
            {"animal": "octopus", "action": "WIGGLE", "motion": "wiggle", "question": "Wiggle your arms gently like an octopus exploring a reef. How many wiggly arms can you imagine?", "reveal": "Excellent wiggling! An octopus has eight flexible arms lined with suckers."},
            {"animal": "crab", "action": "SIDE-STEP", "motion": "side", "question": "Take careful steps to the side like a crab. Keep your space safe and try four side-steps!", "reveal": "Super side-stepping! A crab's jointed legs make sideways movement especially easy."},
        ],
    },
    {
        "id": "farm-move-like-an-animal-01", "theme": "FARM",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png",
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "clues": [
            {"animal": "horse", "action": "TROT", "motion": "bounce", "question": "Lift your knees gently and trot in place like a horse. Can you make a steady clip-clop rhythm?", "reveal": "Terrific trotting! A trot is a two-beat gait that horses can use to travel steadily."},
            {"animal": "chicken", "action": "PECK", "motion": "peck", "question": "Keep your feet still and bob your head carefully like a chicken pecking for food. Ready?", "reveal": "Perfect pecking! Chickens use their beaks to pick up seeds, insects, and other food."},
            {"animal": "pig", "action": "SNIFF", "motion": "wiggle", "question": "Wiggle your nose and sniff the air like a curious pig. What pretend smell can you discover?", "reveal": "Super sniffing! Pigs have an excellent sense of smell and use their snouts to explore."},
            {"animal": "goat", "action": "BALANCE", "motion": "balance", "question": "Hold your arms out and balance safely like a goat on a rocky path. Can you stay steady?", "reveal": "Brilliant balance! A goat's split hooves help it grip uneven and rocky ground."},
        ],
    },
    {
        "id": "friendly-animal-movement-01", "theme": "FRIENDLY ANIMAL",
        "sheet": AUTOMATION / "production-assets" / "snack-suspects-sheet.png",
        "names": ["rabbit", "panda", "monkey", "mouse", "giraffe", "squirrel"],
        "clues": [
            {"animal": "rabbit", "action": "HOP", "motion": "bounce", "question": "Bend your knees a little and make gentle hops like a rabbit. Keep your landing soft and safe!", "reveal": "Happy hopping! Rabbits use powerful back legs to spring forward quickly."},
            {"animal": "monkey", "action": "REACH", "motion": "swing", "question": "Reach one arm, then the other, like a monkey moving between branches. How far can you reach?", "reveal": "Amazing reaching! Many monkeys use long arms and grasping hands to move through trees."},
            {"animal": "giraffe", "action": "STRETCH", "motion": "stretch", "question": "Stretch gently upward like a tall giraffe reaching for leaves. Make your body long without straining.", "reveal": "Lovely stretching! A giraffe's long neck helps it browse leaves high in trees."},
            {"animal": "squirrel", "action": "BALANCE", "motion": "balance", "question": "Hold your arms out and balance like a squirrel moving along a branch. Stay steady in your own safe space!", "reveal": "Wonderful balance! A squirrel uses its long fluffy tail to help balance while climbing and jumping."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    lines = [("intro", f"Make a little safe space and join our {spec['theme'].lower()} movement adventure! Watch each friend, listen to the action, and move in a way that feels comfortable for you.")]
    for index, item in enumerate(spec["clues"], 1):
        lines.append((f"q{index}", f"Our next movement is {item['action'].lower()}. {item['question']}"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "Movement mission complete! You glided, balanced, stretched, and explored like amazing animal friends. Take a calm breath, and we will see you next time!"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def motion_offset(kind: str, t: float) -> tuple[int, int, float]:
    wave = math.sin(t * 3.2)
    if kind in ("bounce", "peck"):
        return 0, round(-28 * abs(wave)), 1.0
    if kind in ("glide", "side", "swing"):
        return round(80 * wave), round(-12 * abs(wave)), 1.0
    if kind in ("wiggle", "paddle"):
        return round(28 * wave), round(18 * math.cos(t * 3.2)), 1.0
    if kind == "stretch":
        return 0, round(-18 * abs(wave)), 1.0 + 0.045 * abs(wave)
    return round(10 * wave), 0, 1.0


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(3, t); draw = ImageDraw.Draw(frame, "RGBA")
        base.panel(draw, (185, 145, 1735, 935), radius=55, width=9)
        base.centered(draw, (960, 300), spec["theme"], base.F62, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 430), "MOVE LIKE AN ANIMAL", base.F78, (224, 74, 67, 255), 2)
        base.centered(draw, (960, 610), "WATCH  •  MOVE  •  DISCOVER", base.F38, (44, 151, 103, 255))
        base.centered(draw, (960, 760), "MAKE A SAFE SPACE AROUND YOU", base.F30, (29, 76, 106, 255))
        return frame.convert("RGB")
    if event["kind"] == "outro":
        return games.ending(t, animals)
    item = event["item"]; reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"] + 14, t).convert("RGBA"); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, f"{spec['theme']} MOVEMENT", f"MOVE {event['index']} OF {len(spec['clues'])}")
    base.panel(draw, (170, 150, 1750, 900), radius=48, width=8)
    base.centered(draw, (960, 245), item["action"], base.F78, (46, 151, 84, 255) if reveal else (224, 74, 67, 255), 2)
    sprite = animals[item["animal"]].copy()
    dx, dy, scale = motion_offset(item["motion"], t if event["kind"] == "think" else 0)
    target = (round(620 * scale), round(470 * scale)); sprite.thumbnail(target, Image.Resampling.LANCZOS)
    frame.alpha_composite(sprite, (960 - sprite.width // 2 + dx, 560 - sprite.height // 2 + dy))
    if reveal:
        lines = base.wrap_lines(draw, item["reveal"], base.F38, 1350)
        y = 820 - (len(lines) - 1) * 25
        for line in lines:
            base.centered(draw, (960, y), line, base.F38, (29, 76, 106, 255)); y += 50
    elif event["kind"] == "think":
        base.centered(draw, (960, 825), "YOUR TURN — KEEP MOVING FOR SIX SECONDS!", base.F38, (29, 76, 106, 255))
        for index in range(6):
            fill = (44, 151, 103, 255) if index <= int((t - event["start"]) % 6) else (225, 231, 226, 255)
            draw.ellipse((690 + index * 95, 870, 740 + index * 95, 920), fill=fill, outline=(29, 76, 106, 255), width=3)
    else:
        lines = base.wrap_lines(draw, item["question"], base.F38, 1400)
        y = 785 - (len(lines) - 1) * 24
        for line in lines:
            base.centered(draw, (960, y), line, base.F38, (29, 76, 106, 255)); y += 50
    return frame.convert("RGB")


def write_metadata(spec: dict, output: Path, total: float) -> None:
    title = f"{spec['theme'].title()} Move Like an Animal | Movement Adventure for Kids"
    doc = {"id": spec["id"], "title": title[:100], "description": f"Make a safe space and join four playful {spec['theme'].lower()} movement missions. Copy each animal's movement for six seconds, then discover how that motion helps the animal.\n\nA gentle Tiny Tales activity supporting listening, body awareness, animal vocabulary, coordination, and active play for children ages 3 to 7. Children should move only in ways that feel comfortable and safe.", "tags": ["movement for kids", "animal movements", "active kids video", "preschool activity", "brain break", "Tiny Tales", f"{spec['theme'].lower()} animals"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(output), "duration_seconds": total, "new_image_generation_calls": 0}
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
        report_doc = json.loads(report.read_text(encoding="utf-8")); report_doc["format"] = "move-like-an-animal"; report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8")
        write_metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__":
    main()
