import json
from pathlib import Path

from hermes_pulse.models import CollectedItem, ItemTimestamps, Provenance


class HermesHistoryConnector:
    id = "hermes_history"
    source_family = "local_context"

    def collect(self, path: str | Path) -> list[CollectedItem]:
        payload = json.loads(Path(path).read_text())
        return [
            CollectedItem(
                id=payload["session_id"],
                source="hermes_history",
                source_kind="conversation",
                title=payload.get("title"),
                body=payload.get("summary"),
                timestamps=ItemTimestamps(created_at=payload.get("created_at")),
                provenance=Provenance(
                    provider="hermes_agent",
                    acquisition_mode="local_store",
                    raw_record_id=payload["session_id"],
                ),
            )
        ]
