import json
from dataclasses import asdict
from pathlib import Path

from hermes_pulse.models import CollectedItem
from hermes_pulse.summarization.base import RAW_ITEMS_RELATIVE_PATH


def write_morning_digest_archive(
    items: list[CollectedItem],
    archive_root: str | Path,
    archive_date: str,
) -> Path:
    archive_directory = Path(archive_root) / archive_date
    raw_items_path = archive_directory / RAW_ITEMS_RELATIVE_PATH

    raw_items_path.parent.mkdir(parents=True, exist_ok=True)

    raw_items_path.write_text(json.dumps([asdict(item) for item in items], indent=2) + "\n")
    return archive_directory
