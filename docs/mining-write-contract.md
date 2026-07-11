# superbot-mineverse — mining action WRITE contract (v1) — TEST GUILD ONLY

> **Status:** `binding`
>
> The versioned WRITE contract between this web app (proposer) and the
> superbot bot side (executor). Machine-checkable twins:
> `schemas/mining_action.v1.schema.json` (the action proposal) and
> `schemas/mining_action_response.v1.schema.json` (the bot's answer), both
> JSON Schema draft 2020-12, enforced in CI by
> `tests/test_write_schema_gate.py`. Where prose and schema disagree, the
> schema wins for shape; this doc wins for semantics.

## Purpose and trust model

The bot owns the live mining state in Postgres; this web app **never**
touches that database and **never** holds the bot token. A web write is
therefore never a write at all — it is a **proposal**: the web server
POSTs a signed action-proposal document to a bot-side endpoint, and the
bot decides, executes (through its single write boundary,
`disbot/services/mining_workflow.py`), audits, and answers. The web app
holds no game rules; a proposal the bot rejects simply did not happen.

```
browser ──POST /api/action──▶ web server ──signed proposal──▶ bot-side endpoint
   ▲        (session cookie      (attaches suid from the        (validates, executes
   │         proves identity)     verified session + HMAC)       via mining_workflow,
   └──────────── response envelope, verbatim ◀── audits, answers)
```

- The **browser** never signs anything and never sees the shared secret;
  it talks only to this web server's `POST /api/action`, authenticated by
  the existing session cookie (docs/auth.md).
- The **web server** derives the actor `suid` from the verified session
  cookie — **never** from anything the browser asserts — attaches the
  snapshot's `guild_id`, signs the proposal (HMAC, below), and relays the
  bot's response envelope verbatim.
- The **bot side** is the only executor. Its endpoint (to be built in the
  superbot repo) validates the signature, the schema, the closed action
  enum, and the test-guild allowlist before touching `mining_workflow.*`.

**TEST GUILD ONLY:** v1 of this contract is scoped to the test economy.
The bot-side handler MUST hold a hard allowlist of test guild ids and
reject every other guild with `guild_not_allowed` — including all live
production guilds — until the owner flips the stage-(d) live-cutover flag.
That flag is the owner's alone; nothing in this contract or its
implementations may widen the allowlist.

## The bot-side endpoint

One route: `POST` to the URL the host provides in `MINING_WRITE_ENDPOINT`
(for example `https://bot.internal:9443/relay/mining/action`). Request and
response bodies are `application/json; charset=utf-8`, one action per
request. The web server is the only intended caller; the endpoint is not
browser-facing.

## Request envelope — `schemas/mining_action.v1.schema.json`

A proposal is a single JSON object, **closed**
(`additionalProperties: false`):

| Field | Type | Required | Semantics |
|---|---|---|---|
| `contract_version` | string, exactly `"1"` | yes | WRITE-contract major version (`const`, mirroring the READ contract's versioning). |
| `action_id` | string, lowercase UUID v4 | yes | Client-generated **idempotency key**, unique per intended action. The browser mints it (`crypto.randomUUID()`) so an end-to-end retry of the same click replays instead of re-executing. |
| `guild_id` | string of digits | yes | Discord guild snowflake — a STRING on the wire, same IEEE-754 rationale as the READ contract. Attached by the web server from the snapshot envelope. |
| `suid` | string of digits | yes | The acting player's superbot user id (Discord user snowflake, string). **Derived server-side from the verified web session cookie — never client-asserted.** A proposal whose `suid` the web server did not itself derive is a bug, full stop. |
| `action` | string from the closed enum below | yes | Which `mining_workflow` op is proposed. |
| `params` | object, shape depends on `action` | yes | Per-action parameters (closed sub-schemas, below). Actions without parameters send `{}`. |

### The action enum (closed, v1)

Each action maps 1:1 to an op behind the bot's single write boundary,
`disbot/services/mining_workflow.py`. v1 deliberately starts with a safe
subset; widening the enum is an additive v1 schema change (new enum entry
+ new params sub-schema + new fixture), done in this repo first.

| `action` | `mining_workflow` op | `params` |
|---|---|---|
| `mine` | `mine` | `{}` — none |
| `descend` | `descend` | `{}` — none |
| `ascend` | `ascend` | `{}` — none |
| `sell` | `sell` | `{"item": <string, len ≥ 1>, "quantity": <int ≥ 1>}` |
| `vault_deposit` | `vault_deposit` | `{"amount": <int ≥ 1>}` — coins moved into the vault |
| `vault_withdraw` | `vault_withdraw` | `{"amount": <int ≥ 1>}` — coins moved out of the vault |
| `equip` | `equip` | `{"item": <string, len ≥ 1>, "slot": <one of the READ contract's 9 slot names>}` |

Every `params` sub-schema is closed (`additionalProperties: false`); the
`equip` slot enum is byte-identical to the READ contract's equipment slot
set (`tool`, `light`, `charm`, `weapon`, `shield`, `helmet`,
`chestplate`, `leggings`, `boots`). An action name outside the enum is
`unknown_action`; params that do not match their action's sub-schema are
`invalid_params`.

Remaining `mining_workflow` ops (`craft`, `quick_craft`, `sell_all`,
`buy`, `vault_deposit_all`, `vault_upgrade`, `build_structure`,
`harvest`, `explore`, `use_item`, `cook`, `unequip`, loadouts, `repair`)
are **out of the v1 enum on purpose** — they join only by additive
contract change, never by the bot accepting an undeclared name.

## Response envelope — `schemas/mining_action_response.v1.schema.json`

The bot answers every well-formed-enough-to-parse proposal with a single
closed JSON object:

| Field | Type | Required | Semantics |
|---|---|---|---|
| `contract_version` | string, exactly `"1"` | yes | Mirrors the request. |
| `action_id` | string, lowercase UUID v4 | yes | Echoes the proposal's idempotency key. |
| `status` | `"accepted"` \| `"rejected"` | yes | Whether the action executed. |
| `reason_code` | string from the closed taxonomy below | yes | Machine-readable outcome. Exactly `"ok"` when accepted; never `"ok"` when rejected (the schema enforces both). |
| `message` | string | yes | Human-readable explanation, safe to show in the UI. |
| `replayed` | boolean | yes | `true` iff this response was served from the idempotency store instead of a fresh execution. |
| `result` | object | on accept only | Present iff `status` is `"accepted"` (schema-enforced both ways). Contains `state_delta` (object: the miner fields this action changed, new values, READ-contract field names — e.g. `{"depth": 2, "coins": 18470}`) and `snapshot_generated_at` (ISO 8601 UTC): the `generated_at` the next READ-contract snapshot reflecting this action will carry or exceed — the freshness pointer that ties the write contract back to the read contract's staleness semantics. |

### HTTP status mapping

| `reason_code` | HTTP | Meaning |
|---|---|---|
| `ok` | 200 | Accepted and executed (or idempotent replay of an accepted action). |
| `malformed_request` | 400 | Body is not valid JSON or fails the request schema at the envelope level. |
| `unsupported_contract_version` | 400 | `contract_version` the executor does not speak. |
| `unknown_action` | 400 | `action` outside the closed enum. |
| `invalid_params` | 400 | `params` fail the action's sub-schema. |
| `invalid_signature` | 401 | HMAC verification failed (wrong/missing signature or headers). |
| `stale_timestamp` | 401 | Signature timestamp outside the skew window. |
| `guild_not_allowed` | 403 | `guild_id` not on the test-guild allowlist — the stage-(d) wall. |
| `actor_not_found` | 404 | `suid` has no player state in that guild. |
| `replayed_action` | 409 | `action_id` seen before **with a different body** (key reuse — a client bug; the original response is NOT returned because the request is not the original request). |
| `economy_rejection` | 422 | The game itself said no (not enough energy/coins/items, depth limits, …) — `mining_workflow`'s domain verdict, relayed. |
| `rate_limited` | 429 | Over the per-actor budget; `Retry-After` header carries seconds. |
| `internal_error` | 500 | Executor fault; safe to retry with the SAME `action_id`. |

An idempotent replay repeats the original response's HTTP status. A
rejected response never has a `result`, and `replayed` on a rejection is
`false` except for replays of stored rejections (below). When a request
is too broken to carry a usable key (unparseable body, unsigned probe,
malformed `action_id`), the executor echoes the placeholder
`action_id` `00000000-0000-4000-8000-000000000000` so the response still
conforms to the schema.

## Idempotency

- `action_id` is the idempotency key. The executor stores, per
  `(guild_id, action_id)`, a digest of the request body plus the complete
  original response (body and HTTP status).
- **Replay** (same `action_id`, byte-equal body digest, inside the
  retention window): return the ORIGINAL response — same status, same
  body except `replayed: true` — and **never re-execute**. Both accepted
  and rejected outcomes are stored and replayed; a retry must not turn a
  rejection into a second evaluation.
- **Key reuse** (same `action_id`, different body digest): reject with
  `replayed_action` (409). Never execute, never return the stored
  response for a request that isn't the original.
- **Retention window**: at least **24 hours** (v1 default; the executor
  may keep more). After the window an `action_id` MAY be treated as new —
  clients must mint a fresh UUID per intended action and only ever reuse
  one to retry that same action.

## Rate limits

Enforced per `(suid, guild_id)` on the executor side. v1 defaults
(executor-configurable, but these are the contract's expectations):

- **Burst**: 10 actions per 10 seconds.
- **Sustained**: 60 actions per minute.

Over budget → HTTP 429, `reason_code: "rate_limited"`, plus a
`Retry-After` header (integer seconds). Rate-limited proposals are NOT
stored for idempotency — retrying the same `action_id` after the window
is a fresh evaluation.

## Transport auth — HMAC request signing

Every request to the bot-side endpoint carries two headers:

| Header | Value |
|---|---|
| `X-Mineverse-Timestamp` | Unix epoch seconds at signing time, as a decimal string (e.g. `1783728000`). |
| `X-Mineverse-Signature` | `hex(HMAC_SHA256(MINING_WRITE_SHARED_SECRET, string_to_sign))`, lowercase hex. |

The string to sign is:

```
string_to_sign = METHOD + "\n" + PATH + "\n" + TIMESTAMP + "\n" + sha256_hex(BODY)
```

- `METHOD` — uppercase HTTP method (`POST`).
- `PATH` — the URL path component of the endpoint (no scheme/host/query),
  e.g. `/relay/mining/action`.
- `TIMESTAMP` — the exact `X-Mineverse-Timestamp` header value.
- `sha256_hex(BODY)` — lowercase hex SHA-256 of the raw request body bytes.

Verification: recompute, compare constant-time
(`hmac.compare_digest`), and reject on mismatch with
`invalid_signature` (401). Then check the timestamp: **skew window ±300
seconds** against the executor's clock; outside it → `stale_timestamp`
(401). Signature first, then timestamp — an unsigned request learns
nothing about the clock. The shared secret lives in the
`MINING_WRITE_SHARED_SECRET` host env var on BOTH sides and is never
committed anywhere.

### Web session → suid binding

`POST /api/action` on this web server accepts, from the browser, only
`{action_id, action, params}`. The web server:

1. verifies the session cookie (existing docs/auth.md machinery) — no
   valid cookie → 401, nothing is relayed;
2. sets `suid` := the cookie's verified Discord user id, and `guild_id`
   := the current snapshot's envelope `guild_id`;
3. assembles the full proposal, signs it, POSTs it to
   `MINING_WRITE_ENDPOINT`, and relays the response envelope verbatim.

There is no code path by which browser input can influence `suid` or
`guild_id`.

## Degraded mode (the default — CI and fresh clones)

Exactly like the OAuth pattern (docs/auth.md): writes are configured by
host env vars ONLY —

| Env var | Meaning |
|---|---|
| `MINING_WRITE_ENDPOINT` | Full URL of the bot-side action endpoint. Absent → writes are OFF. |
| `MINING_WRITE_SHARED_SECRET` | HMAC-SHA256 key for request signing (shared with the bot side). |

With either absent, the web app runs exactly as before: every read view
works, the action buttons render disabled with an honest "writes not
configured" note, and `POST /api/action` answers
`503 {"error": "writes not configured"}`. The full test suite passes
with no env vars set — CI never sees a secret.

## AUDIT REQUIREMENT (binding on the bot-side executor)

**Fact, verified against the superbot oracle:** the bot's single write
boundary, `disbot/services/mining_workflow.py`, currently makes **zero
`emit_audit_action` calls** — its only audit trail today is
`economy_audit_log` rows written on coin legs inside the transaction.
Actions that move no coins therefore leave no audit trail at all, and
even coin-moving actions record nothing about WHO proposed them from
WHERE.

That gap MUST NOT be carried into web-originated writes. The bot-side
relay/handler layer that executes proposals under this contract MUST
record an audit entry for **every** web-originated action — accepted or
rejected — by calling
`emit_audit_action(subsystem="mining", actor_type="web_player", ...)`
or an equivalent extension of the economy-audit mechanism, with at
minimum these fields:

| Field | Content |
|---|---|
| `action_id` | The proposal's idempotency key. |
| `action` | The enum action name. |
| `suid` | The acting player (string snowflake). |
| `guild_id` | The guild (string snowflake). |
| `params_digest` | SHA-256 hex of the canonical `params` JSON (parameters are digested, not inlined, so audit rows stay bounded). |
| `outcome` | `accepted` or `rejected` + the `reason_code`. |
| `timestamp` | ISO 8601 UTC of execution/rejection. |
| `contract_version` | `"1"`. |
| `origin` | The literal `"web"` — distinguishing web-originated actions from Discord-command ones forever. |

Idempotent replays are NOT re-audited (nothing executed); a
`replayed_action` key-reuse rejection IS audited (it is a client anomaly
worth seeing). The audit write belongs in the same transaction as the
state mutation wherever the mechanism allows, so an audited-but-not-
executed or executed-but-not-audited action is impossible.

## Versioning policy

Same regime as the READ contract: `contract_version` is a string,
pinned `const "1"`. Within v1, changes are **additive-only** — new enum
actions (with their params sub-schemas), new OPTIONAL response fields —
made by editing the v1 schema files in place. Any breaking change bumps
to `"2"` in NEW schema files and freezes the v1 files. Executors must
reject versions they do not speak (`unsupported_contract_version`), never
guess.

## Enforcement

- `tests/test_write_schema_gate.py` validates a fixture proposal for
  every enum action (and accepted/rejected response fixtures) against
  both schemas with `jsonschema.Draft202012Validator`, plus negative
  cases proving the gate bites. CI runs it in the same pytest workflows
  that gate the READ contract.
- Stage-(c) reference implementation: the dev/test-only bot **shim**
  `tests/shim/shim_bot.py` (run: `python3 -m tests.shim.shim_bot`)
  implements this contract against an in-memory copy of the committed
  sample snapshot (signature check, schema check, allowlist,
  deterministic transitions, in-memory audit log, idempotent replay) so
  the contract is executable before the real bot-side endpoint exists.
  `tests/test_actions.py` exercises it end to end — including through the
  real web server's `POST /api/action` relay. The shim is NEVER wired
  into the production server path (it lives under `tests/`, not
  `server/`, keeping the backend stdlib-only).
- The real bot-side endpoint is built in the superbot repo against this
  document; its done-criterion is that the shim's contract fixtures
  validate against the real endpoint's behavior.
