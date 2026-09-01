"""Fail-closed YouTube uploader for the Tiny Tales local queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
from typing import Any

from PIL import Image


HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
CLIENT_SECRET = HERE / "secrets" / "youtube-client-secret.json"
TOKEN_FILE = HERE / "runtime" / "youtube-oauth-token.json"
CHANNEL_LOCK = HERE / "runtime" / "youtube-channel-lock.json"
LEDGER_FILE = HERE / "runtime" / "upload-ledger.jsonl"
ATTEMPTS_FILE = HERE / "runtime" / "upload-attempts.json"
THUMBNAIL_LEDGER_FILE = HERE / "runtime" / "thumbnail-upload-ledger.jsonl"
THUMBNAIL_RETRY_FILE = HERE / "runtime" / "thumbnail-retry-state.json"
LOG_FILE = HERE / "logs" / "youtube-upload.log"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class SafetyError(RuntimeError):
    pass


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def setup_logging() -> logging.Logger:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("tiny-tales-upload")
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


def config() -> dict[str, Any]:
    value = load_json(CONFIG_PATH)
    if not isinstance(value, dict):
        raise SafetyError(f"Invalid configuration: {CONFIG_PATH}")
    if value.get("privacy_status") not in {"private", "public"}:
        raise SafetyError("Automation configuration must use private or public visibility")
    if value.get("made_for_kids") is not True:
        raise SafetyError("Automation configuration must mark videos made for kids")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ledger_rows() -> list[dict[str, Any]]:
    if not LEDGER_FILE.exists():
        return []
    rows = []
    with LEDGER_FILE.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SafetyError(f"Corrupt upload ledger line {number}: {exc}") from exc
    return rows


def append_ledger(row: dict[str, Any]) -> None:
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_FILE.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def ffprobe_ok(path: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and "video" in result.stdout


def full_decode_ok(path: Path) -> bool:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        LOGGER.error("Full FFmpeg decode failed for %s: %s", path.name, result.stderr.strip())
    return result.returncode == 0


def evidence_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise SafetyError(f"Future-video quality evidence is missing path field {field!r}")
    path = (HERE.parent / value).resolve()
    try:
        path.relative_to(HERE.parent.resolve())
    except ValueError as exc:
        raise SafetyError(f"Quality evidence path escapes Tiny Tales: {value}") from exc
    if not path.is_file() or path.stat().st_size == 0:
        raise SafetyError(f"Quality evidence file is missing or empty: {path}")
    return path


def validate_future_quality_evidence(video: Path, cfg: dict[str, Any]) -> None:
    cutoff = int(cfg.get("quality_evidence_required_after_unix", 0))
    if video.stat().st_mtime <= cutoff:
        return
    sidecar = video.with_suffix(".json")
    metadata = load_json(sidecar, {})
    if not isinstance(metadata, dict):
        raise SafetyError(f"Future-video metadata is invalid: {sidecar}")
    required_flags = (
        "quality_gate_passed",
        "full_decode_passed",
        "transition_audit_passed",
        "transition_contact_sheet_reviewed",
    )
    missing_flags = [field for field in required_flags if metadata.get(field) is not True]
    if missing_flags:
        raise SafetyError(
            "Future video is blocked until quality evidence is explicitly passed: "
            + ", ".join(missing_flags)
        )
    report_path = evidence_path(metadata.get("quality_report"), "quality_report")
    audit_path = evidence_path(metadata.get("transition_audit"), "transition_audit")
    evidence_path(metadata.get("quality_contact_sheet"), "quality_contact_sheet")
    evidence_path(metadata.get("transition_contact_sheet"), "transition_contact_sheet")
    report = load_json(report_path, {})
    if report.get("passed") is not True:
        raise SafetyError(f"Producer quality report did not pass: {report_path}")
    checks = report.get("checks", {})
    if checks.get("continuous_visual_timeline") is not True:
        raise SafetyError(f"Producer did not prove a continuous visual timeline: {report_path}")
    if checks.get("end_card_is_final_event_only") is not True:
        raise SafetyError(f"Producer did not prove final-card placement: {report_path}")
    audit = load_json(audit_path, None)
    if not isinstance(audit, list) or not audit:
        raise SafetyError(f"Transition audit is invalid: {audit_path}")
    if any(abs(float(item.get("gap_seconds", 1))) > 0.000001 for item in audit):
        raise SafetyError(f"Transition audit contains an uncovered or overlapping interval: {audit_path}")

    semantic_cutoff = int(cfg.get("semantic_motion_required_after_unix", 0))
    if video.stat().st_mtime <= semantic_cutoff:
        return
    semantic_flags = (
        "semantic_motion_reviewed",
        "character_continuity_reviewed",
        "primary_action_motion_reviewed",
        "actual_motion_not_camera_only",
    )
    missing_semantic_flags = [field for field in semantic_flags if metadata.get(field) is not True]
    if missing_semantic_flags:
        raise SafetyError(
            "Video is blocked until meaningful motion and continuity are explicitly reviewed: "
            + ", ".join(missing_semantic_flags)
        )
    semantic_path = evidence_path(metadata.get("semantic_motion_audit"), "semantic_motion_audit")
    evidence_path(metadata.get("semantic_motion_contact_sheet"), "semantic_motion_contact_sheet")
    semantic = load_json(semantic_path, None)
    if not isinstance(semantic, list) or not semantic:
        raise SafetyError(f"Semantic-motion audit is invalid: {semantic_path}")
    required_scene_fields = (
        "scene",
        "primary_action",
        "visible_start_state",
        "visible_action_state",
        "visible_end_state",
        "foreground_moving_elements",
    )
    for scene in semantic:
        if not isinstance(scene, dict) or any(not scene.get(field) for field in required_scene_fields):
            raise SafetyError(f"Semantic-motion audit has an incomplete scene: {semantic_path}")
        if scene.get("camera_only") is not False:
            raise SafetyError(f"Camera-only scene is unacceptable: {semantic_path}")
        if scene.get("character_and_object_continuity") is not True:
            raise SafetyError(f"Character/object continuity failed: {semantic_path}")
        if scene.get("reviewed") is not True:
            raise SafetyError(f"Semantic-motion scene lacks explicit review: {semantic_path}")


def prepared_thumbnail_for(video: Path, cfg: dict[str, Any]) -> Path | None:
    metadata = load_json(video.with_suffix(".json"), {})
    if not isinstance(metadata, dict):
        raise SafetyError(f"Video metadata is invalid: {video.with_suffix('.json')}")
    value = metadata.get("prepared_thumbnail")
    if not value:
        if cfg.get("custom_thumbnail_required") is True:
            raise SafetyError(f"Upload blocked until a reviewed custom thumbnail is prepared: {video.name}")
        return None
    if metadata.get("thumbnail_reviewed") is not True or not metadata.get("thumbnail_hook"):
        raise SafetyError(f"Prepared thumbnail lacks explicit visual review or hook metadata: {video.name}")
    path = evidence_path(value, "prepared_thumbnail")
    if path.stat().st_size > 2_000_000:
        raise SafetyError(f"Prepared thumbnail exceeds YouTube's 2 MB limit: {path}")
    with Image.open(path) as image:
        if image.format != "JPEG" or image.size != (1280, 720):
            raise SafetyError(f"Prepared thumbnail must be a 1280x720 JPEG: {path}")
    return path


def queue_files(cfg: dict[str, Any]) -> list[Path]:
    pending = HERE / cfg["pending_directory"]
    pending.mkdir(parents=True, exist_ok=True)
    uploaded_hashes = {row.get("sha256") for row in ledger_rows() if row.get("video_id")}
    eligible = []
    now = time.time()
    for path in pending.glob("*.mp4"):
        if not path.is_file() or path.stat().st_size == 0:
            continue
        if now - path.stat().st_mtime < int(cfg["minimum_file_age_seconds"]):
            continue
        digest = sha256(path)
        if digest in uploaded_hashes:
            LOGGER.warning("Duplicate content excluded: %s", path.name)
            continue
        try:
            prepared_thumbnail_for(path, cfg)
        except SafetyError as exc:
            LOGGER.warning("Upload queue item excluded: %s", exc)
            continue
        eligible.append(path)
    order = cfg.get("upload_queue_order", "oldest_first")
    if order == "newest_first":
        return sorted(eligible, key=lambda item: (-item.stat().st_mtime, item.name.casefold()))
    if order == "oldest_first":
        return sorted(eligible, key=lambda item: (item.stat().st_mtime, item.name.casefold()))
    raise SafetyError(f"Unsupported upload_queue_order: {order!r}")


def import_google() -> tuple[Any, Any, Any, Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise SafetyError(
            "Google API dependencies are missing. Install automation/requirements.txt into the project virtual environment."
        ) from exc
    return Request, Credentials, InstalledAppFlow, build, MediaFileUpload


def channel_from_service(service: Any) -> dict[str, str]:
    response = service.channels().list(part="id,snippet", mine=True).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise SafetyError(f"OAuth identity returned {len(items)} owned channels; expected exactly one")
    return {"channel_id": items[0]["id"], "channel_name": items[0]["snippet"]["title"]}


def validate_channel(actual: dict[str, str], cfg: dict[str, Any]) -> None:
    if actual["channel_id"] != cfg["channel_id"]:
        raise SafetyError(
            "WRONG CHANNEL: OAuth authorized "
            f"{actual['channel_name']} ({actual['channel_id']}), expected "
            f"{cfg['channel_name']} ({cfg['channel_id']}). Token and channel lock were not changed. "
            "Repeat interactive OAuth and select the Google/Brand Account identity that owns the expected channel."
        )


def write_channel_lock(actual: dict[str, str]) -> None:
    expected = {**actual, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if CHANNEL_LOCK.exists():
        current = load_json(CHANNEL_LOCK)
        if current.get("channel_id") != actual["channel_id"]:
            raise SafetyError("Existing immutable channel lock differs; refusing to replace it")
        return
    CHANNEL_LOCK.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(CHANNEL_LOCK, flags)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(expected, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(CHANNEL_LOCK, stat.S_IREAD)


def interactive_oauth(cfg: dict[str, Any]) -> dict[str, str]:
    if not CLIENT_SECRET.exists():
        raise SafetyError(f"OAuth desktop-client JSON is missing: {CLIENT_SECRET}")
    _, _, InstalledAppFlow, build, _ = import_google()
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    credentials = flow.run_local_server(port=0, open_browser=True, prompt="select_account consent")
    service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    actual = channel_from_service(service)
    validate_channel(actual, cfg)
    write_channel_lock(actual)
    atomic_json(TOKEN_FILE, json.loads(credentials.to_json()))
    LOGGER.info("OAuth verified for %s (%s)", actual["channel_name"], actual["channel_id"])
    return actual


def authorized_service(cfg: dict[str, Any]) -> tuple[Any, dict[str, str]]:
    if not TOKEN_FILE.exists():
        raise SafetyError("OAuth token is missing; scheduled runs never open an interactive browser")
    if not CHANNEL_LOCK.exists():
        raise SafetyError("Immutable channel lock is missing")
    lock = load_json(CHANNEL_LOCK)
    if lock.get("channel_id") != cfg["channel_id"]:
        raise SafetyError("Immutable channel lock does not match configured target; uploads disabled")
    Request, Credentials, _, build, _ = import_google()
    credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        atomic_json(TOKEN_FILE, json.loads(credentials.to_json()))
    if not credentials.valid:
        raise SafetyError("OAuth token is invalid and cannot be refreshed; interactive reauthorization is required")
    service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    actual = channel_from_service(service)
    validate_channel(actual, cfg)
    if lock.get("channel_id") != actual["channel_id"]:
        raise SafetyError("Authorized channel differs from immutable channel lock; uploads disabled")
    return service, actual


def metadata_for(video: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    sidecar = video.with_suffix(".json")
    supplied = load_json(sidecar, {})
    title = supplied.get("title", video.stem.replace("-", " ").replace("_", " ").title())
    if len(title) > 100:
        raise SafetyError(f"YouTube title exceeds 100 characters: {video.name}")
    return {
        "snippet": {
            "title": title,
            "description": supplied.get("description", ""),
            "tags": supplied.get("tags", []),
            "categoryId": str(supplied.get("category_id", cfg["category_id"])),
        },
        "status": {
            "privacyStatus": cfg["privacy_status"],
            "selfDeclaredMadeForKids": True,
        },
    }


def classify_http_error(exc: Exception) -> str:
    text = str(exc)
    lowered = text.casefold()
    if "uploadlimitexceeded" in lowered or "dailylimitexceeded" in lowered:
        return "YouTube daily upload limit exceeded"
    if "quotaexceeded" in lowered or "dailylimitexceededunreg" in lowered:
        return "YouTube API quota/daily limit exceeded"
    return text


def is_safely_retryable_upload_error(exc: Exception) -> bool:
    """Return true only when YouTube definitely rejected the insert request.

    A lost response after a completed insert could otherwise create a duplicate.
    Quota/upload-limit responses do not create a video and are safe to retry.
    """
    lowered = str(exc).casefold()
    quota_markers = (
        "uploadlimitexceeded",
        "dailylimitexceeded",
        "quotaexceeded",
        "quota exceeded",
        "video uploads per day",
    )
    return any(marker in lowered for marker in quota_markers)


def set_custom_thumbnail_record(
    service: Any,
    video_id: str,
    thumbnail: Path,
    title: str | None,
    source_name: str,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    _, _, _, _, MediaFileUpload = import_google()
    response = service.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(str(thumbnail), mimetype="image/jpeg", resumable=False),
    ).execute()
    if not response.get("items"):
        raise SafetyError(f"YouTube did not confirm the prepared thumbnail for {video_id}")
    row = {
        "video_id": video_id,
        "title": title,
        "sha256": sha256(thumbnail),
        "uploaded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "channel_id": cfg["channel_id"],
        "source_name": source_name,
        "prepared_thumbnail": str(thumbnail),
    }
    THUMBNAIL_LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with THUMBNAIL_LEDGER_FILE.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
    return row


def set_custom_thumbnail(service: Any, video_id: str, video: Path, thumbnail: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    metadata = load_json(video.with_suffix(".json"), {})
    return set_custom_thumbnail_record(
        service,
        video_id,
        thumbnail,
        metadata.get("title"),
        video.name,
        cfg,
    )


def retry_pending_thumbnail(service: Any, cfg: dict[str, Any]) -> dict[str, Any] | None:
    state = load_json(THUMBNAIL_RETRY_FILE, {}) or {}
    if not state:
        return None
    thumbnail = evidence_path(state.get("prepared_thumbnail"), "prepared_thumbnail")
    with Image.open(thumbnail) as image:
        if image.format != "JPEG" or image.size != (1280, 720) or thumbnail.stat().st_size > 2_000_000:
            raise SafetyError(f"Pending thumbnail retry file is invalid: {thumbnail}")
    result = set_custom_thumbnail_record(
        service,
        state["video_id"],
        thumbnail,
        state.get("title"),
        state["source_name"],
        cfg,
    )
    atomic_json(THUMBNAIL_RETRY_FILE, {})
    return result


def upload_one(service: Any, video: Path, cfg: dict[str, Any], prepared_thumbnail: Path | None = None) -> dict[str, Any]:
    _, _, _, _, MediaFileUpload = import_google()
    digest = sha256(video)
    attempts = load_json(ATTEMPTS_FILE, {}) or {}
    previous = attempts.get(digest)
    if previous and previous.get("status") == "started":
        raise SafetyError(
            f"Unresolved earlier upload attempt for {video.name}; refusing a possible duplicate. "
            "Check YouTube Studio and the attempt journal before retrying."
        )
    attempts[digest] = {"status": "started", "file": str(video), "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    atomic_json(ATTEMPTS_FILE, attempts)
    body = metadata_for(video, cfg)
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
    except Exception as exc:
        if is_safely_retryable_upload_error(exc):
            attempts[digest] = {
                **attempts[digest],
                "status": "failed_retryable",
                "failed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "error": classify_http_error(exc),
            }
            atomic_json(ATTEMPTS_FILE, attempts)
        raise
    finally:
        # MediaFileUpload keeps its source stream open. Windows will not allow the
        # completed source to be archived until that handle is explicitly closed.
        stream = media.stream()
        if stream and not stream.closed:
            stream.close()
    video_id = response.get("id")
    if not video_id:
        raise SafetyError("YouTube completed the request without returning a video ID")
    row = {
        "uploaded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_name": video.name,
        "source_path": str(video),
        "sha256": digest,
        "video_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}",
        "privacy_status": cfg["privacy_status"],
        "made_for_kids": True,
    }
    append_ledger(row)
    attempts[digest] = {**attempts[digest], "status": "succeeded", "video_id": video_id}
    atomic_json(ATTEMPTS_FILE, attempts)
    if prepared_thumbnail is not None:
        try:
            row["custom_thumbnail"] = set_custom_thumbnail(service, video_id, video, prepared_thumbnail, cfg)
        except Exception as exc:
            # The video ID has already been recorded. A thumbnail failure must
            # never lead to a duplicate video upload.
            row["custom_thumbnail_error"] = classify_http_error(exc)
            metadata = load_json(video.with_suffix(".json"), {})
            atomic_json(THUMBNAIL_RETRY_FILE, {
                "video_id": video_id,
                "title": metadata.get("title"),
                "source_name": video.name,
                "prepared_thumbnail": str(prepared_thumbnail.relative_to(HERE.parent).as_posix()),
            })
            LOGGER.exception("Video uploaded but prepared thumbnail failed for %s", video_id)
    archive = HERE / cfg["archive_directory"]
    archive.mkdir(parents=True, exist_ok=True)
    destination = archive / video.name
    if destination.exists():
        destination = archive / f"{video.stem}-{video_id}{video.suffix}"
    try:
        shutil.move(str(video), str(destination))
        sidecar = video.with_suffix(".json")
        if sidecar.exists():
            shutil.move(str(sidecar), str(destination.with_suffix(".json")))
        row["archived_path"] = str(destination)

        # Generation publishes a byte-for-byte queue copy while retaining its
        # working output for review. Once YouTube has returned an ID and that
        # queue copy is safely archived, remove only an identical working copy
        # so uploaded videos do not accumulate in production-output.
        production_source = HERE / "production-output" / video.name
        if production_source.exists():
            if sha256(production_source) == digest:
                production_source.unlink()
                row["production_output_cleanup"] = "identical archived copy removed"
            else:
                row["production_output_cleanup"] = "retained: content differs from uploaded file"
                LOGGER.warning("Retaining non-identical production output: %s", production_source)
    except OSError as exc:
        # Upload success must never be misreported as an upload failure merely
        # because local post-upload archiving needs manual attention.
        row["archive_error"] = str(exc)
        LOGGER.error("Upload succeeded but local archive failed for %s: %s", video.name, exc)
    return row


def report_base(action: str) -> dict[str, Any]:
    return {"action": action, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "attempted": 0, "successful": 0, "failures": []}


def write_report(path: str | None, report: dict[str, Any]) -> None:
    report["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if path:
        atomic_json(Path(path), report)
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    oauth = sub.add_parser("oauth", help="Run interactive OAuth once on this laptop")
    oauth.add_argument("--interactive", action="store_true", required=True)
    sub.add_parser("verify", help="Verify token, lock, and channels.list(mine=true)")
    dry = sub.add_parser("dry-run", help="Inspect the dedicated new-video queue without uploading")
    dry.add_argument("--report-json")
    run = sub.add_parser("run", help="Upload the next eligible new video using configured queue order")
    run.add_argument("--confirm-upload", action="store_true", help="Required acknowledgement for a real upload")
    run.add_argument("--report-json")
    run.add_argument("--video-name", help="Retry this exact eligible queue filename")
    args = parser.parse_args()
    cfg = config()
    try:
        if args.command == "oauth":
            print(json.dumps(interactive_oauth(cfg), indent=2))
            return 0
        if args.command == "verify":
            _, actual = authorized_service(cfg)
            print(json.dumps(actual, indent=2))
            return 0
        candidates = queue_files(cfg)
        if args.command == "dry-run":
            report = report_base("upload-dry-run")
            report.update({"queue_scope": str(HERE / cfg["pending_directory"]), "existing_outputs_excluded": True, "configured_privacy_status": cfg["privacy_status"], "remaining_upload_count": len(candidates), "next_video": candidates[0].name if candidates else None})
            write_report(args.report_json, report)
            return 0
        if not args.confirm_upload:
            raise SafetyError("Real upload blocked: --confirm-upload is required")
        report = report_base(f"{cfg['privacy_status']}-upload")
        report["privacy_status"] = cfg["privacy_status"]
        service = None
        pending_thumbnail_retry = load_json(THUMBNAIL_RETRY_FILE, {}) or {}
        if pending_thumbnail_retry:
            service, channel = authorized_service(cfg)
            report["verified_channel"] = channel
            try:
                report["thumbnail_retry"] = retry_pending_thumbnail(service, cfg)
            except Exception as exc:
                message = classify_http_error(exc)
                LOGGER.exception("Pending thumbnail retry failed: %s", message)
                report["failures"].append({"thumbnail_retry": message})
                report["remaining_upload_count"] = len(candidates)
                write_report(args.report_json, report)
                return 1
        if not candidates:
            report["remaining_upload_count"] = 0
            write_report(args.report_json, report)
            return 0
        if args.video_name:
            if Path(args.video_name).name != args.video_name:
                raise SafetyError("Retry video must be a filename, not a path")
            matches = [candidate for candidate in candidates if candidate.name == args.video_name]
            if not matches:
                raise SafetyError(f"Requested retry video is not an eligible queue item: {args.video_name}")
            video = matches[0]
        else:
            video = candidates[0]
        validate_future_quality_evidence(video, cfg)
        if not ffprobe_ok(video):
            raise SafetyError(f"Video validation failed: {video}")
        if not full_decode_ok(video):
            raise SafetyError(f"Full video decode failed: {video}")
        if service is None:
            service, channel = authorized_service(cfg)
            report["verified_channel"] = channel
        report["attempted"] = 1
        report["video_name"] = video.name
        try:
            prepared_thumbnail = prepared_thumbnail_for(video, cfg)
            result = upload_one(service, video, cfg, prepared_thumbnail)
            report["successful"] = 1
            report["result"] = result
        except Exception as exc:
            message = classify_http_error(exc)
            LOGGER.exception("Upload failed for %s: %s", video.name, message)
            report["failures"].append({"video_name": video.name, "error": message})
            report["automatic_retry_safe"] = is_safely_retryable_upload_error(exc)
        report["remaining_upload_count"] = len(queue_files(cfg))
        write_report(args.report_json, report)
        return 0 if report["successful"] else 1
    except Exception as exc:
        LOGGER.exception("%s failed", args.command)
        report = report_base(args.command)
        report["failures"].append({"error": classify_http_error(exc)})
        if hasattr(args, "report_json"):
            write_report(args.report_json, report)
        else:
            print(json.dumps(report, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
