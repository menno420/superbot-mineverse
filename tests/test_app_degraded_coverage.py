"""Degraded-mode + defensive-branch coverage for the stdlib server (server/app.py).

Tests-only, ZERO production change. These pin the error/defensive arms of
``server/app.py`` that the happy-path API/auth suites never reach:

* the ``POST /api/action`` guard rail when auth is unconfigured but writes are
  (the 503 "sign-in not configured" arm);
* every malformed-body rejection inside ``_read_action_request`` (empty body,
  invalid JSON, non-object JSON, empty ``action_id``, empty ``action``,
  non-object ``params``) — each folds into the one honest 400;
* the ``_serve_views`` defense-in-depth ``except`` around ``views.build_views``
  (a structurally-valid-but-shaper-hostile snapshot → 500 "snapshot malformed");
* the "a garbage Cookie header is just no cookie" arms of ``_session_user_id``
  and ``_state_binding_cookie``;
* ``do_OPTIONS`` on a non-API path (the stock 501);
* ``guess_type``'s "already carries a charset — don't double-append" arm.

Everything runs in degraded mode over the committed sample with in-process
config objects — NO env vars, NO secrets, NO network beyond loopback — exactly
like CI (mirrors the tests/test_actions.py + tests/test_auth.py fixtures).
"""

import http.client
import json
import sys
import urllib.parse
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import actions, auth, views  # noqa: E402
from server.app import MineverseHandler  # noqa: E402

# --- shared in-process config (no env vars, no network) ----------------------

# A "configured" write relay whose endpoint is never actually hit: every test
# below that uses it is rejected inside _read_action_request (or the auth-config
# gate) BEFORE the server would sign and relay a proposal.
CONFIGURED_WRITES = actions.WriteConfig(
    endpoint="http://127.0.0.1:9/relay/mining/action", secret="test-secret-not-real"
)
UNCONFIGURED_AUTH = auth.AuthConfig(None, None, None, None)

DEEPDELVER = "100000000000000001"  # a real suid in data/sample_snapshot.json


def make_auth_config():
    return auth.AuthConfig(
        client_id="client-id-123",
        client_secret="client-secret-456",
        redirect_uri="http://127.0.0.1:8000/auth/callback",
        signing_key="test-signing-key-not-a-secret",
    )


def session_headers(config, suid):
    """A Content-Type + a VALID signed session cookie for ``suid``."""
    value = auth.make_session_value(config, suid)
    return {
        "Content-Type": "application/json",
        "Cookie": f"{auth.SESSION_COOKIE}={value}",
    }


