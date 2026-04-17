# Roadmap

## Build order

The implementation order should follow architecture seams, not doc history.

### Phase 0 — planning baseline
- finalize canonical docs
- define canonical objects
- define trigger registry
- define collection presets
- define SQLite state plan

### Phase 1 — minimum useful scheduled briefing
Focus on scheduled value first.

Build:
- morning/evening trigger profiles
- calendar connector
- Gmail connector
- Hermes connector
- notes connector
- candidate synthesis core
- digest rendering
- delivery adapter for one destination

Success criteria:
- stable morning/evening digests
- people bundle when schedule permits
- follow-up and resurfacing lanes work without X

### Phase 2 — X as source family
Build:
- X bookmarks
- X likes
- X home timeline diff state model
- X-specific ranking quota rules

Success criteria:
- X adds value without dominating output
- dedupe across home/bookmark/like works
- delivered IDs and suppression behave correctly

### Phase 3 — cross-agent memory imports
Build:
- ChatGPT export/manual import
- Grok manual/share-link import
- conversation provenance tracking

Success criteria:
- imported histories contribute to people/follow-up/resurfacing
- system remains honest about freshness and acquisition mode

### Phase 4 — event-driven triggers
Build:
- leave-now trigger
- mail.operational trigger
- shopping.replenishment trigger
- location-arrival/dwell trigger using minimal heuristics

Success criteria:
- short-form event outputs are useful and non-spammy
- carry-over into later digests works
- approval boundary respected for action_prep

### Phase 5 — self-improvement loop
Build:
- trigger run logs
- usefulness feedback capture
- review.trigger_quality

Success criteria:
- system can suggest threshold/quota tuning from actual logs

## Testing strategy

### Unit tests
- trigger profile selection
- candidate scoring
- suppression logic
- X diff algorithm
- bundle formation

### Integration tests
- morning digest without X still succeeds
- leave-now warning generated from calendar + place context
- bookmark outranks like outranks home diff
- event alert can carry over into evening follow-up
- import-based ChatGPT/Grok artifacts affect ranking with correct provenance

### Golden-output tests
Keep fixed fixtures for:
- morning digest
- evening digest
- leave-now warning
- shopping action prep
- location mini-digest

## Observability milestones
- trigger run counts
- delivery counts
- suppression counts by reason
- average candidate count before/after ranking
- ignored vs useful trigger review later
