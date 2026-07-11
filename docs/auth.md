# Discord OAuth sign-in (stage b) — read personalization only

> **Status:** `reference`
>
> How the Discord OAuth2 sign-in works, how it is configured, and why it
> cannot mutate anything. Source of truth for behavior: `server/auth.py` +
> `server/app.py`; tests: `tests/test_auth.py`.

## What signing in gets you (and all it gets you)

A signed-in browser proves "I am Discord user `<id>`" so the frontend can
render **that user's miner** front and center. Nothing else changes: every
view stays read-only, public views work identically for signed-out visitors,
and the server still serves the committed snapshot verbatim.

## The flow (authorization code, `identify` scope only)

```
browser                     mineverse server                    discord.com
   |                              |                                  |
   |-- GET /auth/login ---------->|                                  |
   |<- 302 with signed `state` ---|  (HMAC-signed, 10 min expiry,    |
   |                              |   no server-side session store)  |
   |-- authorize (scope=identify) ------------------------------->   |
   |<- 302 to OAUTH_REDIRECT_URI?code=...&state=... ---------------  |
   |-- GET /auth/callback?code&state -->|                            |
   |                              |-- verify state (HMAC, expiry)    |
   |                              |-- POST /api/oauth2/token ------->|
   |                              |<- access_token ------------------|
   |                              |-- GET /api/users/@me ----------->|
   |                              |<- {id, ...} ---------------------|
   |<- 302 to / + session cookie -|  (HMAC-SHA256-signed, HttpOnly,  |
   |                              |   SameSite=Lax, 7-day expiry,    |
   |                              |   Secure when redirect is https) |
   |-- GET /api/me (cookie) ----->|                                  |
   |<- {signed_in, user_id, miner}|  (exact string match against     |
   |                              |   miners[].suid in the snapshot) |
```

- **State (CSRF)**: `/auth/login` mints an HMAC-signed token
  (`purpose=oauth-state`, random nonce, expiry); `/auth/callback` verifies
  it before touching the code. No server-side store — the signature is the
  state.
- **Session cookie** (`mineverse_session`): base64url JSON payload
  (`purpose=session`, `uid`, `iat`, `exp`) + base64url HMAC-SHA256 tag.
  Verification uses `hmac.compare_digest` (constant-time); expired,
  tampered, or malformed cookies are treated as signed-out — never an
  error page.
- **`GET /auth/logout`**: clears the cookie (`Max-Age=0`), redirects to `/`.
- **`GET /api/me`**: `{signed_in: false, auth_configured: ...}` without a
  valid cookie; with one, `{signed_in: true, user_id, miner}` where `miner`
  is the snapshot miner whose `suid` (a Discord user id, string on the
  wire) exactly equals the cookie's user id — or `null`, reported honestly.

## Configuration — host env vars ONLY (never the repo, never a file)

| Env var | Meaning |
| --- | --- |
| `DISCORD_OAUTH_CLIENT_ID` | Discord application client id |
| `DISCORD_OAUTH_CLIENT_SECRET` | Discord application client secret |
| `OAUTH_REDIRECT_URI` | The `/auth/callback` URL registered with Discord; an `https://` value also turns on the cookie `Secure` flag |
| `WEB_SESSION_SIGNING_KEY` | HMAC-SHA256 key signing the state + session cookie (any long random string; rotating it signs everyone out) |

No secret is ever committed or written to disk by this app — configuration
is read from the process environment at server start.

## Degraded mode (the default in CI and fresh clones)

With **any** of the four env vars absent the app runs exactly as before
stage b:

- All public snapshot views work (`/`, `/api/snapshot`).
- `GET /api/me` → `{"signed_in": false, "auth_configured": false}`.
- `GET /auth/login` and `/auth/callback` → honest
  `503 {"error": "sign-in not configured"}`.
- The frontend shows a disabled "sign-in not configured" button.

The whole test suite passes with no secrets present — CI never sees a
credential.

## Threat notes

- **State-changing operations are impossible by construction.** The server
  has no write paths (it never writes anything, anywhere), no database, no
  Postgres connection, and no bot token. A stolen or forged cookie could at
  most read what is already public plus the "my miner" framing of data the
  snapshot already exposes.
- **The cookie only proves identity for read personalization.** It carries
  a Discord user id and timestamps, signed — no access token, no secret,
  nothing replayable against Discord.
- **CSRF on the callback** is covered by the signed, expiring `state`;
  cookie theft via script is limited by `HttpOnly`; cross-site sending by
  `SameSite=Lax`; transport by `Secure` under an https redirect URI.
- **The Discord access token is never stored** — it lives for one
  `users/@me` call inside the callback and is discarded.
