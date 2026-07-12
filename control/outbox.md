# superbot-mineverse · outbox

> Lane→manager asks. **One writer: this lane** — append-only; the manager
> consumes entries on its sweep and never edits this file. (Planted
> 2026-07-12 by the ORDER 003 closeout session; no prior outbox existed.)

## 2026-07-12T21:05Z · lane→manager · ⚑ OWNER-ACTION — provision the six host secrets (gate cleared by #42)

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
