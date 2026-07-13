"""Tests for scripts/readiness_check.py — the mechanical live-prod
readiness check (docs/live-prod-cutover.md §6).

NO env vars, NO secrets, NO network beyond loopback: every case injects
its own environ dict (the module never has to touch ``os.environ``), and
the probe cases run against the dev/test bot shim (tests/shim/shim_bot.py)
or a tiny local stub on an ephemeral port — exactly like CI. The
load-bearing invariant, asserted throughout: an env var VALUE never
appears in any output line.
"""

import http.server
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests._server_helpers import run_server  # noqa: E402
from tests.shim.shim_bot import ACTION_PATH, make_shim_server  # noqa: E402

_SPEC = importlib.util.spec_from_file_location(
    "readiness_check", REPO_ROOT / "scripts" / "readiness_check.py"
)
readiness = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(readiness)

# Sentinel values loud enough that any leak into output is unmissable.
FULL_ENV = {
    "DISCORD_OAUTH_CLIENT_ID": "SENTINEL-client-id-do-not-print",
    "DISCORD_OAUTH_CLIENT_SECRET": "SENTINEL-client-secret-do-not-print",
    "OAUTH_REDIRECT_URI": "https://SENTINEL-redirect.example/auth/callback",
    "WEB_SESSION_SIGNING_KEY": "SENTINEL-signing-key-do-not-print",
    "MINING_WRITE_ENDPOINT": "http://SENTINEL-endpoint.example/relay/mining/action",
    "MINING_WRITE_SHARED_SECRET": "SENTINEL-shared-secret-do-not-print",
}


def run_main(argv, environ):
    out = io.StringIO()
    code = readiness.main(argv, environ=environ, stdout=out)
    return code, out.getvalue()


# --- env presence (the CI shape: zero env vars) ------------------------------


def test_documented_env_names_exactly():
    assert readiness.REQUIRED_ENV_VARS == (
        "DISCORD_OAUTH_CLIENT_ID",
        "DISCORD_OAUTH_CLIENT_SECRET",
        "OAUTH_REDIRECT_URI",
        "WEB_SESSION_SIGNING_KEY",
        "MINING_WRITE_ENDPOINT",
        "MINING_WRITE_SHARED_SECRET",
    )


def test_zero_env_vars_is_not_ready_and_exits_nonzero():
    code, output = run_main([], {})
    assert code == 1
    assert "NOT READY" in output
    for name in readiness.REQUIRED_ENV_VARS:
        assert f"{name}" in output
    assert output.count("UNSET") == len(readiness.REQUIRED_ENV_VARS)


def test_fully_provisioned_env_is_ready():
    code, output = run_main([], dict(FULL_ENV))
    assert code == 0
    assert "READY" in output
    assert "NOT READY" not in output
    assert output.count(" SET") >= len(readiness.REQUIRED_ENV_VARS)


def test_partial_env_names_exactly_the_missing_vars():
    env = {k: v for k, v in FULL_ENV.items() if k != "MINING_WRITE_SHARED_SECRET"}
    code, output = run_main([], env)
    assert code == 1
    assert "1 of 6 required env vars unset: MINING_WRITE_SHARED_SECRET" in output


def test_empty_string_counts_as_unset():
    env = dict(FULL_ENV)
    env["WEB_SESSION_SIGNING_KEY"] = ""  # mirrors WriteConfig.from_env's `or None`
    code, output = run_main([], env)
    assert code == 1
    assert "WEB_SESSION_SIGNING_KEY" in output
    assert "UNSET" in output


def test_no_env_value_is_ever_printed():
    for env in (dict(FULL_ENV), {k: v for k, v in list(FULL_ENV.items())[:3]}):
        _, output = run_main([], env)
        for value in env.values():
            assert value not in output
        assert "SENTINEL" not in output


# --- the probe (loopback only, opt-in) ---------------------------------------


@pytest.fixture()
def shim():
    """A running shim on an ephemeral port; yields its base URL."""
    server, state = make_shim_server(port=0, secret="probe-secret-not-a-secret")
    with run_server(server):
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"


def test_probe_accepts_the_contract_401_from_the_shim(shim):
    # An UNSIGNED probe: the shim answers 401 invalid_signature (signature
    # is checked first, so nothing executes and nothing is audited).
    ok, detail = readiness.probe_endpoint(shim + ACTION_PATH)
    assert ok, detail
    assert "invalid_signature" in detail


