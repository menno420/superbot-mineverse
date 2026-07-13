# Session — 2026-07-14 — snapshot contract constant + field-parity audit

> **Status:** `in-progress`
> **Branch:** `claude/snapshot-contract-constant`
> **Venue:** lane worker session (ORDER 006 item 4 — EAP final-night
> worklist; ORDER 007 production-grade doctrine adopted: correctness
> outranks speed, no gate relaxed).

**Goal:** land the build-direct pair ORDER 006 item 4 names, from the two
idea-engine captures at `menno420/idea-engine@2e5d73f`
(`ideas/superbot-mineverse/snapshot-contract-shared-constant-2026-07-11.md`,
`ideas/superbot-mineverse/snapshot-field-parity-audit-2026-07-11.md`):

1. **Shared constant** — promote the schema-derived required-field truth
   out of `tests/test_snapshot.py:22-23` into an importable, vendorable
   `snapshot_contract.py` (stdlib-only, ~20 lines, derives
   `REQUIRED_MINER_FIELDS` / `REQUIRED_ENVELOPE_FIELDS` from
   `schemas/mining_snapshot.v1.schema.json` at import time), switch the
   test to import it, zero behavior change — the FLAG-1 exporter can
   vendor-pin the same artifact so a field rename goes PR-red in CI on
   either side instead of runtime-red at relay cadence.
2. **Field-parity audit** — execute the audit the parity idea doc
   describes (mining_snapshot.v1 vs games-web.character-sheet v1.0.1),
   verifying its probe findings first-hand at both pins, committed as a
   findings table beside `docs/mining-data-contract.md`
   (`docs/findings/`), honest "not measured" where the lane cannot
   measure.

## Close-out

(pending — flipped with the final commit)