def post(url, body: bytes, headers=None):
    parsed = urllib.parse.urlsplit(url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request("POST", parsed.path or "/", body=body, headers=headers or {})
        res = conn.getresponse()
        return res.status, json.loads(res.read())
    finally:
        conn.close()


def raw_request(url, method, path, headers=None):
    """One raw round-trip that tolerates an empty/non-JSON body (401/501/...)."""
    parsed = urllib.parse.urlsplit(url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request(method, path, headers=headers or {})
        res = conn.getresponse()
        return res.status, res.read()
    finally:
        conn.close()


# --- POST /api/action: writes configured, auth NOT → 503 (app.py 299-300) ----


def test_action_with_writes_configured_but_auth_unconfigured_is_503(serve):
    base = serve(write_config=CONFIGURED_WRITES, auth_config=UNCONFIGURED_AUTH)
    body = json.dumps(
        {"action_id": "a1", "action": "mine", "params": {}}
    ).encode()
    status, payload = post(base + "/api/action", body,
                           headers={"Content-Type": "application/json"})
    assert status == 503
    assert payload == {"error": "sign-in not configured"}


# --- _read_action_request malformed bodies → one honest 400 (app.py 375-390) -
# Reachable only past the writes+auth gates with a VALID session, so the
# rejection is the request body itself, not the degraded-mode short-circuits.


@pytest.fixture()
def signed_in_action(serve):
    """(base_url, session_headers) for a fully-configured /api/action seat."""
    auth_config = make_auth_config()
    base = serve(write_config=CONFIGURED_WRITES, auth_config=auth_config)
    return base, session_headers(auth_config, DEEPDELVER)


def test_empty_body_is_invalid_action_request(signed_in_action):
    # No body → Content-Length 0 → _read_bounded_body returns None (app.py 375-376).
    base, headers = signed_in_action
    status, payload = post(base + "/api/action", b"", headers=headers)
    assert status == 400
    assert payload == {"error": "invalid action request"}


def test_non_json_body_is_invalid_action_request(signed_in_action):
    # json.loads raises ValueError (app.py 379-380).
    base, headers = signed_in_action
    status, payload = post(base + "/api/action", b"{not valid json", headers=headers)
    assert status == 400
    assert payload == {"error": "invalid action request"}


def test_non_object_json_body_is_invalid_action_request(signed_in_action):
    # Valid JSON, but a list — not the {action_id, action, params} object (app.py 381-382).
    base, headers = signed_in_action
    status, payload = post(base + "/api/action", b"[1, 2, 3]", headers=headers)
    assert status == 400
    assert payload == {"error": "invalid action request"}


def test_empty_action_id_is_invalid_action_request(signed_in_action):
    # Right key set, but action_id is an empty string (app.py 385-386).
    base, headers = signed_in_action
    body = json.dumps({"action_id": "", "action": "mine", "params": {}}).encode()
    status, payload = post(base + "/api/action", body, headers=headers)
    assert status == 400
    assert payload == {"error": "invalid action request"}


def test_non_string_action_is_invalid_action_request(signed_in_action):
    # action must be a non-empty string; here it is empty (app.py 387-388).
    base, headers = signed_in_action
    body = json.dumps({"action_id": "a1", "action": "", "params": {}}).encode()
    status, payload = post(base + "/api/action", body, headers=headers)
    assert status == 400
    assert payload == {"error": "invalid action request"}


def test_non_object_params_is_invalid_action_request(signed_in_action):
    # params must be an object; here it is a list (app.py 389-390).
    base, headers = signed_in_action
    body = json.dumps({"action_id": "a1", "action": "mine", "params": []}).encode()
    status, payload = post(base + "/api/action", body, headers=headers)
    assert status == 400
    assert payload == {"error": "invalid action request"}


# --- _serve_views defense-in-depth around build_views (app.py 552-554) -------
# The runtime v1 validator refuses every SCHEMA-invalid snapshot at load time
# (503 "snapshot unavailable"), and the view shapers tolerate every malformed
# field a schema-VALID snapshot can carry — so no committed fixture can drive
# build_views to raise. This except is defense-in-depth for a future
# structurally-valid-but-shaper-hostile payload; we exercise it by making the
# shaper itself raise. app.py looks up ``views.build_views`` at call time, and
# the server runs in-process, so the patched attribute is what the handler runs.


def test_build_views_failure_is_a_500_snapshot_malformed(serve, monkeypatch):
    def boom(snapshot, source="sample"):
        raise RuntimeError("shaper hostile payload")

    monkeypatch.setattr(views, "build_views", boom)
    base = serve()  # default committed sample loads + validates fine
    parsed = urllib.parse.urlsplit(base)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request("GET", "/api/views")
        res = conn.getresponse()
        status = res.status
        payload = json.loads(res.read())
    finally:
        conn.close()
    assert status == 500
    assert payload == {"error": "snapshot malformed"}


# --- garbage Cookie header is just "no cookie" (app.py 763-764, 814-815) ------
# SimpleCookie.load() never raises on a *str* Cookie value (it silently skips
# unparseable morsels), so a real HTTP request cannot reach these except arms;
# they exist for a non-str header value. We drive them directly with a headers
# object whose .get returns a non-str, which is exactly what the guard tolerates.


class _NonStrHeaders:
    """A .headers stand-in whose Cookie value is a non-str (bytes)."""

    def get(self, name, default=None):
        return b"not-a-string"  # SimpleCookie.load(bytes) raises → treated as no cookie


def _bare_handler():
    handler = MineverseHandler.__new__(MineverseHandler)
    handler.headers = _NonStrHeaders()
    return handler


def test_session_user_id_treats_a_garbage_cookie_as_no_cookie():
    handler = _bare_handler()
    assert handler._session_user_id(make_auth_config()) is None


def test_state_binding_cookie_treats_a_garbage_cookie_as_none():
    handler = _bare_handler()
    assert handler._state_binding_cookie() is None


# --- do_OPTIONS on a non-API path defers to the stock 501 (app.py 233-234) ---


def test_options_on_a_static_path_is_501(serve):
    base = serve()
    status, _ = raw_request(base, "OPTIONS", "/")
    assert status == 501


# --- guess_type does not double-append a charset (app.py 884-885) ------------


def test_guess_type_passes_through_a_type_that_already_has_a_charset():
    handler = MineverseHandler.__new__(MineverseHandler)
    # super().guess_type reads self.extensions_map; a mapping that already
    # carries a charset must be returned untouched (no "; charset=utf-8" twice).
    handler.extensions_map = {".probe": "text/html; charset=utf-8"}
    assert handler.guess_type("file.probe") == "text/html; charset=utf-8"
