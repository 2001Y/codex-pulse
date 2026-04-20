import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hermes_pulse.models import CollectedItem, Provenance


class AuditContextConnector:
    id = "audit_context"
    source_family = "audit"

    def __init__(self, runner: Callable[[], dict[str, Any]] | None = None) -> None:
        self._runner = runner or (lambda: {})

    def collect(self) -> list[CollectedItem]:
        payload = self._runner()
        lines = [f"{key}: {value}" for key, value in payload.items()]
        return [
            CollectedItem(
                id="audit_context:trigger_quality",
                source="audit_context",
                source_kind="artifact",
                title="Trigger quality review",
                body="\n".join(lines),
                provenance=Provenance(
                    provider="audit_context",
                    acquisition_mode="local_store",
                    raw_record_id="trigger_quality",
                ),
                metadata=payload,
            )
        ]


def load_audit_context_fixture(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())
