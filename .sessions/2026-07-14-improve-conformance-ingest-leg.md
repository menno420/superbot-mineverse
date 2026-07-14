# Session 2026-07-14 — conformance_run.py: opt-in ingest leg

> **Status:** `in-progress`

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

_(pending)_

## 💡 Session idea

_(pending)_

## ⟲ Previous-session review

_(pending)_

- **📊 Model:** fable-5 · standard effort · task-class: conformance_run opt-in ingest leg — unsigned probe folded into exit taxonomy, skip-when-unset (build)
