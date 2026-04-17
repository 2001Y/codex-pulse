# Trigger Model

## Principle

Time-of-day triggers and event-driven triggers should coexist in one registry.
The system should not care whether a trigger came from cron, polling, or webhook once it becomes a `TriggerEvent`.

## Trigger categories

### 1. Scheduled digests
These are broad-scope triggers.

- `digest.morning`
- `digest.evening`

Characteristics:
- wide collection scope
- multi-section output
- larger quota
- lower action aggressiveness by default

### 2. Operational event triggers
These are narrow, high-intent triggers.

- `calendar.leave_now`
- `calendar.gap_window`
- `mail.operational`
- `shopping.replenishment`

Characteristics:
- tight collection scope
- short output
- higher urgency
- can escalate to action preparation

### 3. Context / location triggers
These use movement or place change as the trigger substrate.

- `location.area_change`
- `location.arrival`
- `location.dwell`
- later: `location.routine_break`

Example use cases:
- nearby saved restaurant reminder
- sightseeing / detour ideas
- arrival-aware prep before the next appointment
- location-aware replenishment or pickup suggestions

### 4. Self-review triggers
These improve the system itself.

- `review.trigger_quality`

This trigger inspects logs and asks:
- which triggers were useful?
- which were noisy?
- which were late or early?
- which should be retuned or suppressed?

## Practical trigger catalog

| Trigger | Purpose | Typical output | Default action ceiling |
|---|---|---|---|
| `digest.morning` | prep for the day | `digest` | 1 |
| `digest.evening` | closure and carry-over | `digest` | 1 |
| `location.arrival` | detect likely arrival | `mini_digest` or `nudge` | 1 |
| `location.dwell` | detect meaningful staying time | `mini_digest` | 1 |
| `calendar.leave_now` | lateness prevention | `warning` | 1 |
| `calendar.gap_window` | opportunistic suggestions before next event | `mini_digest` | 1 |
| `mail.operational` | react to reservation/delivery/change | `warning` or `action_prep` | 2 |
| `shopping.replenishment` | repurchase / refill / restock | `action_prep` | 2 |
| `review.trigger_quality` | self-improvement | `summary_for_review` | 0 |

## TriggerProfile examples

### Morning
```json
{
  "id": "digest.morning.default",
  "family": "scheduled",
  "eventType": "digest.morning",
  "collectionPreset": "broad_day_start",
  "outputMode": "digest",
  "actionCeiling": 1,
  "cooldownMinutes": 360,
  "quotas": { "x_items": 3, "resurface_items": 3, "people_bundles": 2 }
}
```

### Leave-now
```json
{
  "id": "calendar.leave_now.default",
  "family": "event",
  "eventType": "calendar.leave_now",
  "collectionPreset": "narrow_leave_now",
  "outputMode": "warning",
  "actionCeiling": 1,
  "cooldownMinutes": 20
}
```

### Replenishment
```json
{
  "id": "shopping.replenishment.default",
  "family": "event",
  "eventType": "shopping.replenishment",
  "collectionPreset": "shopping_context",
  "outputMode": "action_prep",
  "actionCeiling": 2,
  "cooldownMinutes": 1440
}
```

## Location triggers: v1 heuristics

A simple arrival heuristic is enough for v1.
For example:
- moved more than ~800m
- recent average speed fell from travel speed to low speed
- current area stayed roughly stable for 8-15 minutes

This is enough to infer “likely arrived somewhere” without overbuilding a location intelligence subsystem.

## Mail triggers: v1 interpretation

Only operational mail should trigger immediate behavior.
Examples:
- reservation confirmation/change
- delivery notification
- payment issue
- calendar invite / reschedule
- commerce / subscription events

Generic newsletters should not be an event trigger.
They may still feed digest content if relevant.

## Trigger coexistence rules

### Scheduled digests do not replace event triggers
Morning/evening provide broad coherence.
Event triggers provide timeliness.

### Event triggers do not eliminate digest carry-over
If something was already alerted by an event trigger but remains open, it may reappear later inside digest follow-up sections.

### Trigger-specific suppression is mandatory
Global dedupe is insufficient.
Suppression should consider:
- trigger family
- candidate kind
- still-open status
- cooldown window
- delivery outcome

## Self-improvement loop

`review.trigger_quality` should periodically inspect:
- notification rate
- dismiss / ignore rate
- repeated false positives
- time-to-usefulness
- trigger overlap

Outputs should be suggestions like:
- raise dwell threshold
- lower leave-now buffer
- reduce X quota in evening
- suppress shopping reminders for 7 days after dismissal
