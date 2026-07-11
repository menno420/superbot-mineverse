# superbot-mineverse · status
updated: 2026-07-11T18:21:00Z
phase: POLISH + ROBUSTNESS SHIPPED — PRs #32 (housekeeping) / #33 (a11y+responsive) / #34 (server robustness) all merged on green; pytest is now a VERIFIED-BLOCKING required check on main (owner flipped it 2026-07-11); no in-flight lanes — remaining work externally blocked (bot-lane FLAGs 1+2, owner env vars); loop stays at blocked cadence ~60 min
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN; engaged = no unrendered banners + live CI gate (substrate-gate + pytest both required contexts on main ruleset) + session loop engaged — all met
last-shipped: THREE-PR BATCH 2026-07-11 — PR #32 housekeeping: 10 session cards normalized to family-level model names + docs/current-state.md rewritten to match reality. PR #33 a11y/responsive: ARIA tab pattern, landmarks, table captions/scope, reduced-motion support, narrow-viewport reflow, +15 tests. PR #34 server robustness: utf-8 charsets on every Content-Type, sha256 ETag/304 conditional caching on /api/snapshot + /api/views, honest 405 (with Allow) and 404 responses, malformed-snapshot 500 guard, +36 tests. Suite now 242 passed + 1 conformance skip; strict check green. Prior: #29 (self-review), #28, #27 (ORDER 001), #26, #23 (micro-polish — read side renders the ENTIRE v1 contract), #21, #20, #19, #18, #17, #16, #15, #13/#14, #12, #11, #10/#8/#7, #9, #6, #5, #4, #3, #2, #1.
blockers: none
orders: acked=001,002 done=001,002
⚑ needs-owner: 1 item — provision the six env vars to switch sign-in on (and, for test-guild write mode, the write-endpoint pair). Structured OWNER-ACTION block below. The pytest-required-check ask is RESOLVED/VERIFIED (owner did it 2026-07-11 — see the resolved block below). Bot-lane FLAGs below stay informational until the manager picks them up.
notes: coordinator heartbeat, session cse_017yrng4qx2LcLNqKb5AGoe8 — HONEST STATE: no in-flight lanes; all remaining work is externally blocked: (1) Builder-lane FLAG 1 (READ relay projection) + FLAG 2 (WRITE endpoint) — specs on main; (2) owner env vars (six names); (3) stage-5 live-prod owner flag; (4) audit-trail e2e + real-endpoint conformance run once (1)/(2) exist. LOOP CADENCE: blocked pace — chain links ~60 min (current link fires 18:27Z), failsafe cron every 2h unchanged; inbox checked each wake. OWNER-ACTION 1 and both bot-lane ⚑ FLAGs carried verbatim below (this Project is this file's SOLE writer; overwritten whole, never appended). Housekeeping this heartbeat: removed released claims control/claims/claude-web-a11y-responsive.md (rode PR #33) and control/claims/claude-server-robustness.md (rode PR #34); deletions ride this control-lane PR per pattern. ORDER 002 self-review (window 2026-07-10 20:00Z → 2026-07-11 10:20Z) lives in git history of this file (PR #29 / commit 2f2d33a) — summary: 24 PRs merged on green in ~3h, one classifier denial recorded+complied, one false alarm corrected, gitignore regression fixed in PR #5, nothing shipped red.

## PYTEST GATE — RESOLVED/VERIFIED 2026-07-11 (was OWNER-ACTION 2)

RESOLVED: the owner made pytest a required (blocking) status check on the
main ruleset on 2026-07-11. VERIFIED with merge-timing evidence — merges now
wait for pytest: PR #32 merged 2s AFTER its pytest check-run completed;
PR #33 merged 2s after; PR #34 merged 3s after. (Contrast the pre-fix gap:
PR #16 merged 28s BEFORE pytest finished.) Every future merge is test-gated
with zero coordinator babysitting. Original ask preserved for the record:
WHAT: make pytest blocking: add the pytest workflow as a required status check on main. — DONE by owner 2026-07-11.
WHERE: Settings → Rules → Rulesets → main ruleset → "Require status checks to pass" (context `pytest`). — DONE.
HOW: add context exactly `pytest`. — DONE.
WHY-IT-MATTERS: previously a PR whose tests fail could still merge; now it cannot.
UNBLOCKS: unblocked — every merge is test-gated (evidence above).
VERIFIED-NEEDED: verified done — PRs #32/#33/#34 each merged only seconds after pytest completed (2s/2s/3s), never before.

## ⚑ OWNER-ACTION 1 — switch sign-in on (and test-guild write mode)

WHAT: provision host env vars: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY, MINING_WRITE_ENDPOINT, MINING_WRITE_SHARED_SECRET — the last two only for test-guild write mode.
WHERE: the host environment that runs the web server (wherever you launch server/ from), plus the Discord Developer Portal for the client id/secret and redirect URI; MINING_WRITE_ENDPOINT/MINING_WRITE_SHARED_SECRET come from the bot lane once its write endpoint exists (FLAG 2 below).
HOW: set the variables above in the server's environment; OAUTH_REDIRECT_URI must exactly match the redirect URI registered in the Discord app; WEB_SESSION_SIGNING_KEY is any long random secret you generate; MINING_WRITE_SHARED_SECRET must match the bot endpoint's HMAC key.
WHY-IT-MATTERS: until the OAuth four exist, players cannot sign in — the site runs in degraded (read-only, anonymous) mode by design; until the write pair exists, the action UI stays in TEST ECONOMY degraded mode with no live write path.
UNBLOCKS: the My-miner signed-in view goes live on server restart with the OAuth vars; test-guild write mode goes live once the write pair is set and the bot endpoint (FLAG 2) ships.
VERIFIED-NEEDED: agent sessions have no access to the host environment or the Discord Developer Portal — only the owner can provision secrets; code paths verified in degraded mode plus tests (130 passing with zero env vars).

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
  blocked on the bot-lane FLAGs and/or the owner items above.

## Externally pending (unchanged)

- Builder-lane FLAG 1 (READ relay projection) + FLAG 2 (WRITE endpoint) —
  specs above, on main.
- Owner env vars — the six names in OWNER-ACTION 1.
- Stage-5 live-prod owner flag — untouched, owner-only, never agent-decided.
- Once the real endpoint exists: audit-trail e2e verification (3-step
  procedure in docs/live-prod-cutover.md) + conformance run of
  tests/test_actions.py via SHIM_CONFORMANCE_BASE_URL.

## Ladder + deepening backlog

- Ladder: 0 ✓ · (a) ✓ · (b) ✓ · (c) ✓ web-side · (d) PREPARED ✓ — live-prod
  is OWNER-FLAG-GATED, never agent-decided; test-guild read-write pending
  FLAG 1 + FLAG 2 + owner env vars.
- Backlog (never-idle): audit-trail end-to-end verification and the
  real-endpoint conformance run (both wait on the Builder lane); more
  contract fields, views, and tests as they surface.

## Routine + chain (verbatim record)

Failsafe: trig_01K8xmAKYS5S2HLy1HPANM7j cron 20 */2 * * * (unchanged, every
2h at :20).
Chain link: re-armed each wake as run_once triggers from worker seats —
current link fires 18:27Z (trigger ids recorded in the coordinator log);
cadence returns to ~15 min when new orders or unblocked work appear;
send_later is self-session-only on worker seats (no target param).
