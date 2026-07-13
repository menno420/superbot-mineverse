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
