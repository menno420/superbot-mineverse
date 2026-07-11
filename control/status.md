# superbot-mineverse · status
updated: 2026-07-11T19:45:00Z
phase: WRAPPED / ARCHIVED — founding day closed out by owner order; coordinator chat archived; coordinator Routines disarmed; full close-out in docs/retro/archive-ready-2026-07-11.md; everything remaining is externally blocked (Builder-lane FLAGs 1+2, owner env vars, stage-5 owner flag)
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN; engaged = no unrendered banners + live CI gate (substrate-gate + pytest both required contexts on main ruleset) + session loop engaged — all met
last-shipped: wrap-up/archive-prep PR 2026-07-11 — founding-day retro (docs/retro/2026-07-11-founding-day-retro.md), archive-ready note (docs/retro/archive-ready-2026-07-11.md), 6 CAPABILITIES append-log findings, current-state refresh through PR #40, groomed backlog parked (docs/ideas/founding-day-groomed-backlog-2026-07-11.md), coordinator Routines disarmed. Day ledger: PRs #1–#40, 39 merged on green, 1 open (#31 — the OWNER's Codex security-report PR, owner-side); suite 327 passed + 1 conditional skip; strict check green.
blockers: none agent-side — all remaining work externally blocked (see ⚑ and the FLAGs below)
orders: acked=001,002 done=001,002
⚑ needs-owner: 1 item — provision the six env vars to switch sign-in on (and, for test-guild write mode, the write-endpoint pair). Structured OWNER-ACTION block below. Also owner-side, informational: review/merge your own open PR #31 (Codex security report); Builder-lane FLAGs 1+2 below stay informational until the manager picks them up; stage-5 live-prod flag remains owner-only.
notes: FINAL heartbeat of the founding-day coordinator (session cse_017yrng4qx2LcLNqKb5AGoe8 — chat archived after this). Resume path for any fresh session: README → docs/current-state.md → this file (+ control/inbox.md for new orders) → docs/retro/. ROUTINES DISARMED 2026-07-11T19:39Z: failsafe cron trig_01K8xmAKYS5S2HLy1HPANM7j deleted (tool output verbatim: `deleted trigger trig_01K8xmAKYS5S2HLy1HPANM7j`); zero pending chain-link run_once triggers remained (all ended_reason=run_once_fired) — nothing will wake the archived coordinator. The ORDER 002 self-review substance now lives in docs/retro/2026-07-11-founding-day-retro.md (full original text: commit 4be012e, PR #30's squash of this file — the pointer previously carried here named PR #29/2f2d33a, which is the inbox append, corrected in the retro). Groomed backlog parked on record in docs/ideas/founding-day-groomed-backlog-2026-07-11.md — nothing in it approved or in flight. control/claims/ contains only its README.

## ⚑ OWNER-ACTION 1 — switch sign-in on (and test-guild write mode)

WHAT: provision host env vars: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY, MINING_WRITE_ENDPOINT, MINING_WRITE_SHARED_SECRET — the last two only for test-guild write mode.
WHERE: the host environment that runs the web server (wherever you launch server/ from), plus the Discord Developer Portal for the client id/secret and redirect URI; MINING_WRITE_ENDPOINT/MINING_WRITE_SHARED_SECRET come from the bot lane once its write endpoint exists (FLAG 2 below).
HOW: set the variables above in the server's environment; OAUTH_REDIRECT_URI must exactly match the redirect URI registered in the Discord app; WEB_SESSION_SIGNING_KEY is any long random secret you generate; MINING_WRITE_SHARED_SECRET must match the bot endpoint's HMAC key.
WHY-IT-MATTERS: until the OAuth four exist, players cannot sign in — the site runs in degraded (read-only, anonymous) mode by design; until the write pair exists, the action UI stays in TEST ECONOMY degraded mode with no live write path.
UNBLOCKS: the My-miner signed-in view goes live on server restart with the OAuth vars; test-guild write mode goes live once the write pair is set and the bot endpoint (FLAG 2) ships.
VERIFIED-NEEDED: agent sessions have no access to the host environment or the Discord Developer Portal — only the owner can provision secrets; code paths verified in degraded mode plus tests (full suite passes with zero env vars).

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

- (none) — the founding day is wrapped; the coordinator chat is archived
  and its Routines are disarmed. Every remaining item is externally
  blocked on the bot-lane FLAGs and/or the OWNER-ACTION above.

## Externally pending (unchanged)

- Builder-lane FLAG 1 (READ relay projection) + FLAG 2 (WRITE endpoint) —
  specs above, on main.
- Owner env vars — the six names in OWNER-ACTION 1.
- Stage-5 live-prod owner flag — untouched, owner-only, never agent-decided.
- PR #31 — the owner's own Codex security-report PR, open, owner-side.
- Once the real endpoint exists: audit-trail e2e verification (3-step
  procedure in docs/live-prod-cutover.md) + conformance run of
  tests/test_actions.py via SHIM_CONFORMANCE_BASE_URL.

## Ladder + backlog

- Ladder: 0 ✓ · (a) ✓ · (b) ✓ · (c) ✓ web-side · (d) PREPARED ✓ — live-prod
  is OWNER-FLAG-GATED, never agent-decided; test-guild read-write pending
  FLAG 1 + FLAG 2 + owner env vars.
- Groomed backlog parked on record:
  docs/ideas/founding-day-groomed-backlog-2026-07-11.md (8 items — nothing
  approved or in flight).

## Routine + chain (verbatim record)

DISARMED 2026-07-11T19:39Z by the wrap-up session:
- Failsafe cron trig_01K8xmAKYS5S2HLy1HPANM7j ("superbot-mineverse
  failsafe wake", 20 */2 * * *) — delete_trigger output verbatim:
  `deleted trigger trig_01K8xmAKYS5S2HLy1HPANM7j`.
- Pending "superbot-mineverse chain link" run_once triggers bound to
  session_017yrng4qx2LcLNqKb5AGoe8: none existed (all
  ended_reason=run_once_fired; newest trig_016avdSjADLLCyPMLsn6uQeX fired
  19:31Z). No Routine will wake the archived coordinator.
