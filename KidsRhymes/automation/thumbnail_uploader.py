"""Fail-closed manual uploader for reviewed Tiny Tales custom thumbnails."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from PIL import Image

import uploader


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "thumbnail-manifest.json"
THUMBNAILS = HERE / "thumbnails"
LEDGER = HERE / "runtime" / "thumbnail-upload-ledger.jsonl"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def load_manifest() -> dict:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cfg = uploader.config()
    if doc.get("version") != 1 or doc.get("channel_id") != cfg["channel_id"]:
        raise uploader.SafetyError("Thumbnail manifest channel lock is invalid")
    items = doc.get("items")
    if not isinstance(items, list) or not items:
        raise uploader.SafetyError("Thumbnail manifest has no items")
    ids = [item.get("video_id") for item in items]
    if len(ids) != len(set(ids)):
        raise uploader.SafetyError("Thumbnail manifest contains duplicate video IDs")
    for item in items:
        path = THUMBNAILS / f"{item['video_id']}.jpg"
        if not path.is_file() or path.stat().st_size == 0 or path.stat().st_size > 2_000_000:
            raise uploader.SafetyError(f"Thumbnail file is missing, empty, or over 2 MB: {path}")
        with Image.open(path) as image:
            if image.size != (1280, 720) or image.format != "JPEG":
                raise uploader.SafetyError(f"Thumbnail must be 1280x720 JPEG: {path}")
    return doc


def append_ledger(row: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("dry-run", "run"))
    parser.add_argument("--confirm-upload", action="store_true")
    args = parser.parse_args()
    doc = load_manifest()
    if args.command == "dry-run":
        print(json.dumps({"action": "thumbnail-dry-run", "count": len(doc["items"]), "video_ids": [item["video_id"] for item in doc["items"]]}, indent=2))
        return 0
    if not args.confirm_upload:
        raise uploader.SafetyError("Real thumbnail upload requires --confirm-upload")
    service, channel = uploader.authorized_service(uploader.config())
    video_ids = [item["video_id"] for item in doc["items"]]
    response = service.videos().list(part="id,snippet", id=",".join(video_ids)).execute()
    actual = {item["id"]: item for item in response.get("items", [])}
    if set(actual) != set(video_ids):
        raise uploader.SafetyError("One or more exact thumbnail target videos are absent")
    for item in doc["items"]:
        video = actual[item["video_id"]]
        if video["snippet"]["channelId"] != doc["channel_id"] or video["snippet"]["title"] != item["expected_title"]:
            raise uploader.SafetyError(f"Thumbnail target identity mismatch: {item['video_id']}")
    _, _, _, _, MediaFileUpload = uploader.import_google()
    results = []
    for item in doc["items"]:
        path = THUMBNAILS / f"{item['video_id']}.jpg"
        result = service.thumbnails().set(
            videoId=item["video_id"],
            media_body=MediaFileUpload(str(path), mimetype="image/jpeg", resumable=False),
        ).execute()
        if not result.get("items"):
            raise uploader.SafetyError(f"YouTube did not confirm thumbnail set: {item['video_id']}")
        row = {
            "video_id": item["video_id"],
            "title": item["expected_title"],
            "sha256": digest(path),
            "uploaded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "channel_id": channel["channel_id"],
        }
        append_ledger(row)
        results.append(row)
    print(json.dumps({"action": "thumbnail-upload", "successful": len(results), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
