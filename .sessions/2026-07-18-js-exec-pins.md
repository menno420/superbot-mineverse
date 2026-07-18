# Session — 2026-07-18 — JS-exec pins for three pure web/app.js functions

> **Status:** `complete`
> **Branch:** `claude/js-exec-pins`
> **Timestamp (UTC):** Sat Jul 18 2026

**Scope:** close the residual JS-logic coverage gap for three pure functions
in `web/app.js` that were only ever asserted as served bytes (string
presence), never EXECUTED. Add real vm-executed vector tests to
`tests/test_js_logic.py` using the module's existing node `vm` harness
(`run_js_ops` / `js_call`), mirroring `test_biome_name_fallbacks_and_clamping`
and `test_format_age_unit_boundaries`:

1. `vaultTierPips(level, levelMax)` (`web/app.js` :907) — filled `●` count is
   `clamp(level, 0..levelMax)`, hollow `○` count is `max(0, levelMax - level)`.
   Vectors pin normal fill, `level > max` clamp, negative `level` clamp to 0,
   `level == max` all filled, and the `max = 0` edge.
2. `snapshotIsStale(staleness)` (`web/app.js` :931) — only the DETERMINISTIC
   branches are pinned to avoid wall-clock flake: `source === "sample"` short-
   circuits to `false` (even with an ancient epoch), a non-number
   `generated_at_epoch` is `false`, and a clearly-ancient epoch (`0`) with a
   non-sample source is `true`. The `Date.now()`-relative "recent → false"
   branch is deliberately NOT asserted with a fixed epoch (it would flake).
3. `bandTintClass(depth)` (`web/app.js` :1191) — `band-depth-${clamp(depth,
   0..3)}`. Vectors pin `depth` 0..3 exact, `depth > 3` clamp to 3, negative
   clamp to 0.

Test-only, zero runtime change — no `web/`, `server/`, or `data/` bytes move.

Born-red HOLD armed by this card (Status `in-progress`); the owner flips it to
complete after review of the merged PR.

## 💡 Session idea

The vm harness now covers every pure clamp/branch helper the frontend renders
against, but the render CALLERS (`renderLadder` painting `bandTintClass`, the
vault card painting `vaultTierPips`, the staleness header painting
`snapshotIsStale`) are still only string-asserted. A follow-up could stand up
one thin DOM shim over the existing `vm` sandbox (a recording `createElement`
that keeps `className`/`textContent`) so a render function can be executed once
against a fixed snapshot and its emitted class/text tree pinned — catching a
caller that wires the right helper to the wrong element, which pure-function
vectors alone can never see.

## ⟲ Previous-session review

`.sessions/2026-07-17-ingest-monotonicity-gate.md` (backend hardening) added
the `generated_at`-monotonic replay gate to `POST /api/snapshot/ingest`
(`409 stale_snapshot`, byte-unchanged on reject) and reconciled the ordering
clause in `docs/mining-data-contract.md`. Sound and well-scoped; its 💡 (a
producer-lag signal exposing the gap between newest accepted `generated_at`
and the freshest `snapshot_generated_at` promised by a write accept) is
orthogonal to this test-only lane and remains open for a backend pickup.

- **📊 Model:** Claude Opus 4.x · medium · test writing — vm-exec pins for three pure JS fns
