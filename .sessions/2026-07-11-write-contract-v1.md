# Session 2026-07-11 — stage (c) WRITE contract v1 (part 1: contract + schemas)

> **Status:** `complete`

## Plan

Execute stage (c) WRITE CONTRACT v1 part 1 (coordinator-assigned, TEST
GUILD ONLY): formalize the web→bot action-proposal channel as a versioned
contract — `docs/mining-write-contract.md` (prose) with machine twins
`schemas/mining_action.v1.schema.json` (proposal envelope) and
`schemas/mining_action_response.v1.schema.json` (executor answer), both
draft 2020-12, `additionalProperties: false` discipline matching the READ
contract. Envelope: `contract_version` const `"1"`, `action_id` UUID v4
idempotency key, string snowflakes (`guild_id`, `suid` — suid derived
server-side from the verified session, never client-asserted), a CLOSED
action enum mapped 1:1 to `mining_workflow` ops (safe set: mine, descend,
ascend, sell, vault_deposit, vault_withdraw, equip) with closed per-action
params sub-schemas. Response: accepted/rejected + closed reason-code
taxonomy + idempotent-replay flag + state delta / snapshot freshness
pointer. Spec covers HMAC transport signing
(`X-Mineverse-Signature`/`X-Mineverse-Timestamp`,
`MINING_WRITE_SHARED_SECRET`, ±300 s skew), idempotency retention,
rate-limit defaults, hard test-guild allowlisting (`guild_not_allowed`
until the owner's stage-(d) flag), and the BINDING audit requirement
closing the oracle's gap: `mining_workflow.py` makes zero
`emit_audit_action` calls today (its only audit is `economy_audit_log`
rows on coin legs), so the bot-side relay MUST audit every web-originated
action. Gate: `tests/test_write_schema_gate.py` — a valid fixture per enum
action, accepted/rejected/replayed response fixtures, and negative cases
proving the gate bites.

Constraints honored: docs + schemas + tests only (no server/web behavior
change in this part); no new runtime deps (jsonschema is already the dev
gate mechanism); no secret values anywhere — env var NAMES only
(`MINING_WRITE_ENDPOINT`, `MINING_WRITE_SHARED_SECRET`);
`control/status.md` / `control/inbox.md` untouched. Work claim:
`control/claims/claude-write-contract.md` (released by part 2's
close-out).

## Close-out

- Shipped the v1 WRITE contract: proposals are signed documents, the bot
  is the only executor (via `disbot/services/mining_workflow.py`), the
  browser never sees the shared secret, and every proposal outside the
  test-guild allowlist dies with `guild_not_allowed` — live cutover is
  the owner's stage-(d) flag, not this contract's.
- Both schemas enforce the READ contract's disciplines: closed envelopes,
  string snowflakes, versioning by const-pinned string with additive-only
  v1 evolution; the equip slot enum is asserted byte-identical to the
  READ contract's equipment slots by a gate test.
- Response taxonomy is closed (13 codes) and cross-tied to status:
  accepted ⇒ `reason_code: ok` + `result` required; rejected ⇒ non-ok
  code + no `result` — both directions schema-enforced and negatively
  tested.
- Audit requirement written as binding, with required fields (action_id,
  action, suid, guild_id, params digest, outcome, timestamp,
  contract_version, origin="web") and the verbatim zero-emit_audit_action
  oracle fact, so the bot-lane builder cannot miss the gap.
- Router + README updated: `docs/AGENT_ORIENTATION.md` data-contracts
  entry and the repo-layout `schemas/` row now reach the write contract.
- verify: `python3 -m pytest -q` → 82 passed (50 pre-existing + 32 new in
  `tests/test_write_schema_gate.py`, no network, no secrets).
  `python3 bootstrap.py check --strict` → all checks passed.
- Guard recipe (deferred): when the real bot-side endpoint lands in the
  superbot repo, point the response-fixture assertions at recorded real
  responses — the seams to keep stable are `ACCEPTED_RESPONSE` /
  `REJECTED_RESPONSE` in `tests/test_write_schema_gate.py` and the two
  schema path constants at its top.

## 💡 Session idea

The reason_code → HTTP status mapping lives only in the contract prose
table; a tiny machine copy (a JSON map in `schemas/` or a constant the
shim and the real endpoint both import/mirror) would let a test assert
the mapping instead of trusting two implementations to read the same
table.

## ⟲ Previous-session review

The stage-(b) card's degraded-mode pattern (env-var presence drives an
honest disabled state, CI never sees a secret) transferred directly into
this contract's degraded-mode section — writing it cost minutes because
the OAuth precedent had already settled the shape. Its deferred
staleness-indicator test idea remains open; the write contract now adds a
second consumer for it (`snapshot_generated_at` freshness pointer), which
raises its value.

- **📊 Model:** Claude Fable 5 · standard effort · task-class: contract-formalization + schema-gate (build)
