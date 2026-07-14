# Session — 2026-07-14 — README refresh to HEAD reality

> **Status:** `in-progress`
> **Branch:** `claude/improve-readme-refresh`
> **Venue:** improvement-wave lane E (owner directive 2026-07-14: "See if
> there is anything else you can come up with or improve"; wave claim
> `control/claims/claude-improvement-wave-2026-07-14.md`, merged #95).

**Goal:** bring `README.md` back in line with the code at HEAD
(harvest at `58657ed`). Verified drift: :29 still says "Stage 0
(current code)" although the live-fed `MINING_SNAPSHOT_PATH` seam
exists (server/app.py:6-15); the :40-44 endpoint list omits
`GET /api/views` (the route the frontend actually renders from,
web/app.js:1858), `POST /api/action` (server/app.py:112) and
`POST /api/snapshot/ingest` (server/app.py:113); the ladder :27 calls
stage d "planned" while it is PREPARED (docs/current-state.md:33-34:
cutover checklist + readiness check); the :105 repo-layout row
describes `server/` as snapshot+static only. Fix those, add the two
snapshot-relay env-var NAMES only (`MINING_SNAPSHOT_PATH`,
`MINING_SNAPSHOT_RELAY_SHARED_SECRET` — server/ingest.py:54,57; never
values), and one quickstart line each for
`scripts/readiness_check.py --probe-ingest` and
`scripts/conformance_run.py`. Docs-only; README.md at repo root is
outside the docs-gate badge scan (bootstrap.py `check_badges` walks
the docs root only), so no Status badge needed.

- **📊 Model:** fable-5 · standard effort · task-class: README refresh to HEAD reality — endpoint list, stage ladder, layout row, relay env names, script quickstarts (docs-only)
