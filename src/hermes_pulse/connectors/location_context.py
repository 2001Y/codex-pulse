import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hermes_pulse.models import CollectedItem, Provenance


class LocationContextConnector:
    id = "location_context"
    source_family = "location"

    def __init__(self, runner: Callable[[], dict[str, Any]] | None = None) -> None:
        self._runner = runner or (lambda: {})

    def collect(self) -> list[CollectedItem]:
        payload = self._runner()
        place = payload.get("place") or "Unknown place"
        maps_url = payload.get("maps_url")
        context = payload.get("context") or []
        body = "\n".join(f"- {value}" for value in context)
        return [
            CollectedItem(
                id=f"location_context:{place}",
                source="location_context",
                source_kind="place",
                title=place,
                body=body,
                url=maps_url,
                provenance=Provenance(
                    provider="location_context",
                    acquisition_mode="local_store",
                    raw_record_id=str(payload.get("arrived_at") or place),
                ),
                metadata={
                    "arrived_at": payload.get("arrived_at"),
                    "context": context,
                    "maps_url": maps_url,
                },
            )
        ]


def load_location_context_fixture(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())
