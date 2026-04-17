# Output, Delivery, and Actions

## Output contracts

The system should emit a small set of explicit output modes.

### `digest`
A multi-section briefing used for morning/evening editions.

### `mini_digest`
A shorter contextual output used for triggers such as location arrival or gap windows.

### `warning`
A high-urgency message such as leave-now or schedule risk.

### `nudge`
A low-urgency suggestion that is worth surfacing but not demanding.

### `action_prep`
An execution-adjacent output that prepares a side effect but stops before approval-required completion.
Examples:
- prefilled purchase candidate
- draft reservation flow
- draft reply / draft reminder

## Morning digest structure

Suggested sections:
- `today`
- `people`
- `incoming`
- `followup`
- `resurface`
- optional `x_now` if relevant and within quota

Morning output should optimize for:
- preparation
- prioritization
- open-loop triage
- contextual recall before meetings

## Evening digest structure

Suggested sections:
- `today`
- `followup`
- `tomorrow`
- `tonight`
- `resurface`

Evening output should optimize for:
- closure
- carry-over
- tomorrow prep
- low-pressure reading / resurfacing

## Event-driven outputs

### Location arrival / dwell
Good shapes:
- short nearby saved-place reminder
- mini context pack before next event
- a few high-signal suggestions when time window allows

### Leave-now
Good shape:
- current risk state
- travel estimate
- recommended departure timing
- optionally one contextual reminder, not a long digest

### Operational mail
Good shape:
- what changed
- why it matters today
- immediate next step if any

### Shopping / replenishment
Good shape:
- what item is likely needed
- why now
- last evidence
- draft action path up to approval boundary

## Execution levels

### Level 0
Observe only. No user-visible output.

### Level 1
Send information / suggestions only.

### Level 2
Prepare action artifacts without finalizing.
Examples:
- draft cart
- draft reservation page opened
- draft message prepared

### Level 3
Perform side effect after user approval.
Examples:
- purchase
- reservation confirmation
- sending a message or email

## Approval gate

The system should make it easy to stop at the boundary before irreversible effects.
This is especially important for:
- commerce
- reservations
- messaging
- financial actions

## Delivery adapters

Keep delivery separate from synthesis.
Potential adapters:
- Slack
- Telegram
- local file / markdown
- email summary
- future app/web UI

## Formatting rule

The same candidate bundle may be rendered differently depending on output mode.
A leave-now warning should not look like a morning digest section.
That is why rendering belongs after synthesis, not before it.

## Key product stance

Do not over-notify.
The system wins when the user feels:
- “that was the right moment”
- “that was exactly enough context”
not when it shows all available evidence.
