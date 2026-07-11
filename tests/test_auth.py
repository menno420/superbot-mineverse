"""Discord OAuth tests (stage b) — signed tokens, HTTP flow, degraded mode.

NO NETWORK EVER: the Discord token exchange and users/@me fetch are
monkeypatched; everything else is a real HTTP round-trip against the
stdlib server on an ephemeral port.
"""

import http.client
import json
import sys
import threading
import time
import urllib.parse
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import auth  # noqa: E402
from server.app import SNAPSHOT_PATH, make_server  # noqa: E402

KNOWN_SUID = "100000000000000001"  # DeepDelver in data/sample_snapshot.json
UNKNOWN_SUID = "999999999999999999"


def make_config(redirect_uri="http://127.0.0.1:8000/auth/callback"):
    return auth.AuthConfig(
        client_id="client-id-123",
        client_secret="client-secret-456",
        redirect_uri=redirect_uri,
        signing_key="test-signing-key-not-a-secret",
    )


UNCONFIGURED = auth.AuthConfig(None, None, None, None)


@pytest.fixture()
def serve():
    """Start the real server on an ephemeral port; yield a base URL factory."""
    servers = []

    def _start(**kwargs):
        server = make_server(port=0, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        host, port = server.server_address[:2]
        return f"http://{host}:{port}"

    yield _start
    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def get(url, headers=None):
    """GET without redirect-following (http.client, not urllib)."""
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request("GET", path, headers=headers or {})
        res = conn.getresponse()
        return res.status, res.headers, res.read()
    finally:
        conn.close()


def cookie_from(headers):
    set_cookie = headers.get("Set-Cookie")
    assert set_cookie, "expected a Set-Cookie header"
    return set_cookie.split(";", 1)[0]  # "name=value"


def state_binding_cookie(config, state):
    """The Cookie-header value binding a browser to ``state`` (what login sets)."""
    return f"{auth.STATE_COOKIE}={auth.make_state_binding(config, state)}"


def login(base):
    """Do /auth/login; return (state, cookie_header) for the callback round-trip."""
    _, headers, _ = get(base + "/auth/login")
    state = urllib.parse.parse_qs(
        urllib.parse.urlsplit(headers["Location"]).query
    )["state"][0]
    return state, cookie_from(headers)  # cookie_from → "mineverse_oauth_state=..."


# --- signed-token unit tests (state + cookie share the format) ------------


def test_sign_verify_round_trip():
    key = b"round-trip-key"
    payload = {"purpose": "session", "uid": KNOWN_SUID, "exp": int(time.time()) + 60}
    token = auth.sign_payload(key, payload)
    assert auth.verify_payload(key, token) == payload


def test_tampered_token_rejected():
    key = b"tamper-key"
    token = auth.sign_payload(
        key, {"purpose": "session", "uid": KNOWN_SUID, "exp": int(time.time()) + 60}
    )
    body, tag = token.split(".")
    # Forge a different uid but keep the original signature.
    forged_body = auth._b64url_encode(
        json.dumps(
            {"purpose": "session", "uid": UNKNOWN_SUID, "exp": int(time.time()) + 60},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    )
    assert auth.verify_payload(key, f"{forged_body}.{tag}") is None
    # Wrong key entirely.
    assert auth.verify_payload(b"other-key", token) is None


def test_expired_token_rejected():
    key = b"expiry-key"
    token = auth.sign_payload(
        key, {"purpose": "session", "uid": KNOWN_SUID, "exp": int(time.time()) - 1}
    )
    assert auth.verify_payload(key, token) is None


def test_malformed_tokens_rejected_cleanly():
    key = b"malformed-key"
    for bad in ("", "no-dot", "a.b.c", "!!!.???", "aGk.aGk", "e30.e30"):
        assert auth.verify_payload(key, bad) is None


def test_session_and_state_purposes_do_not_cross():
    config = make_config()
    state = auth.make_state(config)
    # A valid state token must never be accepted as a session cookie…
    assert auth.read_session_user_id(config, state) is None
    # …and a valid session cookie must never pass as a state.
    cookie = auth.make_session_value(config, KNOWN_SUID)
    assert not auth.verify_state(config, cookie)


def test_state_round_trip_and_expiry():
    config = make_config()
    assert auth.verify_state(config, auth.make_state(config))
    stale = auth.make_state(config, now=time.time() - auth.STATE_TTL_SECONDS - 5)
    assert not auth.verify_state(config, stale)


def test_session_cookie_round_trip_and_expiry():
    config = make_config()
    value = auth.make_session_value(config, KNOWN_SUID)
    assert auth.read_session_user_id(config, value) == KNOWN_SUID
    old = auth.make_session_value(
        config, KNOWN_SUID, now=time.time() - auth.SESSION_TTL_SECONDS - 5
    )
    assert auth.read_session_user_id(config, old) is None


# --- /auth/login -----------------------------------------------------------


def test_login_redirects_to_discord_with_signed_state(serve):
    config = make_config()
    status, headers, _ = get(serve(auth_config=config) + "/auth/login")
    assert status == 302
    location = headers["Location"]
    assert location.startswith(auth.DISCORD_AUTHORIZE_URL + "?")
    params = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)
    assert params["client_id"] == [config.client_id]
    assert params["redirect_uri"] == [config.redirect_uri]
    assert params["response_type"] == ["code"]
    assert params["scope"] == ["identify"]
    assert auth.verify_state(config, params["state"][0])


# --- /auth/callback ---------------------------------------------------------


def stub_discord(monkeypatch, user_id=KNOWN_SUID, calls=None):
    """Monkeypatch the two Discord HTTPS calls; record invocations."""
    calls = calls if calls is not None else []

    def fake_exchange(config, code):
        calls.append(("exchange", code))
        return "fake-access-token"

    def fake_fetch(access_token):
        calls.append(("fetch", access_token))
        return {"id": user_id, "username": "deepdelver"}

    monkeypatch.setattr(auth, "exchange_code", fake_exchange)
    monkeypatch.setattr(auth, "fetch_discord_user", fake_fetch)
    return calls


def test_full_callback_flow_sets_valid_cookie_and_me_maps_miner(
    serve, monkeypatch
):
    config = make_config()
    base = serve(auth_config=config)
    calls = stub_discord(monkeypatch)

    # 1. login hands out the state AND the per-browser binding cookie
    state, state_cookie = login(base)

    # 2. callback (carrying the binding cookie) exchanges the code and sets the
    #    signed session cookie
    query = urllib.parse.urlencode({"code": "auth-code-1", "state": state})
    status, headers, _ = get(
        base + f"/auth/callback?{query}", headers={"Cookie": state_cookie}
    )
    assert status == 302
    assert headers["Location"] == "/"
    set_cookie = headers["Set-Cookie"]
    assert set_cookie.startswith(f"{auth.SESSION_COOKIE}=")
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie
    assert "Secure" not in set_cookie  # http:// redirect URI
    assert calls == [("exchange", "auth-code-1"), ("fetch", "fake-access-token")]
    cookie_value = cookie_from(headers).split("=", 1)[1]
    assert auth.read_session_user_id(config, cookie_value) == KNOWN_SUID

    # 3. /api/me maps the cookie to the snapshot miner (exact suid match)
    status, _, body = get(base + "/api/me", headers={"Cookie": cookie_from(headers)})
    me = json.loads(body)
    assert status == 200
    assert me["signed_in"] is True
    assert me["auth_configured"] is True
    assert me["user_id"] == KNOWN_SUID
    assert me["miner"]["suid"] == KNOWN_SUID
    assert me["miner"]["display_name"] == "DeepDelver"


def test_callback_secure_flag_follows_https_redirect_uri(serve, monkeypatch):
    config = make_config(redirect_uri="https://mineverse.example/auth/callback")
    base = serve(auth_config=config)
    stub_discord(monkeypatch)
    state = auth.make_state(config)
    query = urllib.parse.urlencode({"code": "c", "state": state})
    _, headers, _ = get(
        base + f"/auth/callback?{query}",
        headers={"Cookie": state_binding_cookie(config, state)},
    )
    assert "Secure" in headers["Set-Cookie"]


def test_callback_rejects_bad_state_without_touching_discord(serve, monkeypatch):
    config = make_config()
    base = serve(auth_config=config)
    calls = stub_discord(monkeypatch)
    query = urllib.parse.urlencode({"code": "c", "state": "forged.state"})
    status, headers, body = get(base + f"/auth/callback?{query}")
    assert status == 400
    assert json.loads(body)["error"] == "invalid or expired state"
    assert headers.get("Set-Cookie") is None
    assert calls == []  # the code was never exchanged


def test_callback_rejects_expired_state(serve, monkeypatch):
    config = make_config()
    base = serve(auth_config=config)
    calls = stub_discord(monkeypatch)
    stale = auth.make_state(config, now=time.time() - auth.STATE_TTL_SECONDS - 5)
    query = urllib.parse.urlencode({"code": "c", "state": stale})
    status, _, _ = get(base + f"/auth/callback?{query}")
    assert status == 400
    assert calls == []


def test_callback_rejects_missing_code(serve, monkeypatch):
    config = make_config()
    base = serve(auth_config=config)
    stub_discord(monkeypatch)
    state = auth.make_state(config)
    query = urllib.parse.urlencode({"state": state})
    status, _, body = get(
        base + f"/auth/callback?{query}",
        headers={"Cookie": state_binding_cookie(config, state)},
    )
    assert status == 400
    assert json.loads(body)["error"] == "missing authorization code"


def test_callback_reports_discord_denial(serve):
    base = serve(auth_config=make_config())
    status, _, body = get(base + "/auth/callback?error=access_denied")
    assert status == 400
    assert "access_denied" in json.loads(body)["error"]


def test_callback_discord_failure_is_502(serve, monkeypatch):
    config = make_config()
    base = serve(auth_config=config)

    def boom(config, code):
        raise OSError("simulated discord outage")

    monkeypatch.setattr(auth, "exchange_code", boom)
    state = auth.make_state(config)
    query = urllib.parse.urlencode({"code": "c", "state": state})
    status, _, body = get(
        base + f"/auth/callback?{query}",
        headers={"Cookie": state_binding_cookie(config, state)},
    )
    assert status == 502
    assert json.loads(body)["error"] == "discord token exchange failed"


# --- login-CSRF binding (per-browser state cookie) --------------------------


def test_state_binding_round_trip_and_forgery():
    config = make_config()
    state = auth.make_state(config)
    binding = auth.make_state_binding(config, state)
    assert auth.verify_state_binding(config, state, binding)
    # A binding minted for a different state must not match this one.
    other = auth.make_state(config)
    assert not auth.verify_state_binding(config, state, auth.make_state_binding(config, other))
    # Empty / missing halves reject cleanly (never raise).
    assert not auth.verify_state_binding(config, state, "")
    assert not auth.verify_state_binding(config, "", binding)
    # Without the signing key the binding is unforgeable.
    attacker = make_config()
    attacker.signing_key = "attacker-key-not-the-server-key"
    assert not auth.verify_state_binding(config, state, auth.make_state_binding(attacker, state))


def test_login_sets_httponly_state_binding_cookie(serve):
    config = make_config()
    status, headers, _ = get(serve(auth_config=config) + "/auth/login")
    assert status == 302
    set_cookie = headers["Set-Cookie"]
    assert set_cookie.startswith(f"{auth.STATE_COOKIE}=")
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie
    assert "Secure" not in set_cookie  # http:// redirect URI → no Secure flag
    # The cookie is the binding for the exact state handed to Discord.
    state = urllib.parse.parse_qs(
        urllib.parse.urlsplit(headers["Location"]).query
    )["state"][0]
    binding = cookie_from(headers).split("=", 1)[1]
    assert auth.verify_state_binding(config, state, binding)


def test_login_state_cookie_secure_on_https_redirect_uri(serve):
    config = make_config(redirect_uri="https://mineverse.example/auth/callback")
    _, headers, _ = get(serve(auth_config=config) + "/auth/login")
    assert "Secure" in headers["Set-Cookie"]


def test_callback_rejects_missing_state_cookie(serve, monkeypatch):
    """A valid server-minted state with NO binding cookie is login-CSRF — reject."""
    config = make_config()
    base = serve(auth_config=config)
    calls = stub_discord(monkeypatch)
    state, _ = login(base)  # a genuine, unexpired, server-minted state
    query = urllib.parse.urlencode({"code": "c", "state": state})
    status, headers, body = get(base + f"/auth/callback?{query}")  # no Cookie
    assert status == 400
    assert json.loads(body)["error"] == "invalid or expired state"
    assert headers.get("Set-Cookie") is None
    assert calls == []  # Discord never touched


def test_callback_rejects_mismatched_state_cookie(serve, monkeypatch):
    """A binding cookie from a DIFFERENT login must not unlock this state."""
    config = make_config()
    base = serve(auth_config=config)
    calls = stub_discord(monkeypatch)
    state, _ = login(base)
    _, other_cookie = login(base)  # a second browser's binding cookie
    query = urllib.parse.urlencode({"code": "c", "state": state})
    status, _, body = get(base + f"/auth/callback?{query}", headers={"Cookie": other_cookie})
    assert status == 400
    assert json.loads(body)["error"] == "invalid or expired state"
    assert calls == []  # Discord never touched


def test_callback_accepts_matching_state_cookie(serve, monkeypatch):
    """Same browser: state + its binding cookie → the flow proceeds."""
    config = make_config()
    base = serve(auth_config=config)
    calls = stub_discord(monkeypatch)
    state, state_cookie = login(base)
    query = urllib.parse.urlencode({"code": "auth-code-9", "state": state})
    status, headers, _ = get(base + f"/auth/callback?{query}", headers={"Cookie": state_cookie})
    assert status == 302
    assert headers["Location"] == "/"
    assert calls == [("exchange", "auth-code-9"), ("fetch", "fake-access-token")]


def test_callback_clears_state_binding_cookie_after_use(serve, monkeypatch):
    """The spent state cookie is expired on the successful callback redirect."""
    config = make_config()
    base = serve(auth_config=config)
    stub_discord(monkeypatch)
    state, state_cookie = login(base)
    query = urllib.parse.urlencode({"code": "c", "state": state})
    status, headers, _ = get(base + f"/auth/callback?{query}", headers={"Cookie": state_cookie})
    assert status == 302
    # Two Set-Cookie headers: the session cookie AND an expired state cookie.
    set_cookies = headers.get_all("Set-Cookie")
    state_clear = [c for c in set_cookies if c.startswith(f"{auth.STATE_COOKIE}=")]
    assert state_clear, "callback must clear the state binding cookie"
    assert "Max-Age=0" in state_clear[0]


# --- /api/me ----------------------------------------------------------------


def test_me_signed_out_without_cookie(serve):
    status, _, body = get(serve(auth_config=make_config()) + "/api/me")
    assert status == 200
    assert json.loads(body) == {
        "signed_in": False,
        "auth_configured": True,
        "writes_configured": False,
    }


def test_me_rejects_tampered_cookie(serve):
    config = make_config()
    good = auth.make_session_value(config, KNOWN_SUID)
    body_part, tag = good.split(".")
    tampered = f"{body_part}.{'A' * len(tag)}"
    status, _, body = get(
        serve(auth_config=config) + "/api/me",
        headers={"Cookie": f"{auth.SESSION_COOKIE}={tampered}"},
    )
    assert status == 200
    assert json.loads(body) == {
        "signed_in": False,
        "auth_configured": True,
        "writes_configured": False,
    }


def test_me_rejects_expired_cookie(serve):
    config = make_config()
    expired = auth.make_session_value(
        config, KNOWN_SUID, now=time.time() - auth.SESSION_TTL_SECONDS - 5
    )
    _, _, body = get(
        serve(auth_config=config) + "/api/me",
        headers={"Cookie": f"{auth.SESSION_COOKIE}={expired}"},
    )
    assert json.loads(body)["signed_in"] is False


def test_me_signed_in_without_matching_miner_is_honest_null(serve):
    config = make_config()
    cookie = auth.make_session_value(config, UNKNOWN_SUID)
    _, _, body = get(
        serve(auth_config=config) + "/api/me",
        headers={"Cookie": f"{auth.SESSION_COOKIE}={cookie}"},
    )
    me = json.loads(body)
    assert me["signed_in"] is True
    assert me["user_id"] == UNKNOWN_SUID
    assert me["miner"] is None


# --- /auth/logout -----------------------------------------------------------


def test_logout_clears_cookie_and_redirects_home(serve):
    status, headers, _ = get(serve(auth_config=make_config()) + "/auth/logout")
    assert status == 302
    assert headers["Location"] == "/"
    set_cookie = headers["Set-Cookie"]
    assert set_cookie.startswith(f"{auth.SESSION_COOKIE}=;")
    assert "Max-Age=0" in set_cookie


# --- degraded mode (no env vars — CI runs exactly like this) ----------------


def test_degraded_login_is_honest_503(serve):
    status, _, body = get(serve(auth_config=UNCONFIGURED) + "/auth/login")
    assert status == 503
    assert json.loads(body)["error"] == "sign-in not configured"


def test_degraded_callback_is_honest_503(serve):
    status, _, _ = get(serve(auth_config=UNCONFIGURED) + "/auth/callback?code=x")
    assert status == 503


def test_degraded_me_reports_auth_not_configured(serve):
    status, _, body = get(serve(auth_config=UNCONFIGURED) + "/api/me")
    assert status == 200
    assert json.loads(body) == {
        "signed_in": False,
        "auth_configured": False,
        "writes_configured": False,
    }


def test_degraded_mode_still_serves_snapshot_and_frontend(serve):
    base = serve(auth_config=UNCONFIGURED)
    status, headers, body = get(base + "/api/snapshot")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    assert body == SNAPSHOT_PATH.read_bytes()
    status, _, body = get(base + "/")
    assert status == 200
    assert b"app.js" in body


def test_config_from_env_reads_exactly_the_documented_names():
    env = {
        "DISCORD_OAUTH_CLIENT_ID": "cid",
        "DISCORD_OAUTH_CLIENT_SECRET": "csecret",
        "OAUTH_REDIRECT_URI": "https://example.test/auth/callback",
        "WEB_SESSION_SIGNING_KEY": "k",
    }
    config = auth.AuthConfig.from_env(env)
    assert config.configured
    assert config.cookie_secure
    for missing in env:
        partial_env = {k: v for k, v in env.items() if k != missing}
        assert not auth.AuthConfig.from_env(partial_env).configured, missing
