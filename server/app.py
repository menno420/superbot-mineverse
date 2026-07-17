"""superbot-mineverse stage-1/2 backend — read-only, stdlib-only.

Serves, from the standard library alone (no framework, no database,
no secrets in the repo):

- ``GET /api/snapshot`` — the snapshot as ``application/json``: the
  committed sample (``data/sample_snapshot.json``) by default, or a
  live-fed file when the host sets ``MINING_SNAPSHOT_PATH`` (the
  consume-side seam of the bot READ relay — degraded by default, exactly
  like the OAuth/write vars: unset means the sample, byte-identical
  behavior).  A missing, unreadable, or v1-nonconformant snapshot returns
  an honest ``503 {"error": "snapshot unavailable"}`` instead of a blank
  200 — the same answer whichever file is being served, re-read fresh on
  every request (no caching of a live-fed file, no last-good fallback:
  the server holds no mutable state).
- ``GET /api/views`` — the same snapshot shaped for the frontend's
  deepened read views (``server/views.py``: gear/vault/pack panels,
  depth ladder, leaderboards, inventory browser).  Same honest 503 when
  the snapshot is missing or corrupt.
- ``GET /auth/login`` / ``/auth/callback`` / ``/auth/logout`` and
  ``GET /api/me`` — Discord OAuth2 sign-in for READ personalization only
  (stage b, docs/auth.md).  Configured exclusively via host env vars; with
  them absent the app runs in degraded mode and every public view still
  works.
- ``POST /api/action`` — stage c (docs/mining-write-contract.md): relays a
  signed action PROPOSAL to the bot-side executor named by
  ``MINING_WRITE_ENDPOINT`` (TEST GUILD ONLY). Degraded by default: with
  ``MINING_WRITE_ENDPOINT`` / ``MINING_WRITE_SHARED_SECRET`` absent it
  answers an honest ``503 {"error": "writes not configured"}``.
- ``POST /api/snapshot/ingest`` — the FLAG-1 receive side of the bot→web
  READ relay (server/ingest.py): the bot-side pusher (superbot #2058,
  ``MINING_SNAPSHOT_RELAY_URL``, ~60 s cadence) POSTs the v1 snapshot
  here, HMAC-signed with ``MINING_SNAPSHOT_RELAY_SHARED_SECRET`` under
  the canonical ``server/actions.py`` scheme; verified → v1-validated →
  atomically persisted into the ``MINING_SNAPSHOT_PATH`` file the read
  routes re-read fresh per request. Degraded by default and FAIL CLOSED:
  with the secret or the path absent it answers an honest
  ``503 {"error": "snapshot ingest not configured"}`` — never unsigned
  data, never a write over the committed sample.
- Everything else — the static frontend under ``web/``.

The layering contract (docs/architecture.md): data/ -> server/ -> web/;
the frontend talks to this process only via the JSON API, and this process
never writes GAME STATE itself (signing a cookie or a proposal is not a
write path — the server holds no mutable state, no database, and no bot
credentials; mutations happen only bot-side, behind the write contract).
The one file this process ever touches is the host-provisioned
``MINING_SNAPSHOT_PATH`` relay document the ingest seam replaces whole —
relay transport state, never repo data and never game state.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import urllib.parse
from functools import partial
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from server import (
        actions,
        auth,
        ingest,
        response_validation,
        snapshot_validation,
        views,
    )
except ImportError:  # direct script execution: python3 server/app.py
    import actions  # type: ignore[no-redef]
    import auth  # type: ignore[no-redef]
    import ingest  # type: ignore[no-redef]
    import response_validation  # type: ignore[no-redef]
    import snapshot_validation  # type: ignore[no-redef]
    import views  # type: ignore[no-redef]

LOGGER = logging.getLogger("mineverse")

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"
WEB_ROOT = REPO_ROOT / "web"

# Consume-side seam of the bot READ relay (FLAG 1): when this host env var is
# set, the server serves the snapshot from that path instead of the committed
# sample. Degraded by default — unset (or empty) means the sample, exactly as
# before. The file is re-read fresh and v1-validated on EVERY request, so a
# relay writer that goes missing or emits garbage draws the existing honest
# 503, never a stale or corrupt 200. (Canonical constant lives in
# server/ingest.py — the ingest seam persists into the same file this
# read seam serves; the alias keeps existing importers working.)
ENV_SNAPSHOT_PATH = ingest.ENV_SNAPSHOT_PATH


def snapshot_path_from_env(environ=os.environ) -> Path:
    """The snapshot path the host asks for, or the committed sample.

    Empty string counts as UNSET (mirrors ``actions.WriteConfig.from_env``'s
    ``or None`` convention). The path is NOT existence-checked here: a
    set-but-missing file must surface as the per-request honest 503, not as
    a silent boot-time fallback to sample data.
    """
    configured = environ.get(ENV_SNAPSHOT_PATH) or None
    return Path(configured) if configured else SNAPSHOT_PATH

API_SNAPSHOT = "/api/snapshot"
API_VIEWS = "/api/views"
API_ME = "/api/me"
API_ACTION = "/api/action"
API_SNAPSHOT_INGEST = "/api/snapshot/ingest"
MAX_ACTION_BODY_BYTES = 64 * 1024
AUTH_LOGIN = "/auth/login"
AUTH_CALLBACK = "/auth/callback"
AUTH_LOGOUT = "/auth/logout"

# GET-only API routes — any other verb on these answers 405 + Allow.
GET_ONLY_API_ROUTES = frozenset({API_SNAPSHOT, API_VIEWS, API_ME})
# POST-only API routes — any other verb on these answers 405 + Allow: POST.
POST_ONLY_API_ROUTES = frozenset({API_ACTION, API_SNAPSHOT_INGEST})


class MineverseHandler(SimpleHTTPRequestHandler):
    """Static-file handler with the one JSON API route bolted on."""

    # Injected by make_server via functools.partial.
    snapshot_path: Path = SNAPSHOT_PATH
    auth_config: auth.AuthConfig | None = None
    write_config: actions.WriteConfig | None = None
    ingest_config: ingest.IngestConfig | None = None

    def __init__(
        self,
        *args,
        snapshot_path: Path | None = None,
        auth_config: auth.AuthConfig | None = None,
        write_config: actions.WriteConfig | None = None,
        ingest_config: ingest.IngestConfig | None = None,
        **kwargs,
    ):
        if snapshot_path is not None:
            self.snapshot_path = snapshot_path
        if auth_config is not None:
            self.auth_config = auth_config
        if self.auth_config is None:
            self.auth_config = auth.AuthConfig.from_env()
        if write_config is not None:
            self.write_config = write_config
        if self.write_config is None:
            self.write_config = actions.WriteConfig.from_env()
        if ingest_config is not None:
            self.ingest_config = ingest_config
        if self.ingest_config is None:
            self.ingest_config = ingest.IngestConfig.from_env()
        super().__init__(*args, **kwargs)

    def end_headers(self):  # noqa: N802 (http.server API name)
        """One choke point for headers every response shares.

        ``X-Content-Type-Options: nosniff`` tells browsers never to
        MIME-sniff a response body against its declared ``Content-Type`` —
        emitted here so it rides API JSON, static files, 304s, and error
        pages alike, with no per-handler path able to forget it. Only
        nosniff: X-Frame-Options / Referrer-Policy / CSP are owner policy
        calls, deliberately not asserted here.
        """
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self):  # noqa: N802 (http.server API name)
        route, _, query = self.path.partition("?")
        if route == API_SNAPSHOT:
            self._serve_snapshot()
        elif route == API_VIEWS:
            self._serve_views()
        elif route == API_ME:
            self._serve_me()
        elif route == AUTH_LOGIN:
            self._serve_login()
        elif route == AUTH_CALLBACK:
            self._serve_callback(query)
        elif route == AUTH_LOGOUT:
            self._serve_logout()
        elif route in POST_ONLY_API_ROUTES:
            # Known route, wrong verb: 405 + Allow, not a lying 404.
            self._send_json(405, {"error": "method not allowed"},
                            headers={"Allow": "POST"})
        elif route.startswith("/api/"):
            self._send_json(404, {"error": "unknown API route"})
        else:
            super().do_GET()

    def do_HEAD(self):  # noqa: N802 (http.server API name)
        """HEAD that actually works on the read API routes.

        ``SimpleHTTPRequestHandler``'s inherited ``do_HEAD`` only knows
        static paths, so ``HEAD /api/snapshot|/api/views|/api/me`` used to
        404 even though the 405 handler advertised ``Allow: GET, HEAD``.
        Route ``/api/*`` through the SAME dispatch as ``do_GET`` — the two
        body-write sites (``_send_json``, ``_serve_cacheable_json``)
        suppress the body when ``self.command == "HEAD"`` while still
        emitting every header (Content-Length, ETag, Content-Type +
        charset) identically to GET, so 200/304/404/405/503 all answer
        header-only. Non-API paths keep the inherited static HEAD.
        """
        route, _, _ = self.path.partition("?")
        if route.startswith("/api/"):
            self.do_GET()
        else:
            super().do_HEAD()

    def do_OPTIONS(self):  # noqa: N802 (http.server API name)
        """204 with an honest ``Allow`` per route class.

        Mirrors the ``Allow``-header discipline of
        ``_reject_unsupported_method``: read routes answer
        ``GET, HEAD, OPTIONS``; the two POST routes ``POST, OPTIONS``; an
        unknown ``/api/*`` route the same JSON 404 as every other verb; a
        static path defers to the stock 501 (no CORS surface — the frontend
        is same-origin).
        """
        route, _, _ = self.path.partition("?")
        if route in GET_ONLY_API_ROUTES:
            allow = "GET, HEAD, OPTIONS"
        elif route in POST_ONLY_API_ROUTES:
            allow = "POST, OPTIONS"
        elif route.startswith("/api/"):
            self._send_json(404, {"error": "unknown API route"})
            return
        else:
            self.send_error(501, "Unsupported method (%r)" % self.command)
            return
        self.send_response(204)
        self.send_header("Allow", allow)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):  # noqa: N802 (http.server API name)
        route, _, _ = self.path.partition("?")
        if route == API_ACTION:
            self._serve_action()
        elif route == API_SNAPSHOT_INGEST:
            self._serve_snapshot_ingest()
        else:
            self._reject_unsupported_method()

    def do_PUT(self):  # noqa: N802 (http.server API name)
        self._reject_unsupported_method()

    do_DELETE = do_PUT  # noqa: N815 (http.server API names)
    do_PATCH = do_PUT  # noqa: N815

    def _reject_unsupported_method(self) -> None:
        """405 with an honest Allow header — 404 only for unknown routes.

        Everything the server exposes besides ``POST /api/action`` and
        ``POST /api/snapshot/ingest`` is read-only: GET (plus the HEAD that
        ``SimpleHTTPRequestHandler`` derives from it for static files) is
        the only verb.
        """
        route, _, _ = self.path.partition("?")
        if route in POST_ONLY_API_ROUTES:  # POST is handled before this
            self._send_json(405, {"error": "method not allowed"},
                            headers={"Allow": "POST"})
            return
        if route.startswith("/api/") and route not in GET_ONLY_API_ROUTES:
            self._send_json(404, {"error": "unknown API route"})
            return
        self._send_json(405, {"error": "method not allowed"},
                        headers={"Allow": "GET, HEAD"})

    # --- write proposals (stage c — TEST GUILD ONLY, degraded by default) --

    def _serve_action(self) -> None:
        """Relay a signed action PROPOSAL to the bot-side executor.

        docs/mining-write-contract.md: the browser sends only
        ``{action_id, action, params}``; this server derives ``suid`` from
        the VERIFIED session cookie (never from the browser), attaches the
        snapshot's ``guild_id``, signs with the shared secret the browser
        never sees, and relays the executor's response envelope verbatim —
        after a runtime conformance check plus a status↔reason_code
        coherence check (server/response_validation.py): a non-conformant
        envelope on any status, or a conformant one under an HTTP status
        the contract's mapping table does not pair with its reason_code,
        answers an honest 502 instead of being relayed. Of the executor's
        response HEADERS only the contract-relevant allowlist is forwarded
        (``actions.RELAYED_RESPONSE_HEADERS`` — today ``Retry-After`` on a
        429, when present); everything else stops at the relay.
        """
        write_config = self.write_config
        if not write_config.configured:
            self._send_json(503, {"error": "writes not configured"})
            return
        auth_config = self.auth_config
        if not auth_config.configured:
            self._send_json(503, {"error": "sign-in not configured"})
            return
        user_id = self._session_user_id(auth_config)
        if user_id is None:
            self._send_json(401, {"error": "sign-in required"})
            return
        request = self._read_action_request()
        if request is None:
            self._send_json(400, {"error": "invalid action request"})
            return
        # Ingestion-time v1 validation before we trust the snapshot's guild_id
        # for a signed write proposal — a malformed relay must not be relayed.
        loaded = self._load_valid_snapshot()
        if loaded is None:
            return
        _, snapshot = loaded
        guild_id = snapshot["guild_id"]  # required + string, guaranteed by the check
        proposal = {
            "contract_version": actions.CONTRACT_VERSION,
            "action_id": request["action_id"],
            "guild_id": guild_id,
            "suid": user_id,  # server-derived — the browser cannot assert it
            "action": request["action"],
            "params": request["params"],
        }
        try:
            status, body, relayed_headers = actions.propose(
                write_config, proposal
            )
        except (OSError, ValueError):
            self._send_json(502, {"error": "action relay failed"})
            return
        # Runtime sanity check of the executor's answer BEFORE it reaches the
        # browser: whatever the HTTP status (200 included), a body that is not
        # a conformant v1 response envelope is never relayed — a lying 200 is
        # worse than a clean failure. Passing http_status adds the coherence
        # layer on top: a CONFORMANT envelope whose HTTP status contradicts
        # its reason_code (ok under a 4xx/5xx, a rejection under 200 — the
        # contract's status-mapping table) draws the same 502. Coherent
        # conformant envelopes (contract rejections included) relay verbatim,
        # exactly as before. The distinct error body separates "executor
        # unreachable" ("action relay failed") from "executor answered
        # garbage" for the frontend and the logs.
        problem = response_validation.envelope_error(body, http_status=status)
        if problem is not None:
            LOGGER.warning(
                "executor response (HTTP %s) failed v1 envelope validation: %s",
                status,
                problem,
            )
            self._send_json(502, {"error": "invalid executor response"})
            return
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # Contract-relevant executor headers only (the allowlist propose()
        # already applied — actions.RELAYED_RESPONSE_HEADERS, today exactly
        # Retry-After on a 429): the backoff hint the contract promises
        # clients survives the relay; executor-internal headers never do.
        # A 429 the executor sent WITHOUT the header still relays — header
        # presence is the executor's contract obligation, not a relay
        # refusal condition (the coherence layer above judges status↔body).
        for name, value in relayed_headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_action_request(self) -> dict | None:
        """The browser's ``{action_id, action, params}`` — or None if bogus.

        EXACTLY those three keys: a body carrying ``suid``/``guild_id`` (or
        anything else) is rejected outright so no client input can ever
        reach the identity fields of the proposal.
        """
        body = self._read_bounded_body(MAX_ACTION_BODY_BYTES)
        if body is None:
            return None
        try:
            request = json.loads(body)
        except ValueError:
            return None
        if not isinstance(request, dict):
            return None
        if set(request) != {"action_id", "action", "params"}:
            return None
        if not isinstance(request["action_id"], str) or not request["action_id"]:
            return None
        if not isinstance(request["action"], str) or not request["action"]:
            return None
        if not isinstance(request["params"], dict):
            return None
        return request

    def _read_bounded_body(self, max_bytes: int, *, errors=None) -> bytes | None:
        """THE one bounded POST-body reader: parse ``Content-Length``,
        bounds-check BEFORE reading a byte, then read exactly that many.

        Both POST routes (``/api/action``, ``/api/snapshot/ingest``) come
        through here so a third route can never hand-roll a subtly
        different copy. ``errors`` selects the error emission:

        * ``None`` (quiet — the action path): any length problem returns
          ``None`` with nothing sent, and the caller folds every failure
          into its own single 400.
        * ``(bad_length, too_large)`` (emitting — the ingest path): a
          bad/absent/non-positive length answers ``400 {"error":
          bad_length}``, an oversized one ``413 {"error": too_large}`` —
          both BEFORE the body is drained, deliberately: a client still
          streaming may see a broken pipe instead of the status
          (tests/test_snapshot_ingest.py pins that trade-off).

        A read failure (client vanished mid-body) returns ``None`` with
        nothing extra sent in either mode — the quiet caller's folded 400
        dies on the closed socket, the emitting caller answers nothing.
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0  # bogus header == absent: same rejection below
        if length <= 0:
            if errors is not None:
                self._send_json(400, {"error": errors[0]})
            return None
        if length > max_bytes:
            if errors is not None:
                self._send_json(413, {"error": errors[1]})
            return None
        try:
            return self.rfile.read(length)
        except OSError:
            return None

    # --- snapshot ingest (FLAG 1 receive side — degraded by default) ------

    def _serve_snapshot_ingest(self) -> None:
        """Receive one HMAC-signed v1 snapshot from the bot-side relay.

        The receive half of the bot→web READ relay (server/ingest.py holds
        the seam doctrine): superbot's pusher (#2058) POSTs the snapshot
        JSON here every ~60 s. Order of checks:

        1. FAIL CLOSED unconfigured: without BOTH
           ``MINING_SNAPSHOT_RELAY_SHARED_SECRET`` and
           ``MINING_SNAPSHOT_PATH`` this answers an honest 503 and never
           reads a byte of the body — there is no unsigned mode, no
           built-in secret, and no writing over the committed sample.
        2. Body bounds BEFORE the read (bad/absent length 400, oversized
           413) so an unauthenticated client cannot stream unbounded data.
        3. Transport auth over the RAW bytes (``actions.verify`` — the one
           canonical scheme, constant-time, signature before the ±300 s
           timestamp window): failure is a 401 with the contract reason
           and NOTHING of the body is ever parsed or persisted.
        4. Only then content shape: non-JSON content type 415, malformed
           JSON 400, v1-contract violation 400 (logged) — same validator
           the read side re-checks per request, so nothing non-conformant
           is ever persisted even transiently.
        5. Atomic whole-document replace (``ingest.persist_snapshot``);
           the read routes pick the new document up on their next
           per-request fresh read. Filesystem failure is an honest 500.

        Ordering is last-write-wins (single 60 s sender, no retry —
        contract § Delivery expectations); a replay inside the skew window
        rewrites identical bytes, so acceptance is idempotent by content.
        """
        config = self.ingest_config
        if not config.configured:
            LOGGER.warning(
                "snapshot ingest refused: %s and/or %s unset (fail closed)",
                ingest.ENV_INGEST_SECRET,
                ingest.ENV_SNAPSHOT_PATH,
            )
            self._send_json(503, {"error": "snapshot ingest not configured"})
            return
        body = self._read_bounded_body(
            ingest.MAX_SNAPSHOT_BODY_BYTES,
            errors=("invalid content length", "snapshot too large"),
        )
        if body is None:
            return  # bounds already answered (400/413), or client vanished
        problem = actions.verify(
            config.secret,
            "POST",
            API_SNAPSHOT_INGEST,
            self.headers.get(actions.HEADER_TIMESTAMP) or "",
            body,
            self.headers.get(actions.HEADER_SIGNATURE) or "",
        )
        if problem is not None:
            self._send_json(401, {"error": problem})
            return
        content_type = (
            (self.headers.get("Content-Type") or "").partition(";")[0].strip().lower()
        )
        if content_type != "application/json":
            self._send_json(415, {"error": "content type must be application/json"})
            return
        try:
            snapshot = json.loads(body)
        except ValueError:
            self._send_json(400, {"error": "snapshot is not valid JSON"})
            return
        if not self._snapshot_is_valid(snapshot):
            self._send_json(400, {"error": "snapshot failed v1 validation"})
            return
        try:
            ingest.persist_snapshot(config.path, body)
        except OSError as exc:
            LOGGER.warning("snapshot persist failed: %s", exc)
            self._send_json(500, {"error": "snapshot persist failed"})
            return
        self._send_json(200, {"status": "accepted"})

    def _serve_views(self) -> None:
        """Derived read projection of the snapshot (server/views.py).

        Read-only, no state: the same snapshot ``/api/snapshot`` relays
        verbatim, shaped for the frontend's deepened views.  Missing or
        corrupt snapshot answers the same honest 503; a snapshot that is
        valid JSON but malformed beyond what the shaper tolerates answers
        an honest 500 instead of crashing the request.
        """
        loaded = self._load_valid_snapshot()
        if loaded is None:
            return
        _, snapshot = loaded
        try:
            document = views.build_views(snapshot, self._snapshot_source())
        except Exception:  # noqa: BLE001 — any shaping failure is data-shaped
            self._send_json(500, {"error": "snapshot malformed"})
            return
        self._serve_cacheable_json(json.dumps(document).encode("utf-8"))

    def _snapshot_source(self) -> str:
        """Where this handler's snapshot bytes come from.

        ``"sample"`` iff the configured path IS the committed demo file
        (``MINING_SNAPSHOT_PATH`` unset/empty, or an explicit
        ``snapshot_path=SNAPSHOT_PATH``); any other path — env-fed relay
        file or embedder-passed — is ``"live"``. Path identity only, no
        content sniffing: a relay that happens to relay sample-shaped
        data is still a live feed.
        """
        return "sample" if self.snapshot_path == SNAPSHOT_PATH else "live"

    def _serve_snapshot(self) -> None:
        loaded = self._load_valid_snapshot()
        if loaded is None:
            return
        payload, _ = loaded
        self._serve_cacheable_json(payload)

    def _load_valid_snapshot(self) -> tuple[bytes, dict] | None:
        """Read + parse + v1-validate the snapshot — or answer the honest 503.

        THE one load-validate-or-503 path, shared by all four snapshot
        consumers (``/api/snapshot``, ``/api/views``, ``/api/me``, and the
        ``/api/action`` pre-relay check) so a fifth consumer can never
        forget one half of it.  The file is re-read fresh on EVERY call
        (live-fed relay honesty — no caching, no last-good fallback), and a
        snapshot that is valid JSON but violates the v1 READ contract
        (wrong version, missing/typewrong fields, out-of-band values) is
        refused exactly like a missing or corrupt file — the future live
        bot→web relay is checked here, not only the committed sample in CI.

        Returns ``(raw_bytes, parsed)`` on success — the raw bytes too,
        because ``_serve_snapshot`` ETags and serves the exact file bytes.
        On any failure this helper has already sent
        ``503 {"error": "snapshot unavailable"}`` and returns ``None``:
        the caller just returns.
        """
        try:
            payload = self.snapshot_path.read_bytes()
            snapshot = json.loads(payload)  # never serve corrupt bytes as 200
        except (OSError, ValueError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return None
        if not self._snapshot_is_valid(snapshot):
            self._send_json(503, {"error": "snapshot unavailable"})
            return None
        return payload, snapshot

    def _snapshot_is_valid(self, snapshot: object) -> bool:
        """True iff ``snapshot`` conforms to the v1 READ contract (logs on fail)."""
        try:
            snapshot_validation.validate_snapshot(snapshot)
            return True
        except snapshot_validation.SnapshotInvalid as exc:
            LOGGER.warning("snapshot failed v1 validation at ingestion: %s", exc)
            return False

    # --- conditional caching (committed data — a content hash is honest) --

    def _serve_cacheable_json(self, payload: bytes) -> None:
        """200 with a content-hash ETag, or 304 when the client has it.

        The snapshot is committed repo data, so a strong sha256 ETag is
        cheap and exact.  ``Cache-Control: no-cache`` means "revalidate
        every time", which the ETag makes a near-free 304 round-trip.
        """
        etag = f'"{hashlib.sha256(payload).hexdigest()}"'
        if self._if_none_match_hits(etag):
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command != "HEAD":  # HEAD: identical headers, no body
            self.wfile.write(payload)

    def _if_none_match_hits(self, etag: str) -> bool:
        header = self.headers.get("If-None-Match")
        if not header:
            return False
        candidates = {tag.strip() for tag in header.split(",")}
        # RFC 9110: If-None-Match compares weakly — a W/-prefixed copy of
        # our strong tag (and the * wildcard) still hits.
        return bool(candidates & {etag, f"W/{etag}", "*"})

    # --- Discord OAuth (stage b — read personalization only) -------------

    def _serve_login(self) -> None:
        config = self.auth_config
        if not config.configured:
            self._send_json(503, {"error": "sign-in not configured"})
            return
        state = auth.make_state(config)
        # Bind the login round-trip to THIS browser: the callback will require
        # this cookie and constant-time-compare it against the returned state,
        # so a server-minted state alone can't be replayed from another browser.
        self._redirect(
            auth.build_authorize_url(config, state),
            set_cookie=self._state_cookie_header(auth.make_state_binding(config, state)),
        )

    def _serve_callback(self, query: str) -> None:
        config = self.auth_config
        if not config.configured:
            self._send_json(503, {"error": "sign-in not configured"})
            return
        params = urllib.parse.parse_qs(query)
        if params.get("error"):
            self._send_json(
                400, {"error": f"discord authorization failed: {params['error'][0]}"}
            )
            return
        state = (params.get("state") or [""])[0]
        if not auth.verify_state(config, state):
            self._send_json(400, {"error": "invalid or expired state"})
            return
        # Require the per-browser binding cookie set at /auth/login and
        # constant-time-compare it against the returned state. A missing or
        # mismatched cookie is the same login-CSRF failure as a bad state — one
        # opaque 400 either way, so nothing leaks WHICH check failed.
        binding = self._state_binding_cookie()
        if binding is None or not auth.verify_state_binding(config, state, binding):
            self._send_json(400, {"error": "invalid or expired state"})
            return
        code = (params.get("code") or [""])[0]
        if not code:
            self._send_json(400, {"error": "missing authorization code"})
            return
        try:
            access_token = auth.exchange_code(config, code)
            user = auth.fetch_discord_user(access_token)
        except Exception as exc:  # noqa: BLE001 — any Discord-side failure is a 502
            # The client response stays opaque on purpose; the CAUSE goes to
            # stdout so the host's runtime logs carry it (the 2026-07-12
            # Cloudflare-UA 403 was invisible behind this except for hours).
            print(f"discord token exchange failed: {type(exc).__name__}: {exc}")
            self._send_json(502, {"error": "discord token exchange failed"})
            return
        cookie_value = auth.make_session_value(config, str(user["id"]))
        # Set the session cookie FIRST (so a single-header reader sees it) and
        # clear the now-spent state binding cookie alongside it.
        self._redirect(
            "/",
            set_cookie=[
                self._session_cookie_header(cookie_value),
                self._state_cookie_header("", clear=True),
            ],
        )

    def _serve_logout(self) -> None:
        self._redirect("/", set_cookie=self._session_cookie_header("", clear=True))

    def _serve_me(self) -> None:
        config = self.auth_config
        writes = self.write_config.configured  # degraded-mode flag for the UI
        if not config.configured:
            self._send_json(
                200,
                {
                    "signed_in": False,
                    "auth_configured": False,
                    "writes_configured": writes,
                },
            )
            return
        user_id = self._session_user_id(config)
        if user_id is None:
            self._send_json(
                200,
                {
                    "signed_in": False,
                    "auth_configured": True,
                    "writes_configured": writes,
                },
            )
            return
        # Fourth snapshot load path: like /api/snapshot, /api/views and
        # /api/action, refuse a missing/corrupt/non-conformant snapshot with an
        # honest 503 instead of crashing on it (a valid-JSON but non-object
        # snapshot such as ``[]`` would otherwise raise AttributeError → 500).
        loaded = self._load_valid_snapshot()
        if loaded is None:
            return
        _, snapshot = loaded
        self._send_json(
            200,
            {
                "signed_in": True,
                "auth_configured": True,
                "writes_configured": writes,
                "user_id": user_id,
                "miner": self._find_miner(snapshot, user_id),
            },
        )

    def _session_user_id(self, config: auth.AuthConfig) -> str | None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:  # noqa: BLE001 — a garbage header is just "no cookie"
            return None
        morsel = cookie.get(auth.SESSION_COOKIE)
        if morsel is None or not morsel.value:
            return None
        return auth.read_session_user_id(config, morsel.value)

    def _find_miner(self, snapshot: dict, user_id: str) -> dict | None:
        """Exact string match of the Discord user id against miners[].suid.

        ``snapshot`` is the already-validated v1 payload (see ``_serve_me``): the
        v1 structural check guarantees it is an object with a ``miners`` list, so
        this lookup can never raise on a malformed snapshot.
        """
        for miner in snapshot.get("miners") or []:
            if miner.get("suid") == user_id:
                return miner
        return None

    def _session_cookie_header(self, value: str, *, clear: bool = False) -> str:
        return self._cookie_header(
            auth.SESSION_COOKIE,
            value,
            max_age=0 if clear else auth.SESSION_TTL_SECONDS,
        )

    def _state_cookie_header(self, value: str, *, clear: bool = False) -> str:
        """The per-browser OAuth-state binding cookie (login sets, callback clears)."""
        return self._cookie_header(
            auth.STATE_COOKIE,
            value,
            max_age=0 if clear else auth.STATE_TTL_SECONDS,
        )

    def _cookie_header(self, name: str, value: str, *, max_age: int) -> str:
        parts = [
            f"{name}={value}",
            "Path=/",
            "HttpOnly",
            "SameSite=Lax",
            f"Max-Age={max_age}",
        ]
        if self.auth_config.cookie_secure:
            parts.append("Secure")
        return "; ".join(parts)

    def _state_binding_cookie(self) -> str | None:
        """The per-browser OAuth-state binding cookie value, or ``None``."""
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:  # noqa: BLE001 — a garbage header is just "no cookie"
            return None
        morsel = cookie.get(auth.STATE_COOKIE)
        if morsel is None or not morsel.value:
            return None
        return morsel.value

    def _redirect(
        self, location: str, *, set_cookie: str | list[str] | None = None
    ) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        if set_cookie is not None:
            cookies = [set_cookie] if isinstance(set_cookie, str) else set_cookie
            for cookie in cookies:
                self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(
        self, status: int, body: dict, *, headers: dict[str, str] | None = None
    ) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":  # HEAD: identical headers, no body
            self.wfile.write(payload)

    def send_error(self, code, message=None, explain=None):
        """Cave-art 404 page for unknown NON-API paths — nothing else.

        ``SimpleHTTPRequestHandler`` answers missing static files via
        ``send_error(404)``; that one case gets ``web/404.html`` ("you
        dug too deep") instead of the stock error page. Every other
        status — and every ``/api/*`` route, whose JSON 404/405 bodies
        never pass through here anyway — keeps stock behavior. If the
        page itself is missing, fall back to the stock error honestly.
        """
        # path may be unset when a request fails before parsing completes
        # (e.g. an overlong request line) — those keep stock errors too.
        route, _, _ = getattr(self, "path", "").partition("?")
        if code == 404 and route and not route.startswith("/api/"):
            try:
                payload = (Path(self.directory) / "404.html").read_bytes()
            except OSError:
                payload = None
            if payload is not None:
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)
                return
        super().send_error(code, message, explain)

    def guess_type(self, path):  # noqa: A002 (http.server API name)
        """Static-file Content-Type, always WITH a charset for text.

        ``SimpleHTTPRequestHandler`` guesses ``text/html`` etc. bare; the
        frontend files are UTF-8, so every text-ish type gets an explicit
        ``charset=utf-8`` (binary types pass through untouched).
        """
        ctype = super().guess_type(path)
        if "charset=" in ctype:
            return ctype
        if ctype.startswith("text/") or ctype in (
            "application/javascript",
            "application/json",
            "application/manifest+json",
            "application/xml",
            "image/svg+xml",
        ):
            return f"{ctype}; charset=utf-8"
        return ctype

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass  # keep test output clean; stage 1 needs no access log


def make_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    snapshot_path: Path | None = None,
    web_root: Path = WEB_ROOT,
    auth_config: auth.AuthConfig | None = None,
    write_config: actions.WriteConfig | None = None,
    ingest_config: ingest.IngestConfig | None = None,
) -> ThreadingHTTPServer:
    """Build (but don't start) the server — port 0 picks a free port.

    ``snapshot_path`` defaults to :func:`snapshot_path_from_env` — the
    ``MINING_SNAPSHOT_PATH`` host env var when set, else the committed
    sample; ``auth_config`` defaults to :meth:`auth.AuthConfig.from_env`
    (the four ``DISCORD_OAUTH_*`` / ``OAUTH_REDIRECT_URI`` /
    ``WEB_SESSION_SIGNING_KEY`` host env vars); ``write_config`` defaults to
    :meth:`actions.WriteConfig.from_env` (``MINING_WRITE_ENDPOINT`` /
    ``MINING_WRITE_SHARED_SECRET``); ``ingest_config`` defaults to
    :meth:`ingest.IngestConfig.from_env`
    (``MINING_SNAPSHOT_RELAY_SHARED_SECRET`` + ``MINING_SNAPSHOT_PATH`` —
    the FLAG-1 receive seam, fail-closed when either is unset). Pass any
    explicitly in tests — an explicit argument always beats the
    environment.
    """
    handler = partial(
        MineverseHandler,
        directory=str(web_root),
        snapshot_path=snapshot_path
        if snapshot_path is not None
        else snapshot_path_from_env(),
        auth_config=auth_config if auth_config is not None else auth.AuthConfig.from_env(),
        write_config=write_config
        if write_config is not None
        else actions.WriteConfig.from_env(),
        ingest_config=ingest_config
        if ingest_config is not None
        else ingest.IngestConfig.from_env(),
    )
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    # HOST stays loopback by default (local dev, tests); a container host
    # (Railway) sets HOST=0.0.0.0 to accept external traffic (see Dockerfile).
    bind_host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = make_server(host=bind_host, port=port)
    host, bound_port = server.server_address[:2]
    mode = (
        "configured"
        if auth.AuthConfig.from_env().configured
        else "NOT configured (degraded mode — public views only)"
    )
    write_mode = (
        "configured (TEST ECONOMY)"
        if actions.WriteConfig.from_env().configured
        else "NOT configured (read-only mode)"
    )
    snapshot_mode = (
        f"live-fed ({ENV_SNAPSHOT_PATH})"
        if os.environ.get(ENV_SNAPSHOT_PATH)
        else "committed sample"
    )
    ingest_mode = (
        f"configured (POST {API_SNAPSHOT_INGEST})"
        if ingest.IngestConfig.from_env().configured
        else "NOT configured (relay push refused — fail closed)"
    )
    print(
        f"mineverse on http://{host}:{bound_port} — discord sign-in: {mode}"
        f" — writes: {write_mode} — snapshot: {snapshot_mode}"
        f" — ingest: {ingest_mode}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
