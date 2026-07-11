# superbot-mineverse · status
updated: 2026-07-11T04:27:00Z
phase: DEEPENING — micro-polish (PR #23) MERGED: read side now renders the ENTIRE v1 contract, the deepening well is dry; no in-flight lanes — all remaining work externally blocked (bot-lane FLAGs 1+2, owner env vars, pytest ruleset edit); loop cadence slows ~15→~60 min while blocked
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN; engaged = no unrendered banners + live CI gate (substrate-gate required context on main ruleset) + session loop engaged — all met
last-shipped: MICRO-POLISH MERGED — PR #23 2026-07-11T04:04Z: suid identity line, guild_id in the header, xp.game on the card face, additive-keys defensive tests; pytest 187→191 (+1 conformance skip), all green. MILESTONE: the read side now renders the ENTIRE v1 contract — every required miner field of mining_snapshot.v1 is painted somewhere in the web views; the deepening well is dry. Prior: PR #21 (deepening slice 2, full required-field coverage), #20 (heartbeat), #19 (conformance seam), #18 (deepening slice 1), #17 (heartbeat), #16 (stage d prep), #15, #13/#14 (stage c), #12, #11 (stage b), #10/#8/#7 (stage a), #9, #6, #5, #4, #3, #2, #1.
blockers: none
orders: acked=001 done=001
⚑ needs-owner: 2 items — (1) provision the six env vars to switch sign-in on (and, for test-guild write mode, the write-endpoint pair); (2) make pytest a required (blocking) status check on main. Structured OWNER-ACTION blocks below. Bot-lane FLAGs below stay informational until the manager picks them up.
notes: coordinator heartbeat, boot session cse_017yrng4qx2LcLNqKb5AGoe8 — HONEST STATE: no in-flight lanes; all remaining work is externally blocked: (1) Builder-lane FLAG 1 (READ relay projection) + FLAG 2 (WRITE endpoint) — specs on main; (2) owner env vars (six names) + pytest required-check ruleset edit; (3) audit-trail e2e + real-endpoint conformance run once (1)/(2) exist. LOOP CADENCE: no active orders; externally blocked on Builder-lane FLAGs + owner items; chain links ~60 min (a link is already armed for 05:16Z), failsafe cron every 2h unchanged; inbox checked each wake. Ladder line, both OWNER-ACTION blocks, and both bot-lane ⚑ FLAGs carried verbatim below (this Project is this file's SOLE writer; overwritten whole, never appended). Housekeeping this heartbeat: removed released claim control/claims/claude-micro-polish-identity-xp.md (rode PR #23; deletion rides this control-lane PR per pattern).

## ORDER 001 — DONE

ORDER 001 DONE — PR #27 merged 04:23Z (head 0c11372, 3/3 checks green):
card scaffold in bootstrap.py already emits the 📊 Model: line (marker in
substrate.config.json); family-level standing rule documented in
.sessions/README.md; executing session's committed card carries
"📊 Model: fable-5". Done-when satisfied. Follow-up idea (not ordered):
older cards carry drifted model spellings.

## Micro-polish — MERGED (PR #23 2026-07-11T04:04Z)

- suid identity line, guild_id in the header, xp.game on the card face,
  additive-keys defensive tests; pytest 187 → 191 plus 1 conformance skip,
  all green.
- MILESTONE: the read side now renders the ENTIRE v1 contract — with PR #21's
  full required-field coverage plus this slice's identity/xp paint, nothing
  in schemas/mining_snapshot.v1.schema.json is fetched-but-unpainted. The
  deepening well is dry.
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

- (none) — no in-flight lanes; every remaining backlog item is externally
  blocked on the bot-lane FLAGs and/or the OWNER-ACTION items above.

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

Failsafe: trig_01K8xmAKYS5S2HLy1HPANM7j cron 20 */2 * * * (unchanged, every
2h at :20).
Chain link: re-armed each wake as run_once triggers from worker seats —
re-armed this wake ~60 min out while externally blocked (id in coordinator
log); cadence returns to ~15 min when new orders or unblocked work appear;
send_later is self-session-only on worker seats (no target param).
