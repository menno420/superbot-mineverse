# WRITE-contract conformance runbook — one command

> **Status:** `reference`
>
> One-page operational companion to `docs/live-prod-cutover.md` §1's
> first checkbox. Where this page and the cutover checklist or
> `docs/mining-write-contract.md` disagree, those win.

## Purpose

Run the ENTIRE WRITE-contract fixture sweep (`tests/test_actions.py`)
against the REAL bot-side executor instead of the in-process shim, as
one command. A green sweep is the evidence for cutover §1's first box
— it proves the executor speaks contract v1, not that live prod is go.

## Prerequisites

- The bot-side endpoint is live and pointed at the TEST guild, freshly
  loaded with `data/sample_snapshot.json` (FLAG 2, bot lane).
- The owner-provisioned values are exported in the shell — never in
  files, never printed (`docs/live-prod-cutover.md` §1):
  - `MINING_WRITE_ENDPOINT` — the runner derives the sweep's base URL
    from it (or export `SHIM_CONFORMANCE_BASE_URL`,
    scheme://host[:port] only, to override);
  - `MINING_WRITE_SHARED_SECRET` — the signing secret (override:
    `SHIM_CONFORMANCE_SECRET`, for when the shell's web-host secret
    differs from the conformance target's).

## The single command

```
python3 scripts/conformance_run.py
```

It checks the env (names only; secret shown as sha256 fingerprint at
most, URLs never), sends ONE unsigned reachability probe (must draw
the contract's pre-auth 401; can never execute anything —
`--skip-probe` to omit), runs
`python3 -m pytest tests/test_actions.py -q` through the conformance
seam, and tees output to a timestamped log under `.conformance-runs/`
(git-ignored — NEVER commit results files).

## What PASS means / what FAIL looks like

- **PASS (exit 0):** every contract fixture is green against the real
  executor — §1's first box can be ticked with the log as evidence.
- **Exit 3 — misconfigured:** required env missing/underivable; the
  runner names what to export. The seam's own guard inside pytest
  (base URL set but no secret → pytest exits 4,
  `tests/test_actions.py`) also maps here.
- **Exit 2 — probe failed:** executor unreachable or not speaking
  contract v1 pre-auth; the sweep never starts.
  `scripts/readiness_check.py --probe` is the same handshake.
- **Exit 1 — sweep FAILED:** fixture divergence. Fine print (cutover
  §1): the deterministic-delta assertions assume the committed
  snapshot's starting values, so **reload the test guild's fixture
  data between passes** — a stale guild fails honestly without any
  executor bug. Shim in-memory `state` assertions guard/skip
  themselves in this mode.

## After PASS — the manual 3-step audit verification

Not covered by any sweep (cutover §1's audit checkbox has the full
field list): signed into the test-guild site, do (a) an accepted
`mine`, (b) an economy rejection (`sell` more than held → 422
`economy_rejection`), (c) a byte-identical retry of (a). Verify
bot-side: (a) and (b) each produced exactly ONE audit row, (c)
produced NO new row and answered `replayed: true`.

## Rollback

Anything looks wrong on the live side: `docs/live-prod-cutover.md` §4
— every lever is an owner-held unset, nothing deploys. The flag itself
stays owner-only (§5); this runbook enables nothing.
