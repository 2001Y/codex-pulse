from pathlib import Path

import hermes_pulse.cli
from hermes_pulse.trigger_registry import get_trigger_profile


ROOT = Path(__file__).resolve().parents[1]
LOCATION_FIXTURE_PATH = ROOT / "fixtures/location/location_arrival.json"
SOURCE_REGISTRY_PATH = ROOT / "fixtures/source_registry/sample_sources.yaml"


def test_trigger_registry_exposes_location_arrival_profile() -> None:
    profile = get_trigger_profile("location.arrival.default")

    assert profile.family == "event"
    assert profile.event_type == "location.arrival"
    assert profile.output_mode == "mini_digest"
    assert profile.collection_preset == "location_arrival"


def test_location_arrival_writes_mini_digest(tmp_path: Path) -> None:
    output_path = tmp_path / "mini-digest" / "location-arrival.md"

    assert (
        hermes_pulse.cli.main(
            [
                "location-arrival",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--location-fixture",
                str(LOCATION_FIXTURE_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    content = output_path.read_text()
    assert content.startswith("# Arrival context")
    assert "Shibuya Station" in content
    assert "Pick up package" in content
    assert "Check dinner options nearby" in content
    assert "https://maps.google.com/?q=Shibuya+Station" in content
