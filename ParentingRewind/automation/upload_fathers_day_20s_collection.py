"""Idempotently publish the five authorized Father's Day Shorts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from youtube_auth import SafetyError, atomic_json, authorized_service


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
META_DIR = PROJECT / "metadata" / "fathers-day-20-second-shorts"
JOURNAL = HERE / "runtime" / "fathers-day-20s-upload-journal.json"
EXPECTED_CHANNEL_ID = "UCGb-IUQX2KQa_KA24MwE_aQ"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise SafetyError(f"Expected an object in {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def validate_local(metadata_path: Path) -> tuple[dict[str, Any], Path, Path]:
    metadata = load_json(metadata_path)
    youtube = metadata.get("youtube")
    output = metadata.get("output")
    if metadata.get("upload_authorized") is not True or not isinstance(youtube, dict) or not isinstance(output, dict):
        raise SafetyError(f"Upload is not explicitly authorized in {metadata_path}")
    if youtube.get("privacy") != "public" or youtube.get("made_for_kids") is not False or youtube.get("contains_synthetic_media") is not True:
        raise SafetyError(f"Unsafe YouTube status metadata in {metadata_path}")
    video = PROJECT / str(output["file"])
    thumbnail = PROJECT / str(youtube["thumbnail"])
    if not video.is_file() or not thumbnail.is_file():
        raise SafetyError(f"Missing video or thumbnail for {metadata_path}")
    if sha256(video) != output.get("sha256"):
        raise SafetyError(f"Video hash mismatch for {video}")
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
        "-of", "json", str(video),
    ], text=True))
    video_stream = next(item for item in probe["streams"] if item["codec_type"] == "video")
    audio_stream = next(item for item in probe["streams"] if item["codec_type"] == "audio")
    if abs(float(probe["format"]["duration"]) - 20.0) > 0.15:
        raise SafetyError(f"Unexpected duration for {video}")
    if video_stream.get("codec_name") != "h264" or video_stream.get("width") != 1080 or video_stream.get("height") != 1920:
        raise SafetyError(f"Unexpected video stream for {video}")
    if audio_stream.get("codec_name") != "aac" or audio_stream.get("sample_rate") != "48000" or audio_stream.get("channels") != 2:
        raise SafetyError(f"Unexpected audio stream for {video}")
    return metadata, video, thumbnail


def uploaded_titles(service: Any) -> dict[str, str]:
    channel = service.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    titles: dict[str, str] = {}
    token = None
    while True:
        response = service.playlistItems().list(part="snippet", playlistId=playlist, maxResults=50, pageToken=token).execute()
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            titles[str(snippet.get("title", ""))] = str(snippet.get("resourceId", {}).get("videoId", ""))
        token = response.get("nextPageToken")
        if not token:
            return titles


def readback(service: Any, video_id: str) -> dict[str, Any]:
    response = service.videos().list(part="snippet,status,processingDetails", id=video_id).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise SafetyError(f"Uploaded video {video_id} is not readable")
    return items[0]


def verify(service: Any, video_id: str, title: str) -> dict[str, Any]:
    item = readback(service, video_id)
    snippet, status = item.get("snippet", {}), item.get("status", {})
    if snippet.get("channelId") != EXPECTED_CHANNEL_ID or snippet.get("title") != title:
        raise SafetyError(f"Remote identity/title mismatch for {video_id}")
    if status.get("privacyStatus") != "public" or status.get("selfDeclaredMadeForKids") is not False:
        raise SafetyError(f"Remote audience/privacy mismatch for {video_id}")
    writable = {key: status[key] for key in ("privacyStatus", "license", "embeddable", "publicStatsViewable", "selfDeclaredMadeForKids") if key in status}
    writable["privacyStatus"] = "public"
    writable["selfDeclaredMadeForKids"] = False
    writable["containsSyntheticMedia"] = True
    updated = service.videos().update(part="status", body={"id": video_id, "status": writable}).execute()
    if updated.get("status", {}).get("containsSyntheticMedia") is not True:
        raise SafetyError(f"YouTube did not confirm synthetic-media disclosure for {video_id}")
    return readback(service, video_id)


def attempt_thumbnail(service: Any, video_id: str, thumbnail: Path) -> str:
    try:
        service.thumbnails().set(videoId=video_id, media_body=str(thumbnail)).execute()
        return "set"
    except HttpError as exc:
        if exc.resp.status == 403:
            return "forbidden-by-channel-permission"
        raise


def upload(service: Any, metadata: dict[str, Any], video: Path) -> str:
    youtube = metadata["youtube"]
    body = {
        "snippet": {
            "title": str(youtube["title"]),
            "description": str(youtube["description"]),
            "tags": [str(tag) for tag in youtube["tags"]],
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=False)
    response = None
    try:
        while response is None:
            _, response = request.next_chunk()
    finally:
        stream = media.stream()
        if stream and not stream.closed:
            stream.close()
    video_id = str((response or {}).get("id", ""))
    if not video_id:
        raise SafetyError("YouTube returned no video ID; reconcile remotely before retrying")
    return video_id


def main() -> int:
    service, channel = authorized_service()
    if channel.get("channel_id") != EXPECTED_CHANNEL_ID:
        raise SafetyError("Live OAuth channel is not the immutable Parenting Rewind target")
    journal = load_json(JOURNAL) if JOURNAL.exists() else {"channel_id": EXPECTED_CHANNEL_ID, "videos": {}}
    records = journal.setdefault("videos", {})
    titles = uploaded_titles(service)
    for metadata_path in sorted(META_DIR.glob("*.json")):
        metadata, video, thumbnail = validate_local(metadata_path)
        youtube = metadata["youtube"]
        slug = str(metadata["episode_id"])
        existing = records.get(slug, {})
        video_id = str(existing.get("video_id", ""))
        if not video_id:
            title_match = titles.get(str(youtube["title"]))
            if title_match:
                raise SafetyError(f"Exact title already exists without a journal entry: {youtube['title']} ({title_match})")
            video_id = upload(service, metadata, video)
            records[slug] = {
                "video_id": video_id,
                "url": f"https://youtu.be/{video_id}",
                "title": youtube["title"],
                "source_sha256": metadata["output"]["sha256"],
                "thumbnail_status": "not-attempted",
            }
            atomic_json(JOURNAL, journal)
        verify(service, video_id, str(youtube["title"]))
        if records[slug].get("thumbnail_status") == "not-attempted":
            records[slug]["thumbnail_status"] = attempt_thumbnail(service, video_id, thumbnail)
        records[slug]["remote_verified"] = True
        records[slug]["privacy"] = "public"
        records[slug]["made_for_kids"] = False
        records[slug]["contains_synthetic_media_confirmed"] = True
        atomic_json(JOURNAL, journal)
        metadata["published"] = True
        metadata["youtube"]["video_id"] = video_id
        metadata["youtube"]["url"] = f"https://youtu.be/{video_id}"
        metadata["youtube"]["thumbnail_status"] = records[slug]["thumbnail_status"]
        atomic_json(metadata_path, metadata)
        print(json.dumps(records[slug]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
