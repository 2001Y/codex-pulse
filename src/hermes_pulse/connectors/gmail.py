import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hermes_pulse.models import CitationLink, CollectedItem, IntentSignals, ItemTimestamps, Provenance


class GmailConnector:
    id = "gmail"
    source_family = "email"

    def __init__(self, runner: Callable[[], list[dict[str, Any]]] | None = None) -> None:
        self._runner = runner or _run_gmail_search

    def collect(self) -> list[CollectedItem]:
        return [_normalize_message(record) for record in self._runner()]


def _normalize_message(record: dict[str, Any]) -> CollectedItem:
    message_id = record["id"]
    labels = record.get("labels") or []
    people = [value for value in [record.get("from"), record.get("to")] if value]
    subject = record.get("subject") or "Email message"
    url = f"https://mail.google.com/mail/u/0/#all/{message_id}"
    unread = "UNREAD" in labels
    return CollectedItem(
        id=f"gmail:{message_id}",
        source="gmail",
        source_kind="email",
        title=subject,
        excerpt=record.get("snippet"),
        body=record.get("body") or record.get("snippet"),
        url=url,
        people=people,
        timestamps=ItemTimestamps(created_at=record.get("date")),
        intent_signals=IntentSignals(unread=unread, unresolved=unread),
        provenance=Provenance(
            provider="gmail",
            acquisition_mode="official_api",
            authority_tier="primary",
            primary_source_url=url,
            raw_record_id=message_id,
        ),
        citation_chain=[CitationLink(label=subject, url=url, relation="primary")],
        metadata={"thread_id": record.get("threadId"), "labels": labels, "open_loop": unread},
    )


def _run_gmail_search() -> list[dict[str, Any]]:
    script = os.environ.get(
        "GOOGLE_WORKSPACE_API_SCRIPT",
        str(Path.home() / ".hermes" / "skills" / "productivity" / "google-workspace" / "scripts" / "google_api.py"),
    )
    result = subprocess.run(
        ["python3", script, "gmail", "search", "in:inbox newer_than:1d"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, list):
        raise ValueError("Gmail API payload must be a list")
    return payload
