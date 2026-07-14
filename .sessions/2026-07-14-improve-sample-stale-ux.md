# Session — 2026-07-14 — sample-vs-live stale-badge UX

> **Status:** `in-progress`
> **Branch:** `claude/improve-sample-stale-ux`
> **Venue:** improvement-wave lane G (owner directive 2026-07-14; wave
> claim `control/claims/claude-improvement-wave-2026-07-14.md`, #95).

**Goal:** the committed sample's `generated_at` is days old, so the
demo PERMANENTLY renders the red "⚠ STALE — snapshot 3d old, expected
every 60s" alarm plus 💤 idle marks on every miner
(web/app.js `renderStaleness` :724-755, `snapshotIsStale` →
`renderMinerCard` :1084-1089) — a false alarm by construction, since
the server KNOWS the bytes came from the committed sample
(server/app.py `snapshot_path_from_env` :98-107 — `MINING_SNAPSHOT_PATH`
unset → `SNAPSHOT_PATH`). Fix: additive `staleness.source:
"sample"|"live"` key in the `/api/views` staleness block
(server/views.py `build_staleness` :571-585); frontend renders a
neutral "committed sample data — live relay not connected" notice
instead of the STALE alarm and skips the 💤 idle marks when
`source === "sample"`; live behavior byte-identical. CAUTION honoured:
tests/test_web_fun.py:118 pins `"staleness?.stale_after_seconds ??
180"` — kept intact (the source short-circuit is ADDED above the
existing math, no pinned substring moves).

- **📊 Model:** fable-5 · standard effort · task-class: sample-vs-live stale-badge UX — additive staleness.source key + neutral demo notice, live path unchanged (build)
