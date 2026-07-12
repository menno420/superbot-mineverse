# Pre-provisioning security report — dormant OAuth + write path

> **Status:** `historical`

> **2026-07-12 update:** this is the point-in-time Codex audit as written on
> 2026-07-11 (pre-provisioning). Both findings below were since remediated on
> `main`: **PR #42** bound the OAuth `state` to the initiating browser
> (login-CSRF fix, Finding 1) and added runtime snapshot validation against
> `schemas/mining_snapshot.v1.schema.json` at ingestion (Finding 2); **PR #45**
> followed up on the live sign-in path (real User-Agent on Discord requests).
> Kept for the record — the findings are no longer open.

Date: 2026-07-11
Scope: `server/app.py`, `server/auth.py`, `server/actions.py`, `server/views.py`, `web/app.js`, and security-relevant tests.

This report audits the security-sensitive surfaces before the owner provisions real Discord OAuth and write-endpoint secrets. The web app currently runs in degraded/read-only mode when those secrets are absent.

## Executive summary

Do not provision production secrets until the OAuth state-binding finding below is fixed or explicitly accepted. The app otherwise fails closed in zero-secret mode, session cookies use HMAC-SHA256 with timing-safe verification, the write path derives identity server-side, and snapshot strings do not currently reach HTML injection sinks.

## Findings

### Finding 1 — OAuth `state` is signed but not bound to the initiating browser/session

- **Severity:** Medium
- **Surface:** OAuth flow
- **Files/lines:** `server/auth.py` (`make_state`, `verify_state`); `server/app.py` (`_serve_login`, `_serve_callback`)
- **Status:** Open

`/auth/login` creates a signed state token and redirects to Discord, but the server does not also set a browser-bound state cookie or store the nonce server-side. The state token contains a purpose, random nonce, and expiry, and callback validation checks only the signature/expiry/purpose.

An arbitrary internet user can request a valid state token, authorize their own Discord account, and cause a victim browser to load a callback URL carrying the attacker-controlled valid state and authorization code. If the Discord code is still valid and unconsumed, the victim can be logged into Mineverse as the attacker. Today this is read-personalization confusion; once writes are enabled, any in-app action the victim clicks would be attributed to the attacker’s Discord user because `suid` is derived from the session cookie.

Recommended remediation: bind OAuth state to the initiating browser, for example with an HttpOnly state cookie checked on callback, a server-side nonce store, or another double-submit pattern. Treat the current state token as a bearer token, not complete CSRF protection.

### Finding 2 — Runtime snapshot ingestion does not enforce the JSON Schema before `/api/views`

- **Severity:** Low for XSS; Medium for robustness if future snapshots are bot-produced and not fully trusted
- **Surface:** Snapshot ingestion
- **Files/lines:** `server/app.py` (`_serve_views`); `server/views.py` (`build_views`); `tests/test_schema_gate.py`
- **Status:** Open

`/api/views` validates that the snapshot is syntactically valid JSON and that the root is an object, but it does not validate the full `schemas/mining_snapshot.v1.schema.json` contract at runtime. The committed sample snapshot is schema-gated in tests, which protects the checked-in sample, but a future live snapshot file could be JSON-valid and schema-invalid.

I did not find a current DOM XSS path from snapshot strings: the frontend renders dynamic text with `textContent`, DOM node creation, table cells, option text, or `title` attributes rather than `innerHTML`. The remaining risk is robustness and resource abuse from poisoned-but-JSON-valid snapshot values, such as out-of-contract integer bounds or unexpected shapes.

Recommended remediation: validate the snapshot against the v1 schema before serving `/api/views` and preferably before `/api/snapshot` returns 200 for live snapshots. If stdlib-only runtime remains a hard requirement, use a lightweight generated validator or enforce the highest-risk bounds explicitly at ingestion.

## Verified clean surfaces

### OAuth flow — partially clean

Clean items:

