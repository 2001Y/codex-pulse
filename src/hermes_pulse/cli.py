import argparse
from collections.abc import Callable, Sequence
from datetime import date, datetime, timezone
from pathlib import Path

from hermes_pulse.archive import write_morning_digest_archive
from hermes_pulse.collection import collect_for_trigger
from hermes_pulse.connectors.feed_registry import FeedRegistryConnector
from hermes_pulse.connectors.hermes_history import HermesHistoryConnector
from hermes_pulse.connectors.notes import NotesConnector
from hermes_pulse.delivery.local_markdown import LocalMarkdownDelivery
from hermes_pulse.models import CollectedItem, TriggerEvent, TriggerScope
from hermes_pulse.rendering import render_morning_digest
from hermes_pulse.source_registry import load_source_registry
from hermes_pulse.synthesis import synthesize_candidates
from hermes_pulse.trigger_registry import get_trigger_profile


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_REGISTRY = REPO_ROOT / "fixtures/source_registry/default_sources.yaml"


class BoundConnector:
    def __init__(self, collector: Callable[[], list[object]]) -> None:
        self._collector = collector

    def collect(self) -> list[object]:
        return self._collector()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-pulse")
    parser.add_argument("command", nargs="?", choices=("morning-digest",))
    parser.add_argument("--source-registry", type=Path)
    parser.add_argument("--feed-fixture", type=Path)
    parser.add_argument("--hermes-history", type=Path)
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    items: list[CollectedItem] = []

    if args.command == "morning-digest":
        markdown, items = _build_morning_digest(args)
        archive_root = args.archive_root or Path.home() / "Pulse"
        write_morning_digest_archive(
            markdown=markdown,
            items=items,
            archive_root=archive_root,
            archive_date=date.today().isoformat(),
        )
    elif args.output is not None:
        markdown = render_morning_digest([], [])
    else:
        return 0

    if args.output is not None:
        LocalMarkdownDelivery().deliver(markdown, args.output)

    return 0


def _build_morning_digest(args: argparse.Namespace) -> tuple[str, list[CollectedItem]]:
    profile = get_trigger_profile("digest.morning.default")
    source_registry = load_source_registry(args.source_registry or DEFAULT_SOURCE_REGISTRY)
    feed_fetcher = _build_feed_fetcher(args.feed_fixture)
    occurred_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    trigger = TriggerEvent(
        id="scheduled:digest.morning.default",
        type=profile.event_type,
        profile_id=profile.id,
        occurred_at=occurred_at,
        scope=TriggerScope(),
    )
    connectors = {
        "feed_registry": BoundConnector(
            lambda: FeedRegistryConnector(fetcher=feed_fetcher).collect(source_registry)
        ),
    }
    if args.hermes_history is not None:
        connectors["hermes_history"] = BoundConnector(
            lambda: HermesHistoryConnector().collect(args.hermes_history)
        )
    if args.notes is not None:
        connectors["notes"] = BoundConnector(lambda: NotesConnector().collect(args.notes))
    items = collect_for_trigger(trigger, profile, connectors)
    candidates = synthesize_candidates(items)
    return render_morning_digest(candidates, items), items


def _build_feed_fetcher(feed_fixture: Path | None) -> Callable[[str], str] | None:
    if feed_fixture is None:
        return None
    payload = feed_fixture.read_text()
    return lambda url: payload


if __name__ == "__main__":
    raise SystemExit(main())
