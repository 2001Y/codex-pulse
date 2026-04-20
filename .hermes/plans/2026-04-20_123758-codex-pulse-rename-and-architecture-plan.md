# Codex Pulse Rename + Architecture Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Reposition `Hermes Pulse` into a Codex-centered architecture — tentatively named **Codex Pulse** — where **Codex CLI performs the AI summarization step**, while **all source acquisition, archival, provenance, scheduling, and delivery remain programmatic** and auditable.

**Architecture:** Keep the current strong separation between source truth and presentation, but simplify the pipeline so the current deterministic markdown summary becomes a fallback/debug artifact, not the primary user-facing output. The primary flow should become: **trigger → collect → archive originals/raw artifacts by date → invoke Codex CLI on the archive directory → store Codex output as the canonical digest → deliver that digest directly to Slack/DM via local script + `slack_direct.py` (or write a file for later delivery)**. This preserves strong provenance while moving sectioning and summarization into the AI layer.

**Tech Stack:** Python 3.11 runtime, existing `hermes_pulse` package, SQLite for state, filesystem archive under `~/Pulse`, Codex CLI for summarization, macOS launchd for scheduling, `~/.hermes/scripts/slack_direct.py` for direct Slack delivery.

---

## Assumption to validate during implementation

This plan assumes the target new product/repo name should be:
- **Product name:** `Codex Pulse`
- **Repository slug:** `codex-pulse`

If the intended name is actually `Codex Plus` or another spelling, implementation should parameterize the rename task so only the literal name/slug swap changes and the rest of the plan remains valid.

---

## Current implementation inventory

### Implemented now

- **Trigger**
  - CLI `morning-digest` entrypoint
  - Hermes cron-based 09:00 job exists today, but this is only one orchestration option
- **Collect**
  - feed registry connector with live fetch
  - optional Hermes history connector
  - optional notes connector
- **Archive**
  - `~/Pulse/YYYY-MM-DD/summary/morning-digest.md`
  - `~/Pulse/YYYY-MM-DD/raw/collected-items.json`
- **Summary generation**
  - deterministic fixed-rule path via `synthesis.py` + `rendering.py`
- **Delivery**
  - local markdown output path
  - Hermes cron currently used to DM the resulting digest
- **Operational hardening**
  - live fetch with browser-like headers
  - per-feed failure tolerance

### Designed but not implemented yet

These are present in docs/architecture but not truly wired in code:

1. **Location / Maps collection**
   - maps saved places
   - location history
   - arrival/dwell triggers
2. **X collection**
   - home timeline diff
   - bookmarks
   - likes
3. **Calendar / Gmail / email connectors**
4. **known_source_search implementation body**
   - currently represented in registry, but not executed as a real retrieval path
5. **primary-source resolution chain**
   - current code stores provenance and citations, but does not yet walk secondary → primary automatically
6. **deep_brief / source_audit as Codex-generated canonical outputs**
7. **raw original preservation beyond normalized JSON**
   - no per-feed raw XML archive yet
8. **launchd + direct Slack delivery path for Pulse**
   - existing alert/report scripts elsewhere use this pattern, but Pulse itself does not yet
9. **Codex CLI summarization path**
   - not yet the actual canonical summary step
10. **removal/demotion of deterministic sectioning as primary path**

---

## Key design decision updates

### 1. Deterministic `summary/` is unnecessary as a primary artifact

The current fixed-rule `summary/morning-digest.md` should **not** remain the primary digest-generation step.

Recommended change:
- move deterministic summary to fallback/debug only
- canonical human-facing summary should be `summary/codex-digest.md`

### 2. Hermes Agent is not required in the final architecture

Because the user explicitly prefers the same operational style as existing local alert/reporting scripts, the preferred production shape is:

- **launchd** schedules the run
- **Pulse script** performs trigger/collect/archive
- **Codex CLI** performs summarization
- **`slack_direct.py`** posts directly to Slack/DM

Hermes Agent may still be useful for:
- ad-hoc development
- debugging
- interactive investigation
- fallback orchestration

But it should not be the mandatory runtime for the final daily digest pipeline.

### 3. Archive root should remain `~/Pulse/`

Even after renaming to Codex Pulse, keep the archive root as:
- `~/Pulse/YYYY-MM-DD/`

