from pathlib import Path

from hermes_pulse.connectors.hermes_history import HermesHistoryConnector
from hermes_pulse.connectors.notes import NotesConnector


def test_hermes_history_connector_normalizes_local_session() -> None:
    connector = HermesHistoryConnector()

    items = connector.collect(Path("fixtures/hermes_history/sample_session.json"))

    assert len(items) == 1
    item = items[0]
    assert item.source == "hermes_history"
    assert item.source_kind == "conversation"
    assert item.title == "Morning planning"
    assert item.provenance is not None
    assert item.provenance.acquisition_mode == "local_store"
    assert item.provenance.provider == "hermes_agent"


def test_notes_connector_normalizes_local_markdown() -> None:
    connector = NotesConnector()

    items = connector.collect(Path("fixtures/notes/sample_notes.md"))

    assert len(items) == 1
    item = items[0]
    assert item.source == "notes"
    assert item.source_kind == "note"
    assert "Call dentist tomorrow morning" in (item.body or "")
    assert item.provenance is not None
    assert item.provenance.acquisition_mode == "local_store"
    assert item.provenance.provider == "notes"
