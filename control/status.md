# superbot-mineverse · status
updated: 2026-07-11T02:19:30Z
phase: stage (b) DISCORD OAUTH merged (PR #11); stage (c) WRITE CONTRACT v1 (test guild only) dispatched; owner flips env vars to switch sign-in on
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN; engaged = no unrendered banners + live CI gate (substrate-gate required context on main ruleset) + session loop engaged — all met
last-shipped: Stage (b) DISCORD OAUTH — PR #11 MERGED 2026-07-11T02:13Z (substrate-gate ✓ + pytest ✓ on head 3131f87; 50 tests). Stage (a) arc closed earlier (PRs #7/#8/#10). Prior: PR #9 (heartbeat), #6 (slots+README), #5 (gitignore), #4, #3, #2, #1.
blockers: none
orders: acked= done=
⚑ needs-owner: 2 items — (1) provision the four Discord OAuth env vars to switch sign-in on; (2) make pytest a required (blocking) status check on main. Structured OWNER-ACTION blocks below. Bot-lane FLAG below stays informational until the manager picks it up.
notes: coordinator heartbeat, boot session cse_017yrng4qx2LcLNqKb5AGoe8 — stage (b) DONE record, owner-action blocks, bot-lane FLAG (carried verbatim), in-flight + staged queue, and routine/chain verbatim records below (this Project is this file's SOLE writer; overwritten whole, never appended).

## Stage (b) DISCORD OAUTH — DONE (PR #11, merged 2026-07-11T02:13Z)

- stdlib OAuth2 identify flow: /auth/login → CSRF state → /auth/callback →
  HMAC-signed HttpOnly cookie; /auth/logout; /api/me maps Discord id →
  miners[].suid.
- Degraded mode is the default (no env vars = sign-in off, read view intact).
- My-miner view in the frontend; prose in docs/auth.md.
- Verified on head 3131f87: substrate-gate ✓ + pytest ✓ (50 tests).

## ⚑ OWNER-ACTION 1 — switch sign-in on

WHAT: provision host env vars to switch sign-in on: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY.
WHERE: the host environment that runs the web server (wherever you launch server/ from), plus the Discord Developer Portal for the client id/secret and redirect URI.
HOW: set the four variables above in the server's environment; OAUTH_REDIRECT_URI must exactly match the redirect URI registered in the Discord app; WEB_SESSION_SIGNING_KEY is any long random secret you generate.
WHY-IT-MATTERS: until these exist, players cannot sign in — the site runs in degraded (read-only, anonymous) mode by design.
UNBLOCKS: the My-miner signed-in view goes live the moment the server restarts with the vars set.
VERIFIED-NEEDED: agent sessions have no access to the host environment or the Discord Developer Portal — only the owner can provision secrets; the code path was verified in degraded mode plus tests (50 passing on 3131f87).

## ⚑ OWNER-ACTION 2 — make pytest blocking

WHAT: make pytest blocking: add the pytest workflow as a required status check on main.
WHERE: Settings → Rules → Rulesets → main ruleset (already requires substrate-gate) → "Require status checks to pass".
HOW: add context exactly `pytest`.
WHY-IT-MATTERS: today a PR whose tests fail can still merge; substrate-gate is required but pytest is advisory.
UNBLOCKS: every future merge is test-gated with zero coordinator babysitting.
VERIFIED-NEEDED: coordinator's one ruleset-modification attempt was classifier-denied (recorded in the gate-audit history); ruleset edits are an owner-only surface. Proof once flipped: next PR's merged_at ≥ pytest check-run completed_at.

## ⚑ FLAG — superbot manager / bot lane (carry verbatim)

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

## IN FLIGHT

- Stage (c) WRITE CONTRACT v1 — TEST GUILD ONLY — dispatched
  2026-07-11T02:18Z to session cse_01J3QL7kEddgSu5zzGtGMAkN. Safety lines
  restated: proposals-only endpoint; every web action audited
  (mining_workflow emits no audit today — the handler layer must add it);
  never live prod; live cutover = owner flag (stage d).

## Staged queue

- [d] LIVE-PROD PREP — owner-flag-gated cutover checklist; never crossed early.

## Routine + chain (verbatim record)

Failsafe: trig_01K8xmAKYS5S2HLy1HPANM7j cron 20 */2 * * *. Chain link:
re-armed each wake as run_once triggers from worker seats — current
trig_01VeAj5ugXkVZ3mFk2VdfJNK fires 2026-07-11T02:19Z. send_later is
self-session-only on worker seats (no target param) — chain links are armed
as run_once triggers from worker seats.
