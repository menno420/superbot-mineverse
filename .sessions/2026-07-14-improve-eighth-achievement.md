# Session 2026-07-14 — eighth achievement: Homesteader

> **Status:** `in-progress`

## Plan

Improvement-wave lane H, PR 1 of 3 (owner directive 2026-07-14; claim
PR #95). Add ONE new deterministic badge to `ACHIEVEMENT_CATALOG`
(server/views.py): **Homesteader** — owns at least one `home`
structure. Follow the 4-stop recipe documented by the
2026-07-11-sample-data-achievement-earners card (constant, catalog
tuple, `earned_achievements` branch, sample earner) — the committed
sample already gives Homesteader two clean earners (DeepDelver home 1,
MagmaMaven home 2), so the sample-data stop is satisfied with zero data
edits and no pinned ordering can move. Update the pinned-winners table
and add boundary + sample-anchored tests; re-validate the sample via
`server.snapshot_validation.validate_snapshot`; confirm the frontend
renders the grown catalog generically (zero JS change expected).

## Close-out

_(pending)_

## 💡 Session idea

_(pending)_

## ⟲ Previous-session review

_(pending)_

- **📊 Model:** fable-5 · standard effort · task-class: 8th achievement badge — catalog + earned branch + pinned-winners tests (build)
