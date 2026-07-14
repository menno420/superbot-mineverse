# Session 2026-07-14 — shared bounded POST-body reader

> **Status:** `in-progress`

## Plan

Improvement-wave lane H, PR 2 of 3 (owner directive 2026-07-14; claim
PR #95). Land the guard recipe from the 2026-07-14-flag1-snapshot-ingest
card's 💡: `server/app.py` parses Content-Length + bounds-checks + reads
the POST body in two hand-rolled copies (`_read_action_request` at
`MAX_ACTION_BODY_BYTES`, `_serve_snapshot_ingest` at
`ingest.MAX_SNAPSHOT_BODY_BYTES`). Extract ONE shared bounded-body
reader parameterized on max-bytes + error emission, PRESERVING every
observable behavior: the action path's single folded 400, the ingest
path's 400-vs-413 distinction, header order, and the answer-before-drain
broken-pipe behavior the ingest card pins. Pure refactor — the existing
action + ingest test gauntlets must pass UNCHANGED.

## Close-out

_(pending)_

## 💡 Session idea

_(pending)_

## ⟲ Previous-session review

_(pending)_

- **📊 Model:** fable-5 · standard effort · task-class: bounded POST-body reader dedupe — pure refactor, byte-identical responses (refactor)
