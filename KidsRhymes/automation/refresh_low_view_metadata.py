"""Fail-closed one-time title and thumbnail refresh for reviewed low-view videos."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from PIL import Image

import uploader


PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = PROJECT / "metadata" / "low-view-title-thumbnail-refresh-2026-08-29.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("dry-run", "run"))
    parser.add_argument("--confirm-update", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--report-json", type=Path, default=PROJECT / "automation" / "runtime" / "low-view-refresh-result.json")
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    cfg = uploader.config()
    if plan.get("version") != 1 or plan.get("channel_id") != cfg["channel_id"]:
        raise uploader.SafetyError("Low-view refresh plan has an invalid channel lock")
    threshold = int(plan.get("threshold", 0))
    items = plan.get("items")
    if threshold < 1 or not isinstance(items, list) or not items:
        raise uploader.SafetyError("Low-view refresh plan is invalid or empty")
    ids = [item["video_id"] for item in items]
    if len(ids) != len(set(ids)):
        raise uploader.SafetyError("Low-view refresh plan contains duplicate IDs")

    thumbnails: dict[str, Path] = {}
    for item in items:
        if item.get("visual_reviewed") is not True:
            raise uploader.SafetyError(f"Thumbnail review is missing: {item['video_id']}")
        path = (PROJECT / item["thumbnail"]).resolve()
        try:
            path.relative_to(PROJECT.resolve())
        except ValueError as exc:
            raise uploader.SafetyError("Thumbnail path escapes Tiny Tales") from exc
        if not path.is_file() or path.stat().st_size > 2_000_000:
            raise uploader.SafetyError(f"Invalid thumbnail file: {path}")
        with Image.open(path) as image:
            if image.size != (1280, 720) or image.format != "JPEG":
                raise uploader.SafetyError(f"Thumbnail must be a 1280x720 JPEG: {path}")
        thumbnails[item["video_id"]] = path

    service, channel = uploader.authorized_service(cfg)
    response = service.videos().list(
        part="id,snippet,statistics,status", id=",".join(ids)
    ).execute()
    actual = {item["id"]: item for item in response.get("items", [])}
    if set(actual) != set(ids):
        raise uploader.SafetyError("One or more exact update targets are absent")

    preflight = []
    for item in items:
        current = actual[item["video_id"]]
        snippet = current["snippet"]
        status = current["status"]
        views = int(current.get("statistics", {}).get("viewCount", 0))
        if snippet["channelId"] != plan["channel_id"]:
            raise uploader.SafetyError(f"Wrong-channel target: {item['video_id']}")
        if snippet["title"] != item["expected_old_title"]:
            raise uploader.SafetyError(f"Title changed since planning: {item['video_id']}")
        if views >= threshold:
            raise uploader.SafetyError(f"Target is no longer below {threshold} views: {item['video_id']}")
        if status.get("privacyStatus") != "public" or status.get("madeForKids") is not True:
            raise uploader.SafetyError(f"Target status is not public/made-for-kids: {item['video_id']}")
        preflight.append({
            "video_id": item["video_id"], "views": views,
            "old_title": snippet["title"], "new_title": item["new_title"],
            "thumbnail_sha256": digest(thumbnails[item["video_id"]]),
        })

    if args.command == "dry-run":
        print(json.dumps({"action": "low-view-refresh-dry-run", "channel": channel, "items": preflight}, indent=2))
        return 0
    if not args.confirm_update:
        raise uploader.SafetyError("Real title/thumbnail updates require --confirm-update")

    _, _, _, _, MediaFileUpload = uploader.import_google()
    results = []
    for item in items:
        current = actual[item["video_id"]]
        snippet = current["snippet"]
        preserved = {
            "title": item["new_title"],
            "description": snippet.get("description", ""),
            "categoryId": snippet.get("categoryId", "27"),
        }
        if snippet.get("tags"):
            preserved["tags"] = snippet["tags"]
        updated = service.videos().update(
            part="snippet", body={"id": item["video_id"], "snippet": preserved}
        ).execute()
        if updated.get("snippet", {}).get("title") != item["new_title"]:
            raise uploader.SafetyError(f"YouTube did not confirm new title: {item['video_id']}")
        thumb_result = service.thumbnails().set(
            videoId=item["video_id"],
            media_body=MediaFileUpload(str(thumbnails[item["video_id"]]), mimetype="image/jpeg", resumable=False),
        ).execute()
        if not thumb_result.get("items"):
            raise uploader.SafetyError(f"YouTube did not confirm thumbnail: {item['video_id']}")
        results.append({
            **next(row for row in preflight if row["video_id"] == item["video_id"]),
            "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "title_confirmed": True,
            "thumbnail_confirmed": True,
        })

    verify = service.videos().list(part="id,snippet", id=",".join(ids)).execute()
    verified = {item["id"]: item for item in verify.get("items", [])}
    for item in items:
        if verified.get(item["video_id"], {}).get("snippet", {}).get("title") != item["new_title"]:
            raise uploader.SafetyError(f"Read-back title mismatch: {item['video_id']}")
    report = {
        "action": "low-view-title-thumbnail-refresh",
        "channel": channel,
        "threshold": threshold,
        "successful": len(results),
        "results": results,
    }
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
