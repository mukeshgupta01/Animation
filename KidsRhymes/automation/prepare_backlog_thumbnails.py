"""Render and explicitly release reviewed custom thumbnails for queued legacy videos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

from generate_thumbnails import make_creative_thumbnail


HERE = Path(__file__).resolve().parent
PLAN = HERE / "backlog-thumbnail-plan.json"
PENDING = HERE / "pending-uploads"
ARCHIVE = HERE / "archive"
OUTPUT = HERE / "thumbnails"
REVIEW = HERE / "runtime" / "backlog-thumbnail-review-contact-sheet.jpg"
EXPECTED_CHANNEL = "UCEn9N-ITQHshjgt6fy7fxnw"


def load_plan() -> list[dict[str, object]]:
    document = json.loads(PLAN.read_text(encoding="utf-8"))
    if document.get("version") != 1 or document.get("channel_id") != EXPECTED_CHANNEL:
        raise RuntimeError("Backlog thumbnail plan channel/version lock failed")
    items = document.get("items")
    if not isinstance(items, list) or not items:
        raise RuntimeError("Backlog thumbnail plan is empty")
    ids = [str(item.get("id", "")) for item in items]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise RuntimeError("Backlog thumbnail plan has missing or duplicate IDs")
    return items


def validate_source(item: dict[str, object]) -> tuple[dict[str, object], Path]:
    stem = str(item["id"])
    location = PENDING if (PENDING / f"{stem}.mp4").is_file() else ARCHIVE
    video = location / f"{stem}.mp4"
    sidecar = location / f"{stem}.json"
    if not video.is_file() or not sidecar.is_file():
        raise RuntimeError(f"Pending source is missing: {stem}")
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    if metadata.get("id", stem) != stem or not metadata.get("title"):
        raise RuntimeError(f"Pending metadata identity is invalid: {stem}")
    artwork = HERE / str(item["artwork"])
    if not artwork.is_file() or artwork.stat().st_size == 0:
        raise RuntimeError(f"Reviewed artwork is missing: {artwork}")
    return metadata, location


def render(items: list[dict[str, object]]) -> list[Path]:
    paths: list[Path] = []
    for item in items:
        validate_source(item)
        creative_item = {
            "video_id": item["id"],
            "artwork": item["artwork"],
            "hook": item["hook"],
            "hook_position": item["hook_position"],
            "accent": item["accent"],
        }
        path = make_creative_thumbnail(creative_item)
        with Image.open(path) as image:
            if image.format != "JPEG" or image.size != (1280, 720):
                raise RuntimeError(f"Invalid prepared thumbnail: {path}")
        if path.stat().st_size > 2_000_000:
            raise RuntimeError(f"Prepared thumbnail exceeds 2 MB: {path}")
        paths.append(path)

    cell_width, cell_height = 640, 390
    columns = min(4, len(paths))
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#111a33")
    draw = ImageDraw.Draw(sheet)
    for index, (item, path) in enumerate(zip(items, paths)):
        preview = Image.open(path).convert("RGB").resize((cell_width, 360), Image.Resampling.LANCZOS)
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        sheet.paste(preview, (x, y))
        draw.text((x + 8, y + 365), str(item["id"]), fill="white")
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW, quality=92)
    return paths


def release(items: list[dict[str, object]]) -> list[str]:
    released: list[str] = []
    for item in items:
        metadata, location = validate_source(item)
        stem = str(item["id"])
        if location == ARCHIVE:
            continue
        thumbnail = OUTPUT / f"{stem}.jpg"
        if not thumbnail.is_file() or thumbnail.stat().st_size == 0:
            raise RuntimeError(f"Render and review the thumbnail before release: {thumbnail}")
        with Image.open(thumbnail) as image:
            if image.format != "JPEG" or image.size != (1280, 720):
                raise RuntimeError(f"Invalid reviewed thumbnail: {thumbnail}")
        metadata["prepared_thumbnail"] = f"automation/thumbnails/{stem}.jpg"
        metadata["thumbnail_hook"] = str(item["hook"])
        metadata["thumbnail_reviewed"] = True
        metadata["thumbnail_artwork"] = f"automation/{item['artwork']}"
        sidecar = location / f"{stem}.json"
        temporary = sidecar.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(sidecar)
        released.append(stem)
    return released


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("render", "release-reviewed"))
    args = parser.parse_args()
    items = load_plan()
    if args.command == "render":
        paths = render(items)
        print(json.dumps({"rendered": len(paths), "files": [str(path) for path in paths], "review": str(REVIEW)}, indent=2))
        return
    released = release(items)
    print(json.dumps({"released": len(released), "ids": released}, indent=2))


if __name__ == "__main__":
    main()
