from pathlib import Path

from hermes_pulse.connectors.feed_registry import FeedRegistryConnector
from hermes_pulse.source_registry import load_source_registry


FIXTURE_XML = Path("fixtures/feed_samples/official_feed.xml").read_text()


def test_feed_registry_connector_collects_feed_items_with_provenance() -> None:
    entries = load_source_registry(Path("fixtures/source_registry/sample_sources.yaml"))
    connector = FeedRegistryConnector(fetcher=lambda url: FIXTURE_XML)

    items = connector.collect(entries)

    assert len(items) == 2

    official_item = next(item for item in items if item.source == "official-blog")
    assert official_item.source_kind == "feed_item"
    assert official_item.title == "Launch update"
    assert official_item.url == "https://example.com/posts/launch-update"
    assert official_item.provenance is not None
    assert official_item.provenance.authority_tier == "primary"
    assert official_item.provenance.acquisition_mode == "rss_poll"
    assert official_item.citation_chain[0].relation == "primary"
    assert official_item.citation_chain[0].url == "https://example.com/posts/launch-update"

    secondary_item = next(item for item in items if item.source == "trusted-secondary-blog")
    assert secondary_item.provenance is not None
    assert secondary_item.provenance.authority_tier == "trusted_secondary"
    assert secondary_item.provenance.acquisition_mode == "atom_poll"
