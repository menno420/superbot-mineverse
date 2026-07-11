# superbot-mineverse · status
updated: 2026-07-11T03:58:00Z
phase: DEEPENING — read-views slice 2 (PR #21) MERGED: EVERY required miner field now renders; micro-polish slice in flight; ladder PREPARED through (d) — live-prod remains OWNER-FLAG-GATED; test-guild read-write waits on bot lanes + owner env vars
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN; engaged = no unrendered banners + live CI gate (substrate-gate required context on main ruleset) + session loop engaged — all met
last-shipped: READ-VIEWS DEEPENING SLICE 2 MERGED — PR #21 (a2672dc) 2026-07-11T03:40Z: skills panel + structures panel, per-depth-band position mini-map, snapshot-staleness UX with 180s threshold, energy meter; tests 163→187, all green; all shaping schema-derived. COVERAGE MILESTONE: every required miner field of mining_snapshot.v1 now renders in the web views. Prior: PR #20 (heartbeat), #19 (conformance seam), #18 (deepening slice 1), #17 (heartbeat), #16 (stage d prep), #15, #13/#14 (stage c), #12, #11 (stage b), #10/#8/#7 (stage a), #9, #6, #5, #4, #3, #2, #1.
blockers: none
orders: acked= done=
⚑ needs-owner: 2 items — (1) provision the six env vars to switch sign-in on (and, for test-guild write mode, the write-endpoint pair); (2) make pytest a required (blocking) status check on main. Structured OWNER-ACTION blocks below. Bot-lane FLAGs below stay informational until the manager picks them up.
notes: coordinator heartbeat, boot session cse_017yrng4qx2LcLNqKb5AGoe8 — deepening slice 2 MERGED record (full required-field coverage), remaining micro view gaps + micro-polish dispatch, ladder prepared, owner-action blocks + both bot-lane FLAGs carried verbatim, in-flight + backlog + routine/chain verbatim records below (this Project is this file's SOLE writer; overwritten whole, never appended). Housekeeping this heartbeat: removed released claim control/claims/claude-slice2-deep-views.md (rode PR #21; deletion deferred to this control-lane PR per pattern).

## Deepening slice 2 — MERGED (PR #21 a2672dc 2026-07-11T03:40Z)

- Skills panel + structures panel; per-depth-band position mini-map;
  snapshot-staleness UX with 180s threshold; energy meter. Tests 163 → 187,
  all green; all view shaping schema-derived (no hand-listed fields).
- COVERAGE MILESTONE: every required miner field in
  schemas/mining_snapshot.v1.schema.json now renders somewhere in the web
  views.
- Remaining view gaps (micro): suid and guild_id are fetched but unpainted;
  xp.game is not on the card face. Micro-polish slice dispatched — see IN
  FLIGHT.
- LADDER: 0 ✓ · (a) ✓ · (b) ✓ · (c) ✓ web-side · (d) PREPARED ✓ — live-prod
  remains OWNER-FLAG-GATED (never agent-decided). Test-guild read-write still
  waits on: Builder lane WRITE endpoint (FLAG 2) + READ relay projection
  (FLAG 1) + owner env vars (OWNER-ACTION 1).

## ⚑ OWNER-ACTION 1 — switch sign-in on (and test-guild write mode)

WHAT: provision host env vars: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY, MINING_WRITE_ENDPOINT, MINING_WRITE_SHARED_SECRET — the last two only for test-guild write mode.
WHERE: the host environment that runs the web server (wherever you launch server/ from), plus the Discord Developer Portal for the client id/secret and redirect URI; MINING_WRITE_ENDPOINT/MINING_WRITE_SHARED_SECRET come from the bot lane once its write endpoint exists (FLAG 2 below).
HOW: set the variables above in the server's environment; OAUTH_REDIRECT_URI must exactly match the redirect URI registered in the Discord app; WEB_SESSION_SIGNING_KEY is any long random secret you generate; MINING_WRITE_SHARED_SECRET must match the bot endpoint's HMAC key.
WHY-IT-MATTERS: until the OAuth four exist, players cannot sign in — the site runs in degraded (read-only, anonymous) mode by design; until the write pair exists, the action UI stays in TEST ECONOMY degraded mode with no live write path.
UNBLOCKS: the My-miner signed-in view goes live on server restart with the OAuth vars; test-guild write mode goes live once the write pair is set and the bot endpoint (FLAG 2) ships.
VERIFIED-NEEDED: agent sessions have no access to the host environment or the Discord Developer Portal — only the owner can provision secrets; code paths verified in degraded mode plus tests (130 passing with zero env vars).

## ⚑ OWNER-ACTION 2 — make pytest blocking

WHAT: make pytest blocking: add the pytest workflow as a required status check on main.
WHERE: Settings → Rules → Rulesets → main ruleset (already requires substrate-gate) → "Require status checks to pass".
HOW: add context exactly `pytest`.
WHY-IT-MATTERS: today a PR whose tests fail can still merge; substrate-gate is required but pytest is advisory. NEW EVIDENCE: PR #16 auto-merged on substrate-gate alone — pytest went green 28s AFTER the merge landed.
UNBLOCKS: every future merge is test-gated with zero coordinator babysitting.
VERIFIED-NEEDED: coordinator's one ruleset-modification attempt was classifier-denied (recorded in the gate-audit history); ruleset edits are an owner-only surface. Proof once flipped: next PR's merged_at ≥ pytest check-run completed_at (PR #16 shows the current gap live).

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

- Micro-polish slice (paint suid + guild_id, surface xp.game on the card
  face) — dispatched 2026-07-11T03:56Z, session cse_014zpnwjGjP4ETFJ3wiZcVEv.

## Ladder + deepening backlog

- Ladder: 0 ✓ · (a) ✓ · (b) ✓ · (c) ✓ web-side · (d) PREPARED ✓ — live-prod
  is OWNER-FLAG-GATED, never agent-decided; test-guild read-write pending
  FLAG 1 + FLAG 2 + owner env vars.
- Backlog (never-idle): audit-trail end-to-end verification (waits on the
  Builder lane's real endpoint; 3-step procedure in
  docs/live-prod-cutover.md); conformance run of tests/test_actions.py
  against the real endpoint via SHIM_CONFORMANCE_BASE_URL once it exists —
  both wait on the Builder lane; more contract fields, views, and tests as
  they surface.

## Routine + chain (verbatim record)

Failsafe: trig_01K8xmAKYS5S2HLy1HPANM7j cron 20 */2 * * * (next 04:20Z).
Chain link: re-armed each wake as run_once triggers from worker seats —
current link fires ~04:11Z (id in coordinator log); send_later is
self-session-only on worker seats (no target param).
