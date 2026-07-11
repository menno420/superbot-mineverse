# superbot-mineverse · status
updated: 2026-07-11T19:11:00Z
phase: FUN PASS SHIPPED (owner-requested) — PRs #36 (cave visual theme) / #37 (fun layer) merged on green on top of the earlier same-day #32–#35 batch; one in-flight lane: fun mop-up slice dispatched 19:09Z; everything else externally blocked (bot-lane FLAGs 1+2, owner env vars)
health: green
kit: v1.8.0 · check: green · engaged: yes   # check --strict GREEN; engaged = no unrendered banners + live CI gate (substrate-gate + pytest both required contexts on main ruleset) + session loop engaged — all met
last-shipped: FUN PASS (owner-requested) 2026-07-11 — PR #36 cave visual theme: mine-shaft cross-section with pixel avatars + record flags, biome strata, ore rarity SVG icons, vault chest / energy lantern / durability bars, podium + count-up animation, all JS effects gated behind prefersReducedMotion. PR #37 fun layer: server-derived achievements in build_views under an additive key, Konami-code diamond rain, 10-click easter-egg toast, stale-snapshot 💤 idle state, console ASCII art, miner VS comparison view, cave-art HTML 404 page with JSON API behavior byte-identical. Test suite 242 → 314 passed + 1 conformance skip; strict check green. Earlier same day: PRs #32 (housekeeping) / #33 (a11y+responsive) / #34 (server robustness) / #35 (heartbeat) — pytest gate verified blocking on every one of these merges. Prior: #29 (self-review), #28, #27 (ORDER 001), #26, #23 (micro-polish — read side renders the ENTIRE v1 contract), #21, #20, #19, #18, #17, #16, #15, #13/#14, #12, #11, #10/#8/#7, #9, #6, #5, #4, #3, #2, #1.
blockers: none
orders: acked=001,002 done=001,002
⚑ needs-owner: 1 item — provision the six env vars to switch sign-in on (and, for test-guild write mode, the write-endpoint pair). Structured OWNER-ACTION block below. The pytest-required-check ask is RESOLVED/VERIFIED (owner did it 2026-07-11 — see the resolved block below). Bot-lane FLAGs below stay informational until the manager picks them up.
notes: coordinator heartbeat, session cse_017yrng4qx2LcLNqKb5AGoe8 — HONEST STATE: one in-flight lane (fun mop-up slice, see IN FLIGHT); all other remaining work is externally blocked: (1) Builder-lane FLAG 1 (READ relay projection) + FLAG 2 (WRITE endpoint) — specs on main; (2) owner env vars (six names); (3) stage-5 live-prod owner flag; (4) audit-trail e2e + real-endpoint conformance run once (1)/(2) exist. LOOP CADENCE: active pace while the mop-up lane runs — chain link ~19:15Z (trigger ids recorded in the coordinator log), failsafe cron every 2h unchanged; inbox checked each wake. OWNER-ACTION 1 and both bot-lane ⚑ FLAGs carried verbatim below (this Project is this file's SOLE writer; overwritten whole, never appended). Housekeeping this heartbeat: verified control/claims/ contains only README.md — the fun-lane claims were already retired; no deletions needed. ORDER 002 self-review (window 2026-07-10 20:00Z → 2026-07-11 10:20Z) lives in git history of this file (PR #29 / commit 2f2d33a) — summary: 24 PRs merged on green in ~3h, one classifier denial recorded+complied, one false alarm corrected, gitignore regression fixed in PR #5, nothing shipped red.

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

- Fun mop-up slice — dispatched 2026-07-11T19:09Z, worker session
  cse_018MdQSKkNJSCinYbwL7Fw9W. Scope: sample-data enrichment so some miners
  actually earn badges, PNG share card, Konami-code prefix-input fix, small
  JS helper extractions.

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
current link fires ~19:15Z at active pace (trigger ids recorded in the
coordinator log); cadence returns to blocked ~60 min if the mop-up lane
closes with nothing unblocked; send_later is self-session-only on worker
seats (no target param).