This preserves the user’s preferred mental model and avoids unnecessary churn in the source-truth storage path.

---

## Target architecture

### Canonical flow

1. **Trigger**
   - launchd scheduled run (e.g. 09:00)
   - later: feed/event/location triggers
2. **Collect**
   - source registry and live connectors gather source material
3. **Archive**
   - save raw/original artifacts, derived normalized artifacts, metadata
4. **Summarize**
   - invoke Codex CLI on the archive directory
5. **Deliver**
   - send Codex output directly to Slack/DM with `slack_direct.py`
6. **Audit / State**
   - update SQLite + metadata files

### Desired archive layout

```text
~/Pulse/YYYY-MM-DD/
  raw/
    collected-items.json
    feeds/
      <source-id>.xml
  derived/
    normalized-items.json
    codex-prompt.md
  summary/
    codex-digest.md
    fallback-digest.md             # optional deterministic fallback/debug only
  metadata/
    run.json
    sources.json
    failures.json
```

---

## Detailed implementation plan

### Task 1: Rename product/repo identity from Hermes Pulse to Codex Pulse

**Objective:** Align product name, repo slug, local path, metadata, docs, and scripts.

**Files / systems:**
- Modify: `README.md`
- Modify: `README.ja.md`
- Modify: `package.json`
- Modify: `_docs/README.md`
- Modify: `_docs/01-product-thesis.md`
- Modify: `_docs/02-system-architecture.md`
- Modify: `_docs/08-roadmap.md`
- Modify: SVG titles/labels in `assets/overview-architecture.svg` and `.ja.svg`
- Update GitHub repo slug from `hermes-pulse` to `codex-pulse`
- Update local directory from `~/.hermes/hermes-pulse` to `~/.hermes/codex-pulse`
- Update `origin` remote
- Update cron/plans naming strings

**Step 1: Write failing tests / checks**
- package/project name check
- targeted doc branding assertions

**Step 2: Verify failure**
- confirm old `Hermes Pulse` strings still present in key identity files

**Step 3: Write minimal implementation**
- rename identity layer only first

**Step 4: Verify pass**
- rerun identity checks and broader tests

**Step 5: Commit**
```bash
git add README.md README.ja.md package.json _docs assets
git commit -m "docs: rename Hermes Pulse to Codex Pulse"
```

---

### Task 2: Add a Codex summarization abstraction

**Objective:** Make Codex CLI the canonical summary generator while keeping collection/delivery code non-AI.

**Files:**
- Create: `src/codex_pulse/summarization/base.py`
- Create: `src/codex_pulse/summarization/codex_cli.py`
- Create: `tests/test_codex_summarizer.py`

**Behavior:**
- input: archive directory path
- build prompt from raw/derived artifacts
- execute Codex CLI one-shot summarization
- write `summary/codex-digest.md`
- return path/content

**Prompt requirements:**
- prioritize primary sources
- keep direct links
- do not over-compress if detail matters
- mark uncertainty explicitly
- allow Codex to decide sectioning rather than fixed Python rules

---

### Task 3: Archive true originals, not just normalized collected JSON

**Objective:** Strengthen source truth before handing work to Codex.

**Files:**
- Modify: `src/codex_pulse/archive.py`
- Modify: `src/codex_pulse/connectors/feed_registry.py`
- Create: `tests/test_archive_raw_feeds.py`

**Behavior:**
- persist raw feed payloads per source under `raw/feeds/`
- persist normalized items under `derived/normalized-items.json`
- persist failure/fetch metadata under `metadata/`
- do not require HTML/page snapshots; raw feed payloads plus normalized JSON are sufficient for the first codex-oriented architecture

---

### Task 4: Demote deterministic sectioning/rendering to fallback only

**Objective:** Remove fixed-rule digest generation from the primary user path.

**Files:**
- Modify: `src/codex_pulse/rendering.py`
- Modify: `src/codex_pulse/synthesis.py`
- Modify: `src/codex_pulse/cli.py`
- Add tests for fallback path

**Behavior:**
- deterministic render stays available for:
  - fallback
  - tests
  - debugging
- canonical output is no longer `summary/morning-digest.md`
- fallback output becomes `summary/fallback-digest.md`

---

### Task 5: Make CLI pipeline Codex-first

