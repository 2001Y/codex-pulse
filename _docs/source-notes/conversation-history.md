# Source Note: Conversation History

## Goal

Unify conversation-derived context across multiple agent ecosystems without pretending that all platforms expose identical access methods.

## Covered systems

- Hermes Agent
- ChatGPT
- Grok
- future agent systems later

## Acquisition reality

### Hermes Agent
Strongest path for v1.
Preferred access:
- local session store
- local DB / CLI / exports

### ChatGPT
Consumer chat history is not a clean always-on read API for normal integrations.
Realistic v1 paths:
- official export import
- manual transcript import
- share-link import where useful
- browser automation only as experimental opt-in

### Grok
Similar constraint class.
Realistic v1 paths:
- manual transcript import
- share-link import
- future export path if validated

## Why provenance is mandatory

Conversation context may enter through:
- live local storage
- exported ZIPs
- copied transcript text
- shared links
- future browser automation

Without provenance, the system cannot explain:
- freshness
- trust level
- acquisition mode
- re-import behavior

## Normalization target

Conversation items should preserve enough structure for:
- topic overlap
- people / org overlap
- unresolved/open-loop detection
- resurfacing
- preparation before future meetings

Suggested normalized fields:
- title
- timestamps
- participant/entity hints
- topical tags
- unresolved flag
- provenance
- raw artifact references

## Product role of conversations

Conversations should not only be summarized for nostalgia.
They matter because they feed:
- people prep
- follow-up detection
- unresolved loop discovery
- resurfacing of forgotten but current context

## Honesty rule

Do not promise a cleaner live sync path than the source actually supports.
The architecture should explicitly distinguish:
- live-local
- official export
- share-link
- manual import
- experimental automation
