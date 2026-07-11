# Session 2026-07-11 — server robustness: charsets, conditional caching, honest 404/405, malformed-snapshot guard

> **Status:** `complete`

## Plan

Server-only HTTP polish — stdlib `server/app.py` + tests, no contract,
schema, OAuth-flow, or write-path semantic changes:

1. **Charset on every Content-Type** — API JSON already declared
   `charset=utf-8`; the static files (`text/html`, `text/css`,
   `application/javascript`) went out bare. Override `guess_type` to
   append `charset=utf-8` to every text-ish type.
2. **Conditional caching on the committed-data endpoints** —
   `GET /api/snapshot` and `GET /api/views` serve committed repo data,
   so a strong content-hash (sha256) ETag is honest and cheap:
   `If-None-Match` hit → 304 empty; `Cache-Control: no-store` becomes
   `no-cache` (revalidate every time) on exactly these two routes.
3. **Honest 404/405** — GET on `POST /api/action` (and PUT/DELETE/
   PATCH anywhere) answered a lying 404 or a bare 405; now: known
   route + wrong verb → 405 with an `Allow` header (JSON body on
   `/api/*`), unknown `/api/*` → JSON 404 on every method, static
   miss → the stdlib HTML 404.
4. **Malformed-snapshot guard** — a snapshot that is valid JSON but
   not an object now 503s on BOTH read routes (previously
   `/api/snapshot` relayed it as a 200); a valid JSON object the view
   shaper chokes on (proven: `equipment` as a string raises
   `AttributeError` in `build_views`) now answers a clean
   `500 {"error": "snapshot malformed"}` instead of crashing the
   request thread mid-response.
5. **Regression net** — new `tests/test_server_robustness.py`
   (http.client round-trips so 304/405 arrive as plain responses).

Constraints honored: Python 3.10 stdlib only (one new import:
`hashlib`); read-only server, no state; `/api/me`, `/api/action` and
the auth routes keep `no-store` and their exact response shapes;
`control/status.md` / `control/inbox.md` untouched.

## Close-out

- `server/app.py`: `guess_type` override (charset for text types);
  `_serve_cacheable_json` + `_if_none_match_hits` (strong sha256 ETag,
  RFC 9110 weak-compare: `W/`-prefixed and `*` forms hit, comma lists
  parsed) now used by `_serve_snapshot` and `_serve_views`;
  `_serve_snapshot` additionally rejects non-object JSON as the same
  honest 503; `_serve_views` wraps `views.build_views` so any shaping
  failure is a clean 500; `do_GET` answers 405 + `Allow: POST` on
  `/api/action`; new `do_PUT`/`do_DELETE`/`do_PATCH` +
  `_reject_unsupported_method` route every wrong verb to 405 with an
  honest `Allow` (unknown `/api/*` stays a JSON 404); `_send_json`
  grew an optional `headers=` kwarg.
- `tests/test_server_robustness.py`: 36 new tests (206 → 242 passed;
  the base already carries a11y PR #33's 15, this branch rebased onto
  it) — charset pins on 7 routes + error bodies, ETag stability, 304
  round-trips (exact/weak/wildcard/miss), JSON-404 on every method,
  405 + Allow matrix over the read routes and `/api/action`, and the
  malformed-snapshot trio (non-object → 503 both routes, shaper-choker
  → clean 500, missing → 503).
- Existing pins kept green untouched: `POST /api/nope` → 404 and
  `POST /` → 405 (`tests/test_actions.py::test_post_routes_stay_honest`),
  all of `tests/test_api.py` / `tests/test_views.py` / auth tests.
- verify: `python3 -m pytest -q` → 242 passed, 1 skipped (was 206 + 1
  after a11y PR #33 merged; 191 + 1 at session start);
  `python3 bootstrap.py check --strict` → all checks passed.
- Claim `control/claims/claude-server-robustness.md` rides this PR;
  removal is deferred to the next control-lane PR, per the established
  pattern.

## 💡 Session idea

`/api/views` re-reads and re-shapes the snapshot on every request and
hashes the serialized document just to compute the ETag. The snapshot
is committed data — a tiny mtime-keyed memo (path, mtime) → (payload,
etag) in the handler class would make the 304 path allocation-free
without adding any mutable state that outlives the file it mirrors.

## ⟲ Previous-session review

The web-a11y-responsive session (same worker, previous slice) showed
the value of pinning served bytes over unit internals — this slice
kept that style but dropped to `http.client` because `urllib` turns
304/405 into exceptions and hides headers. One friction-to-guard find
from probing rather than reading: `views.build_views` looked total
(every branch isinstance-guarded) but a string `equipment` still
raises `AttributeError` via `shape_miner`'s `.get` chain. Guard
recipe if a future slice hardens the shaper instead: make
`shape_miner` (`server/views.py`) tolerate non-dict `equipment` /
`gear_wear`, then flip
`tests/test_server_robustness.py::test_snapshot_the_shaper_chokes_on_is_a_clean_500`
to pin the degraded-200 instead of the 500.

- **📊 Model:** fable-5 · standard effort · task-class: server HTTP robustness (build)
