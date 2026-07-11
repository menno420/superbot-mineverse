# Session 2026-07-11 — conformance env seam: SHIM_CONFORMANCE_BASE_URL opt-in switch (tests + docs only)

> **Status:** `complete`

## Plan

Land the guard recipe deferred by the stage-(d) prep session
(`.sessions/2026-07-11-live-prod-cutover.md` § Close-out): replace the
hand-edit "conformance swap" in `docs/live-prod-cutover.md` §1 with an
env-var seam in `tests/test_actions.py`. When `SHIM_CONFORMANCE_BASE_URL`
is set, the `shim` fixture yields that external base URL instead of
booting the in-process shim, so the SAME contract fixtures exercise the
real bot-side endpoint; the signing secret is `MINING_WRITE_SHARED_SECRET`
(the contract's canonical env name, `server/actions.py` `ENV_SECRET`) with
`SHIM_CONFORMANCE_SECRET` as an override. Hard constraints: with the env
vars unset (CI, fresh clones) behavior is byte-identical to today — green,
hermetic, loopback-only, zero env vars read; secret values are never
printed anywhere (output, skip reasons, failure messages); no file under
`server/`, `web/`, `schemas/`, or `data/` changes.

## Close-out

- `tests/test_actions.py`: module-level seam (`CONFORMANCE_BASE_URL` /
  `CONFORMANCE_MODE` / secret resolution with a fail-fast, value-free
  `pytest.exit` when the base URL is set without any secret); `shim`
  fixture yields `(None, <external base>)` in conformance mode;
  `new_action_id()` mints random UUID v4s in conformance mode (a real
  executor retains idempotency keys ≥24 h across runs — the deterministic
  counter would 409 the second sweep); `post()` grew https support for an
  https target; in-memory assertions (`state.audit_log`, executed-once
  snapshot evidence) guard on `state is not None`; the all-in-memory
  audit-fields test skips in conformance mode (audit verification against
  the real endpoint is the checklist's manual step); one new
  conformance-only smoke test (unsigned probe → 401 `invalid_signature`,
  the `readiness_check.py --probe` handshake) skips by default with the
  honest reason "SHIM_CONFORMANCE_BASE_URL not set;
  conformance-vs-real-endpoint run skipped (hermetic CI default)".
- Secret-reuse decision: reuse `MINING_WRITE_SHARED_SECRET` because
  `actions.sign`/`actions.verify` is the one canonical signing
  implementation and that env name is already the documented shared-secret
  channel on both hosts; `SHIM_CONFORMANCE_SECRET` overrides it for the
  shell-already-exports-a-different-web-host-secret case. Documented in
  docs/live-prod-cutover.md §1.
- `docs/live-prod-cutover.md` §1: the hand-edit evidence paragraph is now
  the env-var invocation (verbatim command block) + fine print (base URL
  is scheme+host only; state-assertions guard/skip; reload
  `data/sample_snapshot.json` between passes). `docs/mining-write-contract.md`
  § Enforcement points its done-criterion at the same seam.
- verify: `python3 -m pytest -q` → 130 passed, 1 skipped (the new
  conformance smoke, skipped by design with zero env vars; no network
  beyond loopback). `python3 bootstrap.py check --strict` → all checks
  passed.
- Runtime diff surface: zero — tests, docs, claim, session card only.
- Claim `control/claims/claude-conformance-env-seam.md` rides this PR
  (write-contract pattern: released by the next PR that touches
  control/).
- Two tests carried absolute-value assertions that only hold with the
  per-test-fresh in-process snapshot (the vault test's coin totals sit
  downstream of the sell test's +30; the end-to-end mine's `energy == 40`
  sits downstream of three earlier mines) — against a PERSISTENT external
  target those went red even on a freshly loaded fixture. Made exactly
  those two conformance-tolerant (relative/shape assertions on the wire;
  the absolute values still pinned whenever `state is not None`, i.e. in
  every default run). Verified both ways: default run green and hermetic;
  a full conformance sweep against one persistent local shim instance
  (loopback, throwaway secret) green with the audit test skipped.
- Known limit (documented in the checklist's fine print): repeat sweeps
  against the same target need the test-guild state reloaded from
  `data/sample_snapshot.json` between passes — first-run absolutes like
  `diamond == 10` are drift detectors by design, not re-runnable.

## 💡 Session idea

A `pytest --collect-only`-time banner (one line, value-free) saying which
mode the run is in — "conformance target: EXTERNAL (env)" vs "in-process
shim" — would make CI logs self-explaining when someone wonders whether a
green run proved anything about the real endpoint.

## ⟲ Previous-session review

The stage-(d) prep session's guard recipe was precise enough to implement
verbatim (fixture anchor, env name, skip-the-degraded-block warning) —
recipes that name exact anchors pay off. Two drifts it missed, caught
here: the deterministic `new_action_id()` counter is replay-poison
against a persistent executor (idempotency retention makes "rerun the
sweep" a 409 storm unless conformance mode mints random UUIDs), and two
absolute-value economy assertions could never go green against any
persistent target because earlier tests in the same sweep move the same
miner's coins/energy (see Close-out).

- **📊 Model:** fable-5 · standard effort · task-class: test seam + procedure docs (tests+docs, hermetic default preserved)
