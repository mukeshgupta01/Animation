"""Read-only Tiny Tales view audit for exact live uploads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import uploader


HERE = Path(__file__).resolve().parent
UPLOAD_LEDGER = HERE / "runtime" / "upload-ledger.jsonl"


def chunks(values: list[str], size: int = 50):
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=20)
    parser.add_argument("--report-json", default="runtime/low-view-audit.json")
    parser.add_argument("--ledger-only", action="store_true")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    if args.threshold < 1:
        raise uploader.SafetyError("View threshold must be positive")

    cfg = uploader.config()
    service, channel = uploader.authorized_service(cfg)
    channel_response = service.channels().list(
        part="contentDetails", id=channel["channel_id"]
    ).execute()
    items = channel_response.get("items", [])
    if len(items) != 1:
        raise uploader.SafetyError("Expected exactly one locked channel")
    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    ordered_ids: list[str] = []
    token = None
    while True:
        response = service.playlistItems().list(
            part="contentDetails", playlistId=uploads_id, maxResults=50,
            pageToken=token,
        ).execute()
        ordered_ids.extend(
            item["contentDetails"]["videoId"] for item in response.get("items", [])
        )
        token = response.get("nextPageToken")
        if not token:
            break

    actual: dict[str, dict] = {}
    for group in chunks(ordered_ids):
        response = service.videos().list(
            part="id,snippet,statistics,status", id=",".join(group)
        ).execute()
        for item in response.get("items", []):
            if item["snippet"]["channelId"] != channel["channel_id"]:
                raise uploader.SafetyError(f"Wrong-channel video returned: {item['id']}")
            actual[item["id"]] = item

    rows = []
    for rank, video_id in enumerate(ordered_ids, start=1):
        item = actual.get(video_id)
        if not item:
            continue
        rows.append({
            "recency_rank": rank,
            "video_id": video_id,
            "title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "tags": item["snippet"].get("tags", []),
            "category_id": item["snippet"].get("categoryId", "27"),
            "published_at": item["snippet"].get("publishedAt"),
            "views": int(item.get("statistics", {}).get("viewCount", 0)),
            "privacy": item["status"].get("privacyStatus"),
            "made_for_kids": item["status"].get("madeForKids"),
        })

    if args.ledger_only:
        ledger_ids = set()
        if UPLOAD_LEDGER.exists():
            for line in UPLOAD_LEDGER.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    if row.get("video_id"):
                        ledger_ids.add(row["video_id"])
        rows = [row for row in rows if row["video_id"] in ledger_ids]

    low = [row for row in rows if row["views"] < args.threshold]
    top = sorted(rows, key=lambda row: (-row["views"], row["recency_rank"]))[:max(1, args.top)]
    report = {
        "version": 1,
        "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "channel_id": channel["channel_id"],
        "channel_name": channel["channel_name"],
        "threshold": args.threshold,
        "comparison": "strictly less than threshold",
        "total_live_uploads": len(rows),
        "low_view_count": len(low),
        "top_videos": top,
        "low_view_videos": low,
    }
    destination = HERE / args.report_json
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "channel_id": channel["channel_id"],
        "total_live_uploads": len(rows),
        "low_view_count": len(low),
        "top_videos": [
            {key: row[key] for key in ("video_id", "views", "title", "published_at")}
            for row in top
        ],
        "low_view_videos": [
            {key: row[key] for key in ("recency_rank", "video_id", "views", "title")}
            for row in low
        ],
        "report": str(destination),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
