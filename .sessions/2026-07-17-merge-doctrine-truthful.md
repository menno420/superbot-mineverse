# Session — 2026-07-17 — Correct merge doctrine to the truth

> **Status:** `complete`
> **Branch:** `claude/merge-doctrine-truthful`
> **Timestamp (UTC):** Fri Jul 17 16:45:43 UTC 2026

**Owner live order (2026-07-17, verbatim):** "Please remove any mention of
'human gated' I have never and will never review an unmerged PR."

**Scope:** correct the false "owner reviews/merges unmerged PRs" doctrine to
the truth: green `claude/*` PRs auto-land via GitHub-native auto-merge (armed
by `.github/workflows/auto-merge-enabler.yml`); the owner never reviews
unmerged PRs — the owner reviews already-MERGED PRs asynchronously. Agents
still do NOT hand-arm / REST-merge; the enabler workflow arms auto-merge and
the green head SHA lands itself.

Born-red HOLD armed by this card (Status `in-progress`); the owner flips it to
complete after review of the merged PR.

## 💡 Session idea

The snapshot-ingest handler v1-validates before persist (server/app.py
`_serve_snapshot_ingest` :443-445) but does NOT check freshness, so a signed
snapshot captured up to ±300 s ago (the `actions.verify` skew window,
server/ingest.py :22) can be replayed to roll the live read back to older
bytes — last-write-wins with no monotonicity gate. Guard recipe: after
`_snapshot_is_valid`, read the currently-persisted file's `generated_at` once
and reject with 409 when the incoming `generated_at` is strictly older
(identical bytes stay idempotent); pin a signed older-`generated_at` payload →
rejected + file byte-unchanged in tests/test_snapshot_ingest.py. Reconcile
first with docs/mining-data-contract.md's explicit "last-write-wins" clause —
this hardens replay without changing the single-sender happy path.

## ⟲ Previous-session review

`.sessions/2026-07-14-improve-sample-stale-ux.md` (lane G, #95 wave) holds up
well: its additive `staleness.source: "sample"|"live"` key sits ABOVE the
existing age math (server/views.py `build_staleness`, web/app.js
`renderStaleness`), so the live path stays byte-identical and the pinned
`stale_after_seconds ?? 180` substring never moved — a clean, low-blast-radius
fix for the permanent false STALE alarm on the committed demo (+4 tests,
588→592). One honest edge it acknowledged but did not close: `_snapshot_source()`
decides sample-vs-live by PATH identity (`snapshot_path == SNAPSHOT_PATH`), so
an embedder pointing `MINING_SNAPSHOT_PATH` at a COPY of the committed sample
reads "live" and the false alarm returns. Its own 💡 (surface the sample's
`generated_at` vintage in the neutral notice) remains open and unclaimed.

- **📊 Model:** opus-4.8 · medium · docs-only — merge-doctrine correction
