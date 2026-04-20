import json
from dataclasses import asdict
from pathlib import Path

from hermes_pulse.models import CollectedItem


SUMMARY_RELATIVE_PATH = Path("summary") / "morning-digest.md"
RAW_ITEMS_RELATIVE_PATH = Path("raw") / "collected-items.json"


def write_morning_digest_archive(
    markdown: str,
    items: list[CollectedItem],
    archive_root: str | Path,
    archive_date: str,
) -> Path:
    archive_directory = Path(archive_root) / archive_date
    summary_path = archive_directory / SUMMARY_RELATIVE_PATH
    raw_items_path = archive_directory / RAW_ITEMS_RELATIVE_PATH

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    raw_items_path.parent.mkdir(parents=True, exist_ok=True)

    summary_path.write_text(markdown)
    raw_items_path.write_text(json.dumps([asdict(item) for item in items], indent=2) + "\n")
    return archive_directory