- OAuth is fail-closed when any required env var is absent: client id, client secret, redirect URI, and signing key must all be present.
- `/auth/login` and `/auth/callback` return `503 {"error": "sign-in not configured"}` in degraded mode.
- Callback validates state before exchanging the authorization code.
- Missing authorization code is rejected.
- Discord access tokens are not stored in cookies or persisted; they are used to fetch `/users/@me` and then discarded.
- Redirect URI is host-env controlled, not request controlled, and the same configured URI is used for the authorize URL and token exchange.

Caveat: redirect URI format is not validated beyond presence. If the owner provisions an `http://` production redirect URI, cookies will omit `Secure` because the `Secure` flag follows the redirect URI scheme.

### Session cookies — clean

- Token format is `base64url(json payload).base64url(hmac_sha256 tag)`.
- Verification rejects malformed tokens, bad base64, bad JSON, missing or expired `exp`, and bad signatures.
- Signature comparison uses `hmac.compare_digest`.
- State and session purposes are separated; a state token is not accepted as a session.
- Session cookies carry `iat` and one-week `exp`.
- Cookie flags include `Path=/`, `HttpOnly`, `SameSite=Lax`, and `Max-Age`; `Secure` is added for HTTPS redirect URIs.
- Empty, missing, garbage, tampered, and expired cookies resolve to signed-out behavior rather than exceptions or partial trust.

Operational caveat: there is no graceful signing-key rotation field. Rotating `WEB_SESSION_SIGNING_KEY` invalidates all sessions, which is fail-closed but abrupt.

### HMAC write path — clean with replay caveat

- Writes are fail-closed when `MINING_WRITE_ENDPOINT` or `MINING_WRITE_SHARED_SECRET` is absent.
- Even when writes are configured, the web server requires OAuth configuration and a verified session cookie.
- Browser requests are constrained to exactly `{action_id, action, params}`; extra keys such as `suid` or `guild_id` are rejected.
- The server derives `suid` from the verified session cookie and `guild_id` from the snapshot.
- The outbound proposal is JSON-canonicalized with compact separators and sorted keys before signing.
- The HMAC string-to-sign includes method, path, timestamp, and SHA-256 digest of the body.
- Verification uses `hmac.compare_digest` and checks signature before timestamp freshness.
- Client-facing error paths are generic for invalid browser bodies and relay failures.

Replay caveat: the web server does not maintain a transport nonce store. Replay resistance depends on timestamp freshness plus bot-side `action_id` idempotency. The shim tests cover byte-identical replay and action-id reuse, but the real bot endpoint must preserve the same contract before production cutover.

Canonicalization caveat: the signed path uses `urlsplit(config.endpoint).path`; endpoint query parameters are not signed. The owner should not provision a write endpoint whose authorization or routing depends on query parameters.

### Snapshot ingestion — XSS clean, schema-runtime not clean

- No current `innerHTML`/HTML-string insertion path was found in `web/app.js`.
- Dynamic miner names, item names, biome strings, board cells, inventory cells, auth UI text, and action responses are rendered as text.
- Runtime schema enforcement remains open as Finding 2.

### Degraded mode — clean

- With zero OAuth secrets, login and callback return 503 and do not call Discord.
- With zero write secrets, `/api/action` returns 503 before reading action body, session, snapshot, or relaying anything.
- `/api/me` in unconfigured auth mode reports signed out and `auth_configured: false`.
- Public snapshot and frontend routes remain available.
- The frontend disables sign-in when auth is not configured and disables action buttons when writes are not configured.

## Test/check notes from this audit

Commands run during the audit:

- `python -m pytest tests/test_auth.py tests/test_actions.py tests/test_api.py tests/test_schema_gate.py tests/test_snapshot.py` — warning: collection failed because the environment was missing `jsonschema`, required by `tests/test_actions.py` and `tests/test_schema_gate.py`.
- `python -m pytest tests/test_auth.py tests/test_api.py tests/test_snapshot.py tests/test_views.py` — passed: 98 tests.
