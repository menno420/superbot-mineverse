# Session 2026-07-14 — conformance_run.py: opt-in ingest leg

> **Status:** `complete`

## Plan

Improvement-wave lane H, PR 3 of 3 (owner directive 2026-07-14; claim
PR #95). Land the 💡 from the 2026-07-14-readiness-ingest-leg card:
`scripts/conformance_run.py` already vendors the readiness write probe
(`_load_readiness_probe()`, :186-194) but its sweep covers the WRITE
seam only. Mirror `scripts/readiness_check.py --probe-ingest` as an
opt-in `--probe-ingest` leg: one deliberately UNSIGNED POST to the URL
in `MINING_SNAPSHOT_RELAY_URL` — 401/503 = pass, 200 = SECURITY FAIL,
URL unset = skipped-never-failed. Reuse
`readiness_check.probe_ingest_endpoint` through the importlib loader
(renamed to return the module, not one function); failures fold into
the existing exit-code taxonomy (probe failures are exit 2). No
secrets, no fabricated env, no real network in tests — extend
`tests/test_conformance_run.py` with the injected-prober pattern
`tests/test_readiness.py` uses. Update `docs/live-prod-cutover.md`'s
one-command-wrapper parenthetical (it enumerates the wrapper's legs).

## Close-out

- `scripts/conformance_run.py` (+81/−7): `--probe-ingest` flag +
  `run_ingest_probe(environ, stdout, prober=None)` — one UNSIGNED POST
  to the URL in `MINING_SNAPSHOT_RELAY_URL` (new `ENV_INGEST_URL`
  constant), reusing `readiness_check.probe_ingest_endpoint` through
  the importlib loader, which is renamed `_load_readiness()` and now
  returns the MODULE (the 💡's exact suggestion) so both probes come
  from one implementation. Semantics mirror the readiness twin
  verbatim: 401 (configured) / 503 (fail-closed) = pass, unsigned 200
  = SECURITY FAIL, URL unset = skipped-never-failed (the READ relay is
  optional at every stage, so the write sweep's exit semantics are
  untouched). Failure folds into the existing taxonomy: exit 2
  (`EXIT_PROBE_FAILED`), aborting before the sweep. No secrets, no
  fabricated env, no URL/value ever printed (SET/UNSET hygiene held);
  `main()` grew an `ingest_prober=None` injection seam mirroring
  `readiness_check.build_report`'s.
- `tests/test_conformance_run.py` (+5): injected-prober pattern from
  tests/test_readiness.py — skip-when-unset (prober never called, ok),
  probe-hits-the-env-URL + sentinel never printed, honest failure
  naming the readiness twin, `main()` exits 2 before the sweep on a
  failed leg (no subprocess ran), prober untouched without the flag on
  the pre-sweep abort path. Zero real network.
- `docs/live-prod-cutover.md`: the §1 one-command-wrapper parenthetical
  (the only place the doc enumerates the wrapper's legs) now names the
  opt-in ingest leg and its skip rule.
- Fix round (own diff): first test run red — `assert "sweep:" not in
  output` collided with the abort text "before the sweep:"; tightened
  to `"sweep: python3"`. One fix, then green.
- verify: `python3 -m pytest -q` → `603 passed, 1 skipped` (598 + 5
  new); `python3 bootstrap.py check --strict` → exit 0.

## 💡 Session idea

`conformance_run.py --probe-ingest` and `readiness_check.py
--probe-ingest` now print near-identical skip/ok/FAILED lines from two
hand-rolled call sites (readiness's lives inside `build_report`, this
one in `run_ingest_probe`). If either seam grows a THIRD consumer (or
the probes gain a new answer class), extract a tiny shared
`format_probe_line(kind, ok, detail)` into readiness_check so the
wording can't drift between the two CLIs — today the duplication is two
lines per site and not worth a seam. Dedupe checked: no card or
docs/ideas entry covers probe-line formatting.

## ⟲ Previous-session review

The 2026-07-14-readiness-ingest-leg card's 💡 was written as a
turn-key recipe and it cashed exactly as promised: the loader rename it
prescribed (`return the module, not one function`) was the right first
move, its "skip-not-fail on unset URL exactly like this session's
report wiring" boundary survived translation into the wrapper's
different control flow (a bool gate before the sweep rather than a
report line), and naming `tests/test_conformance_run.py` as the
pattern file meant zero test-style archaeology. Its self-criticism
habit is also worth copying: it flagged its predecessor's stale-base
under-report, and this session hit no such drift because the wave
rails force a resync before every branch. One gap: the recipe never
said where in the wrapper's ORDER the leg belongs — before or after
the write probe — which this session had to decide (after: reachability
of the primary seam first, both probes before any pytest cost).

- **📊 Model:** fable-5 · standard effort · task-class: conformance_run opt-in ingest leg — unsigned probe folded into exit taxonomy, skip-when-unset (build)
