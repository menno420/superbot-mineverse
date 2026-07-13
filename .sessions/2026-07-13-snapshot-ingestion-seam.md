# Session — 2026-07-13 — snapshot ingestion seam (FLAG 1 consume side)

> **Status:** `in-progress`
> **Branch:** `claude/snapshot-ingestion-seam`
> **Venue:** lane worker session (ORDER 004 night run — item 5, consume side
> of the bot-lane FLAGs).

**Goal:** build the consume-side ingestion seam for the bot READ relay
(FLAG 1 in `control/status.md`): a `MINING_SNAPSHOT_PATH` host env var that,
when set, points the server at a live-fed snapshot file instead of the
committed `data/sample_snapshot.json`; unset → existing behavior
byte-identical (degraded-by-default doctrine, same pattern as the six
OAuth/write vars). Runtime v1 validation (`server/snapshot_validation.py`)
and per-request fresh reads already exist at all four load paths and are NOT
rebuilt — an invalid/missing live-fed file keeps answering the existing
honest 503. Committed fixtures (valid bot-shaped snapshot distinct from the
sample + invalid: schema violation, corrupt JSON, wrong version) + tests for
the seam; docs env-var names updated (names only, never values).
