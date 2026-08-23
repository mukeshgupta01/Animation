"""Produce one local-only representative redesign with a new cast and setting."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

from produce_authorized_batch import (
    FPS,
    VOICE,
    create_voice,
    media_duration,
    render_video,
    validate,
    word_boundaries,
    write_ass,
    write_srt,
)


PROJECT = Path(__file__).resolve().parents[1]
ASSET = PROJECT / "production-assets" / "kitchen-siblings-storyboard-01.png"
WORK = PROJECT / "production-work" / "redesign-01-kitchen-siblings-v1"
OUTPUT = PROJECT / "output" / "parenting-rewind-redesign-01-kitchen-siblings-v1.mp4"
META = PROJECT / "metadata" / "parenting-rewind-redesign-01-kitchen-siblings-v1.json"
TITLE = "When Both Kids Want the Same Job"
NARRATION = " ".join([
    "Both children want the mixing bowl, and dinner help turns into a tug-of-war.",
    "Choosing a winner immediately can leave one child feeling pushed aside and both children competing for your approval.",
    "Before reacting, pause for one breath so you can step in as a calm safety boundary, not another loud voice.",
    "Try this: I will not let you pull the bowl; Maya mixes until the timer rings, while Leo puts out the napkins; then you swap jobs.",
    "The goal is not forced harmony; make turns predictable, give each child a meaningful role, and praise the specific teamwork you see.",
])


def split_panels() -> list[Path]:
    target_dir = WORK / "panels"
    target_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(ASSET).convert("RGB")
    targets = []
    for index in range(6):
        target = target_dir / f"panel-{index}.jpg"
        targets.append(target)
        if target.exists():
            continue
        row, col = divmod(index, 3)
        margin = 7
        x1 = round(col * source.width / 3) + margin
        x2 = round((col + 1) * source.width / 3) - margin
        y1 = round(row * source.height / 2) + margin
        y2 = round((row + 1) * source.height / 2) - margin
        source.crop((x1, y1, x2, y2)).save(target, quality=95)
    return targets


async def main() -> None:
    if OUTPUT.exists():
        print(f"Preserving existing representative: {OUTPUT}")
        return
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    META.parent.mkdir(parents=True, exist_ok=True)
    audio = WORK / "narration.mp3"
    boundaries = WORK / "narration-boundaries.jsonl"
    await create_voice(NARRATION, audio, boundaries)
    voice_duration = media_duration(audio)
    total = math.ceil((voice_duration + 1.5) * FPS) / FPS
    cues = word_boundaries(boundaries, 0.45, 0.45 + voice_duration)
    srt = WORK / "captions.srt"
    ass = WORK / "overlay.ass"
    write_srt(cues, srt)
    write_ass(TITLE, total, cues, ass)
    metadata = {
        "status": "local-review-only",
        "episode_id": "parenting-rewind-redesign-01-kitchen-siblings",
        "version": "v1",
        "title": f"{TITLE} | Parenting Rewind",
        "audience_intent": "Adults and parents; not directed to children",
        "education_scope": "General parenting education only; not personalised therapy, diagnosis, or medical advice.",
        "narration": {"type": "synthetic", "voice": VOICE, "rate": "-5%", "pitch": "-1Hz", "transcript": NARRATION},
        "research": {
            "reviewed_on": "2026-08-23",
            "source": {
                "organization": "American Academy of Pediatrics / HealthyChildren.org",
                "title": "Sibling Relationships: How to Help Your Kids Build Healthy Bonds",
                "url": "https://www.healthychildren.org/English/family-life/family-dynamics/Pages/Sibling-Synergy.aspx"
            },
            "claim_limits": ["A timer and divided jobs are practical examples, not guaranteed solutions.", "Adults should intervene immediately when safety is at risk."]
        },
        "artwork": {"primary_asset": "production-assets/kitchen-siblings-storyboard-01.png", "new_image_generation_calls": 1, "new_cast": True, "new_setting": True},
        "music": {"type": "original locally synthesized emotional score", "narration_sidechain_ducking": True, "ambient_background_noise": False, "sound_effects": False},
        "captions": {"burned_in": True, "sidecar": "production-work/redesign-01-kitchen-siblings-v1/captions.srt"},
        "published": False,
        "upload_authorized": False,
    }
    META.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    panels = split_panels()
    render_video(panels, [0, 1, 2, 3, 4, 5], total, audio, ass, OUTPUT, WORK)
    metadata["output"] = {"file": str(OUTPUT.relative_to(PROJECT)), "duration_seconds": total, "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest().upper()}
    META.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = validate(OUTPUT, total, srt, META, WORK)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
