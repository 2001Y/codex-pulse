from pathlib import Path

from hermes_pulse.models import CollectedItem, Provenance


class NotesConnector:
    id = "notes"
    source_family = "local_context"

    def collect(self, path: str | Path) -> list[CollectedItem]:
        body = Path(path).read_text()
        return [
            CollectedItem(
                id=Path(path).stem,
                source="notes",
                source_kind="note",
                title=body.splitlines()[0].lstrip("# ") if body else None,
                body=body,
                provenance=Provenance(
                    provider="notes",
                    acquisition_mode="local_store",
                    raw_record_id=str(Path(path)),
                ),
            )
        ]
