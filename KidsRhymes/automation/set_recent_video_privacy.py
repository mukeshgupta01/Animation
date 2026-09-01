"""Fail-closed privacy update for the seven Tiny Tales videos released 2026-08-31/09-01."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import uploader


TARGETS = {
    "qYQHMgq61Fs": "Felix Firefly's Night-Light Parade | Pattern Story for Kids",
    "TStyNqaucQQ": "Basil Beaver's Leaky River Workshop | Engineering Story for Kids",
    "mKIhJftPCoo": "Gus Gecko's Upside-Down Museum | Position Words for Kids",
    "oQlxxCIzIpM": "Nellie Narwhal and the Northern Lights | Colour Adventure for Kids",
    "4hMcSA6koBA": "Tilly Turtle's Travelling Bakery | Opposites Story for Kids",
    "EJVfLAdz_2s": "Pogo Penguin's Wobbly Ice Bridge | Building Story for Kids",
    "qYuipr3PBt4": "Zara Zebra's Musical Crossing | Rhythm Story for Kids",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("dry-run", "run"))
    parser.add_argument("--confirm-private", action="store_true")
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path(__file__).resolve().parent / "runtime" / "recent-video-privacy-result.json",
    )
    args = parser.parse_args()
    if args.command == "run" and not args.confirm_private:
        raise uploader.SafetyError("Real privacy updates require --confirm-private")

    cfg = uploader.config()
    service, channel = uploader.authorized_service(cfg)
    ids = list(TARGETS)
    response = service.videos().list(part="id,snippet,status", id=",".join(ids)).execute()
    actual = {item["id"]: item for item in response.get("items", [])}
    if set(actual) != set(ids):
        raise uploader.SafetyError("One or more exact privacy targets are absent")

    preflight = []
    for video_id, expected_title in TARGETS.items():
        item = actual[video_id]
        if item["snippet"].get("channelId") != cfg["channel_id"]:
            raise uploader.SafetyError(f"Wrong-channel target: {video_id}")
        if item["snippet"].get("title") != expected_title:
            raise uploader.SafetyError(f"Title mismatch: {video_id}")
        if item["status"].get("madeForKids") is not True:
            raise uploader.SafetyError(f"Made-for-kids flag mismatch: {video_id}")
        preflight.append({
            "video_id": video_id,
            "title": expected_title,
            "current_privacy": item["status"].get("privacyStatus"),
            "target_privacy": "private",
        })

    if args.command == "dry-run":
        print(json.dumps({"action": "recent-video-privacy-dry-run", "channel": channel, "items": preflight}, indent=2))
        return 0

    changed = []
    for row in preflight:
        if row["current_privacy"] != "private":
            service.videos().update(
                part="status",
                body={
                    "id": row["video_id"],
                    "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": True},
                },
            ).execute()
            changed.append(row["video_id"])

    verify = service.videos().list(part="id,snippet,status", id=",".join(ids)).execute()
    verified = {item["id"]: item for item in verify.get("items", [])}
    for video_id, expected_title in TARGETS.items():
        item = verified.get(video_id, {})
        if item.get("snippet", {}).get("channelId") != cfg["channel_id"]:
            raise uploader.SafetyError(f"Read-back channel mismatch: {video_id}")
        if item.get("snippet", {}).get("title") != expected_title:
            raise uploader.SafetyError(f"Read-back title mismatch: {video_id}")
        if item.get("status", {}).get("privacyStatus") != "private":
            raise uploader.SafetyError(f"Read-back privacy mismatch: {video_id}")
        if item.get("status", {}).get("madeForKids") is not True:
            raise uploader.SafetyError(f"Read-back made-for-kids mismatch: {video_id}")

    report = {
        "action": "recent-videos-made-private",
        "channel": channel,
        "verified_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "changed": changed,
        "verified_private": ids,
    }
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
