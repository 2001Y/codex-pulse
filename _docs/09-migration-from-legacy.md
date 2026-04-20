# Migration from Legacy Docs

## Refresh summary

This repo has been refreshed from a **digest-centric planning set** into a **unified trigger-driven architecture**.
Morning and evening editions are now modeled as scheduled trigger profiles inside the same system that also handles:
- location / dwell triggers
- calendar proximity warnings
- operational mail
- shopping / replenishment
- trigger self-review

Hermes-specific assumptions were removed from the core architecture and retained only as runtime or acquisition examples.
The X work remains first-class, but it is now framed around official `xurl` / X API signals (`bookmarks`, `likes`, `reverse chronological home timeline`) rather than legacy "timeline diff" wording.

## Why the old shape was replaced

The old repository had good ingredients but weak system boundaries:
- digest docs and proactive trigger docs sat beside each other rather than forming one model
- X had deeper implementation detail than some more central product dimensions
- canonical objects were too digest-shaped and not trigger-shaped enough

## Old-to-new mapping

| Legacy concept | New home |
|---|---|
| overview / requirements | `01-product-thesis`, `03-trigger-model` |
| old architecture | `02-system-architecture`, `07-state-memory-and-audit` |
| connectors & ingestion | `04-collection-and-connectors`, `source-notes/conversation-history` |
| X timeline diff | `source-notes/x`, `07-state-memory-and-audit` |
| proactive life agent trigger ideas | `03-trigger-model`, `06-output-delivery-and-actions` |
| competitive research / references | intentionally removed from canonical core |

## Terminology changes

### Old framing
- morning digest
- evening digest
- proactive life agent (separate conceptual branch)

### New framing
- scheduled trigger profiles
- event-driven trigger profiles
- one shared trigger-driven operating briefing engine

## Legacy file policy

Legacy docs were intentionally removed after their important concepts were redistributed into the new canonical set.
The goal is lower ambiguity, not archival completeness inside the active docs tree.
