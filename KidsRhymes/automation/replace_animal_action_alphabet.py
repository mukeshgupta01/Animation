"""Replace one verified Tiny Tales Animal Action Alphabet upload, fail closed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import uploader


OLD_VIDEO_ID = "DTLx7vnHwd8"
OLD_TITLE = "Animal Action Alphabet A-Z | Move and Learn with 26 Animals"
NEW_TITLE = "Move Like 26 Animals! | A–Z Animal Alphabet for Kids"
SOURCE_NAME = "animal-action-alphabet-a-to-z-01-relaunch.mp4"
MASTER_NAME = "animal-action-alphabet-a-to-z-01.mp4"


def save_report(path: Path, value: dict) -> None:
    value["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    uploader.atomic_json(path, value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-replace", action="store_true")
    args = parser.parse_args()

    cfg = uploader.config()
    here = Path(__file__).resolve().parent
    master = here / "archive" / MASTER_NAME
    source = here / "pending-uploads" / SOURCE_NAME
    metadata_path = source.with_suffix(".json")
    report_path = here / "runtime" / "animal-action-alphabet-relaunch.json"

    if not master.is_file() or not source.is_file() or not metadata_path.is_file():
        raise uploader.SafetyError("Replacement master, queue copy, or sidecar is missing")
    master_hash = uploader.sha256(master)
    source_hash = uploader.sha256(source)
    if master_hash != source_hash:
        raise uploader.SafetyError("Replacement queue copy is not byte-for-byte identical to the reviewed master")

    ledger_matches = [row for row in uploader.ledger_rows() if row.get("video_id") == OLD_VIDEO_ID]
    if len(ledger_matches) != 1:
        raise uploader.SafetyError("The upload ledger does not contain exactly one old target row")
    if ledger_matches[0].get("source_name") != MASTER_NAME or ledger_matches[0].get("sha256") != master_hash:
        raise uploader.SafetyError("Old upload ledger identity or source hash does not match the reviewed master")

    metadata = uploader.load_json(metadata_path, {})
    if metadata.get("title") != NEW_TITLE or metadata.get("replacement_of") != OLD_VIDEO_ID:
        raise uploader.SafetyError("Replacement metadata identity failed")
    if metadata.get("made_for_kids") is not True or metadata.get("privacy") != "public":
        raise uploader.SafetyError("Replacement audience or privacy metadata failed")
    thumbnail = uploader.prepared_thumbnail_for(source, cfg)
    if thumbnail is None:
        raise uploader.SafetyError("Reviewed custom thumbnail is missing")
    if not uploader.ffprobe_ok(source) or not uploader.full_decode_ok(source):
        raise uploader.SafetyError("Replacement source validation or full decode failed")

    service, channel = uploader.authorized_service(cfg)
    response = service.videos().list(
        part="id,snippet,status,contentDetails", id=OLD_VIDEO_ID
    ).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise uploader.SafetyError("Exact old video target is absent or ambiguous")
    old = items[0]
    if old["snippet"].get("channelId") != cfg["channel_id"]:
        raise uploader.SafetyError("Old target belongs to the wrong channel")
    if old["snippet"].get("title") != OLD_TITLE:
        raise uploader.SafetyError("Old target title mismatch")
    if old["status"].get("privacyStatus") != "public":
        raise uploader.SafetyError("Old target is not public")
    if old["status"].get("madeForKids") is not True:
        raise uploader.SafetyError("Old target made-for-kids setting mismatch")

    report = {
        "action": "animal-action-alphabet-relaunch",
        "verified_channel": channel,
        "old_video_id": OLD_VIDEO_ID,
        "old_title": OLD_TITLE,
        "old_duration": old.get("contentDetails", {}).get("duration"),
        "new_title": NEW_TITLE,
        "source_name": SOURCE_NAME,
        "source_sha256": source_hash,
        "thumbnail": str(thumbnail),
        "preflight_passed": True,
        "delete_request_sent": False,
        "old_video_confirmed_absent": False,
        "upload_started": False,
    }
    save_report(report_path, report)
    if not args.confirm_replace:
        print(json.dumps({**report, "mode": "dry-run", "report": str(report_path)}, indent=2))
        return 0

    service.videos().delete(id=OLD_VIDEO_ID).execute()
    report["delete_request_sent"] = True
    report["deleted_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_report(report_path, report)
    for _ in range(15):
        readback = service.videos().list(part="id", id=OLD_VIDEO_ID).execute()
        if not readback.get("items"):
            report["old_video_confirmed_absent"] = True
            break
        time.sleep(2)
    save_report(report_path, report)
    if not report["old_video_confirmed_absent"]:
        raise uploader.SafetyError("One delete request was sent but absence is not confirmed; do not retry deletion")

    report["upload_started"] = True
    save_report(report_path, report)
    result = uploader.upload_one(service, source, cfg, thumbnail)
    report["upload_result"] = result
    report["new_video_id"] = result["video_id"]
    save_report(report_path, report)

    verify = service.videos().list(
        part="id,snippet,status,contentDetails", id=result["video_id"]
    ).execute()
    new_items = verify.get("items", [])
    if len(new_items) != 1:
        raise uploader.SafetyError("Replacement upload returned an ID but API read-back is absent")
    new = new_items[0]
    expected = uploader.metadata_for((here / "archive" / SOURCE_NAME), cfg)
    if new["snippet"].get("channelId") != cfg["channel_id"]:
        raise uploader.SafetyError("Replacement read-back channel mismatch")
    if new["snippet"].get("title") != expected["snippet"]["title"]:
        raise uploader.SafetyError("Replacement read-back title mismatch")
    if new["snippet"].get("description") != expected["snippet"]["description"]:
        raise uploader.SafetyError("Replacement read-back description mismatch")
    if new["status"].get("privacyStatus") != "public" or new["status"].get("madeForKids") is not True:
        raise uploader.SafetyError("Replacement read-back privacy or audience mismatch")
    report["readback_verified"] = True
    report["new_duration"] = new.get("contentDetails", {}).get("duration")
    save_report(report_path, report)
    print(json.dumps({
        "action": "animal-action-alphabet-replaced",
        "channel": channel,
        "old_video_id": OLD_VIDEO_ID,
        "delete_requests_sent": 1,
        "old_video_confirmed_absent": True,
        "new_video_id": result["video_id"],
        "new_title": NEW_TITLE,
        "readback_verified": True,
        "thumbnail_uploaded": "custom_thumbnail" in result,
        "report": str(report_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