**Objective:** Change `morning-digest` so it does:
- collect
- archive
- Codex summarize
- fallback only on failure

**Files:**
- Modify: `src/codex_pulse/cli.py`
- Modify: `tests/test_end_to_end_morning_digest.py`
- Add: `tests/test_morning_digest_codex_path.py`

**Behavior:**
- `codex-digest.md` is canonical
- fallback render only if Codex summarization fails
- raw archive always written

---

### Task 6: Implement direct Slack/DM delivery without Hermes Agent

**Objective:** Make delivery identical in spirit to existing local alert/reporting scripts.

**Files / systems:**
- Create: `~/.hermes/scripts/codex_pulse_daily.py` or keep a repo-local runner and add a small wrapper script
- Reuse: `~/.hermes/scripts/slack_direct.py`
- Create tests around output selection if repo-local

**Behavior:**
- run Pulse CLI / runtime
- read `summary/codex-digest.md`
- post directly to Slack DM with `slack_direct.post_message`
- no Hermes Agent required in the hot path

**Why this matches the user request:**
- same pattern as macOS load/resource alert scripts
- lightweight
- deterministic orchestration + AI only at Codex summarization step

---

### Task 7: Replace Hermes cron with launchd-based scheduling

**Objective:** Make Codex Pulse a self-contained local service.

**Files / systems:**
- `~/Library/LaunchAgents/com.akitani.codex-pulse-daily.plist`
- wrapper script under `~/.hermes/scripts/` or `~/Pulse/bin/`

**Behavior:**
- schedule 09:00 daily run with launchd
- write archives under `~/Pulse/YYYY-MM-DD/`
- summarize with Codex CLI
- post to Slack directly

**Validation:**
- manual script run
- direct Slack post check
- `launchctl print`
- `launchctl kickstart -k`

---

### Task 8: Expand source registry implementation

**Objective:** Fill the gap between designed and implemented collection.

**Implemented now:**
- live feed registry
- starter registry entries

**Still missing implementation:**
- X connectors
- location connectors
- calendar/email connectors
- true `known_source_search`

**Priority order:**
1. `known_source_search`
2. calendar/email
3. X bookmarks/likes/home diff
4. location/maps

---

## Designed-but-not-yet-implemented list (explicit)

This is the concise list the user asked for.

### Collection domain gaps
- `known_source_search` real retrieval logic
- Calendar connector
- Gmail / email connector
- X home timeline connector
- X bookmarks connector
- X likes connector
- Maps saved places connector
- location history / arrival / dwell connector
- ChatGPT export/manual/share-link connector
- Grok export/manual/share-link connector

### Archive/source-truth gaps
- raw per-feed XML persistence
- raw HTML/page snapshot persistence
- run metadata file
- source/failure metadata files
- richer derived normalized artifact set

### Summary generation gaps
- Codex CLI summarizer abstraction
- Codex prompt generation from archive directory
- `summary/codex-digest.md` as canonical output
- fallback-only deterministic summary path
- removal of fixed-rule primary sectioning

### Delivery/runtime gaps
- direct Slack delivery script for Pulse
- launchd-based daily scheduling for Pulse
- removal of Hermes cron dependency in production path
- DM root/thread behavior formalization for Pulse-specific daily digests

### Product rename gaps
- repo/product rename to Codex Pulse
- local path rename
- origin/GitHub slug rename
- cron/script/plist naming updates

---

## Validation strategy

### Unit tests
- Codex summarizer mocked path
- archive raw + derived file layout
- fallback path on Codex failure
- direct Slack delivery selection

### Integration tests
- fixture-backed end-to-end archive → Codex summarize → delivery selection
- live-feed happy path with archive creation
- launchd wrapper dry run (script-level)

### Manual verification
- run daily script manually
- inspect `~/Pulse/YYYY-MM-DD/`
- confirm raw, derived, metadata, summary folders exist
- confirm Slack receives `summary/codex-digest.md`
- confirm no Hermes Agent dependency in the delivery hot path

---

## Recommended final stance

**Codex Pulse** should become:
- programmatic collection and archival for source truth
- Codex CLI for the actual digest generation
- launchd + `slack_direct.py` for scheduling and delivery
- deterministic summary/rendering only as a fallback/debug layer

That is the cleanest answer to the user’s desired architecture.
