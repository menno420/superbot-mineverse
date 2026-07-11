"""superbot-mineverse stage-1/2 backend — read-only, stdlib-only.

Serves, from the standard library alone (no framework, no database,
no secrets in the repo):

- ``GET /api/snapshot`` — the committed sample snapshot
  (``data/sample_snapshot.json``) as ``application/json``.  A missing or
  unreadable snapshot returns an honest ``503 {"error": "snapshot
  unavailable"}`` instead of a blank 200.
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

import json
import os
import urllib.parse
from functools import partial
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from server import actions, auth
except ImportError:  # direct script execution: python3 server/app.py
    import actions  # type: ignore[no-redef]
    import auth  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"
WEB_ROOT = REPO_ROOT / "web"

API_SNAPSHOT = "/api/snapshot"
API_ME = "/api/me"
API_ACTION = "/api/action"
MAX_ACTION_BODY_BYTES = 64 * 1024
AUTH_LOGIN = "/auth/login"
AUTH_CALLBACK = "/auth/callback"
AUTH_LOGOUT = "/auth/logout"


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
        elif route == API_ME:
            self._serve_me()
        elif route == AUTH_LOGIN:
            self._serve_login()
        elif route == AUTH_CALLBACK:
            self._serve_callback(query)
        elif route == AUTH_LOGOUT:
            self._serve_logout()
        elif route.startswith("/api/"):
            self._send_json(404, {"error": "unknown API route"})
        else:
            super().do_GET()

    def do_POST(self):  # noqa: N802 (http.server API name)
        route, _, _ = self.path.partition("?")
        if route == API_ACTION:
            self._serve_action()
        elif route.startswith("/api/"):
            self._send_json(404, {"error": "unknown API route"})
        else:
            self._send_json(405, {"error": "method not allowed"})

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
            guild_id = snapshot["guild_id"]
        except (OSError, ValueError, KeyError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
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

    def _serve_snapshot(self) -> None:
        try:
            payload = self.snapshot_path.read_bytes()
            json.loads(payload)  # never serve a corrupt snapshot as a 200
        except (OSError, ValueError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    # --- Discord OAuth (stage b — read personalization only) -------------

    def _serve_login(self) -> None:
        config = self.auth_config
        if not config.configured:
            self._send_json(503, {"error": "sign-in not configured"})
            return
        state = auth.make_state(config)
        self._redirect(auth.build_authorize_url(config, state))

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
        self._redirect("/", set_cookie=self._session_cookie_header(cookie_value))

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
        self._send_json(
            200,
            {
                "signed_in": True,
                "auth_configured": True,
                "writes_configured": writes,
                "user_id": user_id,
                "miner": self._find_miner(user_id),
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

    def _find_miner(self, user_id: str) -> dict | None:
        """Exact string match of the Discord user id against miners[].suid."""
        try:
            snapshot = json.loads(self.snapshot_path.read_bytes())
        except (OSError, ValueError):
            return None
        for miner in snapshot.get("miners") or []:
            if miner.get("suid") == user_id:
                return miner
        return None

    def _session_cookie_header(self, value: str, *, clear: bool = False) -> str:
        parts = [
            f"{auth.SESSION_COOKIE}={value}",
            "Path=/",
            "HttpOnly",
            "SameSite=Lax",
            f"Max-Age={0 if clear else auth.SESSION_TTL_SECONDS}",
        ]
        if self.auth_config.cookie_secure:
            parts.append("Secure")
        return "; ".join(parts)

    def _redirect(self, location: str, *, set_cookie: str | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        if set_cookie is not None:
            self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

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
    port = int(os.environ.get("PORT", "8000"))
    server = make_server(port=port)
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
