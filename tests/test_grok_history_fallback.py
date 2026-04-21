import json
import sqlite3
from pathlib import Path

import hermes_pulse.cli
from hermes_pulse.connectors.grok_history import GrokHistoryConnector
from hermes_pulse.exporters.grok_history_fallback import ChromeHistoryGrokExporter


EPOCH_OFFSET = 11644473600000000


def _chrome_time(unix_seconds: int) -> int:
    return unix_seconds * 1_000_000 + EPOCH_OFFSET


def _build_history_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "create table urls (id integer primary key, url text, title text, visit_count integer, typed_count integer, last_visit_time integer, hidden integer default 0)"
        )
        rows = [
            (1, "https://grok.com/c/conv-1?rid=aaa", "First title - Grok", 2, 0, _chrome_time(1_710_000_000), 0),
            (2, "https://grok.com/c/conv-1", "Grok", 3, 0, _chrome_time(1_710_000_100), 0),
            (3, "https://grok.com/c/conv-2?rid=bbb", "Second title - Grok", 1, 0, _chrome_time(1_710_000_200), 0),
            (4, "https://grok.com/", "Grok", 4, 0, _chrome_time(1_710_000_300), 0),
            (5, "https://example.com/not-grok", "Ignore", 1, 0, _chrome_time(1_710_000_400), 0),
        ]
        connection.executemany(
            "insert into urls (id, url, title, visit_count, typed_count, last_visit_time, hidden) values (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.commit()
    finally:
        connection.close()


def test_chrome_history_grok_exporter_writes_canonical_index_and_manifest(tmp_path: Path) -> None:
    history_db = tmp_path / "History"
    output_dir = tmp_path / "export"
    _build_history_db(history_db)

    result = ChromeHistoryGrokExporter().export(history_db, output_dir)

    index_payload = json.loads((output_dir / "conversations.index.json").read_text())
    manifest = json.loads((output_dir / "manifest.json").read_text())

    assert result["conversation_count"] == 2
    assert [item["conversationId"] for item in index_payload["conversations"]] == ["conv-2", "conv-1"]
    assert index_payload["conversations"][0]["canonicalUrl"] == "https://grok.com/c/conv-2"
    assert index_payload["conversations"][1]["title"] == "First title"
    assert index_payload["conversations"][1]["urlVariants"] == [
        "https://grok.com/c/conv-1",
        "https://grok.com/c/conv-1?rid=aaa",
    ]
    assert manifest["provider"] == "grok"
    assert manifest["acquisition_mode"] == "local_browser_history"
    assert manifest["history_db_path"] == str(history_db)


def test_refresh_grok_history_fallback_command_invokes_exporter(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    class FakeExporter:
        def export(self, history_db_path: str | Path, output_dir: str | Path) -> dict[str, object]:
            calls.append({"history_db_path": Path(history_db_path), "output_dir": Path(output_dir)})
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            (Path(output_dir) / "manifest.json").write_text("{}")
            return {"conversation_count": 1}

    monkeypatch.setattr(hermes_pulse.cli, "ChromeHistoryGrokExporter", lambda: FakeExporter())
    history_db = tmp_path / "History"
    history_db.write_text("placeholder")
    output_dir = tmp_path / "grok-fallback"

    assert (
        hermes_pulse.cli.main(
            [
                "refresh-grok-history-fallback",
                "--history-db",
                str(history_db),
                "--output-dir",
                str(output_dir),
            ]
        )
        == 0
    )

    assert calls == [{"history_db_path": history_db, "output_dir": output_dir}]


def test_grok_history_connector_uses_manifest_acquisition_mode(tmp_path: Path) -> None:
    export_dir = tmp_path / "grok-fallback"
    export_dir.mkdir()
    (export_dir / "conversations.index.json").write_text(
        json.dumps(
            {
                "conversations": [
                    {
                        "conversationId": "conv-1",
                        "title": "History fallback title",
                        "canonicalUrl": "https://grok.com/c/conv-1",
                        "modifyTime": "2026-04-21T12:00:00Z",
                    }
                ]
            }
        )
    )
    (export_dir / "manifest.json").write_text(
        json.dumps({"provider": "grok", "acquisition_mode": "local_browser_history"})
    )

    items = GrokHistoryConnector().collect(export_dir)

    assert len(items) == 1
    assert items[0].provenance is not None
    assert items[0].provenance.acquisition_mode == "local_browser_history"
    assert items[0].metadata["response_count"] == 0
