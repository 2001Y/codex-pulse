# Source Note: X

## Role of X in the system

X is both:
- an **external change surface**
- a **personal memory surface**

But X should be treated as **source-specific**, not system-defining.
The product should still work if X access is degraded.

## Three X streams

Model X as three related but different streams:
- `x_home_timeline`
- `x_bookmarks`
- `x_likes`

Their intent strength is different:
- bookmark = explicit save intent
- like = weaker taste signal
- home timeline = noisy novelty stream

## Home timeline diff problem

Home timeline diff cannot rely only on a single `last_seen_id` because:
- feed ordering can shift
- older posts can reappear
- the same post can later appear via bookmark or like
- delivered items must not be resent blindly

## Recommended per-source state

Persist:
- `last_poll_at`
- `last_top_id`
- `seen_ids` (TTL/LRU, e.g. 7-14 days)
- `last_snapshot_ids` (top N, e.g. 100-300)
- `delivered_ids`

## Recommended algorithm

### Home timeline
1. fetch latest `N`
2. compute `candidate_ids = current_ids - seen_ids`
3. filter by recency / grace window
4. remove `delivered_ids`
5. update state

### Bookmarks / likes
1. fetch latest `N`
2. unseen IDs become additions
3. removals can be ignored in v1
4. update `seen_ids` and `delivered_ids`

## De-duplication across X streams

If the same post appears in multiple streams, merge into one canonical post with multiple source tags.

Example metadata:

```json
{
  "sources": ["x_home_timeline", "x_bookmark"],
  "first_seen_via": "x_home_timeline",
  "saved": true,
  "liked": false
}
```

## Inclusion policy

Home timeline items should only appear when they overlap with:
- today/tomorrow schedule
- a near-future person/org
- recent conversation themes
- saved-interest clusters
- or unusually high-signal novelty within quota

Bookmarks and likes can also enter via resurfacing when:
- not recently surfaced
- context overlap exists
- long-neglected but still useful

## Quota stance

Do not let X dominate output.
Examples:
- morning/evening digest: at most one X-focused section
- total visible X items: small fixed quota
- event-driven triggers: X should usually be supporting evidence, not the trigger itself

## Fallback order when home access is constrained

1. official home timeline API
2. synthetic home from selected lists / followed-user streams
3. bookmarks + likes + selected list diffs
4. browser automation as opt-in experimental fallback

## Product takeaway

The right product posture is:
- careful delta detection
- aggressive dedupe
- strict quota control
- ranking below explicit user intent
