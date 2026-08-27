"""Fail-closed OAuth setup and channel verification for Parenting Rewind."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import time
from typing import Any


HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
CLIENT_SECRET = HERE / "secrets" / "youtube-client-secret.json"
TOKEN_FILE = HERE / "runtime" / "youtube-oauth-token.json"
CHANNEL_LOCK = HERE / "runtime" / "youtube-channel-lock.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
]


class SafetyError(RuntimeError):
    """Raised when identity verification cannot safely continue."""


def load_json(path: Path) -> dict[str, Any]:
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
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def imports() -> tuple[Any, Any, Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise SafetyError(
            "Google API packages are missing. Run Setup-YouTubeApi.ps1 first."
        ) from exc
    return Request, Credentials, InstalledAppFlow, build


def owned_channel(service: Any) -> dict[str, str]:
    response = service.channels().list(part="id,snippet", mine=True).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise SafetyError(
            f"OAuth identity returned {len(items)} owned channels; expected exactly one."
        )
    return {
        "channel_id": items[0]["id"],
        "channel_name": items[0]["snippet"]["title"],
    }


def require_expected_channel(actual: dict[str, str], expected: dict[str, Any]) -> None:
    if actual["channel_id"] != expected["channel_id"]:
        raise SafetyError(
            "WRONG CHANNEL: Google returned "
            f"{actual['channel_name']} ({actual['channel_id']}), but Parenting Rewind is locked to "
            f"{expected['channel_name']} ({expected['channel_id']}). No token or lock was saved."
        )


def create_or_check_lock(actual: dict[str, str]) -> None:
    expected_lock = {
        **actual,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if CHANNEL_LOCK.exists():
        current = load_json(CHANNEL_LOCK)
        if current.get("channel_id") != actual["channel_id"]:
            raise SafetyError("Existing immutable channel lock differs; refusing to replace it.")
        return
    CHANNEL_LOCK.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(CHANNEL_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(expected_lock, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(CHANNEL_LOCK, stat.S_IREAD)


def setup() -> dict[str, str]:
    expected = load_json(CONFIG_PATH)
    if not CLIENT_SECRET.exists():
        raise SafetyError(f"OAuth desktop-client JSON is missing: {CLIENT_SECRET}")
    _, _, InstalledAppFlow, build = imports()
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    credentials = flow.run_local_server(port=0, open_browser=True, prompt="select_account consent")
    service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    actual = owned_channel(service)
    require_expected_channel(actual, expected)
    create_or_check_lock(actual)
    atomic_json(TOKEN_FILE, json.loads(credentials.to_json()))
    return actual


def authorized_service() -> tuple[Any, dict[str, str]]:
    expected = load_json(CONFIG_PATH)
    if not TOKEN_FILE.exists() or not CHANNEL_LOCK.exists():
        raise SafetyError("OAuth token or immutable channel lock is missing; run setup first.")
    lock = load_json(CHANNEL_LOCK)
    if lock.get("channel_id") != expected["channel_id"]:
        raise SafetyError("The immutable channel lock does not match config; API access disabled.")
    Request, Credentials, _, build = imports()
    credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        atomic_json(TOKEN_FILE, json.loads(credentials.to_json()))
    if not credentials.valid:
        raise SafetyError("OAuth token is invalid; interactive authorization is required.")
    service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    actual = owned_channel(service)
    require_expected_channel(actual, expected)
    if actual["channel_id"] != lock.get("channel_id"):
        raise SafetyError("Live channel differs from immutable lock; API access disabled.")
    return service, actual


def verify() -> dict[str, str]:
    _, actual = authorized_service()
    return actual


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["setup", "verify"])
    args = parser.parse_args()
    try:
        actual = setup() if args.command == "setup" else verify()
        print(f"Verified: {actual['channel_name']} ({actual['channel_id']})")
        print("No video was uploaded.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
