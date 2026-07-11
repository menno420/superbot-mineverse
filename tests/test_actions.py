"""WRITE contract v1 end-to-end tests (stage c) — shim conformance, signing,
idempotent replay, allowlist, degraded mode.

NO NETWORK beyond loopback, NO env vars, NO secrets: everything runs
against the dev/test bot shim (tests/shim/shim_bot.py) and the real web
server on ephemeral ports, exactly like CI. Every shim response is
validated against schemas/mining_action_response.v1.schema.json and every
proposal the tests craft against schemas/mining_action.v1.schema.json, so
the shim IS the executable form of docs/mining-write-contract.md.

Opt-in conformance seam (docs/live-prod-cutover.md §1): setting
SHIM_CONFORMANCE_BASE_URL points the ``shim`` fixture — and therefore the
same contract fixtures — at an EXTERNAL executor (the real bot-side
endpoint) instead of the in-process shim, signing with
MINING_WRITE_SHARED_SECRET (override: SHIM_CONFORMANCE_SECRET). With the
env vars unset — the default, and the only mode CI ever runs — nothing in
this file reads the network beyond loopback or any env var.
"""

import http.client
import json
import os
import sys
import threading
import time
import urllib.parse
import uuid
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import actions, auth  # noqa: E402
from server.app import make_server  # noqa: E402
from tests.shim.shim_bot import (  # noqa: E402
    ACTION_PATH,
    PLACEHOLDER_ACTION_ID,
    make_shim_server,
)

# --- conformance seam (opt-in, docs/live-prod-cutover.md §1) -----------------
#
# Default (env vars unset — CI, fresh clones): everything in this file runs
# against the in-process shim on loopback, hermetically, exactly as before.
#
# Set SHIM_CONFORMANCE_BASE_URL (scheme://host[:port] — the tests append
# /relay/mining/action themselves) and the ``shim`` fixture yields that
# EXTERNAL executor instead, so the same contract fixtures exercise the real
# bot-side endpoint. The signing secret then comes from
# MINING_WRITE_SHARED_SECRET (the contract's canonical env name,
# server/actions.py ENV_SECRET) or its override SHIM_CONFORMANCE_SECRET —
# for when the shell already carries a web-host secret that differs from the
# conformance target's. Secret VALUES are never printed anywhere.
CONFORMANCE_BASE_URL = (
    os.environ.get("SHIM_CONFORMANCE_BASE_URL") or ""
).rstrip("/") or None
CONFORMANCE_MODE = CONFORMANCE_BASE_URL is not None
_CONFORMANCE_SECRET = (
    os.environ.get("SHIM_CONFORMANCE_SECRET")
    or os.environ.get(actions.ENV_SECRET)
    or None
)
if CONFORMANCE_MODE and _CONFORMANCE_SECRET is None:
    pytest.exit(
        "SHIM_CONFORMANCE_BASE_URL is set but no signing secret is available:"
        " export MINING_WRITE_SHARED_SECRET (or SHIM_CONFORMANCE_SECRET) with"
        " the conformance target's test-guild secret",
        returncode=4,
    )

TEST_SECRET = (
    _CONFORMANCE_SECRET if CONFORMANCE_MODE else "shim-test-secret-not-a-secret"
)
TEST_GUILD_ID = "987654321098765432"  # the committed sample snapshot's guild
DEEPDELVER = "100000000000000001"  # depth 3, 41 energy, 18450 coins
PEBBLEPICKER = "100000000000000004"  # depth 0 — ascend must be vetoed
UNKNOWN_SUID = "999999999999999999"

ACTION_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "mining_action.v1.schema.json").read_text()
)
RESPONSE_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "mining_action_response.v1.schema.json").read_text()
)
ACTION_VALIDATOR = Draft202012Validator(ACTION_SCHEMA, format_checker=FormatChecker())
RESPONSE_VALIDATOR = Draft202012Validator(
    RESPONSE_SCHEMA, format_checker=FormatChecker()
)

_uuid_counter = iter(range(1, 10_000))


def new_action_id():
    if CONFORMANCE_MODE:
        # A real executor retains idempotency keys for ≥24 h ACROSS runs
        # (contract § "Idempotency") — the deterministic counter below would
        # replay yesterday's sweep as `replayed_action` 409s. Random per run.
        return str(uuid.uuid4())
    return f"00000000-0000-4000-8000-{next(_uuid_counter):012d}"


