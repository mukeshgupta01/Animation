"""Create five local-only redesigned episodes using three visual families at most twice each."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

from produce_authorized_batch import (
    FPS, VOICE, create_voice, media_duration, render_video, validate,
    word_boundaries, write_ass, write_srt,
)


PROJECT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT / "output"
WORK_ROOT = PROJECT / "production-work" / "redesigned-bundle-2026-08-23"
META_DIR = PROJECT / "metadata"

CDC_DIRECTIONS = {
    "organization": "Centers for Disease Control and Prevention",
    "title": "Tips for Giving Directions",
    "url": "https://www.cdc.gov/parenting-toddlers/communication/giving-directions.html",
}
AAP_SLEEP = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Toddler Bedtime Trouble: 7 Tips for Parents",
    "url": "https://www.healthychildren.org/English/healthy-living/sleep/Pages/bedtime-trouble.aspx",
}
CDC_PRAISE = {
    "organization": "Centers for Disease Control and Prevention",
    "title": "Tips for Child-led Play",
    "url": "https://www.cdc.gov/parenting-toddlers/communication/special-playtime.html",
}

EPISODES = [
    {
        "number": 2,
        "slug": "bedtime-stalling",
        "title": "When Bedtime Keeps Moving",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": AAP_SLEEP,
        "narration": [
            "The bedtime book ends, and your six-year-old suddenly needs water, another hug, and one more important question.",
            "Answering every new request can quietly teach that the routine ends only after enough stalling.",
            "Pause before sounding frustrated, because the boundary will be easier to hear when your voice stays steady.",
            "Try this: Our bedtime steps are pajamas, one book, and lights out; the book is finished, so now it is cuddle and goodnight.",
            "A predictable routine can be warm and firm at the same time; repeat the sequence instead of inventing a new argument each night.",
        ],
    },
    {
        "number": 3,
        "slug": "leaving-playground",
        "title": "Leaving the Playground Without a Chase",
        "asset": "playground-leaving-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 1, 2, 3, 4, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "The playground is wonderful until it is time to leave and your three-year-old sits down in protest.",
            "Calling from the gate and adding warning after warning can teach that the first direction does not matter.",
            "Pause, move close, and decide on one ending you are ready to follow through with.",
            "Say: One final slide, then hold my hand to the gate; after the slide, repeat the direction without reopening the decision.",
            "A concrete last turn makes the transition predictable, while calm follow-through shows that the limit is real.",
        ],
    },
    {
        "number": 4,
        "slug": "one-more-story",
        "title": "The One-More-Story Loop",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": AAP_SLEEP,
        "narration": [
            "One more story sounds small, but five extra stories can turn connection into a nightly negotiation.",
            "Announcing the limit only after reading makes the ending feel unexpected to a tired child.",
            "Rewind to before the first page and make the plan visible and simple.",
            "Say: Tonight you may choose one long book or two short books; after our choice, the books rest until tomorrow.",
            "Choices work when both options fit your limit; enjoy the reading fully, then close the routine as promised.",
        ],
    },
    {
        "number": 5,
        "slug": "notice-teamwork",
        "title": "Praise the Teamwork You Want Repeated",
        "asset": "kitchen-siblings-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": CDC_PRAISE,
        "narration": [
            "Two children can help with dinner for ten minutes, yet the one argument may receive all of your attention.",
            "A quick good job is kind, but it does not tell either child which action helped the family.",
            "Pause long enough to look for one specific piece of cooperation, even if the whole task is not perfect.",
            "Try: You waited for your turn with the bowl, and you carried the napkins carefully; that helped dinner get ready.",
            "Specific praise makes teamwork visible, and noticing small successful steps gives children a clearer behavior to repeat.",
        ],
    },
    {
        "number": 6,
        "slug": "playground-warning",
        "title": "Give a Warning That Means Something",
        "asset": "playground-leaving-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 2, 1, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Five minutes left can become four more warnings until nobody believes the clock.",
            "Repeating a direction without acting teaches a child to wait for the louder or later version.",
            "Before the warning, choose the exact final activity and what will happen next.",
            "Say: Two more turns on the slide, then we hold hands to the path; count the turns calmly and follow through after the second.",
            "The purpose of a warning is predictability, not bargaining; use one clear cue, an observable ending, and steady action.",
        ],
    },
]


def split_panels(asset: Path, grid: list[int], target_dir: Path) -> list[Path]:
    columns, rows = grid
    if columns * rows != 6:
        raise ValueError(f"Expected six panels, got grid {grid}")
    target_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(asset).convert("RGB")
    targets = []
    for index in range(6):
        target = target_dir / f"panel-{index}.jpg"
        targets.append(target)
        if target.exists():
            continue
        row, col = divmod(index, columns)
        margin = 7
        x1 = round(col * source.width / columns) + margin
        x2 = round((col + 1) * source.width / columns) - margin
        y1 = round(row * source.height / rows) + margin
        y2 = round((row + 1) * source.height / rows) - margin
        source.crop((x1, y1, x2, y2)).save(target, quality=95)
    return targets


async def produce(spec: dict) -> dict:
    episode_id = f"parenting-rewind-redesign-{spec['number']:02d}-{spec['slug']}"
    output = OUTPUT_DIR / f"{episode_id}-v1.mp4"
    work = WORK_ROOT / episode_id
    meta_path = META_DIR / f"{episode_id}-v1.json"
    quality = work / "quality-report.json"
    if output.exists() and quality.exists() and json.loads(quality.read_text(encoding="utf-8")).get("passed"):
        return {"episode": episode_id, "status": "preserved-existing"}
    work.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    narration = " ".join(spec["narration"])
    audio = work / "narration.mp3"
    boundaries = work / "narration-boundaries.jsonl"
    await create_voice(narration, audio, boundaries)
    voice_duration = media_duration(audio)
    total = math.ceil((voice_duration + 1.5) * FPS) / FPS
    cues = word_boundaries(boundaries, 0.45, 0.45 + voice_duration)
    srt, ass = work / "captions.srt", work / "overlay.ass"
    write_srt(cues, srt)
    write_ass(spec["title"], total, cues, ass)
    asset_path = PROJECT / "production-assets" / spec["asset"]
    panels = split_panels(asset_path, spec["grid"], work / "panels")
    metadata = {
        "status": "local-review-only", "episode_id": episode_id, "version": "v1",
        "title": f"{spec['title']} | Parenting Rewind",
        "audience_intent": "Adults and parents; not directed to children",
        "education_scope": "General parenting education only; not personalised therapy, diagnosis, or medical advice.",
        "narration": {"type": "synthetic", "voice": VOICE, "rate": "-5%", "pitch": "-1Hz", "transcript": narration},
        "research": {"reviewed_on": "2026-08-23", "source": spec["source"], "claim_limits": ["Suggested wording is an example, not a guaranteed result.", "Adapt expectations to the individual child and safety context."]},
        "artwork": {"primary_asset": f"production-assets/{spec['asset']}", "panel_order": spec["order"], "recycled_visuals_approved": spec["number"] in (4, 5, 6), "new_image_generation_calls": 0},
        "music": {"type": "original locally synthesized emotional score", "narration_sidechain_ducking": True, "ambient_background_noise": False, "sound_effects": False},
        "captions": {"burned_in": True, "sidecar": str(srt.relative_to(PROJECT))},
        "published": False, "upload_authorized": False,
    }
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    render_video(panels, spec["order"], total, audio, ass, output, work)
    metadata["output"] = {"file": str(output.relative_to(PROJECT)), "duration_seconds": total, "sha256": hashlib.sha256(output.read_bytes()).hexdigest().upper()}
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = validate(output, total, srt, meta_path, work)
    return {"episode": episode_id, "status": "completed", "duration_seconds": report["duration_seconds"]}


async def main() -> None:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-ledger.json").write_text(json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
