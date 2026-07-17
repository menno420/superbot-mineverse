# Session — 2026-07-17 — Sample vintage in the neutral notice

> **Status:** `complete`
> **Branch:** `claude/sample-vintage-notice`
> **Timestamp (UTC):** Fri Jul 17 2026

**Scope:** close the open 💡 carried forward from the sample-stale-UX lane —
the neutral "committed sample data" notice names the SITUATION but never says
HOW OLD the demo data is. Surface the committed sample's `generated_at` vintage
in that neutral notice so the age is transparent, additive and live-path-safe.

Born-red HOLD armed by this card (Status `in-progress`); the owner flips it to
complete after review of the merged PR.

## 💡 Session idea

`_snapshot_source()` (server/app.py) decides sample-vs-live by PATH identity
(`snapshot_path == SNAPSHOT_PATH`), so an embedder pointing
`MINING_SNAPSHOT_PATH` at a COPY of the committed sample reads "live" and the
permanent false STALE alarm returns — the exact edge the sample-source key was
meant to kill. A content-identity fallback (when the configured path's bytes
hash-match the committed sample, classify "sample" regardless of path) would
close it without touching the happy path; pin a temp-copy-of-sample snapshot →
still classified "sample" in tests/test_app_snapshot_source.py. Reconcile first
with the sample-source design note that path identity is deliberate.

## ⟲ Previous-session review

The ingest-monotonicity-gate idea (guard `_serve_snapshot_ingest` so a signed
older-`generated_at` replay inside the ±300 s skew window is rejected 409
instead of silently rolling the live read backward) is a sound, low-blast-radius
replay hardening that sits cleanly above the v1-validate-then-persist path and
leaves the single-sender happy path untouched. Its one real prerequisite —
reconciling with the data contract's explicit "last-write-wins" clause before
adding a monotonicity gate — is correctly flagged as the first step, so the
idea is ready to pick up as-is.

- **📊 Model:** opus-4.8 · medium · frontend-ux — sample vintage notice
