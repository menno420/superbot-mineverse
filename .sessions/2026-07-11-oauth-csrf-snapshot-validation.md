# Session 2026-07-11 — OAuth login-CSRF binding + runtime snapshot validation (security)

> **Status:** `in-progress`

## Plan

Two security hardening slices on the stdlib web server, no contract or
schema changes, no new balance numbers, player-visible nouns stay in DATA:

1. **OAuth login-CSRF binding.** `server/auth.py` mints an HMAC-signed,
   expiring, single-purpose `state` token but with NO per-browser binding
   ("no server-side store"): `/auth/login` sets no cookie, so
   `verify_state` accepts any server-minted, unexpired token from ANY
   browser — a classic login-CSRF gap (an attacker can graft a victim's
   browser onto the attacker's Discord identity). Fix, keeping the existing
   signing/TTL and staying stateless:
   - `/auth/login` sets an HttpOnly + SameSite=Lax (+ Secure on https)
     cookie carrying a keyed-MAC BINDING of the state it just minted.
   - `/auth/callback` REQUIRES that cookie and constant-time-compares
     (`hmac.compare_digest`) the recomputed binding against the state
     param before touching Discord; missing or mismatched cookie → the
     same 400 as a bad state. The state binding cookie is cleared
     (expired) on the successful redirect.

2. **Runtime snapshot validation at ingestion.** The v1 READ schema
   (`schemas/mining_snapshot.v1.schema.json`) is enforced only in CI
   (`tests/test_schema_gate.py`). Add RUNTIME validation where the server
   loads the snapshot (`server/app.py` `_serve_snapshot`, `_serve_views`,
   `_serve_action`) so a malformed live bot→web relay payload is refused
   with an honest 503 + a logged warning, not served as 200 / relayed.
   Runtime stays STDLIB-ONLY by contract (jsonschema is dev/test only), so
   the check is a compact schema-DERIVED structural validator
   (`server/snapshot_validation.py`) that reads the committed schema and
   enforces required fields + types + the version pin (plus the bounds /
   patterns / enums / additionalProperties the contract actually declares).
   The authoritative gate remains the CI jsonschema validator.

Constraints honored: Python 3.10 stdlib only; Oracle balance constants
stay verbatim (no new numbers introduced); the web app still reads the
snapshot only via the data contract (no bot Postgres, no bot token);
`control/inbox.md` never edited; `substrate-gate.yml` untouched.

## Close-out

*(filled in on completion)*

- **📊 Model:** opus-4.8 · high effort · task-class: OAuth login-CSRF binding + runtime snapshot validation (security)
