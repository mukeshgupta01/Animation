"""Time-boxed, resumable generation manifest runner."""

from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
CONFIG = HERE / "config.json"
MANIFEST = HERE / "generation-manifest.json"
STATE = HERE / "runtime" / "generation-state.json"
LOG = HERE / "logs" / "generation.log"


def load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


LOG.parent.mkdir(parents=True, exist_ok=True)
LOGGER = logging.getLogger("tiny-tales-generation")
LOGGER.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
LOGGER.addHandler(handler)


def validate_manifest() -> list[dict[str, Any]]:
    manifest = load(MANIFEST, {})
    items = manifest.get("items")
    if manifest.get("version") != 1 or not isinstance(items, list):
        raise RuntimeError("Invalid generation manifest")
    seen = set()
    for item in items:
        required = {"id", "name", "command", "working_directory", "output"}
        if not required.issubset(item) or not isinstance(item["command"], list) or not item["command"]:
            raise RuntimeError(f"Invalid generation item: {item}")
        if item["id"] in seen:
            raise RuntimeError(f"Duplicate generation ID: {item['id']}")
        seen.add(item["id"])
    return items


def resolved_project_path(value: str) -> Path:
    path = (PROJECT / value).resolve()
    try:
        path.relative_to(PROJECT.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Manifest path escapes project: {value}") from exc
    return path


def terminate_tree(process: subprocess.Popen[Any]) -> None:
    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)


def publish(item: dict[str, Any], output: Path) -> None:
    if not item.get("publish_to_upload_queue", True):
        return
    pending = HERE / load(CONFIG, {})["pending_directory"]
    pending.mkdir(parents=True, exist_ok=True)
    destination = pending / output.name
    if destination.exists():
        if destination.stat().st_size == output.stat().st_size:
            return
        raise RuntimeError(f"Upload queue destination already exists with different content: {destination}")
    shutil.copy2(output, destination)
    metadata = item.get("youtube")
    if metadata:
        save(destination.with_suffix(".json"), metadata)


def summary(items: list[dict[str, Any]], states: dict[str, Any]) -> dict[str, Any]:
    completed = [item["name"] for item in items if states.get(item["id"], {}).get("status") == "completed"]
    remaining = [item["name"] for item in items if states.get(item["id"], {}).get("status") != "completed"]
    failed = [item["name"] for item in items if states.get(item["id"], {}).get("status") == "failed"]
    return {"total": len(items), "completed_count": len(completed), "remaining_count": len(remaining), "failed_count": len(failed), "completed_names": completed, "remaining_names": remaining, "failed_names": failed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--max-seconds", type=int)
    parser.add_argument("--max-items", type=int, default=1, help="Maximum new videos to generate in this process")
    parser.add_argument("--report-json")
    args = parser.parse_args()
    state_doc = load(STATE, {"version": 1, "items": {}})
    items = validate_manifest()
    # The former fallback generated only disappearance-memory episodes. The
    # user asked on 2026-08-23 not to create that format frequently, so an
    # exhausted manifest now stays exhausted. Add deliberately varied,
    # reviewed items to the manifest instead of synthesizing repetitive work.
    states = state_doc.setdefault("items", {})
    before = summary(items, states)
    if args.count_only:
        result = {"action": "generation-count-only", **before, "generated_this_run": [], "failures_this_run": []}
        if args.report_json:
            save(Path(args.report_json), result)
        print(json.dumps(result, indent=2))
        return 0
    cfg = load(CONFIG, {})
    limit = args.max_seconds or int(cfg.get("generation_cycle_seconds", 17100))
    started = time.monotonic()
    generated: list[str] = []
    failures: list[dict[str, str]] = []
    attempted_items = 0
    for item in items:
        output = resolved_project_path(item["output"])
        current = states.get(item["id"], {})
        if current.get("status") == "completed":
            continue
        if output.exists() and output.stat().st_size > 0:
            states[item["id"]] = {"status": "completed", "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "reason": "pre-existing output preserved"}
            publish(item, output)
            save(STATE, state_doc)
            if "_continuous_index" in item:
                state_doc["continuous_index"] = item["_continuous_index"] + 1
                save(STATE, state_doc)
            continue
        remaining = limit - (time.monotonic() - started)
        if remaining <= 1 or attempted_items >= max(1, args.max_items):
            break
        attempted_items += 1
        working = resolved_project_path(item["working_directory"])
        states[item["id"]] = {"status": "running", "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        save(STATE, state_doc)
        LOGGER.info("Starting generation: %s", item["name"])
        process = subprocess.Popen(item["command"], cwd=working, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            return_code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            terminate_tree(process)
            states[item["id"]] = {"status": "pending", "last_error": "cycle time limit reached; item will resume next cycle"}
            save(STATE, state_doc)
            break
        if return_code == 0 and output.exists() and output.stat().st_size > 0:
            states[item["id"]] = {"status": "completed", "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            publish(item, output)
            generated.append(item["name"])
            if "_continuous_index" in item:
                state_doc["continuous_index"] = item["_continuous_index"] + 1
        else:
            message = f"generator exit code {return_code}; expected output not found" if return_code == 0 else f"generator exit code {return_code}"
            states[item["id"]] = {"status": "failed", "last_error": message, "failed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            failures.append({"name": item["name"], "error": message})
            LOGGER.error("Generation failed: %s: %s", item["name"], message)
        save(STATE, state_doc)
    result = {"action": "generation-cycle", **summary(items, states), "generated_this_run": generated, "failures_this_run": failures, "elapsed_seconds": round(time.monotonic() - started, 1)}
    if args.report_json:
        save(Path(args.report_json), result)
    print(json.dumps(result, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
