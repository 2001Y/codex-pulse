import json
import tomllib
from datetime import date
from pathlib import Path

import hermes_pulse.cli
from hermes_pulse.models import CitationLink, CollectedItem, ItemTimestamps, Provenance


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY_PATH = ROOT / "fixtures/source_registry/sample_sources.yaml"
HERMES_HISTORY_PATH = ROOT / "fixtures/hermes_history/sample_session.json"
NOTES_PATH = ROOT / "fixtures/notes/sample_notes.md"


def test_main_entrypoint_exists_and_exits_successfully() -> None:
    assert hermes_pulse.cli.main([]) == 0


def test_main_writes_morning_digest_markdown_to_output_path(tmp_path: Path) -> None:
    output_path = tmp_path / "deliveries" / "morning-digest.md"

    assert hermes_pulse.cli.main(["--output", str(output_path)]) == 0
    assert output_path.exists()
    assert output_path.read_text().startswith("# Morning Digest\n")


def test_morning_digest_uses_live_feed_fetching_when_no_fixture_is_provided(
    monkeypatch, tmp_path: Path
) -> None:
    fetchers: list[object] = []

    class FakeFeedRegistryConnector:
        def __init__(self, fetcher=None) -> None:
            fetchers.append(fetcher)

        def collect(self, entries):
            assert [entry.id for entry in entries if entry.rss_url] == [
                "official-blog",
                "trusted-secondary-blog",
            ]
            return [
                CollectedItem(
                    id="official-blog:live-fetch-item",
                    source="official-blog",
                    source_kind="feed_item",
                    title="Live fetch item",
                    excerpt="Fetched from registry URL.",
                    url="https://example.com/posts/live-fetch-item",
                    timestamps=ItemTimestamps(created_at="Mon, 20 Apr 2026 08:00:00 GMT"),
                    provenance=Provenance(
                        provider="example.com",
                        acquisition_mode="rss_poll",
                        authority_tier="primary",
                        primary_source_url="https://example.com/posts/live-fetch-item",
                        raw_record_id="live-fetch-item",
                    ),
                    citation_chain=[
                        CitationLink(
                            label="Live fetch item",
                            url="https://example.com/posts/live-fetch-item",
                            relation="primary",
                        )
                    ],
                )
            ]

    monkeypatch.setattr(hermes_pulse.cli, "FeedRegistryConnector", FakeFeedRegistryConnector)
    output_path = tmp_path / "deliveries" / "morning-digest.md"

    assert (
        hermes_pulse.cli.main(
            [
                "morning-digest",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--hermes-history",
                str(HERMES_HISTORY_PATH),
                "--notes",
                str(NOTES_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    assert fetchers == [None]
    assert "Live fetch item" in output_path.read_text()


def test_morning_digest_skips_optional_local_context_when_paths_are_omitted(
    monkeypatch, tmp_path: Path
) -> None:
    fetchers: list[object] = []

    class FakeFeedRegistryConnector:
        def __init__(self, fetcher=None) -> None:
            fetchers.append(fetcher)

        def collect(self, entries):
            assert [entry.id for entry in entries if entry.rss_url] == [
                "official-blog",
                "trusted-secondary-blog",
            ]
            return [
                CollectedItem(
                    id="official-blog:live-only-item",
                    source="official-blog",
                    source_kind="feed_item",
                    title="Live only item",
                    excerpt="Fetched without local context.",
                    url="https://example.com/posts/live-only-item",
                    timestamps=ItemTimestamps(created_at="Mon, 20 Apr 2026 08:00:00 GMT"),
                    provenance=Provenance(
                        provider="example.com",
                        acquisition_mode="rss_poll",
                        authority_tier="primary",
                        primary_source_url="https://example.com/posts/live-only-item",
                        raw_record_id="live-only-item",
                    ),
                    citation_chain=[
                        CitationLink(
                            label="Live only item",
                            url="https://example.com/posts/live-only-item",
                            relation="primary",
                        )
                    ],
                )
            ]

    class UnexpectedHermesHistoryConnector:
        def collect(self, path):
            raise AssertionError("hermes history connector should not be used")

    class UnexpectedNotesConnector:
        def collect(self, path):
            raise AssertionError("notes connector should not be used")

    monkeypatch.setattr(hermes_pulse.cli, "FeedRegistryConnector", FakeFeedRegistryConnector)
    monkeypatch.setattr(hermes_pulse.cli, "HermesHistoryConnector", UnexpectedHermesHistoryConnector)
    monkeypatch.setattr(hermes_pulse.cli, "NotesConnector", UnexpectedNotesConnector)
    output_path = tmp_path / "deliveries" / "morning-digest.md"

    assert (
        hermes_pulse.cli.main(
            [
                "morning-digest",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    assert fetchers == [None]
    assert "Live only item" in output_path.read_text()


def test_morning_digest_archives_summary_and_raw_items_under_explicit_archive_root(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "deliveries" / "morning-digest.md"
    archive_root = tmp_path / "archive-root"
    archive_date = date.today().isoformat()

    assert (
        hermes_pulse.cli.main(
            [
                "morning-digest",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--hermes-history",
                str(HERMES_HISTORY_PATH),
                "--notes",
                str(NOTES_PATH),
                "--archive-root",
                str(archive_root),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    summary_path = archive_root / archive_date / "summary" / "morning-digest.md"
    raw_items_path = archive_root / archive_date / "raw" / "collected-items.json"

    assert summary_path.exists()
    assert summary_path.read_text() == output_path.read_text()
    raw_items = json.loads(raw_items_path.read_text())
    assert [item["source"] for item in raw_items] == ["hermes_history", "notes"]
    assert raw_items[0]["id"] == "session-123"


def test_morning_digest_defaults_archive_root_to_home_pulse_directory(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(hermes_pulse.cli.Path, "home", classmethod(lambda cls: tmp_path))
    archive_date = date.today().isoformat()

    assert (
        hermes_pulse.cli.main(
            [
                "morning-digest",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--hermes-history",
                str(HERMES_HISTORY_PATH),
                "--notes",
                str(NOTES_PATH),
            ]
        )
        == 0
    )

    summary_path = tmp_path / "Pulse" / archive_date / "summary" / "morning-digest.md"
    raw_items_path = tmp_path / "Pulse" / archive_date / "raw" / "collected-items.json"

    assert summary_path.exists()
    assert summary_path.read_text().startswith("# Morning Digest\n")
    raw_items = json.loads(raw_items_path.read_text())
    assert len(raw_items) == 2
    assert raw_items[1]["id"] == "sample_notes"


def test_pyproject_declares_console_entrypoint() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["hermes-pulse"] == "hermes_pulse.cli:main"
