"""Make the seven rejected 2026-09-01 replacement uploads private, fail closed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import uploader


TARGETS = {
    "0CacEgX5rAg": "Felix Firefly's Night-Light Parade | Pattern Story for Kids",
    "lwD7Zhn47W4": "Basil Beaver's Leaky River Workshop | Engineering Story for Kids",
    "tdgKPtS8PJI": "Gus Gecko's Upside-Down Museum | Position Words for Kids",
    "RBuSJYnlFLk": "Nellie Narwhal and the Northern Lights | Colour Adventure for Kids",
    "g0C7_xVAqlo": "Tilly Turtle's Travelling Bakery | Opposites Story for Kids",
    "5q5TjZRHQkM": "Pogo Penguin's Wobbly Ice Bridge | Building Story for Kids",
    "tn7EAIhLiYQ": "Zara Zebra's Musical Crossing | Rhythm Story for Kids",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("dry-run", "run"))
    parser.add_argument("--confirm-private", action="store_true")
    args = parser.parse_args()
    if args.command == "run" and not args.confirm_private:
        raise uploader.SafetyError("Real privacy updates require --confirm-private")
    cfg = uploader.config()
    service, channel = uploader.authorized_service(cfg)
    response = service.videos().list(part="id,snippet,status", id=",".join(TARGETS)).execute()
    actual = {item["id"]: item for item in response.get("items", [])}
    if set(actual) != set(TARGETS):
        raise uploader.SafetyError("One or more exact replacement targets are absent")
    rows = []
    for video_id, title in TARGETS.items():
        item = actual[video_id]
        if item["snippet"].get("channelId") != cfg["channel_id"]:
            raise uploader.SafetyError(f"Wrong channel: {video_id}")
        if item["snippet"].get("title") != title:
            raise uploader.SafetyError(f"Title mismatch: {video_id}")
        if item["status"].get("madeForKids") is not True:
            raise uploader.SafetyError(f"Made-for-kids mismatch: {video_id}")
        rows.append({"video_id": video_id, "title": title,
                     "current_privacy": item["status"].get("privacyStatus")})
    if args.command == "dry-run":
        print(json.dumps({"action": "rejected-replacements-private-dry-run",
                          "channel": channel, "items": rows}, indent=2))
        return 0
    for row in rows:
        if row["current_privacy"] != "private":
            service.videos().update(
                part="status",
                body={"id": row["video_id"], "status": {
                    "privacyStatus": "private", "selfDeclaredMadeForKids": True,
                }},
            ).execute()
    verify = service.videos().list(part="id,snippet,status", id=",".join(TARGETS)).execute()
    verified = {item["id"]: item for item in verify.get("items", [])}
    for video_id, title in TARGETS.items():
        item = verified.get(video_id, {})
        if item.get("snippet", {}).get("channelId") != cfg["channel_id"] or item.get("snippet", {}).get("title") != title:
            raise uploader.SafetyError(f"Read-back identity mismatch: {video_id}")
        if item.get("status", {}).get("privacyStatus") != "private" or item.get("status", {}).get("madeForKids") is not True:
            raise uploader.SafetyError(f"Read-back status mismatch: {video_id}")
    report = {"action": "rejected-replacements-made-private", "channel": channel,
              "verified_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "verified_private": list(TARGETS)}
    path = Path(__file__).resolve().parent / "runtime" / "rejected-replacements-private.json"
    uploader.atomic_json(path, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
