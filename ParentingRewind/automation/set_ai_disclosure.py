"""Set YouTube's altered/synthetic-content disclosure for Parenting Rewind."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from youtube_auth import SafetyError, authorized_service


HERE = Path(__file__).resolve().parent
REPORT = HERE / "runtime" / "ai-disclosure-update-report.json"
EXPECTED_CHANNEL_ID = "UCGb-IUQX2KQa_KA24MwE_aQ"


def upload_video_ids(service: Any) -> list[str]:
    channel = service.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids: list[str] = []
    token = None
    while True:
        response = service.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids.extend(item["contentDetails"]["videoId"] for item in response.get("items", []))
        token = response.get("nextPageToken")
        if not token:
            return ids


def video_items(service: Any, ids: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for start in range(0, len(ids), 50):
        response = service.videos().list(part="snippet,status", id=",".join(ids[start:start + 50])).execute()
        items.extend(response.get("items", []))
    return items


def writable_status(status: dict[str, Any]) -> dict[str, Any]:
    keep = ("privacyStatus", "license", "embeddable", "publicStatsViewable", "selfDeclaredMadeForKids")
    value = {key: status[key] for key in keep if key in status}
    if status.get("publishAt") and status.get("privacyStatus") == "private":
        value["publishAt"] = status["publishAt"]
    value["containsSyntheticMedia"] = True
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-set-ai-label-yes", action="store_true")
    args = parser.parse_args()
    service, channel = authorized_service()
    try:
        if channel.get("channel_id") != EXPECTED_CHANNEL_ID:
            raise SafetyError("Authorized channel is not immutable Parenting Rewind target.")
        ids = upload_video_ids(service)
        items = video_items(service, ids)
        if any(item.get("snippet", {}).get("channelId") != EXPECTED_CHANNEL_ID for item in items):
            raise SafetyError("Upload playlist contained a video outside Parenting Rewind.")
        plan = [{"video_id": item["id"], "title": item["snippet"]["title"]} for item in items]
        if not args.confirm_set_ai_label_yes:
            print(json.dumps({"channel": channel, "video_count": len(plan), "planned_updates": len(plan), "note": "videos.list does not expose containsSyntheticMedia; direct update responses are verified instead"}, indent=2))
            return 0
        updated = []
        failures = []
        for item in items:
            response = service.videos().update(part="status", body={"id": item["id"], "status": writable_status(item["status"])}).execute()
            if response.get("status", {}).get("containsSyntheticMedia") is True:
                updated.append(item["id"])
            else:
                failures.append(item["id"])
        report = {"channel": channel, "video_count": len(ids), "api_confirmed_yes_count": len(updated), "api_confirmed_video_ids": updated, "verification_failures": failures, "verification_method": "containsSyntheticMedia=true in each successful videos.update response"}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2 if failures else 0
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
