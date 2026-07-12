# superbot-mineverse · status
updated: 2026-07-12T21:03:00Z
phase: ORDER 003 closeout — merge verification, kit re-render check, heartbeat + owner secrets ask (branch claude/order-003-closeout). COORDINATOR-DELEGATED heartbeat write — the coordinator seat authorized this status overwrite.
health: green
kit: v1.8.0
last-shipped: #45 — auth: real User-Agent on Discord requests (Cloudflare 403s urllib's default); merged 2026-07-12T18:22:10Z.
blockers: none
orders: acked=001,002,003 done=001,002,003
⚑ needs-owner: provision the six host env secrets (block below) — the SECURITY BEFORE SECRETS gate is CLEAR (#42 in main).
notes: .claude/CLAUDE.md verified current — `python3 bootstrap.py render` output is byte-identical to the planted file (no hand-edit, no diff). Work claim: control/claims/claude-order-003-closeout.md (deleted at session close).

## Truth-stamp (API-verified 2026-07-12T20:56Z)

- PR #42 (security: OAuth login-CSRF binding + snapshot validation at ingestion) MERGED 2026-07-12T13:54:21Z, merge commit 3591c77; payload confirmed in main (server/auth.py binding, server/snapshot_validation.py, server/app.py wiring, +22 tests).
- PR #44 (deploy: Dockerfile + HOST env binding, Railway) MERGED 2026-07-12T16:49:58Z, merge commit ac312e8.
- PR #45 (auth: real User-Agent on Discord requests) MERGED 2026-07-12T18:22:10Z, merge commit e6d4ac7.
- PR #31 (Codex pre-provisioning security report) MERGED 2026-07-12T19:52:53Z, merge commit 52fe2ca; docs/pre-provisioning-security-report-2026-07-11.md in main.
- Open PRs at session boot: ZERO (API list, 2026-07-12T20:56Z).
- Local suite on main @ 52fe2ca: 359 passed, 1 skipped; `python3 bootstrap.py check --strict` → all checks passed.

## ⚑ OWNER-ACTION — provision the six host secrets (gate cleared by #42)

WHAT: set the six environment secrets on the web host so sign-in and (later) test-guild writes can leave degraded mode: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY, MINING_WRITE_ENDPOINT, MINING_WRITE_SHARED_SECRET. Names only — values stay owner-side, never in this repo.
WHERE: Railway dashboard → project `superbot-mineverse` → service `web` → Variables tab (the live host since #44); the client id/secret and redirect URI come from the Discord Developer Portal → your app → OAuth2.
HOW: paste-ready, names only — fill each value yourself:
  - Railway UI: Variables → New Variable → name `DISCORD_OAUTH_CLIENT_ID` (repeat for `DISCORD_OAUTH_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`, `WEB_SESSION_SIGNING_KEY`, `MINING_WRITE_ENDPOINT`, `MINING_WRITE_SHARED_SECRET`) → Deploy.
  - Or Railway CLI: `railway variables --set "WEB_SESSION_SIGNING_KEY=<value>"` (one per name).
  - Note: per PR #44/#45, DISCORD_OAUTH_CLIENT_ID, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY (and per #45's live evidence the client secret) were already provisioned on Railway during the owner-live session — the outstanding pair is MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET, which additionally waits on the bot lane's write endpoint (FLAG 2).
WHY-IT-MATTERS: until the OAuth four are set players cannot sign in (site runs read-only anonymous by design); until the write pair is set the action UI stays in TEST ECONOMY degraded mode.
UNBLOCKS: signed-in My-miner view on next deploy; test-guild write mode once the bot write endpoint (FLAG 2) exists and the write pair is set.
VERIFIED-NEEDED: agent sessions have no access to the Railway host environment or the Discord Developer Portal (docs/CAPABILITIES.md); only the owner provisions secrets. The ordering gate is now satisfied: #42 (login-CSRF binding) merged 2026-07-12T13:54:21Z, so sign-in never runs unbound.
RISK: OAUTH_REDIRECT_URI must exactly match the URI registered in the Discord app or every callback 400s; MINING_WRITE_SHARED_SECRET must match the bot endpoint's HMAC key or all writes are refused; never paste secret values into any repo file or PR.

## next-2-tasks baton

1. After the write pair (MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET) and the bot-lane WRITE endpoint (FLAG 2) exist: run the conformance suite against the real endpoint (tests/test_actions.py via SHIM_CONFORMANCE_BASE_URL) + the audit-trail e2e per docs/live-prod-cutover.md.
2. Verify live sign-in end-to-end on the Railway host post-#45 (UA fix) and record the outcome in docs/current-state.md; if green, close the loop on the bot-lane READ relay (FLAG 1) so real snapshots flow through the #42 ingestion validation.

## Externally pending (pointers, unchanged)

- Bot-lane FLAG 1 (READ relay) + FLAG 2 (WRITE endpoint) — full verbatim specs preserved at control/status.md@52fe2ca (git history) and summarized in docs/current-state.md § Externally pending.
- Stage-(d) live-prod flag — owner-only, via a control/inbox.md ORDER.
- Groomed backlog: docs/ideas/founding-day-groomed-backlog-2026-07-11.md.
