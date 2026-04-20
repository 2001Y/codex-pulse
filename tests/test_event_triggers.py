from pathlib import Path

import hermes_pulse.cli
from hermes_pulse.trigger_registry import get_trigger_profile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY_PATH = ROOT / "fixtures/source_registry/sample_sources.yaml"
MAIL_FIXTURE_PATH = ROOT / "fixtures/google_workspace/gmail_operational_messages.json"
SHOPPING_NOTES_PATH = ROOT / "fixtures/notes/shopping_replenishment.md"
FEED_FIXTURE_PATH = ROOT / "fixtures/feed_samples/official_feed.xml"
SEARCH_FIXTURE_PATH = ROOT / "fixtures/search_samples/known_source_results.html"


def test_trigger_registry_exposes_mail_operational_profile() -> None:
    profile = get_trigger_profile("mail.operational.default")

    assert profile.family == "event"
    assert profile.event_type == "mail.operational"
    assert profile.output_mode == "warning"
    assert profile.collection_preset == "mail_operational"


def test_trigger_registry_exposes_shopping_replenishment_profile() -> None:
    profile = get_trigger_profile("shopping.replenishment.default")

    assert profile.family == "event"
    assert profile.event_type == "shopping.replenishment"
    assert profile.output_mode == "action_prep"
    assert profile.collection_preset == "shopping_replenishment"


def test_trigger_registry_exposes_feed_update_profile() -> None:
    profile = get_trigger_profile("feed.update.default")

    assert profile.family == "event"
    assert profile.event_type == "feed.update"
    assert profile.output_mode == "nudge"
    assert profile.collection_preset == "known_source_delta"


def test_mail_operational_warning_writes_changed_reservation_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "warnings" / "mail-operational.md"

    assert (
        hermes_pulse.cli.main(
            [
                "mail-operational",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--gmail-fixture",
                str(MAIL_FIXTURE_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    warning = output_path.read_text()
    assert warning.startswith("# Operational mail")
    assert "Dinner reservation time changed" in warning
    assert "Reservations <reservations@example.com>" in warning
    assert "Your dinner reservation was moved to 19:30." in warning


def test_shopping_replenishment_writes_action_prep(tmp_path: Path) -> None:
    output_path = tmp_path / "action-prep" / "shopping.md"

    assert (
        hermes_pulse.cli.main(
            [
                "shopping-replenishment",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--notes",
                str(SHOPPING_NOTES_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    action_prep = output_path.read_text()
    assert action_prep.startswith("# Shopping action prep")
    assert "Coffee beans" in action_prep
    assert "Kurasu" in action_prep
    assert "Running low for this week" in action_prep
    assert "https://example.com/products/coffee-beans" in action_prep


def test_feed_update_writes_nudge_for_primary_source_update(tmp_path: Path) -> None:
    output_path = tmp_path / "nudges" / "feed-update.md"

    assert (
        hermes_pulse.cli.main(
            [
                "feed-update",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--feed-fixture",
                str(FEED_FIXTURE_PATH),
                "--search-fixture",
                str(SEARCH_FIXTURE_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    nudge = output_path.read_text()
    assert nudge.startswith("# Feed update")
    assert "Launch update" in nudge
    assert "official-blog" in nudge
    assert "https://example.com/posts/launch-update" in nudge
