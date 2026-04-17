# System Architecture

## One-system model

Do not build separate systems for:
- morning digest
- evening digest
- proactive trigger messages

Build **one trigger-driven system** with different trigger profiles.

## Topology

A single runner / daemon / CLI is enough for v1.
It can be activated by:
- cron
- lightweight polling
- webhooks when available
- manual invocation for testing

## Canonical A-F pipeline

### A. Trigger events
The system begins with a `TriggerEvent` produced by a `TriggerProfile`.
Examples:
- `digest.morning`
- `digest.evening`
- `location.arrival`
- `calendar.leave_now`
- `mail.operational`
- `shopping.replenishment`
- `review.trigger_quality`

### B. Collection
The trigger chooses a narrow `AcquisitionPlan`.
The system collects only what is needed for that trigger:
- live data where possible
- imported artifacts when live access is unavailable
- recent state for suppression and carry-over

### C. Synthesis / ranking / suppression
Collected evidence is turned into:
- normalized items
- bundles
- candidates
- suppression decisions

This is where the product actually decides what matters.

### D. Output generation
The system chooses one output contract:
- `digest`
- `mini_digest`
- `warning`
- `nudge`
- `action_prep`
- later: `summary_for_review`, `handoff`

### E. Delivery / action execution
After output generation, the system:
- delivers the result
- or prepares a user-approved action
- or drafts but does not send

### F. State / memory / audit
Persist:
- cursors
- artifact provenance
- delivery history
- suppression decisions
- approval history
- trigger feedback
- run logs

## Canonical objects

### TriggerEvent
```ts
export type TriggerEvent = {
  id: string
  type: string
  profileId: string
  occurredAt: string
  scope: {
    timeWindow?: { start: string; end: string }
    placeWindow?: { lat: number; lon: number; radiusM?: number }
    entities?: string[]
  }
  evidenceRefs?: string[]
  metadata?: Record<string, unknown>
}
```

### TriggerProfile
```ts
export type TriggerProfile = {
  id: string
  family: 'scheduled' | 'event' | 'review'
  eventType: string
  collectionPreset: string
  outputMode: 'digest' | 'mini_digest' | 'warning' | 'nudge' | 'action_prep'
  actionCeiling: 0 | 1 | 2 | 3
  cooldownMinutes?: number
  rankingWeights?: Record<string, number>
  quotas?: Record<string, number>
}
```

### CollectedItem
```ts
export type CollectedItem = {
  id: string
  source: string
  sourceKind: 'event' | 'email' | 'conversation' | 'note' | 'post' | 'place' | 'artifact'
  title?: string
  excerpt?: string
  body?: string
  url?: string
  people?: string[]
  topics?: string[]
  placeRefs?: string[]
  timestamps?: {
    createdAt?: string
    updatedAt?: string
    startAt?: string
    endAt?: string
  }
  intentSignals?: {
    saved?: boolean
    liked?: boolean
    unread?: boolean
    unresolved?: boolean
  }
  provenance: {
    provider: string
    acquisitionMode: 'local_store' | 'official_api' | 'official_export' | 'share_link_import' | 'manual_import' | 'browser_automation_experimental'
    artifactId?: string
    rawRecordId?: string
  }
  metadata?: Record<string, unknown>
}
```

### Candidate
```ts
export type Candidate = {
  id: string
  kind: 'today' | 'people' | 'incoming' | 'resurface' | 'followup' | 'tomorrow' | 'tonight' | 'warning' | 'action_prep'
  itemIds: string[]
  triggerRelevance: number
  actionability: 'none' | 'info' | 'prep' | 'approval_needed'
  score: number
  reasons: string[]
  suppressionScope?: string[]
}
```

## Degradation rules

The system must still work when some connectors are unavailable.
Examples:
- no ChatGPT import available -> still produce briefings from calendar/email/X/Hermes
- no X home access -> still use bookmarks/likes or omit X gracefully
- no maps/place data -> still produce people/open-loop lanes

## Why not microservices

The repo is about correctness of selection, ranking, and action gating.
Microservice decomposition would increase ceremony before proving value.

v1 should prefer:
- one codebase
- one local DB
- one trigger registry
- one shared ranking/suppression core
- thin source adapters
- thin delivery adapters
