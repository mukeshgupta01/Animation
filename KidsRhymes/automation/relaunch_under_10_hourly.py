"""Replace the exact reviewed under-ten-view set using native hourly YouTube scheduling."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from PIL import Image

import uploader


PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = PROJECT / "metadata" / "under-10-hourly-relaunch-2026-09-09.json"
DEFAULT_REPORT = PROJECT / "automation" / "runtime" / "under-10-hourly-relaunch-result.json"


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def save(path: Path, value: dict) -> None:
    value["updated_utc"] = utc_now()
    uploader.atomic_json(path, value)


def load_package(plan: dict) -> list[dict]:
    if plan.get("version") != 1 or plan.get("channel_id") != "UCEn9N-ITQHshjgt6fy7fxnw":
        raise uploader.SafetyError("Invalid immutable channel lock in relaunch plan")
    if plan.get("publish_interval_seconds") != 3600:
        raise uploader.SafetyError("Relaunch interval must be exactly one hour")
    items = plan.get("items")
    if not isinstance(items, list) or len(items) != 17:
        raise uploader.SafetyError("Expected the reviewed set of exactly 17 videos")
    if len({item["old_video_id"] for item in items}) != 17:
        raise uploader.SafetyError("Duplicate old video ID in relaunch plan")

    anchor = parse_utc(plan["first_publish_utc"])
    package = []
    ledger = uploader.ledger_rows()
    for index, item in enumerate(items):
        metadata_path = PROJECT / item["metadata"]
        source = PROJECT / item["source"]
        thumbnail = PROJECT / item["thumbnail"]
        if not metadata_path.is_file() or not source.is_file() or not thumbnail.is_file():
            raise uploader.SafetyError(f"Missing relaunch package file: {item['old_video_id']}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not metadata.get("title") or not metadata.get("description") or not metadata.get("tags"):
            raise uploader.SafetyError(f"Incomplete canonical metadata: {item['old_video_id']}")
        if metadata.get("made_for_kids") is not True or str(metadata.get("category_id")) != "27":
            raise uploader.SafetyError(f"Invalid canonical audience/category: {item['old_video_id']}")
        digest = uploader.sha256(source)
        if digest != item["source_sha256"]:
            raise uploader.SafetyError(f"Reviewed master hash mismatch: {item['old_video_id']}")
        matches = [row for row in ledger if row.get("video_id") == item["old_video_id"]]
        if len(matches) != 1 or matches[0].get("sha256") != digest:
            raise uploader.SafetyError(f"Upload ledger/source identity mismatch: {item['old_video_id']}")
        with Image.open(thumbnail) as image:
            if image.format != "JPEG" or image.size != (1280, 720) or thumbnail.stat().st_size > 2_000_000:
                raise uploader.SafetyError(f"Invalid reviewed thumbnail: {item['old_video_id']}")
        package.append({
            **item,
            "metadata_path": metadata_path,
            "source_path": source,
            "thumbnail_path": thumbnail,
            "metadata_document": metadata,
            "publish_at": (anchor.timestamp() + index * 3600),
        })
    return package


def preflight_live(service, cfg: dict, package: list[dict]) -> list[dict]:
    ids = [item["old_video_id"] for item in package]
    response = service.videos().list(part="id,snippet,status,statistics,contentDetails", id=",".join(ids)).execute()
    live = {item["id"]: item for item in response.get("items", [])}
    if set(live) != set(ids):
        raise uploader.SafetyError("One or more exact old upload targets are absent")
    rows = []
    for item in package:
        video = live[item["old_video_id"]]
        snippet = video["snippet"]
        status = video["status"]
        metadata = item["metadata_document"]
        if snippet.get("channelId") != cfg["channel_id"]:
            raise uploader.SafetyError(f"Wrong-channel target: {item['old_video_id']}")
        if snippet.get("title") != metadata["title"] or snippet.get("description") != metadata["description"]:
            raise uploader.SafetyError(f"Live metadata changed: {item['old_video_id']}")
        if set(snippet.get("tags", [])) != set(metadata["tags"]) or snippet.get("categoryId") != "27":
            raise uploader.SafetyError(f"Live tags/category changed: {item['old_video_id']}")
        views = int(video.get("statistics", {}).get("viewCount", 0))
        if views >= 10:
            raise uploader.SafetyError(f"Video is no longer below ten views: {item['old_video_id']}")
        if status.get("privacyStatus") != "public" or status.get("madeForKids") is not True:
            raise uploader.SafetyError(f"Old target is not public and made for kids: {item['old_video_id']}")
        rows.append({
            "old_video_id": item["old_video_id"],
            "title": metadata["title"],
            "views": views,
            "duration": video.get("contentDetails", {}).get("duration"),
            "source": str(item["source_path"]),
            "source_sha256": item["source_sha256"],
            "thumbnail": str(item["thumbnail_path"]),
            "publish_at": datetime.fromtimestamp(item["publish_at"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    return rows


def validate_masters(package: list[dict]) -> None:
    for item in package:
        if not uploader.ffprobe_ok(item["source_path"]):
            raise uploader.SafetyError(f"FFprobe validation failed: {item['old_video_id']}")
        if not uploader.full_decode_ok(item["source_path"]):
            raise uploader.SafetyError(f"Full decode failed: {item['old_video_id']}")


def upload_scheduled(service, item: dict, report: dict, state: dict, report_path: Path) -> str:
    _, _, _, _, MediaFileUpload = uploader.import_google()
    metadata = item["metadata_document"]
    publish_at = datetime.fromtimestamp(item["publish_at"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": True,
        },
    }
    media = MediaFileUpload(str(item["source_path"]), chunksize=8 * 1024 * 1024, resumable=True)
    request = service.videos().insert(
        part="snippet,status", body=body, media_body=media, notifySubscribers=False
    )
    response = None
    try:
        while response is None:
            _, response = request.next_chunk()
    finally:
        stream = media.stream()
        if stream and not stream.closed:
            stream.close()
    video_id = response.get("id") if response else None
    if not video_id:
        raise uploader.SafetyError("Upload completed without returning a video ID")
    state["new_video_id"] = video_id
    state["uploaded_utc"] = utc_now()
    save(report_path, report)
    uploader.append_ledger({
        "uploaded_utc": state["uploaded_utc"],
        "source_name": item["source_path"].name,
        "source_path": str(item["source_path"]),
        "sha256": item["source_sha256"],
        "video_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}",
        "privacy_status": "private",
        "publish_at": publish_at,
        "made_for_kids": True,
        "replacement_of": item["old_video_id"],
        "relaunch_batch": "under-10-hourly-2026-09-09",
    })
    uploader.set_custom_thumbnail_record(
        service, video_id, item["thumbnail_path"], metadata["title"], item["source_path"].name, uploader.config()
    )
    state["thumbnail_uploaded"] = True
    save(report_path, report)
    return video_id


def verify_replacement(service, cfg: dict, item: dict, video_id: str) -> None:
    mismatch = None
    for attempt in range(30):
        response = service.videos().list(part="id,snippet,status,contentDetails", id=video_id).execute()
        videos = response.get("items", [])
        if len(videos) != 1:
            mismatch = f"Replacement read-back absent: {video_id}"
        else:
            video = videos[0]
            snippet = video["snippet"]
            status = video["status"]
            metadata = item["metadata_document"]
            expected_publish = datetime.fromtimestamp(item["publish_at"], timezone.utc)
            actual_publish = parse_utc(status.get("publishAt", "1970-01-01T00:00:00Z"))
            if snippet.get("channelId") != cfg["channel_id"]:
                mismatch = f"Replacement channel mismatch: {video_id}"
            elif snippet.get("title") != metadata["title"] or snippet.get("description") != metadata["description"]:
                mismatch = f"Replacement metadata mismatch: {video_id}"
            elif set(snippet.get("tags", [])) != set(metadata["tags"]) or snippet.get("categoryId") != "27":
                mismatch = f"Replacement tags/category mismatch: {video_id}"
            elif status.get("privacyStatus") != "private" or status.get("madeForKids") is not True:
                mismatch = f"Replacement scheduling/audience mismatch: {video_id}"
            elif actual_publish != expected_publish:
                mismatch = f"Replacement publish time mismatch: {video_id}"
            else:
                return
        if attempt < 29:
            time.sleep(5)
    raise uploader.SafetyError(mismatch)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("dry-run", "run"))
    parser.add_argument("--confirm-relaunch", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    package = load_package(plan)
    cfg = uploader.config()
    service, channel = uploader.authorized_service(cfg)
    if args.command == "dry-run":
        preflight = preflight_live(service, cfg, package)
        validate_masters(package)
        print(json.dumps({
            "action": "under-10-hourly-relaunch-preflight",
            "channel": channel,
            "count": len(preflight),
            "all_full_decodes_passed": True,
            "windows_scheduled_task_created": False,
            "native_youtube_hourly_schedule": True,
            "items": preflight,
        }, indent=2))
        return 0
    if not args.confirm_relaunch:
        raise uploader.SafetyError("Real deletion/relaunch requires --confirm-relaunch")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if args.report.is_file():
        report = json.loads(args.report.read_text(encoding="utf-8"))
        if report.get("action") != "under-10-hourly-relaunch" or len(report.get("items", [])) != 17:
            raise uploader.SafetyError("Existing relaunch report cannot be resumed safely")
        for item, state in zip(package, report["items"]):
            if state.get("old_video_id") != item["old_video_id"]:
                raise uploader.SafetyError("Existing relaunch report order/identity mismatch")
            if state.get("state") == "verified_scheduled":
                if not state.get("new_video_id"):
                    raise uploader.SafetyError("Verified state lacks a replacement video ID")
                verify_replacement(service, cfg, item, state["new_video_id"])
            elif state.get("state") == "upload_started":
                if not state.get("new_video_id"):
                    raise uploader.SafetyError("Unresolved upload attempt has no video ID; inspect live channel before retry")
                verify_replacement(service, cfg, item, state["new_video_id"])
                state["state"] = "verified_scheduled"
                state["readback_verified"] = True
                save(args.report, report)
            elif state.get("state") != "pending":
                raise uploader.SafetyError(f"Unresolved destructive state: {item['old_video_id']}")
        pending = [item for item, state in zip(package, report["items"]) if state.get("state") == "pending"]
        if pending:
            preflight_live(service, cfg, pending)
            if report.get("all_full_decodes_passed") is not True:
                validate_masters(pending)
                report["all_full_decodes_passed"] = True
                save(args.report, report)
    else:
        preflight_live(service, cfg, package)
        validate_masters(package)
        if parse_utc(plan["first_publish_utc"]) <= datetime.now(timezone.utc):
            raise uploader.SafetyError("First native publish time is no longer in the future")
        report = {
            "action": "under-10-hourly-relaunch",
            "channel": channel,
            "started_utc": utc_now(),
            "first_publish_utc": plan["first_publish_utc"],
            "publish_interval_seconds": 3600,
            "windows_scheduled_task_created": False,
            "all_full_decodes_passed": True,
            "items": [{"old_video_id": item["old_video_id"], "state": "pending"} for item in package],
        }
        save(args.report, report)

    for item, state in zip(package, report["items"]):
        if state.get("state") == "verified_scheduled":
            continue
        if datetime.fromtimestamp(item["publish_at"], timezone.utc) <= datetime.now(timezone.utc):
            raise uploader.SafetyError(f"Pending native publish time is no longer in the future: {item['old_video_id']}")
        state["state"] = "delete_request_about_to_send"
        save(args.report, report)
        service.videos().delete(id=item["old_video_id"]).execute()
        state["delete_request_sent"] = True
        state["deleted_utc"] = utc_now()
        save(args.report, report)
        for _ in range(15):
            if not service.videos().list(part="id", id=item["old_video_id"]).execute().get("items"):
                state["old_confirmed_absent"] = True
                break
            time.sleep(2)
        if not state.get("old_confirmed_absent"):
            raise uploader.SafetyError(f"Delete sent but absence not confirmed: {item['old_video_id']}")
        state["state"] = "upload_started"
        state["publish_at"] = datetime.fromtimestamp(item["publish_at"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        save(args.report, report)
        new_id = upload_scheduled(service, item, report, state, args.report)
        verify_replacement(service, cfg, item, new_id)
        state["state"] = "verified_scheduled"
        state["readback_verified"] = True
        save(args.report, report)

    report["completed_utc"] = utc_now()
    report["successful"] = 17
    save(args.report, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
