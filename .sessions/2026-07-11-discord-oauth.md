# Session 2026-07-11 — stage (b) Discord OAuth sign-in

> **Status:** `complete`

## Plan

Execute stage (b) DISCORD OAUTH (coordinator-assigned): stdlib-only Discord
OAuth2 authorization-code flow, `identify` scope only — `server/auth.py`
(HMAC-signed CSRF state + session cookie, constant-time verification,
urllib-based token exchange / users/@me) + routes in `server/app.py`
(`/auth/login`, `/auth/callback`, `/auth/logout`, `GET /api/me` mapping the
cookie's Discord user id to `miners[].suid` by exact string match). Config
via HOST env vars ONLY (`DISCORD_OAUTH_CLIENT_ID`,
`DISCORD_OAUTH_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`,
`WEB_SESSION_SIGNING_KEY`); with any absent the app runs DEGRADED — all
public views unchanged, `/api/me` says `auth_configured: false`,
`/auth/login` answers an honest 503, frontend shows a disabled
"sign-in not configured" button, full test suite green with zero secrets.
Frontend: "My miner" section (reuses the miner-card renderer) + sign-in/out
controls, vanilla JS, no build step. Tests: monkeypatched Discord calls
(no network ever) covering the full callback flow, state CSRF, cookie
sign/verify/tamper/expiry, degraded mode, and /api/me miner mapping —
keeping all 25 existing tests green. Docs: README auth section +
`docs/auth.md` (flow, env vars, degraded mode, threat notes).

Constraints honored: no new dependencies (stdlib `hmac`/`hashlib`/
`urllib`/`http.cookies`); no secret committed or written to any file;
`control/status.md` / `control/inbox.md` / `substrate-gate.yml` untouched.
Work claim: `control/claims/claude-discord-oauth.md`.

## Close-out

- Shipped `server/auth.py`: one signed-token format for CSRF state and
  session cookie (`base64url(json)+"."+base64url(hmac_sha256)`), payloads
  carry `purpose`/`exp`, verification via `hmac.compare_digest`, expired/
  tampered/malformed tokens reject to `None` — never an exception path.
- Routes live in `server/app.py`: login 302s to Discord with a signed
  state; callback verifies state BEFORE touching the code, exchanges it,
  fetches `users/@me`, sets `mineverse_session` (HttpOnly, SameSite=Lax,
  Max-Age 7d, Secure iff `OAUTH_REDIRECT_URI` is https), redirects `/`;
  logout clears; `/api/me` returns `{signed_in, auth_configured, user_id,
  miner|null}` with exact-string suid lookup against the snapshot.
- Degraded mode verified by tests: unconfigured server serves snapshot +
  frontend unchanged; auth endpoints honest (503 / `auth_configured:
  false`).
- Frontend: `#my-miner-section` renders the signed-in user's miner via the
  existing `renderMinerCard`; honest "no miner found in this snapshot"
  when the suid has no match; auth controls swap between Sign in with
  Discord / Sign out / disabled "sign-in not configured".
- verify: `python3 -m pytest -q` → 50 passed (25 pre-existing + 25 new in
  `tests/test_auth.py`, no network, no secrets). `python3 bootstrap.py
  check --strict` → all checks passed.
- Guard recipe (deferred): if a real staging Discord app is ever wired,
  add one opt-in smoke test hitting `auth.exchange_code` behind an env
  flag (`pytest -k live_discord`, skipped by default) — the seams to keep
  stable are `auth.exchange_code(config, code)` and
  `auth.fetch_discord_user(access_token)`, the exact two functions the
  suite monkeypatches.

## 💡 Session idea

`/api/me` re-reads and re-parses the whole snapshot on every call; when the
real relay lands (bigger snapshots, real traffic), an mtime-keyed cache in
the handler would keep the read path O(1) per request — worth pairing with
the staleness-indicator test idea from the previous card.

## ⟲ Previous-session review

The stage-(a) card's contract discipline paid off directly: `suid` being a
string-on-the-wire snowflake (IEEE-754 note in the contract) made the
Discord-user-id ↔ miner mapping an exact string compare with zero
coercion bugs. Its deferred idea (executable staleness test) remains open —
carried forward rather than silently dropped.

- **📊 Model:** fable-5 · standard effort · task-class: auth-flow + degraded-mode hardening (build)
