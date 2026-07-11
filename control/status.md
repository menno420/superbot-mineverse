# superbot-mineverse · status
updated: 2026-07-11T02:01:36Z
phase: stage (a) READ CONTRACT v1 merged (PR #7); stage (b) DISCORD OAUTH dispatched; stage (a) lane on close-out + pytest-enforcement follow-up
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN (0 findings) since PR #6 (slots rendered, UNRENDERED banner gone); engaged = no unrendered banners + live CI gate (substrate-gate required context on main ruleset) + session loop engaged — all met
last-shipped: Stage (a) READ CONTRACT v1 — PR #7 MERGED 2026-07-11T01:57Z (substrate-gate ✓ + pytest workflow ✓ on head, 25 tests). Prior: PR #6 (slots+README, strict RED→GREEN), PR #5 (gitignore fix), #4 (heartbeat), #3 (close-out), #2 (ORDER 000 skeleton), #1 (heartbeat).
blockers: none
orders: acked= done=
⚑ needs-owner: none blocking (bot-lane FLAG below is informational until the manager picks it up)
notes: coordinator heartbeat, boot session cse_017yrng4qx2LcLNqKb5AGoe8 — stage (a) DONE record, bot-lane FLAG, gate-audit note, in-flight + staged queue, and routine/chain verbatim records below (this Project is this file's SOLE writer; overwritten whole, never appended).

## Stage (a) READ CONTRACT v1 — DONE (PR #7, merged 2026-07-11T01:57Z)

- docs/mining-data-contract.md + schemas/mining_snapshot.v1.schema.json —
  single source of truth; tests derive REQUIRED_MINER_FIELDS from the schema.
- pytest schema gate (tests/test_schema_gate.py, Draft202012Validator).
- Enveloped sample payload: schema_version "1", generated_at, guild_id string,
  miners[]; suid is a STRING — snowflakes exceed double precision.
- Frontend shows contract version + generated_at timestamp.

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

## Gate-audit note

Earlier "substrate-gate advisory" suspicion DISPROVED — main ruleset requires
context ["substrate-gate"] (read via enable-auto-merge job of PR #5). Open
enforcement item: pytest workflow is NOT a required context; repo-side fix
under investigation by the stage (a) lane, else owner ask follows.
Coordinator's one ruleset-modification attempt was classifier-denied
(recorded; moot).

## IN FLIGHT

- Stage (b) DISCORD OAUTH — dispatched 2026-07-11T02:00Z to session
  cse_013ferJBGveGH6u1edbBicFB: per-player read view; env vars
  DISCORD_OAUTH_CLIENT_ID / DISCORD_OAUTH_CLIENT_SECRET / OAUTH_REDIRECT_URI /
  WEB_SESSION_SIGNING_KEY — owner ⚑ when it lands; degraded mode required.
- Stage (a) lane — close-out + pytest-enforcement follow-up (make pytest a
  required context, or produce the owner ask).

## Staged queue

- [c] WRITE CONTRACT v1 — TEST GUILD ONLY; must spec the audit emission
  (mining_workflow makes zero emit_audit_action calls today).
- [d] LIVE-PROD PREP — owner-flag-gated cutover checklist; never crossed early.

## Routine + chain (verbatim record)

Failsafe: trig_01K8xmAKYS5S2HLy1HPANM7j cron 20 */2 * * *, next run
2026-07-11T02:20:00Z. Chain link: trig_01A9Zh2vh47V8fXwPtKYMSpk fires
2026-07-11T02:02:57Z, re-armed each wake as run_once triggers from worker
seats. send_later is self-session-only on worker seats (no target param) —
chain links are armed as run_once triggers from worker seats.
