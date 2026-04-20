from pathlib import Path
from urllib.parse import parse_qs, urlparse

from hermes_pulse.connectors.known_source_search import KnownSourceSearchConnector
from hermes_pulse.models import SourceRegistryEntry


FIXTURE_HTML = Path("fixtures/search_samples/known_source_results.html").read_text()


def test_known_source_search_connector_collects_domain_constrained_results_with_provenance() -> None:
    entry = SourceRegistryEntry(
        id="discovery-only-source",
        source_family="discovery_blog",
        domain="discover.example.net",
        title="Discovery Source",
        acquisition_mode="known_source_search",
        authority_tier="discovery_only",
        search_hints=["rumors", "supply chain"],
        topical_scopes=["discovery"],
        language="en",
        requires_primary_confirmation=True,
    )

    connector = KnownSourceSearchConnector(fetcher=lambda url: FIXTURE_HTML)

    items = connector.collect([entry])

    assert len(items) == 1
    item = items[0]
    assert item.id == "discovery-only-source:https://discover.example.net/2026/04/discovery-scoop"
    assert item.source == "discovery-only-source"
    assert item.source_kind == "document"
    assert item.title == "Discovery scoop"
    assert item.excerpt == "A focused rumor roundup from a curated source."
    assert item.url == "https://discover.example.net/2026/04/discovery-scoop"
    assert item.provenance is not None
    assert item.provenance.provider == "discover.example.net"
    assert item.provenance.acquisition_mode == "known_source_search"
    assert item.provenance.authority_tier == "discovery_only"
    assert item.provenance.primary_source_url == "https://discover.example.net/2026/04/discovery-scoop"
    assert item.provenance.raw_record_id == "https://discover.example.net/2026/04/discovery-scoop"
    assert item.citation_chain[0].label == "Discovery scoop"
    assert item.citation_chain[0].url == "https://discover.example.net/2026/04/discovery-scoop"
    assert item.citation_chain[0].relation == "secondary"
    assert item.metadata["search_rank"] == 1
    assert item.metadata["search_query"] == "site:discover.example.net rumors supply chain"


def test_known_source_search_connector_builds_site_scoped_query_and_skips_non_search_entries() -> None:
    requested_urls: list[str] = []

    def fetcher(url: str) -> str:
        requested_urls.append(url)
        return FIXTURE_HTML

    entries = [
        SourceRegistryEntry(
            id="discovery-only-source",
            source_family="discovery_blog",
            domain="discover.example.net",
            title="Discovery Source",
            acquisition_mode="known_source_search",
            authority_tier="discovery_only",
            search_hints=["rumors", "supply chain"],
        ),
        SourceRegistryEntry(
            id="official-blog",
            source_family="company_updates",
            domain="example.com",
            title="Example Official Blog",
            acquisition_mode="rss_poll",
            authority_tier="primary",
            rss_url="https://example.com/feed.xml",
            search_hints=["official updates"],
        ),
    ]

    items = KnownSourceSearchConnector(fetcher=fetcher).collect(entries)

    assert len(items) == 1
    assert len(requested_urls) == 1
    parsed = urlparse(requested_urls[0])
    assert parsed.netloc == "html.duckduckgo.com"
    assert parsed.path == "/html/"
    assert parse_qs(parsed.query)["q"] == ["site:discover.example.net rumors supply chain"]
