from pathlib import Path

import hermes_pulse.connectors.feed_registry as feed_registry_module
from hermes_pulse.connectors.feed_registry import FeedRegistryConnector
from hermes_pulse.models import SourceRegistryEntry
from hermes_pulse.source_registry import load_source_registry


FIXTURE_XML = Path("fixtures/feed_samples/official_feed.xml").read_text()
RDF_FIXTURE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns="http://purl.org/rss/1.0/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <channel rdf:about="https://applech2.com/">
    <title>Applech2</title>
    <link>https://applech2.com/</link>
    <description>Apple rumors and news.</description>
  </channel>
  <item rdf:about="https://applech2.com/2026/04/index-update">
    <title>Index update</title>
    <link>https://applech2.com/2026/04/index-update</link>
    <description>Rumor roundup.</description>
  </item>
</rdf:RDF>
"""


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


def test_feed_registry_connector_collects_rdf_feed_items_with_provenance() -> None:
    entry = SourceRegistryEntry(
        id="applech2",
        source_family="news",
        domain="applech2.com",
        title="Applech2",
        acquisition_mode="rss_poll",
        authority_tier="trusted_secondary",
        rss_url="https://applech2.com/index.rdf",
    )
    connector = FeedRegistryConnector(fetcher=lambda url: RDF_FIXTURE_XML)

    items = connector.collect([entry])

    assert len(items) == 1
    item = items[0]
    assert item.id == "applech2:https://applech2.com/2026/04/index-update"
    assert item.source == "applech2"
    assert item.title == "Index update"
    assert item.excerpt == "Rumor roundup."
    assert item.url == "https://applech2.com/2026/04/index-update"
    assert item.provenance is not None
    assert item.provenance.primary_source_url == "https://applech2.com/2026/04/index-update"
    assert item.citation_chain[0].relation == "secondary"


def test_feed_registry_connector_fetches_live_payloads_when_no_fetcher_is_provided(monkeypatch) -> None:
    requested_urls: list[str] = []

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return FIXTURE_XML.encode("utf-8")

    def fake_urlopen(url: str, *args, **kwargs) -> DummyResponse:
        requested_urls.append(url)
        return DummyResponse()

    monkeypatch.setattr(feed_registry_module, "urlopen", fake_urlopen)
    entry = SourceRegistryEntry(
        id="official-blog",
        source_family="company_updates",
        domain="example.com",
        title="Example Official Blog",
        acquisition_mode="rss_poll",
        authority_tier="primary",
        rss_url="https://example.com/feed.xml",
    )

    items = FeedRegistryConnector().collect([entry])

    assert requested_urls == ["https://example.com/feed.xml"]
    assert [item.title for item in items] == ["Launch update"]
