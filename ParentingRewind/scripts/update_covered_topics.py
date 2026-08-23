"""Rebuild Parenting Rewind's human-readable covered-topic index from metadata."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
METADATA = PROJECT / "metadata"
OUTPUT = PROJECT / "output"
INDEX = PROJECT / "COVERED-TOPICS.md"


def normalize_title(value: str) -> str:
    return value.replace(" | Parenting Rewind", "").strip()


def candidate_outputs(path: Path, doc: dict) -> set[str]:
    names = {path.stem, f"parenting-rewind-{path.stem}"}
    output = doc.get("output")
    if isinstance(output, dict) and output.get("file"):
        names.add(Path(output["file"]).stem)
    elif isinstance(output, str):
        names.add(Path(output).stem)
    return names


def is_durable_active_metadata(path: Path) -> bool:
    """Keep approved/offloaded active episodes active when MP4s live in OneDrive."""
    name = path.name.casefold()
    return name.startswith("parenting-rewind-redesign-") or name.startswith("pilot-01-") or name.startswith("pilot-02-")


def main() -> None:
    active = {path.stem for path in OUTPUT.glob("*.mp4")}
    topics: dict[str, dict] = defaultdict(lambda: {"files": [], "active": False})
    for path in sorted(METADATA.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        title = normalize_title(str(doc.get("title") or path.stem.replace("-", " ").title()))
        entry = topics[title.casefold()]
        entry["title"] = title
        entry["files"].append(path.name)
        entry["active"] = entry["active"] or is_durable_active_metadata(path) or bool(candidate_outputs(path, doc) & active)

    active_count = sum(1 for item in topics.values() if item["active"])
    lines = [
        "# Covered topics",
        "",
        f"Updated: {date.today().isoformat()}",
        "",
        "Check this index and `metadata/` before approving or scripting a new topic. `Active` means a matching MP4 is currently in `output/`; `historical` includes prior, rejected, or superseded work and should still be considered when avoiding repetition.",
        "",
        f"Unique topics: {len(topics)} ({active_count} active; {len(topics) - active_count} historical-only).",
        "",
        "## Topic index",
        "",
    ]
    for item in sorted(topics.values(), key=lambda value: (not value["active"], value["title"].casefold())):
        status = "active" if item["active"] else "historical"
        lines.append(f"- [{status}] {item['title']} — metadata: {', '.join(item['files'])}")
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {INDEX} with {len(topics)} unique topics")


if __name__ == "__main__":
    main()
