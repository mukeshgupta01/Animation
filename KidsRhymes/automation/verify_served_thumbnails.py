"""Fetch served Tiny Tales thumbnails and compare them with reviewed local JPEGs."""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageChops, ImageDraw, ImageStat

import uploader


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "thumbnail-manifest.json"
THUMBNAILS = HERE / "thumbnails"
OUTPUT = HERE / "runtime" / "served-thumbnail-verification-contact-sheet.jpg"


def rms_difference(left: Image.Image, right: Image.Image) -> float:
    difference = ImageChops.difference(left.convert("RGB"), right.convert("RGB"))
    values = ImageStat.Stat(difference).rms
    return sum(value * value for value in values) ** 0.5 / len(values) ** 0.5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", action="append", dest="video_ids")
    parser.add_argument("--max-rms", type=float, default=10.0)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    items = manifest["items"]
    if args.video_ids:
        requested = set(args.video_ids)
        items = [item for item in items if item["video_id"] in requested]
        found = {item["video_id"] for item in items}
        if found != requested:
            raise RuntimeError(f"Unknown thumbnail IDs: {sorted(requested - found)}")
    service, _channel = uploader.authorized_service(uploader.config())
    response = service.videos().list(
        part="id,snippet,status",
        id=",".join(item["video_id"] for item in items),
    ).execute()
    actual = {item["id"]: item for item in response.get("items", [])}
    if set(actual) != {item["video_id"] for item in items}:
        raise RuntimeError("One or more exact thumbnail target videos are absent")
    served_images: list[tuple[dict, Image.Image, float]] = []
    for item in items:
        video_id = item["video_id"]
        video = actual[video_id]
        if video["snippet"]["channelId"] != manifest["channel_id"] or video["snippet"]["title"] != item["expected_title"]:
            raise RuntimeError(f"Thumbnail target identity mismatch: {video_id}")
        thumbnail_url = video["snippet"]["thumbnails"]["maxres"]["url"]
        request = Request(
            thumbnail_url,
            headers={"User-Agent": "Tiny-Tales-Thumbnail-Verifier/1.0"},
        )
        with urlopen(request, timeout=30) as response:
            served = Image.open(BytesIO(response.read())).convert("RGB")
        local = Image.open(THUMBNAILS / f"{video_id}.jpg").convert("RGB")
        if served.size != (1280, 720):
            raise RuntimeError(f"Served thumbnail is not 1280x720: {video_id} {served.size}")
        rms = rms_difference(local, served)
        if rms > args.max_rms:
            raise RuntimeError(f"Served thumbnail differs unexpectedly: {video_id} RMS={rms:.3f}")
        served_images.append((item, served, rms))
    width = 640
    height = 390
    columns = min(3, len(served_images))
    rows = (len(served_images) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * width, rows * height), "#101d38")
    for index, (item, served, rms) in enumerate(served_images):
        preview = served.resize((width, 360), Image.Resampling.LANCZOS)
        x = (index % columns) * width
        y = (index // columns) * height
        sheet.paste(preview, (x, y))
        draw = ImageDraw.Draw(sheet)
        draw.text((x + 8, y + 364), f"{item['video_id']} | served 1280x720 | RMS {rms:.3f}", fill="white")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUTPUT, quality=92)
    print(json.dumps({
        "verified": len(served_images),
        "results": [{"video_id": item["video_id"], "size": [1280, 720], "rms": round(rms, 3)} for item, _image, rms in served_images],
        "contact_sheet": str(OUTPUT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
