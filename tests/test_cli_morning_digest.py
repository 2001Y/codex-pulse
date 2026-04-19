import tomllib
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


def test_pyproject_declares_console_entrypoint() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["hermes-pulse"] == "hermes_pulse.cli:main"
