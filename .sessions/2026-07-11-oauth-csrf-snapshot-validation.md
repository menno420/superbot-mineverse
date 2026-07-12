# Session 2026-07-11 — OAuth login-CSRF binding + runtime snapshot validation (security)

> **Status:** `complete`

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

- **`server/auth.py`:** new `STATE_COOKIE`, `make_state_binding` (keyed MAC
  of the state) and `verify_state_binding` (constant-time
  `hmac.compare_digest`, rejects empty halves without raising). The
  existing `make_state`/`verify_state` signing + TTL are untouched — the
  per-browser binding is layered on top, still stateless.
- **`server/app.py`:** `_serve_login` sets the state-binding cookie
  (HttpOnly + SameSite=Lax, Secure on https) alongside the redirect;
  `_serve_callback` now REQUIRES that cookie and constant-time-compares
  it against the returned state before touching Discord (missing/mismatch
  → the same opaque `400` as a bad state), and clears the spent state
  cookie on the success redirect. Cookie plumbing refactored into
  `_cookie_header` + `_state_cookie_header` + `_state_binding_cookie`;
  `_redirect` now accepts one OR a list of `Set-Cookie` values.
  Runtime snapshot validation wired into `_serve_snapshot`,
  `_serve_views`, and `_serve_action` via `_snapshot_is_valid` (logs a
  warning, returns honest `503`).
- **`server/snapshot_validation.py` (new):** stdlib-only, schema-DERIVED
  structural validator over the committed v1 schema (type/const/enum/
  required/properties/additionalProperties/items/$ref/minimum/maximum/
  pattern/propertyNames). Subset of Draft 2020-12; the CI jsonschema gate
  stays authoritative.
- **Tests:** `tests/test_auth.py` +8 CSRF-binding cases (unit
  round-trip/forgery; login sets HttpOnly cookie; Secure on https;
  callback rejects missing / mismatched cookie, accepts match, clears the
  cookie after use); existing callback tests threaded through the new
  binding cookie. `tests/test_snapshot_validation.py` (new) — 11 unit +
  4 HTTP `503`-at-ingestion cases. `tests/test_server_robustness.py` —
  the former shaper-choke `500` case is now refused earlier at ingestion
  as `503` (updated + documented).
- verify: `python3 -m pytest -q` → **349 passed, 1 skipped** (baseline
  327 + 1); `python3 bootstrap.py check --strict` → exit 0.
- Shipped as PR #42 (READY, not draft) — this security PR GATES the owner
  provisioning the six OAuth/write env secrets (merge before provisioning
  so sign-in never runs without the browser binding).

## Follow-up — reviewer-confirmed defect fixes (2026-07-11, later)

Two defects raised on PR #42 review, fixed as follow-up commits on this same
branch (CSRF fix untouched — verified correct):

- **DEFECT 1 (MED) — validator silently ignored unimplemented schema keywords.**
  `server/snapshot_validation.py`: `_check` ignored any JSON-Schema keyword it
  did not implement, so the runtime validator drifted from CI. Proven case:
  `biomes` has `maxItems: 4`, but a snapshot with 5000 entries PASSED runtime
  while CI's jsonschema rejected it. Fix (both halves): (1) implemented the
  stdlib size/length family — `maxItems`/`minItems` (arrays),
  `maxLength`/`minLength` (strings), `maxProperties`/`minProperties` (objects);
  the committed schema uses `maxItems`, the rest are covered for parity. (2)
  Added a **fail-loud drift guard**: `_check` now refuses (invalid → 503 + a
  logged warning naming the keyword) any *validation* keyword not in the
  explicit `_HANDLED_KEYWORDS` set, unless it is in the explicit
  `_NOOP_KEYWORDS` annotation allow-list (`$schema`, `$id`, `$anchor`,
  `$comment`, `$defs`, `definitions`, `title`, `description`, `examples`,
  `default`, `readOnly`, `writeOnly`, `deprecated`, `format`). Confirmed the
  committed valid sample still validates clean.

- **DEFECT 2 (LOW/MED) — /api/me was a fourth, unvalidated snapshot load path.**
  `server/app.py` `_find_miner` loaded the snapshot with no structural check;
  a valid-JSON-but-non-object snapshot (`[]`) raised `AttributeError` → HTTP 500
  for a signed-in user. `_serve_me` now loads + validates via the existing
  `_snapshot_is_valid` (honest 503 + log, same as the read routes) and passes
  the validated snapshot into `_find_miner` (now a pure lookup that cannot
  raise). Confirmed no other unvalidated snapshot load sites remain (the four:
  `_serve_snapshot`, `_serve_views`, `_serve_action`, `_serve_me`).

- **Tests (regression — fail before / pass after):** `tests/test_snapshot_validation.py`
  +6 (maxItems reject + within-bound accept, full size/length family via
  synthetic schemas, fail-loud on unimplemented keyword with warning assertion,
  no-op annotation keywords tolerated, HTTP 503 on a maxItems-violating
  snapshot); `tests/test_auth.py` +1 (`/api/me` with a `[]` snapshot → 503 for
  a signed-in user, not 500).
- verify: `python3 -m pytest -q` → **356 passed, 1 skipped** (was 349 + 1; +7);
  `python3 bootstrap.py check --strict` → exit 0.

## 💡 Session idea

`make_state_binding` recomputes a keyed MAC over the raw `state` string;
because the signed `state` already embeds a random `nonce`, a future slice
could bind on the nonce alone (shorter cookie, same guarantee) and expose
a single `state_binding_matches(config, state, cookie)` helper that both
`/auth/callback` and any future re-auth path share, so the compare lives
in exactly one place.

## ⟲ Previous-session review

The `server-robustness` card's close-out left a precise guard recipe for
the `views.build_views` shaper-choke `500` path — that note made it
obvious that adding ingestion validation would move that case's bite
earlier (to a `503` before the shaper runs), so I updated that one test
deliberately rather than being surprised by a red. Friction worth
flagging forward: runtime validation now makes the `_serve_views`
`build_views` try/except effectively defense-in-depth (structurally
valid data reaches it), so a future slice hardening the shaper should
treat that `500` as a belt-and-suspenders path, not a primary one.

- **📊 Model:** opus-4.8 · high effort · task-class: OAuth login-CSRF binding + runtime snapshot validation (security)
