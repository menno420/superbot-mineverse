"""superbot-mineverse stage-1/2 backend — read-only, stdlib-only.

Serves, from the standard library alone (no framework, no database,
no secrets in the repo):

- ``GET /api/snapshot`` — the committed sample snapshot
  (``data/sample_snapshot.json``) as ``application/json``.  A missing or
  unreadable snapshot returns an honest ``503 {"error": "snapshot
  unavailable"}`` instead of a blank 200.
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
- Everything else — the static frontend under ``web/``.

The layering contract (docs/architecture.md): data/ -> server/ -> web/;
the frontend talks to this process only via the JSON API, and this process
never writes anything itself (signing a cookie or a proposal is not a
write path — the server holds no mutable state, no database, and no bot
credentials; mutations happen only bot-side, behind the write contract).
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
    from server import actions, auth, snapshot_validation, views
except ImportError:  # direct script execution: python3 server/app.py
    import actions  # type: ignore[no-redef]
    import auth  # type: ignore[no-redef]
    import snapshot_validation  # type: ignore[no-redef]
    import views  # type: ignore[no-redef]

LOGGER = logging.getLogger("mineverse")

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"
WEB_ROOT = REPO_ROOT / "web"

API_SNAPSHOT = "/api/snapshot"
API_VIEWS = "/api/views"
API_ME = "/api/me"
API_ACTION = "/api/action"
MAX_ACTION_BODY_BYTES = 64 * 1024
AUTH_LOGIN = "/auth/login"
AUTH_CALLBACK = "/auth/callback"
AUTH_LOGOUT = "/auth/logout"

# GET-only API routes — any other verb on these answers 405 + Allow.
GET_ONLY_API_ROUTES = frozenset({API_SNAPSHOT, API_VIEWS, API_ME})


class MineverseHandler(SimpleHTTPRequestHandler):
    """Static-file handler with the one JSON API route bolted on."""

    # Injected by make_server via functools.partial.
    snapshot_path: Path = SNAPSHOT_PATH
    auth_config: auth.AuthConfig | None = None
    write_config: actions.WriteConfig | None = None

    def __init__(
        self,
        *args,
        snapshot_path: Path | None = None,
        auth_config: auth.AuthConfig | None = None,
        write_config: actions.WriteConfig | None = None,
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
        super().__init__(*args, **kwargs)

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
        elif route == API_ACTION:
            # Known route, wrong verb: 405 + Allow, not a lying 404.
            self._send_json(405, {"error": "method not allowed"},
                            headers={"Allow": "POST"})
        elif route.startswith("/api/"):
            self._send_json(404, {"error": "unknown API route"})
        else:
            super().do_GET()

    def do_POST(self):  # noqa: N802 (http.server API name)
        route, _, _ = self.path.partition("?")
        if route == API_ACTION:
            self._serve_action()
        else:
            self._reject_unsupported_method()

    def do_PUT(self):  # noqa: N802 (http.server API name)
        self._reject_unsupported_method()

    do_DELETE = do_PUT  # noqa: N815 (http.server API names)
    do_PATCH = do_PUT  # noqa: N815

    def _reject_unsupported_method(self) -> None:
        """405 with an honest Allow header — 404 only for unknown routes.

        Everything the server exposes besides ``POST /api/action`` is
        read-only: GET (plus the HEAD that ``SimpleHTTPRequestHandler``
        derives from it for static files) is the only verb.
        """
        route, _, _ = self.path.partition("?")
        if route == API_ACTION:  # POST is handled before this is reached
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
        never sees, and relays the executor's response envelope verbatim.
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
        try:
            snapshot = json.loads(self.snapshot_path.read_bytes())
        except (OSError, ValueError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        # Ingestion-time v1 validation before we trust the snapshot's guild_id
        # for a signed write proposal — a malformed relay must not be relayed.
        if not self._snapshot_is_valid(snapshot):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
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
            status, body = actions.propose(write_config, proposal)
        except (OSError, ValueError):
            self._send_json(502, {"error": "action relay failed"})
            return
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_action_request(self) -> dict | None:
        """The browser's ``{action_id, action, params}`` — or None if bogus.

        EXACTLY those three keys: a body carrying ``suid``/``guild_id`` (or
        anything else) is rejected outright so no client input can ever
        reach the identity fields of the proposal.
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        if not 0 < length <= MAX_ACTION_BODY_BYTES:
            return None
        try:
            request = json.loads(self.rfile.read(length))
        except (OSError, ValueError):
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

    def _serve_views(self) -> None:
        """Derived read projection of the snapshot (server/views.py).

        Read-only, no state: the same snapshot ``/api/snapshot`` relays
        verbatim, shaped for the frontend's deepened views.  Missing or
        corrupt snapshot answers the same honest 503; a snapshot that is
        valid JSON but malformed beyond what the shaper tolerates answers
        an honest 500 instead of crashing the request.
        """
        try:
            snapshot = json.loads(self.snapshot_path.read_bytes())
        except (OSError, ValueError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        # Same ingestion-time v1 validation as /api/snapshot: refuse to shape a
        # snapshot that does not conform to the READ contract.
        if not self._snapshot_is_valid(snapshot):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        try:
            document = views.build_views(snapshot)
        except Exception:  # noqa: BLE001 — any shaping failure is data-shaped
            self._send_json(500, {"error": "snapshot malformed"})
            return
        self._serve_cacheable_json(json.dumps(document).encode("utf-8"))

    def _serve_snapshot(self) -> None:
        try:
            payload = self.snapshot_path.read_bytes()
            snapshot = json.loads(payload)  # never serve corrupt bytes as 200
        except (OSError, ValueError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        # Runtime v1-contract validation at ingestion: a snapshot that is valid
        # JSON but violates the READ contract (wrong version, missing/typewrong
        # fields, out-of-band values) is refused with an honest 503 — the future
        # live bot→web relay is checked here, not only the committed sample in CI.
        if not self._snapshot_is_valid(snapshot):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        self._serve_cacheable_json(payload)

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
        except Exception:  # noqa: BLE001 — any Discord-side failure is a 502
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
        try:
            snapshot = json.loads(self.snapshot_path.read_bytes())
        except (OSError, ValueError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        if not self._snapshot_is_valid(snapshot):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
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
    snapshot_path: Path = SNAPSHOT_PATH,
    web_root: Path = WEB_ROOT,
    auth_config: auth.AuthConfig | None = None,
    write_config: actions.WriteConfig | None = None,
) -> ThreadingHTTPServer:
    """Build (but don't start) the server — port 0 picks a free port.

    ``auth_config`` defaults to :meth:`auth.AuthConfig.from_env` (the four
    ``DISCORD_OAUTH_*`` / ``OAUTH_REDIRECT_URI`` / ``WEB_SESSION_SIGNING_KEY``
    host env vars); ``write_config`` defaults to
    :meth:`actions.WriteConfig.from_env` (``MINING_WRITE_ENDPOINT`` /
    ``MINING_WRITE_SHARED_SECRET``). Pass either explicitly in tests.
    """
    handler = partial(
        MineverseHandler,
        directory=str(web_root),
        snapshot_path=snapshot_path,
        auth_config=auth_config if auth_config is not None else auth.AuthConfig.from_env(),
        write_config=write_config
        if write_config is not None
        else actions.WriteConfig.from_env(),
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
    print(
        f"mineverse on http://{host}:{bound_port} — discord sign-in: {mode}"
        f" — writes: {write_mode}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
