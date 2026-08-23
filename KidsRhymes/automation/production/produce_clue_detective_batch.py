"""Render three local-only Tiny Tales Animal Clue Detective adventures."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import subprocess

import edge_tts
from PIL import Image, ImageDraw

import produce_snack_video as base
import produce_animal_games as games


AUTOMATION = base.AUTOMATION
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
META_DIR = AUTOMATION.parent / "metadata"

EPISODES = [
    {
        "id": "jungle-animal-clue-detectives-01",
        "theme": "JUNGLE",
        "sheet": AUTOMATION / "production-assets" / "jungle-animals-sheet.png",
        "names": ["lion", "tiger", "elephant", "zebra", "hippopotamus", "crocodile"],
        "clues": [
            {"answer": "zebra", "question": "Who wears black-and-white stripes, and has a different pattern from every other member of its family?", "choices": ["tiger", "zebra", "lion"], "reveal": "The zebra! Every zebra has its own stripe pattern, like a fingerprint."},
            {"answer": "elephant", "question": "Who uses a long trunk to smell, drink, breathe, and pick things up?", "choices": ["elephant", "crocodile", "hippopotamus"], "reveal": "The elephant! A trunk is a nose, a drinking helper, and a powerful tool."},
            {"answer": "crocodile", "question": "Who has a long armoured body and can replace many teeth during its life?", "choices": ["lion", "crocodile", "tiger"], "reveal": "The crocodile! New teeth can replace older teeth again and again."},
            {"answer": "tiger", "question": "Who is a giant cat with orange fur and dark stripes?", "choices": ["zebra", "lion", "tiger"], "reveal": "The tiger! No two tigers have exactly the same stripe pattern."},
        ],
    },
    {
        "id": "farm-animal-clue-detectives-01",
        "theme": "FARM",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png",
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "clues": [
            {"answer": "sheep", "question": "Who grows a warm woolly coat that people can carefully shear?", "choices": ["goat", "sheep", "cow"], "reveal": "The sheep! Wool helps a sheep stay warm in cool weather."},
            {"answer": "pig", "question": "Who uses a strong sensitive snout to explore the ground and search for food?", "choices": ["pig", "horse", "chicken"], "reveal": "The pig! A pig's excellent sense of smell helps it investigate its surroundings."},
            {"answer": "chicken", "question": "Who has feathers, lays eggs, and communicates with many different calls?", "choices": ["cow", "chicken", "goat"], "reveal": "The chicken! Chickens use different sounds to warn, call, and communicate."},
            {"answer": "horse", "question": "Who can rest while standing and can also lie down for deeper sleep?", "choices": ["sheep", "pig", "horse"], "reveal": "The horse! Strong leg structures help a horse relax while standing."},
        ],
    },
    {
        "id": "colourful-bird-clue-detectives-01",
        "theme": "COLOURFUL BIRD",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png",
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "clues": [
            {"answer": "toucan", "question": "Who has an enormous colourful bill that helps reach fruit on small branches?", "choices": ["parrot", "toucan", "owl"], "reveal": "The toucan! Its large bill is surprisingly light because it contains many air spaces."},
            {"answer": "penguin", "question": "Who is a bird that uses its wings like flippers to fly through water?", "choices": ["penguin", "flamingo", "peacock"], "reveal": "The penguin! Penguins are powerful swimmers even though they do not fly through the air."},
            {"answer": "flamingo", "question": "Who gets its famous pink colour from pigments found in its food?", "choices": ["owl", "flamingo", "parrot"], "reveal": "The flamingo! Its food helps colour its feathers pink."},
            {"answer": "peacock", "question": "Who can fan long colourful tail feathers into a huge sparkling display?", "choices": ["toucan", "penguin", "peacock"], "reveal": "The peacock! The grand fan is made from long feathers growing above its shorter tail."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    theme = spec["theme"].lower()
    lines = [("intro", f"Welcome, Tiny Tales detectives! We have a {theme} mystery mission. Listen to each clue, choose a friend, and reveal the answer!")]
    for index, item in enumerate(spec["clues"], 1):
        options = ", ".join(item["choices"][:-1]) + f", or {item['choices'][-1]}"
        lines.append((f"q{index}", f"Here is your next clue. {item['question']} Is it {options}?"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "Mystery solved! You listened, looked closely, and discovered amazing animal clues. See you on our next Tiny Tales mission!"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def make_timeline(work: Path, spec: dict, lines: list[tuple[str, str]]) -> tuple[list[dict], list[tuple[str, float]], float]:
    lengths = {key: base.duration(voice_path(work, key)) for key, _ in lines}
    events: list[dict] = []
    tracks: list[tuple[str, float]] = []
    cursor = 0.3

    def add(kind: str, length: float, **data: object) -> dict:
        nonlocal cursor
        event = {"kind": kind, "start": cursor, "end": cursor + length, **data}
        events.append(event)
        cursor = event["end"]
        return event

    event = add("intro", max(7.0, lengths["intro"] + 0.8)); tracks.append(("intro", event["start"] + 0.1))
    for index, item in enumerate(spec["clues"], 1):
        event = add("question", lengths[f"q{index}"] + 0.4, index=index, item=item); tracks.append((f"q{index}", event["start"] + 0.1))
        add("think", 6.0, index=index, item=item)
        event = add("reveal", lengths[f"a{index}"] + 1.0, index=index, item=item); tracks.append((f"a{index}", event["start"] + 0.15))
    event = add("outro", max(8.0, lengths["outro"] + 0.8)); tracks.append(("outro", event["start"] + 0.1))
    return events, tracks, math.ceil(cursor * base.ART_FPS) / base.ART_FPS


def frame_for(event: dict, t: float, spec: dict, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(0, t); draw = ImageDraw.Draw(frame, "RGBA")
        base.panel(draw, (190, 155, 1730, 925), radius=55, width=9)
        base.centered(draw, (960, 315), f"{spec['theme']} ANIMAL", base.F78, (224, 74, 67, 255), 2)
        base.centered(draw, (960, 435), "CLUE DETECTIVES", base.F78, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 650), "LISTEN  •  CHOOSE  •  DISCOVER", base.F38, (44, 151, 103, 255))
        return frame.convert("RGB")
    if event["kind"] == "outro":
        return games.ending(t, animals)
    item = event["item"]
    reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"] + len(spec["theme"]), t); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, f"{spec['theme']} CLUE DETECTIVES", f"MYSTERY {event['index']} OF {len(spec['clues'])}")
    base.panel(draw, (155, 155, 1765, 430), radius=38, width=7)
    wording = item["reveal"] if reveal else item["question"]
    lines = base.wrap_lines(draw, wording, base.F48, 1440)
    y = 210 if len(lines) > 1 else 255
    for line in lines:
        base.centered(draw, (960, y), line, base.F48, (46, 151, 84, 255) if reveal else (29, 76, 106, 255)); y += 62
    games.animal_cards(frame, animals, item["choices"], item["answer"], reveal, top=510)
    if event["kind"] == "think":
        base.centered(draw, (960, 470), "YOUR TURN — WHICH ANIMAL FITS THE CLUE?", base.F30, (224, 74, 67, 255))
    return frame.convert("RGB")


def render(work: Path, output: Path, total: float, events: list[dict], tracks: list[tuple[str, float]], spec: dict, animals: dict[str, Image.Image]) -> None:
    silent = work / "silent.mp4"
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{base.W}x{base.H}", "-r", str(base.ART_FPS), "-i", "-", "-an", "-vf", f"fps={base.VIDEO_FPS}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for number in range(math.ceil(total * base.ART_FPS)):
        event = next((e for e in events if e["start"] <= number / base.ART_FPS < e["end"]), events[-1])
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
        inputs += ["-i", str(voice_path(work, key))]
        delay = round(start * 1000)
        filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.22[v{stream}]")
        labels.append(f"[v{stream}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(output)], check=True)


def validate(work: Path, output: Path, total: float, events: list[dict], spec: dict, animals: dict[str, Image.Image]) -> None:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels", "-of", "json", str(output)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    checks = {
        "size": output.stat().st_size > 1_000_000,
        "duration": abs(float(probe["format"]["duration"]) - total) < 0.25,
        "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H,
        "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
    }
    report = {"format": "animal-clue-detectives", "output": str(output), "duration_seconds": float(probe["format"]["duration"]), "checks": checks, "passed": all(checks.values()), "upload_authorized": False}
    (work / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    samples = [events[0]] + [e for e in events if e["kind"] in ("think", "reveal")] + [events[-1]]
    contact = Image.new("RGB", (960, math.ceil(len(samples) / 4) * 135), "white")
    for index, event in enumerate(samples):
        sample = frame_for(event, event["start"] + min(1, (event["end"] - event["start"]) / 2), spec, animals).resize((240, 135), Image.Resampling.LANCZOS)
        contact.paste(sample, ((index % 4) * 240, (index // 4) * 135))
    contact.save(work / "quality-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(f"Quality gate failed: {report}")


def write_metadata(spec: dict, output: Path, total: float) -> None:
    title = f"{spec['theme'].title()} Animal Clue Detectives | Guessing Adventure for Kids"
    metadata = {
        "id": spec["id"],
        "title": title[:100],
        "description": f"Join the Tiny Tales detectives for four {spec['theme'].lower()} animal mysteries. Listen to each clue, choose from three friendly animals, and discover a memorable fact after every answer.\n\nA playful learning adventure supporting listening, animal vocabulary, observation, and early reasoning for children ages 3 to 7.",
        "tags": ["animal clues", "guess the animal", "kids learning", "preschool game", "animal facts", "Tiny Tales", f"{spec['theme'].lower()} animals"],
        "category_id": "27",
        "made_for_kids": True,
        "privacy": "private",
        "upload_authorized": False,
        "output": str(output),
        "duration_seconds": total,
        "new_image_generation_calls": 0,
    }
    META_DIR.mkdir(parents=True, exist_ok=True)
    (META_DIR / f"{spec['id']}.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for spec in EPISODES:
        output = OUTPUT_DIR / f"{spec['id']}.mp4"
        work = WORK_ROOT / spec["id"]
        work.mkdir(parents=True, exist_ok=True)
        report = work / "quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):
            print(f"Preserving completed output: {output}", flush=True)
            continue
        animals = games.extract_grid(spec["sheet"], spec["names"])
        lines = asyncio.run(make_voices(work, spec))
        events, tracks, total = make_timeline(work, spec, lines)
        render(work, output, total, events, tracks, spec, animals)
        validate(work, output, total, events, spec, animals)
        write_metadata(spec, output, total)
        print(json.dumps({"id": spec["id"], "status": "completed", "duration_seconds": total}), flush=True)


if __name__ == "__main__":
    main()
