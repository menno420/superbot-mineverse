# Session — 2026-07-12 — JS logic test harness (backlog item 2)

> **Status:** `in-progress`
> **Branch:** `claude/js-logic-test-harness`
> **Venue:** lane worker session (coordinator-delegated groomed-backlog slice).

**Goal:** close the JS-logic-test gap
(`docs/ideas/founding-day-groomed-backlog-2026-07-11.md` item 2): no
JavaScript executes in CI today — pytest pins served bytes only, and
`konamiNextProgress` (the PR #40 longest-prefix fix) was verified once via
Playwright, never per-CI-run. Build a minimal harness that runs INSIDE
pytest: shell out to preinstalled `node`, load the REAL `web/app.js` under
minimal browser-global shims, and call named pure functions with JSON test
vectors — `konamiNextProgress` thoroughly, plus the other cleanly-pure
text/shaping helpers worth pinning. Zero new CI infrastructure; tests SKIP
with a clear reason when `node` is absent (matching the repo's existing
conditional-skip pattern). No JSON API behavior change; no npm/package.json.