def test_probe_reports_unreachable_endpoints_honestly():
    ok, detail = readiness.probe_endpoint(
        "http://127.0.0.1:9/relay/mining/action", timeout=2
    )
    assert not ok
    assert "unreachable" in detail


def test_probe_rejects_a_non_contract_200():
    class Happy200(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 (http.server API name)
            body = json.dumps({"hello": "world"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A002
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Happy200)
    with run_server(server):
        host, port = server.server_address[:2]
        ok, detail = readiness.probe_endpoint(f"http://{host}:{port}/anything")
        assert not ok
        assert "expected HTTP 401" in detail


def test_probe_rejects_a_401_missing_contract_fields():
    class Bare401(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 (http.server API name)
            body = json.dumps({"reason_code": "invalid_signature"}).encode()
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A002
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Bare401)
    with run_server(server):
        host, port = server.server_address[:2]
        ok, detail = readiness.probe_endpoint(f"http://{host}:{port}/anything")
        assert not ok
        assert "missing contract fields" in detail


# --- probe wiring inside the report (no network — injected prober) -----------


def test_probe_is_skipped_when_endpoint_is_unset():
    env = {k: v for k, v in FULL_ENV.items() if k != "MINING_WRITE_ENDPOINT"}

    def never_called(endpoint):
        raise AssertionError("prober must not run without an endpoint")

    lines, code = readiness.build_report(env, probe=True, prober=never_called)
    output = "\n".join(lines)
    assert code == 1  # the var is UNSET, so not ready regardless
    assert "probe: skipped" in output


def test_probe_failure_fails_the_report_even_with_all_vars_set():
    lines, code = readiness.build_report(
        dict(FULL_ENV), probe=True, prober=lambda endpoint: (False, "boom")
    )
    output = "\n".join(lines)
    assert code == 1
    assert "probe: FAILED — boom" in output
    assert "endpoint probe failed" in output


def test_probe_success_with_all_vars_set_is_ready():
    lines, code = readiness.build_report(
        dict(FULL_ENV), probe=True, prober=lambda endpoint: (True, "contract 401")
    )
    output = "\n".join(lines)
    assert code == 0
    assert "probe: ok — contract 401" in output
    assert "READY" in output


def test_report_without_probe_never_touches_the_prober():
    def never_called(endpoint):
        raise AssertionError("prober must not run without --probe")

    lines, code = readiness.build_report(
        dict(FULL_ENV), probe=False, prober=never_called
    )
    assert code == 0
    assert not any("probe" in line for line in lines)


# --- the ingest-route leg (FLAG 1 — loopback only, opt-in) --------------------
#
# The probe cases run against the REAL app server (server/app.py via the
# shared `serve` fixture) in both of its honest unsigned-answer modes —
# configured (401) and fail-closed unconfigured (503) — plus local stubs
# for the answers the real server must never give. No secrets beyond
# test-local strings, no non-loopback network, exactly like CI.

from server import ingest  # noqa: E402
from server.app import API_SNAPSHOT_INGEST, WEB_ROOT  # noqa: E402

INGEST_URL_ENV = {
    "MINING_SNAPSHOT_RELAY_URL": (
        "http://SENTINEL-ingest.example/api/snapshot/ingest"
    ),
}


def test_ingest_probe_env_name_matches_the_bot_side_pusher():
    assert readiness.INGEST_RELAY_URL_ENV == "MINING_SNAPSHOT_RELAY_URL"


def test_ingest_probe_accepts_the_configured_401_from_the_real_server(
    serve, tmp_path
):
    # Configured ingest (secret + path set): an UNSIGNED probe draws the
    # canonical pre-parse 401 and can never place data.
    target = tmp_path / "relay_snapshot.json"
    base = serve(
        snapshot_path=target,
        web_root=WEB_ROOT,
        ingest_config=ingest.IngestConfig(
            secret="probe-secret-not-a-secret", path=target
        ),
    )
    ok, detail = readiness.probe_ingest_endpoint(base + API_SNAPSHOT_INGEST)
    assert ok, detail
    assert "invalid_signature" in detail
    assert not target.exists()  # the unsigned probe persisted nothing


def test_ingest_probe_accepts_the_fail_closed_503_from_the_real_server(serve):
    # Unconfigured ingest (the default, degraded mode): honest 503,
    # reported ok — fail-closed IS the correct unsigned answer.
    base = serve(web_root=WEB_ROOT)
    ok, detail = readiness.probe_ingest_endpoint(base + API_SNAPSHOT_INGEST)
    assert ok, detail
    assert "fail-closed" in detail
    assert "not configured" in detail


def test_ingest_probe_reds_loudly_on_an_unsigned_200():
    # The one answer the leg exists to catch: an endpoint that ACCEPTS an
    # unsigned snapshot push. NEVER ok, and said in security terms.
    class Accepts200(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 (http.server API name)
            body = json.dumps({"status": "accepted"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A002
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Accepts200)
    with run_server(server):
        host, port = server.server_address[:2]
        ok, detail = readiness.probe_ingest_endpoint(
            f"http://{host}:{port}/api/snapshot/ingest"
        )
        assert not ok
        assert "SECURITY FAILURE" in detail
        assert "UNSIGNED" in detail


def test_ingest_probe_rejects_a_401_without_the_canonical_reason():
    class Bare401(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 (http.server API name)
            body = json.dumps({"error": "who goes there"}).encode()
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A002
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Bare401)
    with run_server(server):
        host, port = server.server_address[:2]
        ok, detail = readiness.probe_ingest_endpoint(
            f"http://{host}:{port}/anything"
        )
        assert not ok
        assert "canonical transport-auth reason" in detail


def test_ingest_probe_rejects_an_unexpected_status():
    class Teapot418(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 (http.server API name)
            body = b"{}"
            self.send_response(418)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A002
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Teapot418)
    with run_server(server):
        host, port = server.server_address[:2]
        ok, detail = readiness.probe_ingest_endpoint(
            f"http://{host}:{port}/anything"
        )
        assert not ok
        assert "expected HTTP 401 or 503" in detail


def test_ingest_probe_reports_unreachable_endpoints_honestly():
    ok, detail = readiness.probe_ingest_endpoint(
        "http://127.0.0.1:9/api/snapshot/ingest", timeout=2
    )
    assert not ok
    assert "unreachable" in detail


# --- ingest-probe wiring inside the report (no network — injected prober) ----


def test_ingest_probe_is_skipped_when_the_relay_url_is_unset():
    def never_called(endpoint):
        raise AssertionError("ingest prober must not run without a URL")

    lines, code = readiness.build_report(
        dict(FULL_ENV), probe_ingest=True, ingest_prober=never_called
    )
    output = "\n".join(lines)
    assert code == 0  # the relay is optional at every stage — never a failure
    assert "ingest probe: skipped" in output
    assert "READY" in output


def test_ingest_probe_failure_fails_the_report_even_with_all_vars_set():
    env = dict(FULL_ENV) | dict(INGEST_URL_ENV)
    lines, code = readiness.build_report(
        env, probe_ingest=True, ingest_prober=lambda endpoint: (False, "boom")
    )
    output = "\n".join(lines)
    assert code == 1
    assert "ingest probe: FAILED — boom" in output
    assert "ingest-route probe failed" in output


def test_ingest_probe_success_with_all_vars_set_is_ready():
    env = dict(FULL_ENV) | dict(INGEST_URL_ENV)
    lines, code = readiness.build_report(
        env,
        probe_ingest=True,
        ingest_prober=lambda endpoint: (True, "fail-closed"),
    )
    output = "\n".join(lines)
    assert code == 0
    assert "ingest probe: ok — fail-closed" in output
    assert "ingest route answered its probe correctly" in output


def test_report_without_probe_ingest_never_touches_the_ingest_prober():
    def never_called(endpoint):
        raise AssertionError("ingest prober must not run without --probe-ingest")

    lines, code = readiness.build_report(
        dict(FULL_ENV) | dict(INGEST_URL_ENV), ingest_prober=never_called
    )
    assert code == 0
    assert not any("ingest" in line for line in lines)


def test_no_env_value_is_ever_printed_with_the_ingest_leg():
    env = dict(FULL_ENV) | dict(INGEST_URL_ENV)
    _, output = run_main(["--probe-ingest"], env)
    for value in env.values():
        assert value not in output
    assert "SENTINEL" not in output