def make_proposal(action, params, *, suid=DEEPDELVER, guild_id=TEST_GUILD_ID,
                  action_id=None):
    return {
        "contract_version": "1",
        "action_id": action_id or new_action_id(),
        "guild_id": guild_id,
        "suid": suid,
        "action": action,
        "params": params,
    }


def assert_response_conforms(payload):
    errors = sorted(
        RESPONSE_VALIDATOR.iter_errors(payload), key=lambda e: list(e.path)
    )
    details = "\n".join(f"- {e.message}" for e in errors)
    assert not errors, f"shim response violates the v1 contract:\n{details}"


@pytest.fixture()
def shim():
    """Yields (state, base_url) — the in-process shim on an ephemeral port.

    In conformance mode (SHIM_CONFORMANCE_BASE_URL set) it yields
    (None, <external base URL>) instead: same fixtures, real executor.
    Tests guard their in-memory assertions on ``state is not None``.
    """
    if CONFORMANCE_MODE:
        yield None, CONFORMANCE_BASE_URL
        return
    server, state = make_shim_server(port=0, secret=TEST_SECRET)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    yield state, f"http://{host}:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


@pytest.fixture()
def serve():
    """The real web server on an ephemeral port; yields a base URL factory."""
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


def post(url, body: bytes, headers=None):
    parsed = urllib.parse.urlsplit(url)
    conn_cls = (
        http.client.HTTPSConnection
        if parsed.scheme == "https"  # an https conformance target
        else http.client.HTTPConnection
    )
    conn = conn_cls(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request("POST", parsed.path or "/", body=body, headers=headers or {})
        res = conn.getresponse()
        return res.status, json.loads(res.read())
    finally:
        conn.close()


def signed_post(base_url, body: bytes, *, secret=TEST_SECRET, timestamp=None,
                signature=None):
    ts = timestamp if timestamp is not None else str(int(time.time()))
    sig = signature if signature is not None else actions.sign(
        secret, "POST", ACTION_PATH, ts, body
    )
    return post(
        base_url + ACTION_PATH,
        body,
        headers={
            "Content-Type": "application/json",
            actions.HEADER_TIMESTAMP: ts,
            actions.HEADER_SIGNATURE: sig,
        },
    )


def send(shim_base, proposal, **kwargs):
    """Sign + POST a proposal; every response is contract-validated."""
    body = json.dumps(proposal, separators=(",", ":"), sort_keys=True).encode()
    status, payload = signed_post(shim_base, body, **kwargs)
    assert_response_conforms(payload)
    return status, payload


# --- signing helpers (server/actions.py is the canonical implementation) ---


def test_sign_verify_round_trip():
    body = b'{"hello":"world"}'
    ts = str(int(time.time()))
    sig = actions.sign(TEST_SECRET, "POST", ACTION_PATH, ts, body)
    assert actions.verify(TEST_SECRET, "POST", ACTION_PATH, ts, body, sig) is None


def test_verify_rejects_bad_signatures():
    body = b"{}"
    ts = str(int(time.time()))
    sig = actions.sign(TEST_SECRET, "POST", ACTION_PATH, ts, body)
    cases = [
        ("", "empty"),
        ("deadbeef", "wrong"),
        (actions.sign("other-secret", "POST", ACTION_PATH, ts, body), "wrong key"),
        (actions.sign(TEST_SECRET, "POST", "/other/path", ts, body), "wrong path"),
        (actions.sign(TEST_SECRET, "POST", ACTION_PATH, ts, b"{ }"), "wrong body"),
    ]
    for bad, label in cases:
        assert actions.verify(
            TEST_SECRET, "POST", ACTION_PATH, ts, body, bad
        ) == "invalid_signature", label
    # A tampered timestamp breaks the signature (it is signed).
    assert actions.verify(
        TEST_SECRET, "POST", ACTION_PATH, str(int(ts) + 1), body, sig
    ) == "invalid_signature"


def test_verify_rejects_stale_timestamps():
    body = b"{}"
    for offset in (-actions.SKEW_SECONDS - 60, actions.SKEW_SECONDS + 60):
        ts = str(int(time.time()) + offset)
        sig = actions.sign(TEST_SECRET, "POST", ACTION_PATH, ts, body)
        assert actions.verify(
            TEST_SECRET, "POST", ACTION_PATH, ts, body, sig
        ) == "stale_timestamp", offset


def test_write_config_reads_exactly_the_documented_env_names():
    env = {
        "MINING_WRITE_ENDPOINT": "http://127.0.0.1:8100/relay/mining/action",
        "MINING_WRITE_SHARED_SECRET": "k",
    }
    assert actions.WriteConfig.from_env(env).configured
    for missing in env:
        partial_env = {k: v for k, v in env.items() if k != missing}
        assert not actions.WriteConfig.from_env(partial_env).configured, missing


# --- shim conformance: every enum action executes deterministically --------


def test_mine_accepted_with_ore_energy_xp_transition(shim):
    state, base = shim
    proposal = make_proposal("mine", {})
    assert not list(ACTION_VALIDATOR.iter_errors(proposal))
    status, payload = send(base, proposal)
    assert status == 200
    assert payload["status"] == "accepted"
    assert payload["reason_code"] == "ok"
    assert payload["replayed"] is False
    delta = payload["result"]["state_delta"]
    assert delta["mining_inventory"]["diamond"] == 10  # depth 3 → diamond, 9+1
    assert delta["energy"]["current"] == 40  # 41 - 1
    assert delta["xp"]["game_total"] == 6245  # 6240 + 5


def test_descend_and_ascend_move_depth_bands(shim):
    state, base = shim
    # SilverSeeker sits at depth 2: descend → 3 (a new record), ascend → 2.
    suid = "100000000000000002"
    status, payload = send(base, make_proposal("descend", {}, suid=suid))
    assert status == 200
    assert payload["result"]["state_delta"] == {"depth": 3, "record_depth": 3}
    status, payload = send(base, make_proposal("ascend", {}, suid=suid))
    assert status == 200
    assert payload["result"]["state_delta"] == {"depth": 2}


def test_sell_moves_inventory_to_coins(shim):
    state, base = shim
    status, payload = send(
        base, make_proposal("sell", {"item": "iron", "quantity": 3})
    )
    assert status == 200
    delta = payload["result"]["state_delta"]
    assert delta["coins"] == 18450 + 30  # 3 × flat price 10
    assert delta["mining_inventory"]["iron"] == 60  # 63 - 3


def test_vault_deposit_and_withdraw_move_coins(shim):
    state, base = shim
    status, payload = send(base, make_proposal("vault_deposit", {"amount": 500}))
    assert status == 200
    delta = payload["result"]["state_delta"]
    if state is not None:  # absolute coin totals assume the per-test-fresh
        assert delta["coins"] == 17950  # snapshot (earlier sweep tests sell)
    assert delta["vault"]["coins"] == 500  # only this test touches the vault
    coins_after_deposit = delta["coins"]
    status, payload = send(base, make_proposal("vault_withdraw", {"amount": 200}))
    assert status == 200
    delta = payload["result"]["state_delta"]
    assert delta["coins"] == coins_after_deposit + 200
    assert delta["vault"]["coins"] == 300


def test_equip_flips_the_gear_slot(shim):
    state, base = shim
    status, payload = send(
        base, make_proposal("equip", {"item": "iron helmet", "slot": "helmet"})
    )
    assert status == 200
    assert payload["result"]["state_delta"]["equipment"]["helmet"] == "iron helmet"


def test_economy_rejections_are_422(shim):
    state, base = shim
    # Ascending from the surface, selling what you don't carry.
    status, payload = send(base, make_proposal("ascend", {}, suid=PEBBLEPICKER))
    assert status == 422
    assert payload["reason_code"] == "economy_rejection"
    status, payload = send(
        base, make_proposal("sell", {"item": "diamond", "quantity": 999})
    )
    assert status == 422
    assert payload["reason_code"] == "economy_rejection"


# --- conformance vs the REAL endpoint (opt-in via SHIM_CONFORMANCE_BASE_URL) --


@pytest.mark.skipif(
    not CONFORMANCE_MODE,
    reason="SHIM_CONFORMANCE_BASE_URL not set; conformance-vs-real-endpoint "
    "run skipped (hermetic CI default)",
)
def test_conformance_target_is_reachable_and_speaks_v1(shim):
    """Reachability smoke for the EXTERNAL executor: one UNSIGNED probe must
    draw the contract's pre-auth rejection — signature-first verification
    means it can never execute anything and is never audited (the same
    handshake as ``scripts/readiness_check.py --probe``)."""
    state, base = shim
    assert state is None  # the fixture handed us the external target
    status, payload = post(
        base + ACTION_PATH, b"{}", headers={"Content-Type": "application/json"}
    )
    assert status == 401
    assert payload["reason_code"] == "invalid_signature"
    assert_response_conforms(payload)


# --- transport auth against the shim ----------------------------------------


def test_shim_rejects_bad_signature(shim):
    state, base = shim
    body = json.dumps(make_proposal("mine", {})).encode()
    status, payload = signed_post(base, body, signature="0" * 64)
    assert status == 401
    assert payload["reason_code"] == "invalid_signature"
    assert_response_conforms(payload)
    if state is not None:  # in-memory evidence — in-process shim only
        assert state.audit_log == []  # unattributable — never audited


def test_shim_rejects_wrong_secret(shim):
    state, base = shim
    body = json.dumps(make_proposal("mine", {})).encode()
    status, payload = signed_post(base, body, secret="some-other-secret")
    assert status == 401
    assert payload["reason_code"] == "invalid_signature"


def test_shim_rejects_stale_timestamp(shim):
    state, base = shim
    body = json.dumps(make_proposal("mine", {})).encode()
    stale = str(int(time.time()) - actions.SKEW_SECONDS - 60)
    status, payload = signed_post(base, body, timestamp=stale)
    assert status == 401
    assert payload["reason_code"] == "stale_timestamp"
    assert_response_conforms(payload)


# --- schema enforcement against the shim -------------------------------------


def test_shim_rejects_malformed_json_body(shim):
    state, base = shim
    status, payload = signed_post(base, b"{not json")
    assert status == 400
    assert payload["reason_code"] == "malformed_request"
    assert payload["action_id"] == PLACEHOLDER_ACTION_ID
    assert_response_conforms(payload)


def test_shim_rejects_unknown_action(shim):
    state, base = shim
    status, payload = send(base, make_proposal("sell_all", {}))
    assert status == 400
    assert payload["reason_code"] == "unknown_action"


def test_shim_rejects_invalid_params(shim):
    state, base = shim
    status, payload = send(base, make_proposal("sell", {"item": "iron"}))
    assert status == 400
    assert payload["reason_code"] == "invalid_params"


def test_shim_rejects_unsupported_contract_version(shim):
    state, base = shim
    proposal = make_proposal("mine", {})
    proposal["contract_version"] = "2"
    status, payload = send(base, proposal)
    assert status == 400
    assert payload["reason_code"] == "unsupported_contract_version"


# --- test-guild allowlist + actor lookup -------------------------------------


def test_shim_rejects_guild_off_the_allowlist(shim):
    state, base = shim
    status, payload = send(
        base, make_proposal("mine", {}, guild_id="111111111111111111")
    )
    assert status == 403
    assert payload["reason_code"] == "guild_not_allowed"
    if state is not None:  # in-memory evidence — in-process shim only
        assert state.audit_log[-1]["outcome"] == "rejected:guild_not_allowed"


def test_shim_rejects_unknown_actor(shim):
    state, base = shim
    status, payload = send(base, make_proposal("mine", {}, suid=UNKNOWN_SUID))
    assert status == 404
    assert payload["reason_code"] == "actor_not_found"


# --- idempotent replay --------------------------------------------------------


def test_replay_returns_original_response_without_reexecuting(shim):
    state, base = shim
    action_id = new_action_id()
    proposal = make_proposal("mine", {}, action_id=action_id)
    status_1, first = send(base, proposal)
    status_2, second = send(base, proposal)  # byte-identical replay
    assert (status_1, status_2) == (200, 200)
    assert first["replayed"] is False
    assert second["replayed"] is True
    stripped = dict(second)
    stripped["replayed"] = False
    assert stripped == first  # the ORIGINAL response, verbatim
    if state is not None:  # in-memory evidence — in-process shim only
        # Executed exactly once: energy dropped 41 → 40, not 39; one audit row.
        miner = state.snapshot["miners"][0]
        assert miner["energy"]["current"] == 40
        assert len(state.audit_log) == 1


def test_action_id_reuse_with_different_body_is_409(shim):
    state, base = shim
    action_id = new_action_id()
    send(base, make_proposal("mine", {}, action_id=action_id))
    status, payload = send(base, make_proposal("descend", {}, action_id=action_id))
    assert status == 409
    assert payload["reason_code"] == "replayed_action"
    if state is not None:  # in-memory evidence — in-process shim only
        assert state.audit_log[-1]["outcome"] == "rejected:replayed_action"
    # And the original response is still intact for a genuine replay.
    status, payload = send(base, make_proposal("mine", {}, action_id=action_id))
    assert status == 200
    assert payload["replayed"] is True


def test_rejected_outcomes_replay_too(shim):
    state, base = shim
    action_id = new_action_id()
    proposal = make_proposal("ascend", {}, suid=PEBBLEPICKER, action_id=action_id)
    status_1, first = send(base, proposal)
    status_2, second = send(base, proposal)
    assert (status_1, status_2) == (422, 422)
    assert second["replayed"] is True
    if state is not None:  # in-memory evidence — in-process shim only
        assert len(state.audit_log) == 1  # the replay was not re-audited


# --- the audit log -------------------------------------------------------------


@pytest.mark.skipif(
    CONFORMANCE_MODE,
    reason="audit rows live in the in-process shim's memory; against the real"
    " endpoint, audit verification is the cutover checklist's manual step"
    " (docs/live-prod-cutover.md §1)",
)
def test_every_authenticated_action_is_audited_with_the_contract_fields(shim):
    state, base = shim
    proposal = make_proposal("sell", {"item": "gold", "quantity": 2})
    send(base, proposal)
    assert len(state.audit_log) == 1
    entry = state.audit_log[0]
    assert entry["action_id"] == proposal["action_id"]
    assert entry["action"] == "sell"
    assert entry["suid"] == DEEPDELVER
    assert entry["guild_id"] == TEST_GUILD_ID
    assert entry["outcome"] == "accepted:ok"
    assert entry["contract_version"] == "1"
    assert entry["origin"] == "web"
    assert len(entry["params_digest"]) == 64  # sha256 hex of the params
    assert entry["timestamp"].endswith("Z")


# --- degraded mode (no env vars — CI runs exactly like this) -------------------


UNCONFIGURED_WRITES = actions.WriteConfig(None, None)
UNCONFIGURED_AUTH = auth.AuthConfig(None, None, None, None)


def make_auth_config():
    return auth.AuthConfig(
        client_id="client-id-123",
        client_secret="client-secret-456",
        redirect_uri="http://127.0.0.1:8000/auth/callback",
        signing_key="test-signing-key-not-a-secret",
    )


def session_headers(config, suid):
    value = auth.make_session_value(config, suid)
    return {
        "Content-Type": "application/json",
        "Cookie": f"{auth.SESSION_COOKIE}={value}",
    }


def browser_body(action, params, **extra):
    request = {"action_id": new_action_id(), "action": action, "params": params}
    request.update(extra)
    return json.dumps(request).encode()


def test_degraded_action_endpoint_is_honest_503(serve):
    base = serve(write_config=UNCONFIGURED_WRITES, auth_config=make_auth_config())
    status, payload = post(base + "/api/action", browser_body("mine", {}))
    assert status == 503
    assert payload == {"error": "writes not configured"}


def test_degraded_me_reports_writes_not_configured(serve):
    base = serve(write_config=UNCONFIGURED_WRITES, auth_config=UNCONFIGURED_AUTH)
    conn_status, payload = post(base + "/api/action", browser_body("mine", {}))
    assert conn_status == 503
    parsed = urllib.parse.urlsplit(base)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request("GET", "/api/me")
        res = conn.getresponse()
        me = json.loads(res.read())
    finally:
        conn.close()
    assert me["writes_configured"] is False


# --- the enabled path, end to end: browser → web server → shim ------------------


@pytest.fixture()
def stack(shim, serve):
    """Shim + web server wired together with matching secrets."""
    state, shim_base = shim
    auth_config = make_auth_config()
    write_config = actions.WriteConfig(
        endpoint=shim_base + ACTION_PATH, secret=TEST_SECRET
    )
    base = serve(auth_config=auth_config, write_config=write_config)
    return state, base, auth_config


def test_signed_in_mine_end_to_end(stack):
    state, base, auth_config = stack
    status, payload = post(
        base + "/api/action",
        browser_body("mine", {}),
        headers=session_headers(auth_config, DEEPDELVER),
    )
    assert status == 200
    assert_response_conforms(payload)
    assert payload["status"] == "accepted"
    delta = payload["result"]["state_delta"]
    assert set(delta) == {"mining_inventory", "energy", "xp"}  # a mine delta
    if state is not None:  # per-test-fresh snapshot → absolute energy holds,
        assert delta["energy"]["current"] == 40  # 41 - 1
        # The suid on the audit row came from the VERIFIED cookie, server-side.
        assert state.audit_log[-1]["suid"] == DEEPDELVER


def test_me_reports_writes_configured_on_the_enabled_stack(stack):
    state, base, auth_config = stack
    parsed = urllib.parse.urlsplit(base)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request("GET", "/api/me")
        me = json.loads(conn.getresponse().read())
    finally:
        conn.close()
    assert me["writes_configured"] is True


def test_action_requires_a_signed_in_session(stack):
    state, base, _ = stack
    status, payload = post(base + "/api/action", browser_body("mine", {}))
    assert status == 401
    assert payload == {"error": "sign-in required"}
    if state is not None:  # in-memory evidence — in-process shim only
        assert state.audit_log == []  # nothing ever reached the shim


def test_browser_cannot_assert_suid_or_guild(stack):
    state, base, auth_config = stack
    for extra in ({"suid": UNKNOWN_SUID}, {"guild_id": "111111111111111111"}):
        status, payload = post(
            base + "/api/action",
            browser_body("mine", {}, **extra),
            headers=session_headers(auth_config, DEEPDELVER),
        )
        assert status == 400, extra
        assert payload == {"error": "invalid action request"}
    if state is not None:  # in-memory evidence — in-process shim only
        assert state.audit_log == []


def test_contract_rejections_relay_verbatim(stack):
    state, base, auth_config = stack
    status, payload = post(
        base + "/api/action",
        browser_body("sell", {"item": "diamond", "quantity": 999}),
        headers=session_headers(auth_config, DEEPDELVER),
    )
    assert status == 422
    assert_response_conforms(payload)
    assert payload["reason_code"] == "economy_rejection"


def test_signed_in_but_unknown_miner_is_actor_not_found(stack):
    state, base, auth_config = stack
    status, payload = post(
        base + "/api/action",
        browser_body("mine", {}),
        headers=session_headers(auth_config, UNKNOWN_SUID),
    )
    assert status == 404
    assert payload["reason_code"] == "actor_not_found"


def test_unreachable_executor_is_honest_502(serve):
    auth_config = make_auth_config()
    dead = actions.WriteConfig(
        endpoint="http://127.0.0.1:9/relay/mining/action", secret=TEST_SECRET
    )
    base = serve(auth_config=auth_config, write_config=dead)
    status, payload = post(
        base + "/api/action",
        browser_body("mine", {}),
        headers=session_headers(auth_config, DEEPDELVER),
    )
    assert status == 502
    assert payload == {"error": "action relay failed"}


def test_post_routes_stay_honest(serve):
    base = serve(write_config=UNCONFIGURED_WRITES, auth_config=UNCONFIGURED_AUTH)
    status, payload = post(base + "/api/nope", b"{}")
    assert status == 404
    status, payload = post(base + "/", b"{}")
    assert status == 405


def test_frontend_ships_the_action_ui_hooks(serve):
    base = serve(write_config=UNCONFIGURED_WRITES, auth_config=UNCONFIGURED_AUTH)
    parsed = urllib.parse.urlsplit(base)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        conn.request("GET", "/")
        body = conn.getresponse().read()
    finally:
        conn.close()
    assert b"test-economy-badge" in body
    assert b"action-panel" in body
