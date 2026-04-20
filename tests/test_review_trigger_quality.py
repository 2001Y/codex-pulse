from pathlib import Path

import hermes_pulse.cli
from hermes_pulse.trigger_registry import get_trigger_profile


ROOT = Path(__file__).resolve().parents[1]
AUDIT_FIXTURE_PATH = ROOT / "fixtures/audit/trigger_quality.json"
SOURCE_REGISTRY_PATH = ROOT / "fixtures/source_registry/sample_sources.yaml"


def test_trigger_registry_exposes_review_trigger_quality_profile() -> None:
    profile = get_trigger_profile("review.trigger_quality.default")

    assert profile.family == "review"
    assert profile.event_type == "review.trigger_quality"
    assert profile.output_mode == "source_audit"
    assert profile.collection_preset == "trigger_quality_audit"


def test_review_trigger_quality_writes_source_audit(tmp_path: Path) -> None:
    output_path = tmp_path / "audit" / "trigger-quality.md"

    assert (
        hermes_pulse.cli.main(
            [
                "review-trigger-quality",
                "--source-registry",
                str(SOURCE_REGISTRY_PATH),
                "--audit-fixture",
                str(AUDIT_FIXTURE_PATH),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    content = output_path.read_text()
    assert content.startswith("# Trigger quality review")
    assert "notification_rate: 14" in content
    assert "ignored_rate: 9" in content
    assert "calendar.leave_now" in content
    assert "trusted-secondary-blog" in content
