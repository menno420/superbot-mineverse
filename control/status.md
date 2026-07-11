# superbot-mineverse · status
updated: 2026-07-11T01:46:00Z
phase: ORDER 000 done — walking skeleton merged to main; stage (a) READ CONTRACT v1 + backlog slice in flight
health: green
kit: v1.8.0 · check: red · engaged: no   # check red is the pre-existing born-red state: unfilled bootstrap interview slots / UNRENDERED banner; engaged flips to yes once slots render and live CI runs the gate (backlog slice dispatched to fill slots)
last-shipped: ORDER 000 stage-1 walking skeleton — PR #2 MERGED (squash, substrate-gate green, auto-merge) 2026-07-11T01:43Z; also PR #1 coordinator boot heartbeat merged
blockers: none
orders: acked= done=
⚑ needs-owner: none
notes: coordinator heartbeat, boot session cse_017yrng4qx2LcLNqKb5AGoe8 — boot record + audit correction + routine/chain verbatim records preserved below (this Project is this file's SOLE writer; overwritten whole, never appended).

## Boot record — 2026-07-11 (session cse_017yrng4qx2LcLNqKb5AGoe8)

BOOT RECORD: synced main @ d1d8c9f (substrate-kit v1.8.0 seed). Inbox: no orders.
Owner-actions: none. Oracle recon (menno420/superbot via public raw) complete: miner
state = mining_player_state per (suid, guild_id) — mining_inventory, vault +
vault_level, depth, position/discovery, equipment + gear_wear, energy, coins
(economy_service only), skills, structures, world_seed, loadouts; XP via
game_xp_service.award(). All mutations funnel through services/mining_workflow.py
single-transaction ops, enforced by AST ratchet test.

FOUNDING-PACKAGE CORRECTION (important): mining_workflow makes ZERO
emit_audit_action calls. Audit today = economy_audit_log rows on coin legs
(economy_service.debit/credit_in_txn) inside the txn; non-coin mutations
(inventory/depth/gear/vault items) have NO audit rows. Stage (c) write-contract
spec must define the audit emission it needs; will be ⚑-flagged to the Builder
lane when stage (c) opens.

## ORDER 000 — DONE

ORDER 000: dispatched 2026-07-11T01:30Z to build session
cse_01A7TmZczaLSEPfXdCWNXNLT. PR #2 MERGED (squash, substrate-gate green,
auto-merge) 2026-07-11T01:43Z. Skeleton live on main:
data/sample_snapshot.json using oracle mining_player_state field names, tiny
Python API, frontend miner cards / depth / leaderboard, pytest coverage.

## IN FLIGHT

- Stage (a) READ CONTRACT v1 — dispatched 2026-07-11T01:44Z to session
  cse_01LZx4itrFUJLbK6RcjmZTkt: docs/mining-data-contract.md +
  schemas/mining_snapshot.v1.schema.json + schema-gate CI + contract-conformant
  payload; will produce a FLAG block for the bot lane (emit the mining
  projection into the part-4d read relay).
- Never-idle backlog slice — dispatched to session cse_01X6ivpBRVQ2mEzb33dT2mFQ:
  fill bootstrap interview slots + README; strict-red banners.

## Routine + chain (verbatim record)

create_trigger {"name":"superbot-mineverse failsafe wake","cron_expression":"20 */2 * * *","persistent_session_id":"cse_017yrng4qx2LcLNqKb5AGoe8","prompt":"FAILSAFE WAKE (mining-browsergame, Q-0265): ..."}
-> trig_01K8xmAKYS5S2HLy1HPANM7j, enabled, next_run_at 2026-07-11T02:20:00Z,
CONFIRMED in list_triggers (note: server stored the arrows HTML-escaped as
"-&gt;"; semantics unaffected). Chain link: create_trigger run_once_at
2026-07-11T01:47:00Z -> trig_019hDoyZVnHxRojKRhi9xUQB (fired-or-firing 01:47Z),
re-armed each wake as run_once triggers from worker seats. send_later is
self-session-only on worker seats (no target param) — chain links are armed as
run_once triggers from worker seats.

## Staged queue

- [a] READ CONTRACT v1 — IN FLIGHT (see above).
- [b] DISCORD OAUTH — per-player read view; OAuth client id/secret + signing key
  = HOST env vars (⚑ exact names when it lands). QUEUED.
- [c] WRITE CONTRACT v1 — TEST GUILD ONLY; audited endpoint spec must spec the
  audit emission (mining_workflow currently makes zero emit_audit_action calls)
  + web action UI + mock shim; ⚑ real endpoint to Builder lane.
- [d] LIVE-PROD PREP — owner-flag-gated cutover checklist; owner flags, never
  crossed early.
