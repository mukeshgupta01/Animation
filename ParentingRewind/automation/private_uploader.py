"""Unattended, fail-closed uploader for Parenting Rewind."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

from googleapiclient.http import MediaFileUpload

from youtube_auth import SafetyError, authorized_service


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
CONFIG_PATH = HERE / "config.json"
METADATA_DIR = PROJECT / "metadata"
RUNTIME_DIR = HERE / "runtime"
LOG_DIR = HERE / "logs"
LEDGER_FILE = RUNTIME_DIR / "upload-ledger.jsonl"
ATTEMPTS_FILE = RUNTIME_DIR / "upload-attempts.json"
LATEST_REPORT = RUNTIME_DIR / "latest-upload-report.json"
LOG_FILE = LOG_DIR / "parenting-rewind-upload.log"


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("parenting-rewind-upload")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    return logger


LOGGER = setup_logging()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_text(value: datetime | None = None) -> str:
    return (value or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_object(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {} if default is None else default
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SafetyError(f"Expected a JSON object in {path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
    temporary.replace(path)


def config() -> dict[str, Any]:
    cfg = load_object(CONFIG_PATH)
    if cfg.get("channel_id") != "UCGb-IUQX2KQa_KA24MwE_aQ":
        raise SafetyError("Configured channel ID is not the immutable Parenting Rewind target.")
    if cfg.get("privacy_status") != "public":
        raise SafetyError("Uploader is authorized for public Parenting Rewind uploads only.")
    if cfg.get("made_for_kids") is not False:
        raise SafetyError("Parenting Rewind must be marked not made for kids.")
    if cfg.get("public_upload_authorized") is not True:
        raise SafetyError("Public upload authorization is not recorded in config.")
    if int(cfg.get("upload_interval_hours", 0)) != 5:
        raise SafetyError("Parenting Rewind upload interval must remain five hours.")
    return cfg


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def ledger_rows() -> list[dict[str, Any]]:
    if not LEDGER_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    with LEDGER_FILE.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SafetyError(f"Corrupt upload ledger line {number}: {exc}") from exc
            if not isinstance(row, dict):
                raise SafetyError(f"Invalid upload ledger line {number}")
            rows.append(row)
    return rows


def append_ledger(row: dict[str, Any]) -> None:
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_FILE.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


def active_upload_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_ids = {
        str(row.get("missing_video_id"))
        for row in rows
        if row.get("event") == "remote-video-missing" and row.get("missing_video_id")
    }
    return [
        row
        for row in rows
        if row.get("video_id") and str(row.get("video_id")) not in missing_ids
    ]


def source_directory(cfg: dict[str, Any]) -> Path | None:
    for raw in cfg.get("source_directories", []):
        candidate = Path(raw)
        if candidate.is_dir():
            return candidate
    return None


def natural_key(path: Path) -> list[Any]:
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", path.name)]


def output_basename(metadata: dict[str, Any]) -> str | None:
    output = metadata.get("output")
    if isinstance(output, dict) and output.get("file"):
        return Path(str(output["file"]).replace("\\", "/")).name
    return None


def metadata_index() -> dict[str, tuple[Path, dict[str, Any]]]:
    index: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(METADATA_DIR.glob("*.json")):
        data = load_object(path)
        names = {path.with_suffix(".mp4").name.casefold()}
        basename = output_basename(data)
        if basename:
            names.add(basename.casefold())
        for name in names:
            index[name] = (path, data)
    return index


def available_videos(folder: Path, rows: list[dict[str, Any]]) -> list[Path]:
    active_rows = active_upload_rows(rows)
    uploaded_hashes = {str(row.get("sha256", "")).upper() for row in active_rows}
    uploaded_names = {str(row.get("source_name", "")).casefold() for row in active_rows}
    now = time.time()
    candidates: list[Path] = []
    for path in folder.glob("*.mp4"):
        try:
            if not path.is_file() or path.stat().st_size <= 0:
                continue
            if now - path.stat().st_mtime < 300:
                continue
            if path.name.casefold() in uploaded_names:
                continue
            digest = sha256(path)
        except OSError as exc:
            LOGGER.warning("OneDrive file is not locally readable yet: %s (%s)", path, exc)
            continue
        if digest in uploaded_hashes:
            continue
        candidates.append(path)
    return sorted(candidates, key=natural_key)


def parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def cadence(rows: list[dict[str, Any]], cfg: dict[str, Any]) -> tuple[int, datetime | None]:
    successes = [row for row in active_upload_rows(rows) if row.get("uploaded_utc")]
    count = len(successes)
    hours = int(cfg["upload_interval_hours"])
    if count == 0:
        return hours, None
    return hours, parse_utc(successes[-1]["uploaded_utc"]) + timedelta(hours=hours)


def common_tags(title: str) -> list[str]:
    tags = [
        "Parenting Rewind",
        "parenting tips",
        "positive parenting",
        "calm parenting",
        "parenting advice",
        "positive discipline",
        "parent child communication",
        "family communication",
        "say this instead",
    ]
    topic = title.split("|")[0].strip()
    if topic and topic.casefold() not in {item.casefold() for item in tags}:
        tags.insert(1, topic)
    return tags


def research_urls(metadata: dict[str, Any]) -> list[str]:
    research = metadata.get("research")
    if not isinstance(research, dict):
        return []
    sources: list[dict[str, Any]] = []
    if isinstance(research.get("source"), dict):
        sources.append(research["source"])
    if isinstance(research.get("sources"), list):
        sources.extend(item for item in research["sources"] if isinstance(item, dict))
    return [str(item["url"]) for item in sources if item.get("url")]


def description_for(title: str, metadata: dict[str, Any]) -> str:
    supplied = metadata.get("description")
    if isinstance(supplied, str) and supplied.strip():
        return supplied.strip()
    topic = title.split("|")[0].strip()
    narration = metadata.get("narration")
    transcript = narration.get("transcript", "") if isinstance(narration, dict) else ""
    parts = [
        f"Parenting moments can escalate quickly. In this Parenting Rewind episode, we revisit {topic.lower()} and share a calmer, clearer response to try next time.",
    ]
    if isinstance(transcript, str) and transcript.strip():
        parts.extend(["", "What this episode covers:", transcript.strip()])
    parts.extend([
        "",
        "Pause. Rewind. Repair.",
        "",
        "Subscribe for practical parenting ideas and calmer ways to reconnect after difficult moments.",
        "",
        "This video provides general parenting education, not personalised therapy, diagnosis or medical advice. Every child and family is different.",
    ])
    urls = research_urls(metadata)
    if urls:
        parts.extend(["", "Research basis:", *urls])
    return "\n".join(parts)[:5000]


def upload_metadata(video: Path, cfg: dict[str, Any]) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    indexed = metadata_index()
    match = indexed.get(video.name.casefold())
    if match is None and video.name.casefold().startswith("parenting-rewind-"):
        match = indexed.get(video.name[len("parenting-rewind-"):].casefold())
    if match is None:
        raise SafetyError(f"No project metadata matches {video.name}; refusing a generic upload.")
    metadata_path, metadata = match
    title = str(metadata.get("title", "")).strip()
    if not title or len(title) > 100:
        raise SafetyError(f"Missing or invalid YouTube title in {metadata_path.name}")
    tags = metadata.get("tags")
    if not isinstance(tags, list) or not tags:
        tags = common_tags(title)
    body = {
        "snippet": {
            "title": title,
            "description": description_for(title, metadata),
            "tags": [str(item) for item in tags],
            "categoryId": str(cfg["category_id"]),
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    return body, metadata_path, metadata


def ffprobe_ok(video: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(video)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and "video" in result.stdout


def recent_video_with_title(service: Any, title: str) -> dict[str, str] | None:
    channel = service.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    response = service.playlistItems().list(part="snippet", playlistId=uploads, maxResults=50).execute()
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        if snippet.get("title") == title:
            return {
                "video_id": snippet["resourceId"]["videoId"],
                "title": title,
            }
    return None


def youtube_video(service: Any, video_id: str) -> dict[str, Any] | None:
    response = service.videos().list(part="snippet,status", id=video_id).execute()
    items = response.get("items", [])
    return items[0] if items else None


def upload_one(service: Any, video: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    body, metadata_path, metadata = upload_metadata(video, cfg)
    digest = sha256(video)
    expected_hash = metadata.get("output", {}).get("sha256") if isinstance(metadata.get("output"), dict) else None
    if expected_hash and str(expected_hash).upper() != digest:
        raise SafetyError(f"SHA-256 mismatch for {video.name}; refusing to upload altered content.")
    attempts = load_object(ATTEMPTS_FILE)
    previous = attempts.get(digest)
    if isinstance(previous, dict) and previous.get("status") == "started":
        existing = recent_video_with_title(service, body["snippet"]["title"])
        if existing:
            row = {
                "uploaded_utc": previous.get("started_utc", utc_text()),
                "source_name": video.name,
                "source_path": str(video),
                "metadata_path": str(metadata_path),
                "sha256": digest,
                "video_id": existing["video_id"],
                "youtube_url": f"https://youtu.be/{existing['video_id']}",
                "title": existing["title"],
                "privacy_status": "public",
                "made_for_kids": False,
                "reconciled_after_interrupted_attempt": True,
            }
            append_ledger(row)
            attempts[digest] = {**previous, "status": "reconciled", "video_id": existing["video_id"]}
            atomic_json(ATTEMPTS_FILE, attempts)
            return row
        raise SafetyError("Unresolved prior attempt was not found in recent uploads; manual review is required.")
    attempts[digest] = {
        "status": "started",
        "source_name": video.name,
        "title": body["snippet"]["title"],
        "started_utc": utc_text(),
    }
    atomic_json(ATTEMPTS_FILE, attempts)
    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True)
    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
        notifySubscribers=False,
    )
    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                LOGGER.info("Upload progress %s: %.1f%%", video.name, status.progress() * 100)
    finally:
        stream = media.stream()
        if stream and not stream.closed:
            stream.close()
    video_id = response.get("id")
    if not video_id:
        raise SafetyError("YouTube completed the request without returning a video ID.")
    row = {
        "uploaded_utc": utc_text(),
        "source_name": video.name,
        "source_path": str(video),
        "metadata_path": str(metadata_path),
        "sha256": digest,
        "video_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}",
        "title": body["snippet"]["title"],
        "privacy_status": "public",
        "made_for_kids": False,
    }
    append_ledger(row)
    attempts[digest] = {**attempts[digest], "status": "succeeded", "video_id": video_id}
    atomic_json(ATTEMPTS_FILE, attempts)
    return row


def report(action: str) -> dict[str, Any]:
    return {
        "action": action,
        "started_utc": utc_text(),
        "attempted": 0,
        "successful": 0,
        "failures": [],
    }


def finish(value: dict[str, Any], path: Path = LATEST_REPORT) -> None:
    value["finished_utc"] = utc_text()
    atomic_json(path, value)
    print(json.dumps(value, indent=2, sort_keys=True))


def run(dry_run: bool, confirm_upload: bool) -> int:
    cfg = config()
    rows = ledger_rows()
    value = report("dry-run" if dry_run else "scheduled-public-upload")
    folder = source_directory(cfg)
    value["source_directory"] = str(folder) if folder else None
    value["uploaded_total"] = len(active_upload_rows(rows))
    hours, next_due = cadence(rows, cfg)
    value["current_interval_hours"] = hours
    value["next_due_utc"] = utc_text(next_due) if next_due else None
    if folder is None:
        value["status"] = "waiting-for-onedrive-folder"
        finish(value)
        return 0
    candidates = available_videos(folder, rows)
    value["remaining_upload_count"] = len(candidates)
    value["next_video"] = candidates[0].name if candidates else None
    if not candidates:
        value["status"] = "queue-empty"
        finish(value)
        return 0
    if next_due and utc_now() < next_due:
        value["status"] = "waiting-for-cadence"
        finish(value)
        return 0
    body, metadata_path, _ = upload_metadata(candidates[0], cfg)
    value["next_title"] = body["snippet"]["title"]
    value["metadata_path"] = str(metadata_path)
    if dry_run:
        value["status"] = "ready"
        finish(value)
        return 0
    if not confirm_upload:
        raise SafetyError("Real upload blocked: --confirm-public-upload is required.")
    video = candidates[0]
    if not ffprobe_ok(video):
        raise SafetyError(f"FFprobe validation failed for {video}")
    service, channel = authorized_service()
    value["verified_channel"] = channel
    value["attempted"] = 1
    value["video_name"] = video.name
    try:
        result = upload_one(service, video, cfg)
        value["successful"] = 1
        value["result"] = result
        value["status"] = "uploaded-public"
        remaining = available_videos(folder, ledger_rows())
        value["remaining_upload_count"] = len(remaining)
        _, following_due = cadence(ledger_rows(), cfg)
        value["next_due_utc"] = utc_text(following_due) if following_due else None
        finish(value)
        return 0
    except Exception as exc:
        LOGGER.exception("Upload failed for %s", video.name)
        value["status"] = "failed"
        value["failures"].append({"video_name": video.name, "error": str(exc)})
        finish(value)
        return 1


def reupload_missing(source_name: str, confirm_upload: bool) -> int:
    cfg = config()
    rows = ledger_rows()
    value = report("verified-missing-reupload")
    folder = source_directory(cfg)
    value["source_directory"] = str(folder) if folder else None
    if folder is None:
        raise SafetyError("OneDrive source folder is unavailable.")
    video = folder / source_name
    if not video.is_file() or video.stat().st_size <= 0:
        raise SafetyError(f"Requested source is unavailable: {source_name}")
    digest = sha256(video)
    prior_rows = [
        row
        for row in active_upload_rows(rows)
        if row.get("source_name") == source_name or str(row.get("sha256", "")).upper() == digest
    ]
    if len(prior_rows) != 1:
        raise SafetyError(
            f"Recovery requires exactly one active ledger match; found {len(prior_rows)}."
        )
    prior = prior_rows[0]
    prior_video_id = str(prior["video_id"])
    value["prior_video_id"] = prior_video_id
    if not confirm_upload:
        raise SafetyError("Recovery upload blocked: --confirm-public-upload is required.")
    if not ffprobe_ok(video):
        raise SafetyError(f"FFprobe validation failed for {video}")
    service, channel = authorized_service()
    value["verified_channel"] = channel
    if youtube_video(service, prior_video_id) is not None:
        raise SafetyError(
            f"Recorded video {prior_video_id} still exists on YouTube; refusing a duplicate upload."
        )
    value["attempted"] = 1
    value["video_name"] = video.name
    try:
        result = upload_one(service, video, cfg)
        append_ledger({
            "event": "remote-video-missing",
            "verified_utc": utc_text(),
            "missing_video_id": prior_video_id,
            "replacement_video_id": result["video_id"],
            "source_name": video.name,
            "sha256": digest,
        })
        value["successful"] = 1
        value["result"] = result
        value["status"] = "reuploaded-public-after-remote-missing"
        value["uploaded_total"] = len(active_upload_rows(ledger_rows()))
        _, following_due = cadence(ledger_rows(), cfg)
        value["next_due_utc"] = utc_text(following_due) if following_due else None
        finish(value)
        return 0
    except Exception as exc:
        LOGGER.exception("Recovery upload failed for %s", video.name)
        value["status"] = "failed"
        value["failures"].append({"video_name": video.name, "error": str(exc)})
        finish(value)
        return 1


def manual_batch(max_uploads: int, confirm_upload: bool) -> int:
    if max_uploads < 1 or max_uploads > 12:
        raise SafetyError("Manual batch size must be between 1 and 12.")
    cfg = config()
    rows = ledger_rows()
    value = report("explicit-manual-public-batch")
    folder = source_directory(cfg)
    value["source_directory"] = str(folder) if folder else None
    value["uploaded_total_before"] = len(active_upload_rows(rows))
    if folder is None:
        raise SafetyError("OneDrive source folder is unavailable.")
    videos = available_videos(folder, rows)[:max_uploads]
    if len(videos) != max_uploads:
        raise SafetyError(
            f"Requested {max_uploads} uploads but only {len(videos)} validated candidates are available."
        )
    value["planned_videos"] = [video.name for video in videos]
    value["results"] = []
    value["email_report_paths"] = []
    for video in videos:
        upload_metadata(video, cfg)
        if not ffprobe_ok(video):
            raise SafetyError(f"FFprobe validation failed for {video}")
    if not confirm_upload:
        raise SafetyError("Manual batch blocked: --confirm-public-upload is required.")
    service, channel = authorized_service()
    value["verified_channel"] = channel
    for video in videos:
        value["attempted"] += 1
        value["video_name"] = video.name
        try:
            result = upload_one(service, video, cfg)
            value["successful"] += 1
            value["results"].append(result)
            email_report = RUNTIME_DIR / f"manual-upload-{result['video_id']}-email-report.json"
            email_value = {
                "action": "explicit-manual-public-batch",
                "started_utc": value["started_utc"],
                "finished_utc": utc_text(),
                "attempted": 1,
                "successful": 1,
                "remaining_upload_count": len(available_videos(folder, ledger_rows())),
                "next_due_utc": None,
                "result": result,
            }
            atomic_json(email_report, email_value)
            value["email_report_paths"].append(str(email_report))
            value["status"] = "manual-public-batch-in-progress"
            atomic_json(LATEST_REPORT, {**value, "finished_utc": utc_text()})
        except Exception as exc:
            LOGGER.exception("Manual batch stopped after failure for %s", video.name)
            value["status"] = "failed"
            value["failures"].append({"video_name": video.name, "error": str(exc)})
            finish(value)
            return 1
    remaining = available_videos(folder, ledger_rows())
    value["remaining_upload_count"] = len(remaining)
    value["uploaded_total"] = len(active_upload_rows(ledger_rows()))
    _, following_due = cadence(ledger_rows(), cfg)
    value["next_due_utc"] = utc_text(following_due) if following_due else None
    for email_path_text in value["email_report_paths"]:
        email_path = Path(email_path_text)
        email_value = load_object(email_path)
        email_value["remaining_upload_count"] = len(remaining)
        email_value["next_due_utc"] = value["next_due_utc"]
        atomic_json(email_path, email_value)
    value["status"] = "uploaded-public-batch"
    finish(value)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dry-run")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--confirm-public-upload", action="store_true")
    recovery_parser = sub.add_parser("reupload-missing")
    recovery_parser.add_argument("--source-name", required=True)
    recovery_parser.add_argument("--confirm-public-upload", action="store_true")
    batch_parser = sub.add_parser("manual-batch")
    batch_parser.add_argument("--max-uploads", type=int, required=True)
    batch_parser.add_argument("--confirm-public-upload", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "reupload-missing":
            return reupload_missing(args.source_name, args.confirm_public_upload)
        if args.command == "manual-batch":
            return manual_batch(args.max_uploads, args.confirm_public_upload)
        return run(args.command == "dry-run", getattr(args, "confirm_public_upload", False))
    except Exception as exc:
        LOGGER.exception("Uploader stopped safely")
        value = report(args.command)
        value["status"] = "failed-safely"
        value["failures"].append({"error": str(exc)})
        finish(value)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
