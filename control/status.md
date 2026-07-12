# superbot-mineverse · status
updated: 2026-07-11T23:51:34Z
phase: SECURITY SLICE IN FLIGHT — login-CSRF fix + runtime snapshot validation on branch security/oauth-csrf-snapshot-validation, shipped as PR #42 (READY, awaiting green + owner merge). Founding day was wrapped/archived (docs/retro/archive-ready-2026-07-11.md); this is a fresh security slice on top.

follow-up (2026-07-11T23:51Z): two reviewer-confirmed defects on PR #42 fixed as new commits on the same branch (CSRF fix untouched). (1) snapshot_validation `_check` now implements the size/length keywords (maxItems/minItems, maxLength/minLength, maxProperties/minProperties) AND fails loud on any unimplemented *validation* keyword (drift guard, explicit no-op annotation allow-list) — closes the maxItems runtime-vs-CI drift. (2) `/api/me` (`_serve_me`/`_find_miner`) now routes through the same validation → honest 503 as the read routes, no longer 500s on a non-object (`[]`) snapshot. Suite now 356 passed + 1 skipped (+7); `bootstrap check --strict` exit 0. Details in .sessions/2026-07-11-oauth-csrf-snapshot-validation.md (Follow-up section). PR #42 stays READY; auto-merge NOT armed.
flagship-stage: web read/write contract prepared through ladder (d) PREPARED; live-prod is owner-flag-gated. This PR hardens the sign-in path BEFORE the six OAuth/write secrets are provisioned.
health: green
kit: v1.8.0 · check: green   # python3 bootstrap.py check --strict → exit 0 with the completed session card in tree
last-shipped: PR #42 security/oauth-csrf-snapshot-validation — (1) OAuth login-CSRF binding: /auth/login sets an HttpOnly+SameSite=Lax(+Secure on https) per-browser cookie bound to the state, /auth/callback requires it and constant-time-compares before touching Discord (existing signing/TTL kept, stateless); (2) runtime snapshot validation at ingestion: stdlib-only schema-derived structural check refuses non-v1 snapshots with an honest 503 on /api/snapshot, /api/views, /api/action (jsonschema stays a dev/test-only, CI-authoritative gate). Suite 349 passed + 1 skipped (baseline 327+1; +22 tests).

## PR #42 — checks (as of this stamp)
- substrate-gate: SUCCESS (green) on head e4504f16.
- pytest (schema-gate.yml job): IN PROGRESS — expected green (349 passed + 1 skipped locally on the pinned dev deps).
- auto-merge-enabler: SKIPPED — this is a security/* branch, the enabler does not arm auto-merge for it; auto-merge is NOT armed and this session will not arm or self-merge it. Owner merges manually.
- Note: this heartbeat commit re-triggers schema-gate on the new head; the pytest context must go green before merge (pytest IS a required context on main — see below).

blockers: none agent-side. PR #42 is READY with substrate-gate green and pytest running; it needs the owner to merge on green. This PR GATES secret provisioning (below).

orders: acked=001,002 done=001,002

## ⚑ needs-owner — unchanged 6-env-secrets list, NOW GATED BY PR #42

⚑ MERGE-ORDER: merge PR #42 (this login-CSRF fix) BEFORE provisioning the secrets below, so sign-in never runs in production without the per-browser binding in place.

WHAT: provision host env vars: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY, MINING_WRITE_ENDPOINT, MINING_WRITE_SHARED_SECRET — the last two only for test-guild write mode.
WHERE: the host environment that runs the web server, plus the Discord Developer Portal for the client id/secret and redirect URI; MINING_WRITE_ENDPOINT/MINING_WRITE_SHARED_SECRET come from the bot lane once its write endpoint exists (FLAG 2 below).
HOW: set the variables in the server's environment; OAUTH_REDIRECT_URI must exactly match the redirect URI registered in the Discord app; WEB_SESSION_SIGNING_KEY is any long random secret you generate; MINING_WRITE_SHARED_SECRET must match the bot endpoint's HMAC key.
WHY-IT-MATTERS: until the OAuth four exist, players cannot sign in — the site runs in degraded (read-only, anonymous) mode by design; until the write pair exists, the action UI stays in TEST ECONOMY degraded mode with no live write path.
UNBLOCKS: the My-miner signed-in view goes live on server restart with the OAuth vars; test-guild write mode goes live once the write pair is set and the bot endpoint (FLAG 2) ships.
VERIFIED-NEEDED: agent sessions have no access to the host environment or the Discord Developer Portal — only the owner provisions secrets. No secret values are ever requested or handled by agents.

Also owner-side, informational: review/merge open PR #31 (owner's Codex security report); Builder-lane FLAGs 1+2 stay informational until the manager picks them up; stage-5 live-prod flag remains owner-only.

## pytest is a required status check on main (evidence for PR #42)

- .github/workflows/schema-gate.yml defines job `pytest` running `python3 -m pytest -q` on every PR + push to main.
- docs/current-state.md L46–48: both substrate-gate AND pytest are required status checks on main (pytest recently added to the ruleset).
- docs/current-state.md L88–89 + this file's history: pytest verified BLOCKING empirically on PRs #32–#35 (merged_at ≥ pytest completed_at).
- Direct branch-protection API was not readable from this session (GitHub App not connected for the org); citation is config + documentation + prior empirical enforcement, not a live ruleset read.

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
(Draft202012Validator, same as tests/test_schema_gate.py). NOTE: PR #42 now
also validates this payload at INGESTION in the web server (stdlib-only,
honest 503 on non-conformance) — a malformed relay is refused, not served.

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

## Externally pending (unchanged)

- Builder-lane FLAG 1 (READ relay projection) + FLAG 2 (WRITE endpoint) — specs above, on main.
- Owner env vars — the six names in ⚑ needs-owner (now gated behind PR #42).
- Stage-5 live-prod owner flag — untouched, owner-only, never agent-decided.
- PR #31 — the owner's own Codex security-report PR, open, owner-side.
- Once the real endpoint exists: audit-trail e2e verification (docs/live-prod-cutover.md) + conformance run of tests/test_actions.py via SHIM_CONFORMANCE_BASE_URL.

## Ladder + backlog

- Ladder: 0 ✓ · (a) ✓ · (b) ✓ + login-CSRF hardened (PR #42) · (c) ✓ web-side · (d) PREPARED ✓ — live-prod is OWNER-FLAG-GATED; test-guild read-write pending FLAG 1 + FLAG 2 + owner env vars.
- Groomed backlog parked on record: docs/ideas/founding-day-groomed-backlog-2026-07-11.md (8 items — nothing approved or in flight).
