"""Render an interactive, fact-checked Ocean Superpower Detective video."""

from __future__ import annotations

import argparse
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
ASSET = AUTOMATION / "production-assets" / "ocean-animals-sheet.png"
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
NAMES = ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"]
FACTS = [
    {"answer": "octopus", "question": "Which ocean animal has three hearts?", "choices": ["crab", "octopus", "dolphin"], "reveal": "The octopus! An octopus has three hearts and blue blood."},
    {"answer": "dolphin", "question": "Which animal can rest half of its brain while the other half stays awake?", "choices": ["dolphin", "sea turtle", "crab"], "reveal": "The dolphin! Keeping half its brain awake helps it remember to breathe."},
    {"answer": "seahorse", "question": "Which ocean dad carries developing babies in a special pouch?", "choices": ["whale", "octopus", "seahorse"], "reveal": "The seahorse! The father carries the developing babies in his pouch."},
    {"answer": "sea turtle", "question": "Which animal can sense Earth's magnetic field like a built-in compass?", "choices": ["sea turtle", "crab", "whale"], "reveal": "The sea turtle! Earth's magnetic field helps sea turtles navigate across the ocean."},
    {"answer": "whale", "question": "Which giant animal must surface to breathe through a blowhole?", "choices": ["octopus", "whale", "seahorse"], "reveal": "The whale! A whale is a mammal and breathes air through a blowhole."},
    {"answer": "crab", "question": "Which animal can look around using eyes on movable stalks?", "choices": ["dolphin", "crab", "sea turtle"], "reveal": "The crab! Its eye stalks help it look in different directions."},
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path) -> list[tuple[str, str]]:
    lines = [("intro", "Welcome, Ocean Superpower Detectives! Listen to each clue, choose an animal, and discover an amazing superpower.")]
    for index, item in enumerate(FACTS, 1):
        options = ", ".join(item["choices"][:-1]) + f", or {item['choices'][-1]}"
        lines.append((f"q{index}", f"Let's investigate the next mystery. {item['question']} Is it {options}?"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "Super detective work! Which ocean superpower surprised you most? See you on our next Tiny Tales mission!"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def timeline(work: Path, lines: list[tuple[str, str]]) -> tuple[list[dict], list[tuple[str, float]], float]:
    lengths = {key: base.duration(voice_path(work, key)) for key, _ in lines}
    events, tracks, cursor = [], [], 0.3
    def add(kind: str, length: float, **data: object) -> dict:
        nonlocal cursor
        event = {"kind": kind, "start": cursor, "end": cursor + length, **data}
        events.append(event); cursor = event["end"]
        return event
    event = add("intro", max(7.0, lengths["intro"] + 0.8)); tracks.append(("intro", event["start"] + 0.1))
    for index, item in enumerate(FACTS, 1):
        event = add("question", lengths[f"q{index}"] + 0.3, index=index, item=item); tracks.append((f"q{index}", event["start"] + 0.1))
        add("think", 6.0, index=index, item=item)
        event = add("reveal", lengths[f"a{index}"] + 1.0, index=index, item=item); tracks.append((f"a{index}", event["start"] + 0.15))
    event = add("outro", max(8.0, lengths["outro"] + 0.8)); tracks.append(("outro", event["start"] + 0.1))
    return events, tracks, math.ceil(cursor * base.ART_FPS) / base.ART_FPS


def frame_for(event: dict, t: float, animals: dict[str, Image.Image]) -> Image.Image:
    if event["kind"] == "intro":
        frame = base.gradient_background(0, t); draw = ImageDraw.Draw(frame, "RGBA")
        base.panel(draw, (210, 170, 1710, 910), radius=55, width=9)
        base.centered(draw, (960, 330), "OCEAN SUPERPOWER", base.F78, (224, 74, 67, 255), 2)
        base.centered(draw, (960, 445), "DETECTIVES", base.F78, (29, 76, 106, 255), 2)
        base.centered(draw, (960, 650), "LISTEN  •  GUESS  •  DISCOVER", base.F38, (44, 151, 103, 255))
        return frame.convert("RGB")
    if event["kind"] == "outro":
        return games.ending(t, animals)
    item = event["item"]; reveal = event["kind"] == "reveal"
    frame = base.gradient_background(event["index"], t); draw = ImageDraw.Draw(frame, "RGBA")
    base.header(frame, "OCEAN SUPERPOWER DETECTIVES", "SOLVE THE MYSTERY")
    base.panel(draw, (170, 165, 1750, 420), radius=38, width=7)
    lines = base.wrap_lines(draw, item["reveal"] if reveal else item["question"], base.F48, 1400)
    y = 245 if len(lines) == 1 else 215
    for line in lines:
        base.centered(draw, (960, y), line, base.F48, (46, 151, 84, 255) if reveal else (29, 76, 106, 255)); y += 64
    games.animal_cards(frame, animals, item["choices"], item["answer"], reveal, top=505)
    if event["kind"] == "think":
        base.centered(draw, (960, 465), "LOOK CLOSELY... WHAT DO YOU THINK?", base.F30, (224, 74, 67, 255))
    return frame.convert("RGB")


def render(work: Path, output: Path, total: float, events: list[dict], tracks: list[tuple[str, float]], animals: dict[str, Image.Image]) -> None:
    silent = work / "silent.mp4"
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{base.W}x{base.H}", "-r", str(base.ART_FPS), "-i", "-", "-an", "-vf", f"fps={base.VIDEO_FPS}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for number in range(math.ceil(total * base.ART_FPS)):
        event = next((e for e in events if e["start"] <= number / base.ART_FPS < e["end"]), events[-1])
        process.stdin.write(frame_for(event, number / base.ART_FPS, animals).tobytes())
        if number % (base.ART_FPS * 15) == 0: print(f"Rendered {number / base.ART_FPS:.0f}/{total:.0f}s", flush=True)
    process.stdin.close()
    if process.wait() != 0: raise RuntimeError("Video render failed")
    bed, sfx = base.make_audio_bed(work, total, events)
    inputs = ["-i", str(silent), "-i", str(bed), "-i", str(sfx)]; filters = ["[1:a]volume=.68[bed]", "[2:a]volume=1.0[sfx]"]; labels = ["[bed]", "[sfx]"]
    for stream, (key, start) in enumerate(tracks, 3):
        inputs += ["-i", str(voice_path(work, key))]; delay = round(start * 1000)
        filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.22[v{stream}]"); labels.append(f"[v{stream}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(output)], check=True)


def quality(work: Path, output: Path, total: float, events: list[dict], animals: dict[str, Image.Image]) -> None:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels", "-of", "json", str(output)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video"); audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    checks = {"size": output.stat().st_size > 1_000_000, "duration": abs(float(probe["format"]["duration"]) - total) < 0.25, "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H, "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2}
    report = {"format": "ocean-superpowers", "output": str(output), "duration_seconds": float(probe["format"]["duration"]), "checks": checks, "passed": all(checks.values())}
    (work / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    samples = [events[0]] + [e for e in events if e["kind"] in ("think", "reveal")] + [events[-1]]
    contact = Image.new("RGB", (960, math.ceil(len(samples) / 4) * 135), "white")
    for i, event in enumerate(samples):
        sample = frame_for(event, event["start"] + min(1, (event["end"] - event["start"]) / 2), animals).resize((240, 135), Image.Resampling.LANCZOS)
        contact.paste(sample, ((i % 4) * 240, (i // 4) * 135))
    contact.save(work / "quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--episode", type=int, default=1); args = parser.parse_args()
    if args.episode != 1: raise RuntimeError("Only curated episode 1 is currently approved")
    if not ASSET.exists(): raise FileNotFoundError(ASSET)
    output = OUTPUT_DIR / "ocean-animal-superpowers-01.mp4"; work = WORK_ROOT / "ocean-superpowers-episode-01"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    if output.exists(): print(f"Completed output already exists; preserving without regeneration: {output}"); return
    animals = games.extract_grid(ASSET, NAMES); lines = asyncio.run(make_voices(work)); events, tracks, total = timeline(work, lines)
    render(work, output, total, events, tracks, animals); quality(work, output, total, events, animals); print(output)


if __name__ == "__main__": main()
