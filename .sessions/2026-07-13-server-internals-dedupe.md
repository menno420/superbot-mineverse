# Session — 2026-07-13 — server internals dedupe (self-initiated)

> **Status:** `in-progress`
> **Branch:** `claude/server-internals-dedupe`
> **Venue:** lane worker session (ORDER 004 night run — generative rung:
> self-initiated, contained, reversible).

**Goal:** land the two refactor ideas recorded by tonight's own session
cards — both genuine 💡 entries, now acted on:

1. **`_load_valid_snapshot` helper** (idea from
   `2026-07-13-snapshot-ingestion-seam`): `server/app.py` repeats the same
   load-validate-or-503 block at all four snapshot load paths
   (`_serve_snapshot`, `_serve_views`, `_serve_me`, `_serve_action`
   pre-relay). Extract ONE
   `_load_valid_snapshot(self) -> tuple[bytes, dict] | None` helper
   (returns the raw payload too — `_serve_snapshot` ETags the exact
   bytes — and sends the honest 503 itself on failure); collapse the four
   sites onto it. Behavior byte-identical; the existing HTTP sections of
   `tests/test_snapshot_validation.py` and the malformed-snapshot tests in
   `tests/test_server_robustness.py` are the safety net.
2. **Cache the parsed schemas** (idea from
   `2026-07-13-write-path-hardening`): `functools.lru_cache` on the two
   `load_schema()` functions only (`server/snapshot_validation.py`,
   `server/response_validation.py`) — the schemas are COMMITTED files,
   immutable under a running server, unlike the live-fed snapshot which
   stays re-read fresh per request. `cache_clear()` is the explicit reload
   seam; add a small test per module pinning cache + seam, and the
   existing valid→valid→corrupt snapshot rewrite test must stay green.

Dedupe, not redesign: diff stays small and mechanical. Baseline at base
(PR #61 head 2f24b60): **520 passed + 1 skipped**.
