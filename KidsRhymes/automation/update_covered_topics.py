"""Rebuild Tiny Tales' human-readable covered-topic index from live media and metadata."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path


AUTOMATION = Path(__file__).resolve().parent
PROJECT = AUTOMATION.parent
INDEX = PROJECT / "COVERED-TOPICS.md"


def main() -> None:
    config_path = AUTOMATION / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    queue_visibility = str(config.get("privacy_status", "private"))
    media: dict[str, set[str]] = {}
    for label, directory in (
        ("archived/uploaded", AUTOMATION / "archive"),
        ("completed local", AUTOMATION / "production-output"),
        (f"queued {queue_visibility} upload", AUTOMATION / "pending-uploads"),
    ):
        for path in directory.glob("*.mp4"):
            media.setdefault(path.stem, set()).add(label)

    titles: dict[str, str] = {}
    manifest_path = AUTOMATION / "generation-manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("items", []):
            titles[Path(item["output"]).stem] = item.get("youtube", {}).get("title", item["name"])
    for path in (PROJECT / "metadata").glob("*.json"):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        item_id = str(doc.get("id") or path.stem)
        titles[item_id] = str(doc.get("title") or item_id.replace("-", " ").title())

    lines = [
        "# Covered topics",
        "",
        f"Updated: {date.today().isoformat()}",
        "",
        "Check this index, `metadata/`, the generation manifest, and the upload ledger before creating a Tiny Tales concept. Retired shadow and matching formats remain covered history and must not be regenerated.",
        "",
        f"Known completed or queued video concepts: {len(media)}.",
        "",
        "## Topic index",
        "",
    ]
    for item_id in sorted(media):
        title = titles.get(item_id, item_id.replace("-", " ").title())
        lines.append(f"- {title} — `{item_id}` — {', '.join(sorted(media[item_id]))}")
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {INDEX} with {len(media)} concepts")


if __name__ == "__main__":
    main()
