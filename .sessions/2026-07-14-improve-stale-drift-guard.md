# Session — 2026-07-14 — staleness-literal drift guard (test-only)

> **Status:** `in-progress`
> **Branch:** `claude/improve-stale-drift-guard`
> **Venue:** improvement-wave lane E (owner directive 2026-07-14; wave
> claim `control/claims/claude-improvement-wave-2026-07-14.md`, #95).

**Goal:** the 180 s / 60 s staleness numbers live in three places —
`server/views.py:52-53` (`SNAPSHOT_CADENCE_SECONDS` /
`STALE_AFTER_SECONDS`, the VERDICT-056-measured constants) and
`web/app.js` `?? N` fallbacks at :740-741 (header staleness line) and
:910 (`snapshotIsStale` card idle check) — but the only test coverage
is `tests/test_web_fun.py:118` pinning the literal STRING
`"staleness?.stale_after_seconds ?? 180"`, which asserts nothing about
the server constants: change views.py and the frontend fallbacks drift
silently. Add one test that regex-extracts every numeric
`stale_after_seconds ?? N` / `cadence_seconds ?? N` fallback from the
served `web/app.js` bytes and asserts each equals the corresponding
`server/views.py` constant, in the style of the existing js-pin tests
(tests/test_js_logic.py `shipped_konami_sequence` regex extraction;
tests/test_web_fun.py served-bytes `js` fixture). Test-only — no
runtime change; suite 587 → 588.

- **📊 Model:** fable-5 · standard effort · task-class: staleness-literal drift guard — JS fallback numbers pinned to server/views.py constants (test-only)
