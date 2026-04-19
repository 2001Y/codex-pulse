from hermes_pulse.models import CollectedItem, IntentSignals, Provenance
from hermes_pulse.synthesis import bundle_candidates_into_sections, synthesize_candidates


def make_item(
    item_id: str,
    *,
    source: str = "notes",
    source_kind: str = "note",
    authority_tier: str | None = None,
    future_relevance: bool = False,
    open_loop: bool = False,
    saved: bool = False,
    explicit_intent: bool = False,
) -> CollectedItem:
    acquisition_mode = "rss_poll" if source_kind == "feed_item" else "local_store"
    return CollectedItem(
        id=item_id,
        source=source,
        source_kind=source_kind,
        title=item_id,
        intent_signals=IntentSignals(saved=saved, unresolved=open_loop),
        provenance=Provenance(
            provider=source,
            acquisition_mode=acquisition_mode,
            authority_tier=authority_tier,
        ),
        metadata={
            "future_relevance": future_relevance,
            "explicit_intent": explicit_intent,
        },
    )


def test_synthesize_candidates_prefers_future_open_loops_authority_and_intent() -> None:
    items = [
        make_item(
            "secondary-feed",
            source="trusted-secondary-blog",
            source_kind="feed_item",
            authority_tier="trusted_secondary",
        ),
        make_item("saved-note", saved=True),
        make_item(
            "primary-feed",
            source="official-blog",
            source_kind="feed_item",
            authority_tier="primary",
        ),
        make_item("open-loop", open_loop=True),
        make_item("future-note", future_relevance=True),
    ]

    candidates = synthesize_candidates(items)
    candidates_by_item_id = {candidate.item_ids[0]: candidate for candidate in candidates}

    assert candidates[0].item_ids == ["future-note"]
    assert candidates_by_item_id["future-note"].score > candidates_by_item_id["open-loop"].score
    assert candidates_by_item_id["open-loop"].score > candidates_by_item_id["primary-feed"].score
    assert candidates_by_item_id["primary-feed"].score > candidates_by_item_id["secondary-feed"].score
    assert candidates_by_item_id["saved-note"].score > candidates_by_item_id["secondary-feed"].score

    assert candidates_by_item_id["future-note"].kind == "today"
    assert candidates_by_item_id["open-loop"].kind == "followup"
    assert candidates_by_item_id["primary-feed"].kind == "incoming"
    assert candidates_by_item_id["saved-note"].kind == "resurface"

    assert "future_relevance" in candidates_by_item_id["future-note"].reasons
    assert "open_loop" in candidates_by_item_id["open-loop"].reasons
    assert "authority:primary" in candidates_by_item_id["primary-feed"].reasons
    assert "saved_signal" in candidates_by_item_id["saved-note"].reasons


def test_bundle_candidates_into_digest_sections_and_sort_by_score() -> None:
    items = [
        make_item(
            "secondary-feed",
            source="trusted-secondary-blog",
            source_kind="feed_item",
            authority_tier="trusted_secondary",
        ),
        make_item("saved-note", saved=True),
        make_item(
            "primary-feed",
            source="official-blog",
            source_kind="feed_item",
            authority_tier="primary",
        ),
        make_item("open-loop", open_loop=True),
        make_item("future-note", future_relevance=True),
    ]

    sections = bundle_candidates_into_sections(synthesize_candidates(items))

    assert list(sections) == ["today", "incoming", "followup", "resurface", "feed_updates"]
    assert [candidate.item_ids[0] for candidate in sections["today"]] == ["future-note"]
    assert sections["incoming"] == []
    assert [candidate.item_ids[0] for candidate in sections["followup"]] == ["open-loop"]
    assert [candidate.item_ids[0] for candidate in sections["resurface"]] == ["saved-note"]
    assert [candidate.item_ids[0] for candidate in sections["feed_updates"]] == [
        "primary-feed",
        "secondary-feed",
    ]
