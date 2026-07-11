# superbot-mineverse · status
updated: 2026-07-11T02:49:52Z
phase: stage (c) WRITE CONTRACT v1 COMPLETE web-side (PRs #13+#14 merged, test economy only); stage (d) LIVE-PROD PREP dispatched; test-guild read-write waits on bot endpoint + owner env vars
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN; engaged = no unrendered banners + live CI gate (substrate-gate required context on main ruleset) + session loop engaged — all met
last-shipped: STAGE (c) WRITE CONTRACT v1 COMPLETE — PR #13 (contract + action/response schemas + 32 schema-gate tests) and PR #14 (mock bot shim tests/shim/shim_bot.py, degraded-by-default action UI with TEST ECONOMY badge, server-side HMAC signing in server/actions.py, 34 e2e tests) both MERGED on green 2026-07-11T02:32Z/02:46Z. Repo: 116 pytest green with zero env vars, strict check green. Prior: PR #12 (heartbeat), #11 (stage b OAuth), #10/#8/#7 (stage a), #9, #6, #5, #4, #3, #2, #1.
blockers: none
orders: acked= done=
⚑ needs-owner: 2 items — (1) provision the six env vars to switch sign-in on (and, for test-guild write mode, the write-endpoint pair); (2) make pytest a required (blocking) status check on main. Structured OWNER-ACTION blocks below. Bot-lane FLAGs below stay informational until the manager picks them up.
notes: coordinator heartbeat, boot session cse_017yrng4qx2LcLNqKb5AGoe8 — stage (c) DONE record, owner-action blocks, two bot-lane FLAGs (READ carried verbatim, WRITE new), in-flight + ladder + deepening backlog, and routine/chain verbatim records below (this Project is this file's SOLE writer; overwritten whole, never appended).

## Stage (c) WRITE CONTRACT v1 — DONE (PRs #13 + #14, merged 2026-07-11T02:32Z / 02:46Z)

- PR #13: write contract v1 — action-proposal envelope, action + response
  schemas (schemas/mining_action.v1.schema.json and response counterpart),
  prose contract, 32 schema-gate tests. Merged on green 02:32Z.
- PR #14: mock bot shim tests/shim/shim_bot.py, degraded-by-default action UI
  with TEST ECONOMY badge, server-side HMAC signing in server/actions.py,
  34 e2e tests. Merged on green 02:46Z.
- Repo state: 116 pytest green with zero env vars; check --strict green.
- Web side complete; test-guild read-write pending the bot WRITE endpoint
  (FLAG 2 below) plus the owner env vars (OWNER-ACTION 1).

## ⚑ OWNER-ACTION 1 — switch sign-in on (and test-guild write mode)

WHAT: provision host env vars: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY, MINING_WRITE_ENDPOINT, MINING_WRITE_SHARED_SECRET — the last two only for test-guild write mode.
WHERE: the host environment that runs the web server (wherever you launch server/ from), plus the Discord Developer Portal for the client id/secret and redirect URI; MINING_WRITE_ENDPOINT/MINING_WRITE_SHARED_SECRET come from the bot lane once its write endpoint exists (FLAG 2 below).
HOW: set the variables above in the server's environment; OAUTH_REDIRECT_URI must exactly match the redirect URI registered in the Discord app; WEB_SESSION_SIGNING_KEY is any long random secret you generate; MINING_WRITE_SHARED_SECRET must match the bot endpoint's HMAC key.
WHY-IT-MATTERS: until the OAuth four exist, players cannot sign in — the site runs in degraded (read-only, anonymous) mode by design; until the write pair exists, the action UI stays in TEST ECONOMY degraded mode with no live write path.
UNBLOCKS: the My-miner signed-in view goes live on server restart with the OAuth vars; test-guild write mode goes live once the write pair is set and the bot endpoint (FLAG 2) ships.
VERIFIED-NEEDED: agent sessions have no access to the host environment or the Discord Developer Portal — only the owner can provision secrets; code paths verified in degraded mode plus tests (116 passing with zero env vars).

## ⚑ OWNER-ACTION 2 — make pytest blocking

WHAT: make pytest blocking: add the pytest workflow as a required status check on main.
WHERE: Settings → Rules → Rulesets → main ruleset (already requires substrate-gate) → "Require status checks to pass".
HOW: add context exactly `pytest`.
WHY-IT-MATTERS: today a PR whose tests fail can still merge; substrate-gate is required but pytest is advisory.
UNBLOCKS: every future merge is test-gated with zero coordinator babysitting.
VERIFIED-NEEDED: coordinator's one ruleset-modification attempt was classifier-denied (recorded in the gate-audit history); ruleset edits are an owner-only surface. Proof once flipped: next PR's merged_at ≥ pytest check-run completed_at.

## ⚑ FLAG 1 — superbot manager / bot lane — READ relay (carry verbatim)

The bot must emit a mining snapshot into the part-4d bot→web read relay
conforming to schemas/mining_snapshot.v1.schema.json (prose:
docs/mining-data-contract.md, both on superbot-mineverse main). Envelope:
schema_version "1", generated_at ISO8601 UTC, guild_id STRING, miners[]; per
miner 16 v1 fields from mining_workflow / mining_player_state (suid string,
display_name, depth, record_depth, position {x,y}, energy
{current,updated_at}, coins, xp {game, game_total, shared_total, level} via
game_xp_service, equipment, gear_wear, mining_inventory, vault, vault_level,
skills, structures). Additive-only within v1; suggested cadence ~60s push +
on-demand. Done = relay payload validates against the v1 schema
(Draft202012Validator, same as tests/test_schema_gate.py).

## ⚑ FLAG 2 — superbot manager / bot lane — WRITE endpoint (carry verbatim)

Builder lane must implement HMAC-signed POST action-proposal endpoint
(suggested /relay/mining/action; web reads MINING_WRITE_ENDPOINT): headers
X-Mineverse-Signature / X-Mineverse-Timestamp, signature over
METHOD\nPATH\nTIMESTAMP\nsha256_hex(body), ±300s skew, key
MINING_WRITE_SHARED_SECRET; validate against
schemas/mining_action.v1.schema.json; closed enum
mine/descend/ascend/sell/vault_deposit/vault_withdraw/equip mapped 1:1 to
mining_workflow ops; idempotency by action_id (same body → replayed:true,
never re-executed, ≥24h retention; different body → 409 replayed_action);
rate limit per (suid,guild_id) 10/10s + 60/min with 429+Retry-After; execute
ONLY via disbot/services/mining_workflow.py; AUDIT EVERY web-originated
action accepted or rejected (emit_audit_action subsystem="mining",
actor_type="web_player", fields
action_id/action/suid/guild_id/params_digest/outcome/timestamp/contract_version/origin="web"
— mining_workflow emits no audit today, handler must add it); hard test-guild
allowlist, other guilds 403 guild_not_allowed until owner's stage-(d) flag.
Done = shim contract fixtures (tests/test_actions.py) pass against the real
endpoint.

## IN FLIGHT

- Stage (d) LIVE-PROD PREP — dispatched 2026-07-11T02:48Z to session
  cse_011mq5eZ9fpHdX1FbMRMA7zg. Deliverable: docs/live-prod-cutover.md,
  owner-flag-gated cutover checklist. THE FLAG IS THE OWNER'S, never
  agent-decided.

## Ladder + deepening backlog

- Ladder: 0 ✓, (a) ✓, (b) ✓, (c) ✓ web-side (test-guild read-write pending
  bot endpoint + env vars), (d) prep in flight.
- Deepening backlog (never-idle): more views (vault panel, inventory browser,
  depth/biome map, XP leaderboard), contract field deepening, more tests.

## Routine + chain (verbatim record)

Failsafe: trig_01K8xmAKYS5S2HLy1HPANM7j cron 20 */2 * * * (next 04:20Z).
Chain link: trig_01X5nvMW4ZK37iZeKRDuxstt fires 02:50:39Z, re-armed each wake
as run_once triggers from worker seats — send_later is self-session-only on
worker seats (no target param).
