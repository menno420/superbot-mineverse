# superbot-mineverse · status
updated: 2026-07-11T01:38:00Z
phase: coordinator boot — main synced @ d1d8c9f, oracle recon done, ORDER 000 walking skeleton dispatched and in flight
health: green
kit: v1.8.0 · check: red · engaged: no   # check red is the pre-existing born-red state: unfilled bootstrap interview slots / UNRENDERED banner; engaged flips to yes once slots render and live CI runs the gate
last-shipped: none
blockers: none
orders: acked= done=
⚑ needs-owner: none
notes: coordinator heartbeat, boot session cse_017yrng4qx2LcLNqKb5AGoe8 — full boot record below (this Project is this file's SOLE writer; overwritten whole, never appended).

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

ORDER 000: dispatched 2026-07-11T01:30Z to build session
cse_01A7TmZczaLSEPfXdCWNXNLT (read-only walking skeleton: committed sample payload
+ tiny Python backend + miner card/depth/leaderboard frontend, READY PR +
auto-merge on claude/* branch). PR: pending at heartbeat time.

## Routine + chain (verbatim record)

create_trigger {"name":"superbot-mineverse failsafe wake","cron_expression":"20 */2 * * *","persistent_session_id":"cse_017yrng4qx2LcLNqKb5AGoe8","prompt":"FAILSAFE WAKE (mining-browsergame, Q-0265): ..."}
-> trig_01K8xmAKYS5S2HLy1HPANM7j, enabled, next_run_at 2026-07-11T02:20:00Z,
CONFIRMED in list_triggers (note: server stored the arrows HTML-escaped as
"-&gt;"; semantics unaffected). Chain link: create_trigger run_once_at
2026-07-11T01:47:00Z -> trig_019hDoyZVnHxRojKRhi9xUQB, confirmed. send_later is
self-session-only on worker seats (no target param) — chain links are armed as
run_once triggers from worker seats.

## Staged queue

- [0] ORDER 000 walking skeleton — IN FLIGHT.
- [a] READ CONTRACT v1 — docs/mining-data-contract.md + versioned JSON schema +
  schema-gate CI; flag bot lane via manager to emit the mining projection into
  the part-4d read relay.
- [b] DISCORD OAUTH — per-player read view; OAuth client id/secret + signing key
  = HOST env vars (⚑ exact names when it lands).
- [c] WRITE CONTRACT v1 — TEST GUILD ONLY; audited endpoint spec (must address
  the audit gap above) + web action UI + mock shim; ⚑ real endpoint to Builder
  lane.
- [d] LIVE-PROD PREP — owner-flag-gated cutover checklist; owner flags, never
  crossed early.

Never-idle backlog: fill bootstrap interview slots (primary_language=Python 3.10,
verify_command, project name, adoption pace=guided) + render --live; write
README.md.
