# Session 2026-07-11 — stage (a) READ contract v1

> **Status:** `in-progress` *(born-red — an ADDED card gates advisory in CI
> per `.github/workflows/substrate-gate.yml`; flipped to `complete` at
> session close per `.sessions/README.md`.)*

## Plan

Execute stage (a) READ CONTRACT v1 (coordinator-assigned): formalize the
bot→web read relay's snapshot shape as a versioned contract —
`docs/mining-data-contract.md` (prose) + `schemas/mining_snapshot.v1.schema.json`
(JSON Schema draft 2020-12, machine twin) — wire a schema gate
(`tests/test_schema_gate.py` + `.github/workflows/schema-gate.yml`,
pinned dev deps in `requirements-dev.txt`), and make the stack consume the
envelope: `data/sample_snapshot.json` conformant (schema_version `"1"`,
`generated_at`, string snowflakes), frontend renders
`snapshot v1 · generated <ts>`, tests derive `REQUIRED_MINER_FIELDS` from
the schema (single source of truth). Oracle-confirmed constraints encoded:
equipment slot enum (tool/light/charm/weapon/shield/helmet/chestplate/
leggings/boots), depth bands 0–3, energy cap 60, vault_level 0–6; dynamic
item/skill/structure maps stay open-keyed.

Constraints honored: still read-only end to end — no auth, no DB, no
secrets; server serves the file unchanged; `control/status.md` /
`control/inbox.md` / `substrate-gate.yml` untouched (single-writer /
kit-owned). Work claim: `control/claims/claude-read-contract-v1.md`.

## Close-out

- Shipped the v1 READ contract: prose + draft 2020-12 schema, strict
  envelope (`additionalProperties: false`) with permissive dynamic maps,
  `schema_version` pinned `const "1"`, snowflakes as strings (IEEE-754
  precision), optional `max_depth`/`biomes` world-shape hints.
- Schema gate live: `tests/test_schema_gate.py` (conformance + negative
  cases + dynamic-key allowance) validated with
  `jsonschema.Draft202012Validator`; CI workflow `schema-gate.yml` runs
  `python3 -m pytest -q` on 3.10 with pinned deps (pytest was NOT
  previously enforced by any workflow — substrate-gate runs only the kit
  check).
- Single source of truth: `tests/test_snapshot.py` now derives
  `REQUIRED_MINER_FIELDS` (and the envelope list) from the schema file.
- verify: `python3 -m pytest -q` → 25 passed. `bootstrap.py check --strict`
  → red only on session-card advisories (this born-red card + the ORDER 000
  card left `in-progress` by its session) — no new failure classes added.
- Guard recipe (deferred): when the real bot-side producer lands, point
  `tests/test_schema_gate.py::test_sample_snapshot_conforms_to_v1` at the
  relay payload fixture it emits — the validator fixture + schema path
  constant are the only two lines to touch.

## 💡 Session idea

The staleness threshold (contract: ~180 s) is currently prose-only — a tiny
frontend test hook (inject a fake `now`, assert the stale indicator renders)
would make the staleness contract executable before the real relay exists.

## ⟲ Previous-session review

ORDER 000's oracle-true field names made this stage almost mechanical — the
contract table wrote itself from the sample. Workflow improvement: the
ORDER 000 card's `[[fill:]]` slots are still unresolved; sessions should
budget five minutes at close to resolve auto-draft slots so the next
previous-session review has a completed card to review.

- **📊 Model:** Claude Fable 5 · standard effort · task-class: contract-formalization + CI-gate (build)
