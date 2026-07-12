"""Discord OAuth2 sign-in (identify scope only) — stdlib-only helpers.

Everything here supports READ personalization and nothing else: a signed
cookie proves "this browser belongs to Discord user <id>" so the frontend
can highlight that user's miner. There are no write paths, no database,
no bot token — see docs/auth.md for the threat notes.

Configuration comes from HOST environment variables ONLY (never files,
never the repo):

- ``DISCORD_OAUTH_CLIENT_ID``     — Discord application client id
- ``DISCORD_OAUTH_CLIENT_SECRET`` — Discord application client secret
- ``OAUTH_REDIRECT_URI``          — the /auth/callback URL registered with
  Discord (its scheme also decides the cookie ``Secure`` flag)
- ``WEB_SESSION_SIGNING_KEY``     — HMAC-SHA256 key for state + cookie

With any of them absent the app runs in DEGRADED MODE: every public
snapshot view works exactly as before, ``/api/me`` reports
``auth_configured: false``, and ``/auth/login`` answers an honest 503.

Signed-token format (used for both the CSRF ``state`` and the session
cookie): ``base64url(json payload) + "." + base64url(hmac_sha256 tag)``.
Payloads carry an ``exp`` unix timestamp; verification is constant-time
(:func:`hmac.compare_digest`) and rejects expired or tampered tokens by
returning ``None`` — never by raising.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request

DISCORD_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_ME_URL = "https://discord.com/api/users/@me"

ENV_CLIENT_ID = "DISCORD_OAUTH_CLIENT_ID"
ENV_CLIENT_SECRET = "DISCORD_OAUTH_CLIENT_SECRET"
ENV_REDIRECT_URI = "OAUTH_REDIRECT_URI"
ENV_SIGNING_KEY = "WEB_SESSION_SIGNING_KEY"

SESSION_COOKIE = "mineverse_session"
STATE_COOKIE = "mineverse_oauth_state"  # per-browser CSRF binding for the login round-trip
STATE_TTL_SECONDS = 10 * 60  # login round-trip budget
SESSION_TTL_SECONDS = 7 * 24 * 3600  # one week of read personalization
HTTP_TIMEOUT_SECONDS = 10

# discord.com sits behind Cloudflare, which rejects urllib's default
# User-Agent ("Python-urllib/3.x") with a 403 — live-verified 2026-07-12
# (same endpoint: curl UA -> 200, python-urllib UA -> 403; the token
# exchange failed in production with a valid client id + secret). Every
# Discord request must carry a real UA.
HTTP_USER_AGENT = "mineverse-web/1.0 (+https://github.com/menno420/superbot-mineverse)"


class AuthConfig:
    """OAuth configuration snapshot. Values may be ``None`` (degraded mode)."""

    def __init__(
        self,
        client_id: str | None,
        client_secret: str | None,
        redirect_uri: str | None,
        signing_key: str | None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.signing_key = signing_key

    @classmethod
    def from_env(cls, environ=os.environ) -> "AuthConfig":
        return cls(
            client_id=environ.get(ENV_CLIENT_ID) or None,
            client_secret=environ.get(ENV_CLIENT_SECRET) or None,
            redirect_uri=environ.get(ENV_REDIRECT_URI) or None,
            signing_key=environ.get(ENV_SIGNING_KEY) or None,
        )

    @property
    def configured(self) -> bool:
        return all(
            (self.client_id, self.client_secret, self.redirect_uri, self.signing_key)
        )

    @property
    def cookie_secure(self) -> bool:
        """``Secure`` cookie flag: on exactly when the redirect URI is https."""
        return bool(self.redirect_uri) and self.redirect_uri.lower().startswith(
            "https://"
        )

    @property
    def key(self) -> bytes:
        if not self.signing_key:
            raise ValueError("auth is not configured (no signing key)")
        return self.signing_key.encode("utf-8")


# --- signed tokens (state + session cookie share one format) --------------


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _mac(key: bytes, message: bytes) -> bytes:
    return hmac.new(key, message, hashlib.sha256).digest()


def sign_payload(key: bytes, payload: dict) -> str:
    """Serialize + HMAC-SHA256-sign ``payload`` into a compact token."""
    body = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    tag = _b64url_encode(_mac(key, body.encode("ascii")))
    return f"{body}.{tag}"


def verify_payload(key: bytes, token: str, *, now: float | None = None) -> dict | None:
    """Return the payload iff signature valid and not expired, else ``None``.

    Constant-time signature comparison; any malformation (wrong shape, bad
    base64, bad JSON, missing/passed ``exp``) rejects cleanly.
    """
    if not isinstance(token, str) or token.count(".") != 1:
        return None
    body, tag = token.split(".", 1)
    try:
        expected = _mac(key, body.encode("ascii"))
        provided = _b64url_decode(tag)
    except (binascii.Error, ValueError, UnicodeEncodeError):
        return None
    if not hmac.compare_digest(expected, provided):
        return None
    try:
        payload = json.loads(_b64url_decode(body))
    except (binascii.Error, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        return None
    if (time.time() if now is None else now) >= exp:
        return None
    return payload


# --- CSRF state ------------------------------------------------------------


def make_state(config: AuthConfig, *, now: float | None = None) -> str:
    """A signed, expiring, single-purpose CSRF token (no server-side store)."""
    issued = time.time() if now is None else now
    return sign_payload(
        config.key,
        {
            "purpose": "oauth-state",
            "nonce": secrets.token_urlsafe(16),
            "exp": int(issued) + STATE_TTL_SECONDS,
        },
    )


def verify_state(config: AuthConfig, token: str, *, now: float | None = None) -> bool:
    payload = verify_payload(config.key, token, now=now)
    return payload is not None and payload.get("purpose") == "oauth-state"


# --- per-browser CSRF binding (login sets it, callback requires it) ---------
#
# The signed ``state`` above proves the token was minted by THIS server and is
# unexpired — but nothing binds it to the browser that started the flow, so any
# server-minted token works from any browser within its TTL (login-CSRF). The
# binding below closes that: ``/auth/login`` drops a cookie carrying a keyed MAC
# of the very state it hands to Discord, and ``/auth/callback`` recomputes that
# MAC from the returned state and constant-time-compares it to the cookie. An
# attacker cannot forge the cookie (it needs the signing key) and cannot read a
# victim's HttpOnly cookie, so a state pasted into a different browser fails the
# compare. Stateless — no server-side store, same as the signed state itself.


def make_state_binding(config: AuthConfig, state: str) -> str:
    """The login-cookie value binding a browser to its ``state`` (keyed MAC).

    Unforgeable without ``config.key``; carries no secret of its own, so it is
    safe to hand to the browser. Expiry is enforced by the state's own ``exp``
    (``verify_state``) and the cookie's ``Max-Age``.
    """
    return _b64url_encode(_mac(config.key, b"oauth-state-binding:" + state.encode("utf-8")))


def verify_state_binding(config: AuthConfig, state: str, cookie_value: str) -> bool:
    """Constant-time check that ``cookie_value`` is the binding for ``state``.

    Rejects a missing/empty state or cookie outright; otherwise compares the
    recomputed binding against the cookie with :func:`hmac.compare_digest`.
    """
    if not state or not cookie_value:
        return False
    return hmac.compare_digest(make_state_binding(config, state), cookie_value)


# --- session cookie ---------------------------------------------------------


def make_session_value(
    config: AuthConfig, user_id: str, *, now: float | None = None
) -> str:
    """Signed cookie payload: Discord user id + issued/expiry timestamps."""
    issued = int(time.time() if now is None else now)
    return sign_payload(
        config.key,
        {
            "purpose": "session",
            "uid": str(user_id),
            "iat": issued,
            "exp": issued + SESSION_TTL_SECONDS,
        },
    )


def read_session_user_id(
    config: AuthConfig, cookie_value: str, *, now: float | None = None
) -> str | None:
    """The verified Discord user id in the cookie, or ``None``."""
    payload = verify_payload(config.key, cookie_value, now=now)
    if payload is None or payload.get("purpose") != "session":
        return None
    uid = payload.get("uid")
    return uid if isinstance(uid, str) and uid else None


# --- Discord HTTPS calls (tests monkeypatch these — no network in CI) ------


def build_authorize_url(config: AuthConfig, state: str) -> str:
    query = urllib.parse.urlencode(
        {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": "identify",
            "state": state,
        }
    )
    return f"{DISCORD_AUTHORIZE_URL}?{query}"


def exchange_code(config: AuthConfig, code: str) -> str:
    """Authorization-code -> access-token exchange. Returns the access token."""
    form = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.redirect_uri,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        }
    ).encode("ascii")
    request = urllib.request.Request(
        DISCORD_TOKEN_URL,
        data=form,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": HTTP_USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        token = json.loads(response.read()).get("access_token")
    if not token:
        raise ValueError("discord token response carried no access_token")
    return token


def fetch_discord_user(access_token: str) -> dict:
    """``GET /api/users/@me`` with the bearer token; returns the user object."""
    request = urllib.request.Request(
        DISCORD_ME_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": HTTP_USER_AGENT,
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        user = json.loads(response.read())
    if not isinstance(user, dict) or not user.get("id"):
        raise ValueError("discord users/@me response carried no id")
    return user
