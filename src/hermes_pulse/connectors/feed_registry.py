from collections.abc import Callable, Sequence
from xml.etree import ElementTree

from hermes_pulse.models import CitationLink, CollectedItem, ItemTimestamps, Provenance, SourceRegistryEntry


class FeedRegistryConnector:
    id = "feed_registry"
    source_family = "feed_registry"

    def __init__(self, fetcher: Callable[[str], str]) -> None:
        self._fetcher = fetcher

    def collect(self, entries: Sequence[SourceRegistryEntry]) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        for entry in entries:
            if not entry.rss_url:
                continue
            payload = self._fetcher(entry.rss_url)
            items.extend(self._parse_items(entry, payload))
        return items

    def _parse_items(self, entry: SourceRegistryEntry, payload: str) -> list[CollectedItem]:
        root = ElementTree.fromstring(payload)
        parsed_items: list[CollectedItem] = []
        for raw_item in root.findall("./channel/item"):
            title = _text(raw_item, "title")
            url = _text(raw_item, "link")
            guid = _text(raw_item, "guid") or url or title or entry.id
            relation = "primary" if entry.authority_tier == "primary" else "secondary"
            parsed_items.append(
                CollectedItem(
                    id=f"{entry.id}:{guid}",
                    source=entry.id,
                    source_kind="feed_item",
                    title=title,
                    excerpt=_text(raw_item, "description"),
                    url=url,
                    timestamps=ItemTimestamps(created_at=_text(raw_item, "pubDate")),
                    provenance=Provenance(
                        provider=entry.domain,
                        acquisition_mode=entry.acquisition_mode,
                        authority_tier=entry.authority_tier,
                        primary_source_url=url,
                        raw_record_id=guid,
                    ),
                    citation_chain=[CitationLink(label=title or entry.title, url=url or entry.rss_url, relation=relation)],
                )
            )
        return parsed_items


def _text(element: ElementTree.Element, tag: str) -> str | None:
    node = element.find(tag)
    if node is None or node.text is None:
        return None
    return node.text.strip()
