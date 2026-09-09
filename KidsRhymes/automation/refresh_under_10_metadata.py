"""Fail-closed title and description-lead refresh for exact low-view Tiny Tales uploads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import uploader


PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = PROJECT / "metadata" / "under-10-metadata-refresh-2026-09-09.json"


def atomic_json(path: Path, document: dict) -> None:
    uploader.atomic_json(path, document)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("dry-run", "run"))
    parser.add_argument("--confirm-update", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--report-json", type=Path, default=PROJECT / "automation" / "runtime" / "under-10-metadata-refresh-result.json")
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    cfg = uploader.config()
    if plan.get("version") != 1 or plan.get("channel_id") != cfg["channel_id"]:
        raise uploader.SafetyError("Metadata refresh plan has an invalid immutable channel lock")
    threshold = int(plan.get("threshold", 0))
    items = plan.get("items")
    if threshold != 10 or not isinstance(items, list) or len(items) != 17:
        raise uploader.SafetyError("Expected the reviewed set of exactly 17 under-ten-view videos")
    ids = [item["video_id"] for item in items]
    if len(set(ids)) != len(ids):
        raise uploader.SafetyError("Metadata refresh plan contains duplicate video IDs")
    for item in items:
        if not 1 <= len(item["new_title"]) <= 100 or len(item["new_lead"]) > 500:
            raise uploader.SafetyError(f"Invalid replacement text: {item['video_id']}")

    service, channel = uploader.authorized_service(cfg)
    response = service.videos().list(part="id,snippet,statistics,status", id=",".join(ids)).execute()
    actual = {item["id"]: item for item in response.get("items", [])}
    if set(actual) != set(ids):
        raise uploader.SafetyError("One or more exact update targets are absent")

    preflight = []
    prepared = {}
    for item in items:
        current = actual[item["video_id"]]
        snippet = current["snippet"]
        status = current["status"]
        views = int(current.get("statistics", {}).get("viewCount", 0))
        if snippet.get("channelId") != plan["channel_id"]:
            raise uploader.SafetyError(f"Wrong-channel target: {item['video_id']}")
        if snippet.get("title") != item["expected_old_title"]:
            raise uploader.SafetyError(f"Live title changed since planning: {item['video_id']}")
        if views >= threshold:
            raise uploader.SafetyError(f"Target is no longer below {threshold} views: {item['video_id']}")
        if status.get("privacyStatus") != "public" or status.get("madeForKids") is not True:
            raise uploader.SafetyError(f"Target is not public and made for kids: {item['video_id']}")
        paragraphs = snippet.get("description", "").split("\n\n", 1)
        suffix = paragraphs[1].strip() if len(paragraphs) == 2 else ""
        new_description = item["new_lead"].strip() + (("\n\n" + suffix) if suffix else "")
        prepared[item["video_id"]] = {
            "title": item["new_title"],
            "description": new_description,
            "tags": snippet.get("tags", []),
            "categoryId": snippet.get("categoryId", "27"),
        }
        preflight.append({
            "video_id": item["video_id"], "views": views,
            "old_title": snippet["title"], "new_title": item["new_title"],
            "description_changed": new_description != snippet.get("description", ""),
            "tags_preserved": snippet.get("tags", []),
        })

    report = {
        "action": "under-10-title-description-refresh",
        "channel": channel,
        "threshold": threshold,
        "metadata_only": True,
        "thumbnails_unchanged": True,
        "items": preflight,
        "successful": 0,
        "results": [],
    }
    if args.command == "dry-run":
        print(json.dumps(report, indent=2))
        return 0
    if not args.confirm_update:
        raise uploader.SafetyError("Real metadata updates require --confirm-update")

    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.report_json, report)
    for item in items:
        video_id = item["video_id"]
        updated = service.videos().update(
            part="snippet", body={"id": video_id, "snippet": prepared[video_id]}
        ).execute()
        snippet = updated.get("snippet", {})
        if snippet.get("title") != prepared[video_id]["title"] or snippet.get("description") != prepared[video_id]["description"]:
            raise uploader.SafetyError(f"YouTube did not confirm replacement metadata: {video_id}")
        report["successful"] += 1
        report["results"].append({
            "video_id": video_id,
            "new_title": item["new_title"],
            "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        atomic_json(args.report_json, report)

    mismatch = None
    for attempt in range(3):
        verify = service.videos().list(part="id,snippet,status", id=",".join(ids)).execute()
        verified = {item["id"]: item for item in verify.get("items", [])}
        mismatch = None
        for item in items:
            video_id = item["video_id"]
            current = verified.get(video_id, {})
            snippet = current.get("snippet", {})
            status = current.get("status", {})
            expected = prepared[video_id]
            if snippet.get("title") != expected["title"] or snippet.get("description") != expected["description"]:
                mismatch = f"Final metadata read-back mismatch: {video_id}"
                break
            if snippet.get("tags", []) != expected["tags"] or snippet.get("categoryId") != expected["categoryId"]:
                mismatch = f"Preserved snippet field changed unexpectedly: {video_id}"
                break
            if status.get("privacyStatus") != "public" or status.get("madeForKids") is not True:
                mismatch = f"Status changed unexpectedly: {video_id}"
                break
        if mismatch is None:
            break
        if attempt < 2:
            time.sleep(2)
    if mismatch is not None:
        raise uploader.SafetyError(mismatch)
    report["readback_passed"] = True
    report["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    atomic_json(args.report_json, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
