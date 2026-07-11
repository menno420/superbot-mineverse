---
state: captured
origin: lab
shipped_pr: null
shipped_repo: null
merged_date: null
outcome: open
---

# Founding-day groomed backlog — parked 2026-07-11 (wrap-up session)

> **Status:** `ideas`

Groomed at day close and parked ON RECORD — none of these are approved or
in flight; each names its trigger condition. Routed per the lifecycle:
the first two are externally blocked, the rest are quick-win/discuss-first
candidates for whichever session picks them up after the blockers clear.

1. **Audit-trail e2e verification + real-endpoint conformance run** —
   BLOCKED on Builder-lane FLAGs 1+2 (bot endpoints). Procedures already
   committed: 3-step audit verification in `docs/live-prod-cutover.md`;
   conformance = run `tests/test_actions.py` against the real endpoint via
   the `SHIM_CONFORMANCE_BASE_URL` env seam.
2. **JS-logic-test gap** — no JavaScript executes in CI; pytest pins served
   bytes only. Konami logic is a pure function verified once via Playwright
   (PR #40), not per-CI-run. If frontend logic grows, bring a JS test
   harness (or keep every logic path a pure function with a documented
   one-time browser verification).
3. **`buildTable()` renderer-callback refactor** — deliberately SKIPPED
   (recorded decision, PR #40 card): the three table bodies differ
   structurally; a shared body builder would be a callback machine, not a
   simplification. Re-open only if a fourth structurally-similar table
   lands.
4. **`tablist()` extraction** — standing rule from the a11y card: extract
   when a SECOND tabbed widget lands. Still exactly one
   (`renderBoardTabs`).
5. **WebAudio muted-default toggle** — ambient cave audio, muted by
   default, honest toggle; must respect reduced-motion/no-autoplay
   discipline.
6. **Seasonal decorations** — date-keyed cosmetic layer over the cave
   theme.
7. **Cosmetic hats by miner id** — deterministic per-suid cosmetic on the
   pixel avatars.
8. **Multi-guild snapshot UI** — the schema's envelope is single-guild
   today; a guild switcher needs contract thought first (discuss-first).
