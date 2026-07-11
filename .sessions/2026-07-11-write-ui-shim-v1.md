# Session 2026-07-11 — stage (c) WRITE contract v1 (part 2: shim + action UI)

> **Status:** `complete`

## Plan

Execute stage (c) part 2 (coordinator-assigned, TEST GUILD ONLY), building
on the merged part-1 contract (PR #13): make the write contract executable
end to end without any bot-side code existing yet. Ship (1) a dev/test-only
bot shim (`tests/shim/shim_bot.py`, runnable via
`python3 -m tests.shim.shim_bot`, NEVER in the prod server path)
implementing the whole contract against an in-memory copy of the committed
snapshot — HMAC verification, schema validation, closed enum, test-guild
allowlist, deterministic transitions (mine → +ore/−energy/+xp,
descend/ascend → depth ±1, sell → inventory−− coins++, vault ops move
coins, equip flips the slot), a per-action in-memory audit log with the
contract's required fields, idempotent replay; (2) the web relay
`POST /api/action` (`server/actions.py` + `server/app.py`): suid derived
from the VERIFIED session cookie, guild_id from the snapshot, HMAC signing
server-side — the browser sends only `{action_id, action, params}` and
never sees the shared secret; (3) action buttons on the signed-in
"My miner" view, DEGRADED BY DEFAULT: enabled only when
`MINING_WRITE_ENDPOINT` (+ `MINING_WRITE_SHARED_SECRET`) is set, with a
persistent TEST ECONOMY badge when on and honest disabled buttons
("Writes not configured — read-only mode") when off; (4) e2e tests for all
of it, green with ZERO env vars (CI's exact shape).

Constraints honored: `server/` stays stdlib-only (the shim lives under
`tests/`, where the dev-only jsonschema gate dep already lives); no secret
values anywhere; `control/status.md` / `control/inbox.md` untouched.
Close-out: claim `control/claims/claude-write-contract.md` released
(deleted) in this PR; the stale oauth claim was already released by
heartbeat #12 — nothing else to prune.

## Close-out

- Shim ships the contract's exact semantics: signature before timestamp
  (constant-time, shared canonical implementation in `server/actions.py`
  so web and shim can never drift), reason-code classification
  (`unknown_action` / `invalid_params` / `malformed_request` /
  `unsupported_contract_version`), placeholder action_id echo for
  unattributable requests, rejected outcomes stored and replayed, 409
  `replayed_action` on key reuse without clobbering the original, audit
  rows carrying action_id/action/suid/guild_id/params_digest/outcome/
  timestamp/contract_version/origin="web".
- Web relay proves the trust model in tests: a browser body carrying
  `suid` or `guild_id` is rejected outright (exactly-three-keys rule), and
  the audit row's suid is asserted to equal the cookie's uid — actor
  binding is server-side by construction.
- Degraded mode verified: no env vars → `/api/action` answers
  `503 {"error": "writes not configured"}`, `/api/me` carries
  `writes_configured: false`, buttons render disabled; the enabled path is
  tested end to end browser→web→shim with matching test secrets.
- Frontend: action rows (mine/descend/ascend, sell item+qty, vault
  amount deposit/withdraw, equip item+slot) on the my-miner view, result
  line showing accepted/rejected outcomes, persistent TEST ECONOMY badge
  in the header whenever writes are configured.
- verify: `python3 -m pytest -q` → 116 passed (82 + 34 new in
  `tests/test_actions.py`; no env vars, no network beyond loopback).
  `python3 bootstrap.py check --strict` → all checks passed.
- Guard recipe (deferred): when the real bot-side endpoint lands, run
  `tests/test_actions.py`'s shim-conformance tests against it by swapping
  the `shim` fixture's base URL for the real endpoint (plus its test
  secret) — the fixture boundary (`make_shim_server` → base URL) is the
  only seam to touch; identical passes = the done-criterion "the shim
  tests' contract fixtures validate against the real endpoint's behavior".

## 💡 Session idea

The shim's deterministic transitions would make a lovely property test:
for any accepted action sequence, replaying the sequence through a fresh
shim must reproduce identical audit digests and final state — a cheap
invariant harness the real bot-side endpoint could later be held to as
well.

## ⟲ Previous-session review

Part 1's decision to pin the equip slot enum byte-identical to the READ
contract paid off immediately: the frontend's slot dropdown and the shim's
executor needed zero translation tables. Friction worth naming: the
`/api/me` exact-dict assertions in `tests/test_auth.py` had to be edited
to admit the new `writes_configured` flag — exact-equality asserts on
growing envelopes trade drift-detection for churn; subset asserts on the
fields under test would have absorbed this additive change.

- **📊 Model:** Claude Fable 5 · standard effort · task-class: contract-executable (shim + relay + UI + e2e) (build)
