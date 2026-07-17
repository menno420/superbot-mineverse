# Session — 2026-07-17 — Ingest freshness gate (generated_at-monotonic)

> **Status:** `in-progress`
> **Branch:** `claude/ingest-monotonicity-gate`
> **Timestamp (UTC):** Fri Jul 17 2026

**Scope:** harden `POST /api/snapshot/ingest` against replay. Today the
receiver HMAC-verifies (±300 s skew, server/ingest.py :22) and v1-validates,
then atomically replaces the live snapshot with NO freshness check — so a
signed snapshot captured up to ~300 s ago can be re-sent to overwrite the
live read with OLDER bytes. Add a `generated_at` freshness gate: an incoming
snapshot whose `generated_at` is strictly OLDER than the currently-persisted
one is rejected `409 {"error": "stale_snapshot"}` and the file is left
byte-unchanged. Equal `generated_at` stays idempotent-accept; newer advances
the read; first ingest and a missing/corrupt current file never block a valid
new push. The single-sender forward path is unchanged.

Reconciled with docs/mining-data-contract.md § Ordering: its clause read as
last-received-wins by arrival order ("no cross-request ordering to
arbitrate") — updated to `generated_at`-monotonic with a replay-hardening
rationale and a `409` row in the response-status table.

Born-red HOLD armed by this card (Status `in-progress`); the owner flips it to
complete after review of the merged PR.

## 💡 Session idea

The write contract's accept response carries `snapshot_generated_at` (the
`generated_at` the next READ snapshot "will carry or exceed" —
docs/mining-write-contract.md :113), but nothing verifies the relayed
snapshot ever reaches that instant. Now that ingest is `generated_at`-
monotonic, a follow-up could surface a producer-side lag signal: expose the
gap between the newest accepted `generated_at` and the freshest
`snapshot_generated_at` promised by a write accept, so a silently-stalled
producer is visible without waiting for the client-side 180 s STALE alarm.

## ⟲ Previous-session review

`.sessions/2026-07-17-merge-doctrine-truthful.md` (docs-only) correctly
excised the false "owner reviews/merges unmerged PRs" doctrine, pinning the
truth that green `claude/*` PRs auto-land via the enabler workflow and the
owner reviews only already-merged PRs. Its 💡 named exactly this ingest
freshness gap (server/app.py `_serve_snapshot_ingest`, server/ingest.py :22),
so this session claims that idea and closes it with the 409 monotonicity gate.

- **📊 Model:** opus-4.8 · medium · backend-hardening — ingest freshness gate
