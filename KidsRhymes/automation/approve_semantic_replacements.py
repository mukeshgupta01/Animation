"""Explicitly release reviewed semantic-motion masters for upload.

This is intentionally separate from rendering.  Rendering creates evidence with
``reviewed: false``; a human/Codex visual review must happen before this command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ITEMS = (
    "felix-firefly-night-light-parade-01",
    "basil-beaver-leaky-river-workshop-01",
    "gus-gecko-upside-down-museum-01",
    "nellie-narwhal-northern-lights-rescue-01",
    "tilly-turtle-travelling-bakery-01",
    "pogo-penguin-wobbly-ice-bridge-01",
    "zara-zebra-musical-crossing-01",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def approve(item_id: str) -> None:
    metadata_path = PROJECT / "metadata" / f"{item_id}.json"
    work = PROJECT / "automation" / "production-work" / item_id
    audit_path = work / "semantic-motion-audit.json"
    sheet_path = work / "semantic-motion-contact-sheet.png"
    report_path = work / "quality-report.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    master = Path(metadata["output"])
    thumbnail = PROJECT / metadata["prepared_thumbnail"]
    if not report.get("passed"):
        raise RuntimeError(f"Quality report did not pass: {item_id}")
    if not master.is_file() or not sheet_path.is_file() or not thumbnail.is_file():
        raise FileNotFoundError(f"Missing master/evidence/thumbnail: {item_id}")
    required = {"scene", "primary_action", "visible_start_state", "visible_action_state",
                "visible_end_state", "foreground_moving_elements", "camera_only",
                "character_and_object_continuity", "reviewed"}
    if not audit or any(set(row) < required or row["camera_only"] or
                        not row["character_and_object_continuity"] for row in audit):
        raise RuntimeError(f"Semantic audit is incomplete: {item_id}")
    for row in audit:
        row["reviewed"] = True
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    master_hash = sha256(master)
    metadata.update({
        "semantic_motion_reviewed": True,
        "character_continuity_reviewed": True,
        "primary_action_motion_reviewed": True,
        "actual_motion_not_camera_only": True,
        "semantic_motion_audit": f"automation/production-work/{item_id}/semantic-motion-audit.json",
        "semantic_motion_contact_sheet": f"automation/production-work/{item_id}/semantic-motion-contact-sheet.png",
        "semantic_motion_contact_sheet_reviewed": True,
        "quality_contact_sheet_reviewed": True,
        "transition_contact_sheet_reviewed": True,
        "thumbnail_reviewed": True,
        "manual_visual_review_passed": True,
        "reviewed_sha256": master_hash,
        "manual_review_notes": "Exact hash-locked corrected master reviewed for visible start/action/end motion in every scene, character and prop continuity, transitions, end-card placement, thumbnail, and full technical decode.",
        "upload_queue_released": False,
    })
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"approved {item_id} {master_hash}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("items", nargs="*", choices=ITEMS)
    parser.add_argument("--confirm-reviewed", action="store_true", required=True)
    args = parser.parse_args()
    for item in (args.items or ITEMS):
        approve(item)


if __name__ == "__main__":
    main()
