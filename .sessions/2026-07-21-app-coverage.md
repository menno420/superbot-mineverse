# Session — 2026-07-21 — Cover server/app.py's degraded-mode + defensive branches with tests

> **Status:** `complete`
> **Branch:** `claude/mineverse-app-coverage`
> **Timestamp (UTC):** Tue Jul 21 2026

## Summary

A contained, single-repo test-coverage slice — tests only, ZERO production
behavior change, entirely in degraded (no-env) mode. `server/app.py` was the
next-thinnest `server/` module (91%; 38 uncovered lines) after the #139
ingest-coverage pass took `server/ingest.py` to 100%. The gaps this slice
closes are the error and defensive arms the happy-path API/auth suites never
walk:

- the `POST /api/action` guard-rail order — writes configured but auth NOT →
  the `503 {"error": "sign-in not configured"}` arm;
- every malformed-body rejection inside `_read_action_request` (empty body,
  invalid JSON, non-object JSON, empty `action_id`, empty `action`, non-object
  `params`), each folding into the one honest `400 {"error": "invalid action
  request"}` — reached with a fully-configured seat + a VALID signed session so
  the body itself is what's rejected;
- the `_serve_views` defense-in-depth `except` around `views.build_views`
  (a structurally-valid-but-shaper-hostile snapshot → `500 {"error":
  "snapshot malformed"}`), driven by making the shaper raise since the runtime
  v1 validator refuses every schema-invalid snapshot earlier and the shapers
  tolerate every malformed field a schema-valid one can carry;
- the "a garbage Cookie header is just no cookie" arms of `_session_user_id`
  and `_state_binding_cookie` (unreachable via a str Cookie — `SimpleCookie.load`
  never raises on one — so driven directly with a non-str header value);
- `do_OPTIONS` on a non-API path → the stock `501`;
- `guess_type`'s "already carries a charset, don't double-append" arm.

12 new tests in the new `tests/test_app_degraded_coverage.py` (mirroring the
`serve` fixture + config-object seams of `tests/test_actions.py` /
`tests/test_auth.py`). They assert real behavior — exact status codes and JSON
error bodies, the no-double-charset passthrough — not smoke. `server/app.py`
goes 91% → ~96%. No `server/*` byte changes.

## 💡 Session idea

Two of `server/app.py`'s defensive arms (`_session_user_id` /
`_state_binding_cookie`'s `except` around `SimpleCookie.load`) are literally
unreachable through a real HTTP request — `load()` never raises on a *str*
Cookie value, only on a non-str one a socket can't deliver — so covering them
needs a direct-method call, not a round-trip. A one-line `docs/` note ("a
guard whose trigger no HTTP client can produce is a UNIT target, not an
integration one; drive it on a `__new__`'d handler") would save the next
coverage session the same rediscovery the cookie branch cost this one.

## ⟲ Previous-session review

Direct predecessor on this seat is **PR #139**
(`claude/mineverse-ingest-coverage`,
`.sessions/2026-07-20-mineverse-ingest-coverage.md`): the ingest-coverage pass
that took `server/ingest.py` 80% → 100% with 15 tests-only units, ZERO product
change, all in degraded mode. This session mirrors that pattern exactly one
module over — same tests-only discipline, same no-env posture, same
least-covered-module targeting — and independently re-confirms the posture #139
documented: the app runs fully in degraded (no-env) mode with the suite green,
since this whole app-coverage slice needed no secrets, OAuth, contract, or
second repo. Upstream of #139 is the **kit-wave #138** (substrate-kit v1.17.0 →
v1.20.1, the current origin/main HEAD 7cea1b8) — pure kit machinery, no
`server/` change; this slice builds cleanly on top of it. Both hold up: #139 is
pure test addition and #138 is pure kit machinery, neither touched the
`server/app.py` branches this session now defends.

- **📊 Model:** Opus 4.8 · medium · test writing
