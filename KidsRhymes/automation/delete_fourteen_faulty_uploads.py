"""Delete the 14 explicitly authorized faulty Tiny Tales uploads, one by one."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import uploader


TARGETS = (
    ("qYQHMgq61Fs", "Felix Firefly's Night-Light Parade | Pattern Story for Kids", "original"),
    ("0CacEgX5rAg", "Felix Firefly's Night-Light Parade | Pattern Story for Kids", "replacement"),
    ("TStyNqaucQQ", "Basil Beaver's Leaky River Workshop | Engineering Story for Kids", "original"),
    ("lwD7Zhn47W4", "Basil Beaver's Leaky River Workshop | Engineering Story for Kids", "replacement"),
    ("mKIhJftPCoo", "Gus Gecko's Upside-Down Museum | Position Words for Kids", "original"),
    ("tdgKPtS8PJI", "Gus Gecko's Upside-Down Museum | Position Words for Kids", "replacement"),
    ("oQlxxCIzIpM", "Nellie Narwhal and the Northern Lights | Colour Adventure for Kids", "original"),
    ("RBuSJYnlFLk", "Nellie Narwhal and the Northern Lights | Colour Adventure for Kids", "replacement"),
    ("4hMcSA6koBA", "Tilly Turtle's Travelling Bakery | Opposites Story for Kids", "original"),
    ("g0C7_xVAqlo", "Tilly Turtle's Travelling Bakery | Opposites Story for Kids", "replacement"),
    ("EJVfLAdz_2s", "Pogo Penguin's Wobbly Ice Bridge | Building Story for Kids", "original"),
    ("5q5TjZRHQkM", "Pogo Penguin's Wobbly Ice Bridge | Building Story for Kids", "replacement"),
    ("qYuipr3PBt4", "Zara Zebra's Musical Crossing | Rhythm Story for Kids", "original"),
    ("tn7EAIhLiYQ", "Zara Zebra's Musical Crossing | Rhythm Story for Kids", "replacement"),
)


def save_report(path: Path, channel: dict, rows: list[dict]) -> None:
    uploader.atomic_json(path, {
        "action": "delete-fourteen-faulty-uploads",
        "verified_channel": channel,
        "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "items": rows,
        "delete_requests_sent": sum(1 for row in rows if row.get("delete_request_sent")),
        "confirmed_absent": sum(1 for row in rows if row.get("confirmed_absent")),
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-delete-all-14", action="store_true", required=True)
    args = parser.parse_args()
    cfg = uploader.config()
    service, channel = uploader.authorized_service(cfg)
    ids = [video_id for video_id, _, _ in TARGETS]
    response = service.videos().list(
        part="id,snippet,status,contentDetails", id=",".join(ids)
    ).execute()
    actual = {item["id"]: item for item in response.get("items", [])}
    if set(actual) != set(ids):
        missing = sorted(set(ids) - set(actual))
        raise uploader.SafetyError(f"Exact preflight target set is incomplete: {missing}")
    rows = []
    for video_id, title, generation in TARGETS:
        item = actual[video_id]
        if item["snippet"].get("channelId") != cfg["channel_id"]:
            raise uploader.SafetyError(f"Wrong-channel target: {video_id}")
        if item["snippet"].get("title") != title:
            raise uploader.SafetyError(f"Title mismatch: {video_id}")
        if item["status"].get("privacyStatus") != "private":
            raise uploader.SafetyError(f"Target is not private: {video_id}")
        if item["status"].get("madeForKids") is not True:
            raise uploader.SafetyError(f"Made-for-kids mismatch: {video_id}")
        rows.append({
            "video_id": video_id,
            "title": title,
            "generation": generation,
            "duration": item.get("contentDetails", {}).get("duration"),
            "preflight_channel_id": cfg["channel_id"],
            "preflight_privacy": "private",
            "delete_request_sent": False,
            "confirmed_absent": False,
        })
    report_path = Path(__file__).resolve().parent / "runtime" / "delete-fourteen-faulty-uploads.json"
    save_report(report_path, channel, rows)
    for row in rows:
        service.videos().delete(id=row["video_id"]).execute()
        row["delete_request_sent"] = True
        row["deleted_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save_report(report_path, channel, rows)
        for _ in range(15):
            readback = service.videos().list(part="id", id=row["video_id"]).execute()
            if not readback.get("items"):
                row["confirmed_absent"] = True
                break
            time.sleep(2)
        save_report(report_path, channel, rows)
        if not row["confirmed_absent"]:
            raise uploader.SafetyError(
                f"One delete request was sent but absence is not confirmed: {row['video_id']}; do not retry"
            )
        print(f"deleted and confirmed absent: {row['video_id']}", flush=True)
    final = service.videos().list(part="id", id=",".join(ids)).execute()
    if final.get("items"):
        raise uploader.SafetyError("Final 14-ID absence check returned one or more videos")
    save_report(report_path, channel, rows)
    print(json.dumps({
        "action": "fourteen-faulty-uploads-deleted",
        "channel": channel,
        "delete_requests_sent": 14,
        "confirmed_absent": 14,
        "video_ids": ids,
        "report": str(report_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
