"""Read back corrected public uploads and preserved private originals."""

from __future__ import annotations

import json
from pathlib import Path
import time

import uploader


ROWS = (
    ("qYQHMgq61Fs", "0CacEgX5rAg", "Felix Firefly's Night-Light Parade | Pattern Story for Kids"),
    ("TStyNqaucQQ", "lwD7Zhn47W4", "Basil Beaver's Leaky River Workshop | Engineering Story for Kids"),
    ("mKIhJftPCoo", "tdgKPtS8PJI", "Gus Gecko's Upside-Down Museum | Position Words for Kids"),
    ("oQlxxCIzIpM", "RBuSJYnlFLk", "Nellie Narwhal and the Northern Lights | Colour Adventure for Kids"),
    ("4hMcSA6koBA", "g0C7_xVAqlo", "Tilly Turtle's Travelling Bakery | Opposites Story for Kids"),
    ("EJVfLAdz_2s", "5q5TjZRHQkM", "Pogo Penguin's Wobbly Ice Bridge | Building Story for Kids"),
    ("qYuipr3PBt4", "tn7EAIhLiYQ", "Zara Zebra's Musical Crossing | Rhythm Story for Kids"),
)


def main() -> int:
    cfg = uploader.config()
    service, channel = uploader.authorized_service(cfg)
    ids = [value for old, new, _ in ROWS for value in (old, new)]
    result = service.videos().list(part="id,snippet,status,contentDetails", id=",".join(ids)).execute()
    actual = {item["id"]: item for item in result.get("items", [])}
    if set(actual) != set(ids):
        raise uploader.SafetyError("One or more original/replacement IDs are absent")
    verified = []
    for old_id, new_id, title in ROWS:
        for video_id, expected_privacy, role in ((old_id, "private", "preserved_original"), (new_id, "public", "corrected_replacement")):
            item = actual[video_id]
            if item["snippet"].get("channelId") != cfg["channel_id"]:
                raise uploader.SafetyError(f"Channel mismatch: {video_id}")
            if item["snippet"].get("title") != title:
                raise uploader.SafetyError(f"Title mismatch: {video_id}")
            if item["status"].get("privacyStatus") != expected_privacy:
                raise uploader.SafetyError(f"Privacy mismatch: {video_id}")
            if item["status"].get("madeForKids") is not True:
                raise uploader.SafetyError(f"Made-for-kids mismatch: {video_id}")
            verified.append({
                "role": role, "video_id": video_id, "title": title,
                "privacy": expected_privacy,
                "made_for_kids": True,
                "duration": item.get("contentDetails", {}).get("duration"),
            })
    report = {
        "action": "recent-replacements-verified",
        "verified_channel": channel,
        "verified_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "items": verified,
    }
    path = Path(__file__).resolve().parent / "runtime" / "recent-replacement-verification.json"
    uploader.atomic_json(path, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
