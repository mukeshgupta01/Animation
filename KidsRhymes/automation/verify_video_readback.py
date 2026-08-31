"""Verify one uploaded Tiny Tales video against its producer metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import uploader


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--report-json")
    args = parser.parse_args()

    metadata_path = (PROJECT / args.metadata).resolve()
    metadata_path.relative_to(PROJECT.resolve())
    expected = json.loads(metadata_path.read_text(encoding="utf-8"))
    config = uploader.config()
    service, channel = uploader.authorized_service(config)
    response = service.videos().list(
        part="id,snippet,status,contentDetails,processingDetails",
        id=args.video_id,
    ).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise RuntimeError(f"Expected one video, received {len(items)}")
    actual = items[0]
    snippet = actual["snippet"]
    status = actual["status"]
    details = actual["contentDetails"]
    processing = actual.get("processingDetails", {})
    checks = {
        "video_id": actual["id"] == args.video_id,
        "channel_id": snippet.get("channelId") == channel["channel_id"],
        "title": snippet.get("title") == expected["title"],
        "description": snippet.get("description") == expected["description"],
        "tags": sorted(snippet.get("tags", []), key=str.casefold) == sorted(expected["tags"], key=str.casefold),
        "category_id": snippet.get("categoryId") == expected["category_id"],
        "privacy_public": status.get("privacyStatus") == "public",
        "made_for_kids": status.get("madeForKids") is True,
        "self_declared_made_for_kids": status.get("selfDeclaredMadeForKids") is True,
        "processing_succeeded": processing.get("processingStatus") == "succeeded",
    }
    report = {
        "video_id": args.video_id,
        "youtube_url": f"https://youtu.be/{args.video_id}",
        "verified_channel": channel,
        "duration": details.get("duration"),
        "definition": details.get("definition"),
        "expected_tags": expected["tags"],
        "actual_tags": snippet.get("tags", []),
        "checks": checks,
        "passed": all(checks.values()),
    }
    if args.report_json:
        report_path = (PROJECT / args.report_json).resolve()
        report_path.relative_to(PROJECT.resolve())
        uploader.atomic_json(report_path, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
