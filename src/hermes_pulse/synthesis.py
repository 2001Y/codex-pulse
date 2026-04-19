from collections.abc import Iterable

from hermes_pulse.models import Candidate, CollectedItem


SECTION_ORDER = ("today", "incoming", "followup", "resurface", "feed_updates")


def synthesize_candidates(items: Iterable[CollectedItem]) -> list[Candidate]:
    candidates = [_candidate_for_item(item) for item in items]
    return sorted(candidates, key=lambda candidate: (-candidate.score, candidate.id))


def bundle_candidates_into_sections(candidates: Iterable[Candidate]) -> dict[str, list[Candidate]]:
    sections = {section: [] for section in SECTION_ORDER}
    for candidate in candidates:
        section = _section_for_candidate(candidate)
        sections[section].append(candidate)
    for section_name in sections:
        sections[section_name].sort(key=lambda candidate: (-candidate.score, candidate.id))
    return sections


def _candidate_for_item(item: CollectedItem) -> Candidate:
    reasons: list[str] = []
    score = 0.0

    if _metadata_flag(item, "future_relevance"):
        score += 4.0
        reasons.append("future_relevance")

    if _is_open_loop(item):
        score += 3.0
        reasons.append("open_loop")

    authority_tier = item.provenance.authority_tier if item.provenance is not None else None
    if item.source_kind == "feed_item":
        authority_score = {
            "primary": 2.0,
            "trusted_secondary": 1.0,
            "discovery_only": 0.5,
        }.get(authority_tier, 0.0)
        if authority_score:
            score += authority_score
            reasons.append(f"authority:{authority_tier}")

    if _has_explicit_intent(item):
        score += 1.5
        reasons.append("saved_signal" if item.intent_signals and item.intent_signals.saved else "explicit_intent")

    return Candidate(
        id=f"candidate:{item.id}",
        kind=_candidate_kind_for_item(item),
        item_ids=[item.id],
        trigger_relevance=score,
        actionability="info",
        score=score,
        reasons=reasons,
        suppression_scope=[item.source, item.id],
    )


def _candidate_kind_for_item(item: CollectedItem) -> str:
    if _metadata_flag(item, "future_relevance"):
        return "today"
    if _is_open_loop(item):
        return "followup"
    if _has_explicit_intent(item):
        return "resurface"
    return "incoming"


def _section_for_candidate(candidate: Candidate) -> str:
    if candidate.kind == "incoming" and candidate.reasons and candidate.item_ids:
        if any(reason.startswith("authority:") for reason in candidate.reasons):
            return "feed_updates"
    if candidate.kind in SECTION_ORDER:
        return candidate.kind
    return "incoming"


def _metadata_flag(item: CollectedItem, key: str) -> bool:
    return bool(item.metadata.get(key, False))


def _is_open_loop(item: CollectedItem) -> bool:
    if item.intent_signals is not None and item.intent_signals.unresolved:
        return True
    return _metadata_flag(item, "open_loop")


def _has_explicit_intent(item: CollectedItem) -> bool:
    if item.intent_signals is not None and item.intent_signals.saved:
        return True
    return _metadata_flag(item, "explicit_intent")
