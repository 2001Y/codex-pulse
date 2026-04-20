from pathlib import Path

import hermes_pulse.cli
from hermes_pulse.trigger_registry import get_trigger_profile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY_PATH = ROOT / "fixtures/source_registry/sample_sources.yaml"
CALENDAR_FIXTURE_PATH = ROOT / "fixtures/google_workspace/calendar_gap_window_events.json"


def test_trigger_registry_exposes_calendar_gap_window_profile() -> None:
    profile = get_trigger_profile("calendar.gap_window.default")

    assert profile.family == "event"
    assert profile.event_type == "calendar.gap_window"
    assert profile.output_mode == "mini_digest"
    assert profile.collection_preset == "calendar_gap_window"


def test_gap_window_writes_mini_digest_for_free_time_before_next_event(tmp_path: Path) -> None:
    output_path = tmp_path / "mini-digest" / "gap-window.md"

    assert (
        hermes_pulse.cli.main(
            [
                "gap-window-mini-digest",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--calendar-fixture",
                str(CALENDAR_FIXTURE_PATH),
                "--now",
                "2026-04-21T10:15:00Z",
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    content = output_path.read_text()
    assert content.startswith("# Gap window")
    assert "135 min free" in content
    assert "Afternoon check-in" in content
    assert "2026-04-21T12:30:00Z" in content


def test_gap_window_skips_output_when_no_meaningful_free_window_exists(tmp_path: Path) -> None:
    output_path = tmp_path / "mini-digest" / "gap-window.md"

    assert (
        hermes_pulse.cli.main(
            [
                "gap-window-mini-digest",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--calendar-fixture",
                str(CALENDAR_FIXTURE_PATH),
                "--now",
                "2026-04-21T12:20:00Z",
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    assert not output_path.exists()
