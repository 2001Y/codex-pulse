import json
from pathlib import Path

import hermes_pulse
from hermes_pulse.connectors.feed_registry import DEFAULT_HEADERS as FEED_HEADERS
from hermes_pulse.connectors.known_source_search import DEFAULT_HEADERS as SEARCH_HEADERS


ROOT = Path(__file__).resolve().parents[1]


def test_package_metadata_and_runtime_strings_use_codex_pulse_identity() -> None:
    package_json = json.loads((ROOT / "package.json").read_text())

    assert package_json["name"] == "codex-pulse"
    assert package_json["description"].startswith("Codex Pulse")
    assert hermes_pulse.__doc__ == "Codex Pulse runtime package."
    assert "CodexPulse/0.1" in FEED_HEADERS["User-Agent"]
    assert "CodexPulse/0.1" in SEARCH_HEADERS["User-Agent"]
    assert "hermes-pulse" not in FEED_HEADERS["User-Agent"]
    assert "hermes-pulse" not in SEARCH_HEADERS["User-Agent"]


def test_user_facing_docs_and_assets_use_codex_pulse_identity() -> None:
    identity_files = [
        ROOT / "README.md",
        ROOT / "README.ja.md",
        ROOT / "_docs" / "README.md",
        ROOT / "_docs" / "01-product-thesis.md",
        ROOT / "_docs" / "source-notes" / "feeds-and-source-registry.md",
        ROOT / "docs" / "plans" / "2026-04-20-codex-pulse-phase1-foundation.md",
        ROOT / "assets" / "overview-architecture.svg",
        ROOT / "assets" / "overview-architecture.ja.svg",
    ]

    for path in identity_files:
        content = path.read_text()
        assert "Codex Pulse" in content, f"expected Codex Pulse identity in {path}"
        assert "Hermes Pulse" not in content, f"unexpected Hermes Pulse identity in {path}"
