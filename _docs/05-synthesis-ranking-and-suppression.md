# Synthesis, Ranking, and Suppression

## Purpose

Collection only gathers evidence.
This stage decides what actually deserves attention.

## Core operations

1. normalize source items
2. link by people, time, place, topic, and unresolved status
3. form bundles
4. create candidates
5. score candidates
6. apply quotas
7. suppress duplicates/noise/recent repeats

## Bundle types

### People bundle
Combines:
- upcoming meeting
- prior conversations
- email threads
- notes
- saved posts or links relevant to that person/org

### Open-loop bundle
Combines:
- unread or unresolved email
- unfinished conversation threads
- follow-up notes
- prior reminders that were not completed

### Resurfacing bundle
Combines:
- neglected bookmarks
- old likes
- stale notes
- prior conversations or documents that newly overlap with current context

### Place/time bundle
Combines:
- current or upcoming place
- travel feasibility
- gap windows
- nearby saved places
- local suggestions when the trigger justifies them

## Ranking signals

Global ranking should prefer:
1. future relevance
2. people overlap with upcoming events
3. open-loop urgency
4. explicit user-intent signal
5. recency / novelty
6. passive signal strength

## X-specific ranking rules

Within the X family:
- bookmark > like > home timeline

X-origin items should be promoted only if at least one is true:
- overlaps with today/tomorrow schedule
- overlaps with a person/org in upcoming meetings
- overlaps with recent conversation topics
- overlaps with saved-interest clusters
- is unusually high-signal and within quota

## Candidate quotas

Quotas prevent the product from becoming a feed dump.

Suggested v1 defaults:
- morning total candidates rendered: 6-10
- evening total candidates rendered: 6-10
- X-specific visible items: 0-3
- resurfacing items: 1-3
- people bundles: up to 2
- warnings: usually 1

## Resurfacing policy

### Bookmarks
- resurfacing can begin relatively early because the save is explicit
- typical age threshold: 3+ days unless strongly relevant sooner

### Likes
- weaker signal, so require more context overlap or longer age
- typical age threshold: 7-90 days depending on quota and overlap

### Notes / conversations
- resurface when linked to a near-future event/person/topic
- otherwise prefer digest carry-over rather than aggressive random recall

## Suppression model

Suppression should not be a single global set.
Use dimensions such as:
- candidate ID
- underlying item IDs
- trigger family
- output mode
- still-open status
- suppression reason
- cooldown expiry

Example reasons:
- already delivered in same trigger family
- already actioned
- recently dismissed
- too weak after ranking cutoff
- duplicate of stronger candidate bundle

## Carry-over behavior

An event alert should not permanently remove an item from later digests if it remains open.
Instead:
- suppress duplicate wording in the short term
- allow re-entry into follow-up lanes if unresolved
- lower score if recently seen but not resolved

## Suggested scoring components

```ts
score =
  futureRelevance * w1 +
  peopleOverlap * w2 +
  openLoopUrgency * w3 +
  explicitIntent * w4 +
  novelty * w5 +
  sourceConfidence * w6 -
  suppressionPenalty -
  alreadyDeliveredPenalty
```

## Product-level safeguard

The synthesis layer is the main guardrail against product drift.
If this layer is weak, the product degenerates into:
- a feed reader
- a mail summarizer
- an X recap
- or an over-notifying proactive bot
