import json
from pathlib import Path

import hermes_pulse.cli
from hermes_pulse.connectors.gmail import GmailConnector
from hermes_pulse.summarization.base import SummaryArtifact


ROOT = Path(__file__).resolve().parents[1]
GMAIL_FIXTURE_PATH = ROOT / "fixtures/google_workspace/gmail_messages.json"
SOURCE_REGISTRY_PATH = ROOT / "fixtures/source_registry/sample_sources.yaml"


def test_gmail_connector_normalizes_messages_from_google_workspace_payload() -> None:
    payload = json.loads(GMAIL_FIXTURE_PATH.read_text())
    connector = GmailConnector(runner=lambda: payload)

    items = connector.collect()

    assert [item.id for item in items] == ["gmail:msg-1", "gmail:msg-2"]
    assert [item.source_kind for item in items] == ["email", "email"]
    assert items[0].title == "Quarterly review moved"
    assert items[0].people == ["Boss <boss@example.com>", "me@example.com"]
    assert items[0].intent_signals is not None
    assert items[0].intent_signals.unread is True
    assert items[0].metadata["open_loop"] is True
    assert items[0].provenance is not None
    assert items[0].provenance.acquisition_mode == "official_api"
    assert items[0].provenance.provider == "gmail"


def test_morning_digest_includes_gmail_fixture_items(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    class StubCodexCliSummarizer:
        def summarize_archive(self, archive_directory: str | Path) -> SummaryArtifact:
            archive_directory = Path(archive_directory)
            raw_items = json.loads((archive_directory / "raw" / "collected-items.json").read_text())
            content = "# Codex Digest\n\n" + "".join(f"- {item['title']}\n" for item in raw_items)
            output_path = archive_directory / "summary" / "codex-digest.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
            calls.append({"raw_items": raw_items, "archive_directory": archive_directory})
            return SummaryArtifact(path=output_path, content=content)

    monkeypatch.setattr(hermes_pulse.cli, "CodexCliSummarizer", StubCodexCliSummarizer)
    output_path = tmp_path / "deliveries" / "morning-digest.md"

    assert (
        hermes_pulse.cli.main(
            [
                "morning-digest",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--gmail-fixture",
                str(GMAIL_FIXTURE_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    assert any(item["source"] == "gmail" for item in calls[0]["raw_items"])
    assert "Quarterly review moved" in output_path.read_text()
