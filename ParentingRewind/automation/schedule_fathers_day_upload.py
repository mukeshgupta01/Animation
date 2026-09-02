"""Upload the approved Father's Day master once and schedule its public release."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from youtube_auth import SafetyError, authorized_service, atomic_json


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
VIDEO = PROJECT / "output" / "parenting-rewind-redesign-86-fathers-day-dads-who-show-up-v1.mp4"
METADATA = PROJECT / "metadata" / "parenting-rewind-redesign-86-fathers-day-dads-who-show-up-v1.json"
THUMBNAIL = PROJECT / "production-work" / "redesigned-bundle-2026-08-23" / "parenting-rewind-redesign-86-fathers-day-dads-who-show-up" / "thumbnail.jpg"
JOURNAL = HERE / "runtime" / "fathers-day-2026-scheduled-upload.json"
EXPECTED_CHANNEL_ID = "UCGb-IUQX2KQa_KA24MwE_aQ"
EXPECTED_SHA256 = "21955C694EFC751E1E31D04733C3E949657C26B02AE8B3AEABC9F2F3309675F7"
PUBLISH_AT_UTC = "2026-09-04T10:00:00Z"  # 8:00 PM Australia/Sydney.


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SafetyError(f"Expected a JSON object in {path}")
    return value


def validate_local_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    if datetime.now(timezone.utc) >= datetime.strptime(PUBLISH_AT_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc):
        raise SafetyError("The authorized Father's Day publication time is no longer in the future.")
    if not VIDEO.is_file() or not THUMBNAIL.is_file() or not METADATA.is_file():
        raise SafetyError("The approved master, metadata or thumbnail is missing.")
    digest = sha256(VIDEO)
    if digest != EXPECTED_SHA256:
        raise SafetyError(f"Approved master hash mismatch: {digest}")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,width,height", "-of", "json", str(VIDEO)],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise SafetyError("FFprobe rejected the approved master.")
    streams = json.loads(probe.stdout).get("streams", [])
    if not streams or streams[0].get("codec_name") != "h264" or streams[0].get("width") != 1080 or streams[0].get("height") != 1920:
        raise SafetyError("Approved master is not the expected 1080x1920 H.264 video.")
    metadata = load_json(METADATA)
    if metadata.get("upload_authorized") is not True:
        raise SafetyError("Metadata does not record explicit upload authorization.")
    schedule = metadata.get("scheduled_publication")
    if not isinstance(schedule, dict) or schedule.get("publish_at_utc") != PUBLISH_AT_UTC:
        raise SafetyError("Metadata does not record the exact authorized publication time.")
    youtube = metadata.get("youtube")
    if not isinstance(youtube, dict) or youtube.get("upload_authorized") is not True:
        raise SafetyError("YouTube metadata does not record explicit upload authorization.")
    return metadata, youtube


def readback(service: Any, video_id: str) -> dict[str, Any]:
    response = service.videos().list(part="snippet,status,contentDetails", id=video_id).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise SafetyError(f"Scheduled video {video_id} is not readable from the locked channel.")
    return items[0]


def require_no_existing_title(service: Any, title: str) -> None:
    channel = service.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    response = service.playlistItems().list(part="snippet", playlistId=uploads, maxResults=50).execute()
    matches = [
        item["snippet"]["resourceId"]["videoId"]
        for item in response.get("items", [])
        if item.get("snippet", {}).get("title") == title
    ]
    if matches:
        raise SafetyError(f"An exact-title video already exists on Parenting Rewind: {matches}")


def verify_remote(item: dict[str, Any], title: str) -> None:
    snippet = item.get("snippet", {})
    status = item.get("status", {})
    if snippet.get("channelId") != EXPECTED_CHANNEL_ID or snippet.get("title") != title:
        raise SafetyError("Scheduled upload read-back did not match the locked channel and title.")
    if status.get("privacyStatus") != "private" or status.get("publishAt") != PUBLISH_AT_UTC:
        raise SafetyError("YouTube did not preserve the private scheduled-publication state.")
    if status.get("selfDeclaredMadeForKids") is not False:
        raise SafetyError("YouTube audience read-back is not explicitly not-made-for-kids.")


def confirm_ai_disclosure(service: Any, item: dict[str, Any]) -> bool:
    current = item.get("status", {})
    keep = ("privacyStatus", "license", "embeddable", "publicStatsViewable", "selfDeclaredMadeForKids")
    writable = {key: current[key] for key in keep if key in current}
    writable["privacyStatus"] = "private"
    writable["publishAt"] = PUBLISH_AT_UTC
    writable["selfDeclaredMadeForKids"] = False
    writable["containsSyntheticMedia"] = True
    response = service.videos().update(part="status", body={"id": item["id"], "status": writable}).execute()
    if response.get("status", {}).get("containsSyntheticMedia") is not True:
        raise SafetyError("YouTube did not API-confirm the altered/synthetic-media disclosure.")
    return True


def attempt_thumbnail(service: Any, video_id: str, journal: dict[str, Any]) -> None:
    if journal.get("thumbnail_attempted") is True:
        return
    journal["thumbnail_attempted"] = True
    try:
        service.thumbnails().set(videoId=video_id, media_body=str(THUMBNAIL)).execute()
        journal["thumbnail_set"] = True
        journal["thumbnail_status"] = "set"
    except HttpError as exc:
        if exc.resp.status != 403:
            raise
        journal["thumbnail_set"] = False
        journal["thumbnail_status"] = "forbidden-by-channel-permission"
    atomic_json(JOURNAL, journal)


def body(youtube: dict[str, Any]) -> dict[str, Any]:
    return {
        "snippet": {
            "title": str(youtube["title"]),
            "description": str(youtube["description"]),
            "tags": [str(tag) for tag in youtube["tags"]],
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": PUBLISH_AT_UTC,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }


def main() -> int:
    _, youtube = validate_local_inputs()
    service, channel = authorized_service()
    if channel.get("channel_id") != EXPECTED_CHANNEL_ID:
        raise SafetyError("Live OAuth channel differs from the immutable Parenting Rewind target.")

    if JOURNAL.exists():
        journal = load_json(JOURNAL)
        video_id = str(journal.get("video_id", ""))
        if not video_id:
            raise SafetyError("Existing scheduling journal has no video ID; manual reconciliation is required.")
        item = readback(service, video_id)
        verify_remote(item, str(youtube["title"]))
        journal["contains_synthetic_media_api_confirmed"] = confirm_ai_disclosure(service, item)
        item = readback(service, video_id)
        verify_remote(item, str(youtube["title"]))
        journal["remote_readback_verified"] = True
        attempt_thumbnail(service, video_id, journal)
        atomic_json(JOURNAL, journal)
        print(json.dumps({"status": "already-scheduled-and-verified", **journal}, indent=2))
        return 0

    upload_body = body(youtube)
    require_no_existing_title(service, str(upload_body["snippet"]["title"]))
    media = MediaFileUpload(str(VIDEO), chunksize=8 * 1024 * 1024, resumable=True)
    request = service.videos().insert(
        part="snippet,status",
        body=upload_body,
        media_body=media,
        notifySubscribers=False,
    )
    response = None
    try:
        while response is None:
            _, response = request.next_chunk()
    finally:
        stream = media.stream()
        if stream and not stream.closed:
            stream.close()
    video_id = str(response.get("id", ""))
    if not video_id:
        raise SafetyError("YouTube did not return a video ID; manual reconciliation is required before any retry.")

    journal = {
        "video_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}",
        "title": upload_body["snippet"]["title"],
        "source_sha256": EXPECTED_SHA256,
        "channel_id": EXPECTED_CHANNEL_ID,
        "privacy_status": "private",
        "publish_at_utc": PUBLISH_AT_UTC,
        "publish_at_sydney": "2026-09-04T20:00:00+10:00",
        "made_for_kids": False,
        "contains_synthetic_media_requested": True,
        "thumbnail_set": False,
    }
    atomic_json(JOURNAL, journal)
    item = readback(service, video_id)
    verify_remote(item, str(youtube["title"]))
    journal["contains_synthetic_media_api_confirmed"] = confirm_ai_disclosure(service, item)
    item = readback(service, video_id)
    verify_remote(item, str(youtube["title"]))
    journal["remote_readback_verified"] = True
    attempt_thumbnail(service, video_id, journal)
    atomic_json(JOURNAL, journal)
    print(json.dumps({"status": "scheduled-and-verified", **journal}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
