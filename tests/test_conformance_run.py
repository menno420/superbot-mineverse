"""Tests for scripts/conformance_run.py — the one-command WRITE-contract
conformance sweep wrapper (docs/conformance-runbook.md).

Pure parts only: env resolution, secret fingerprinting, report/verdict
formatting, results-file naming, and the missing-env main() path. NO
network, NO subprocess, NO env vars read — every case injects its own
environ dict, exactly like tests/test_readiness.py. The load-bearing
invariant, asserted throughout: neither a secret VALUE nor an endpoint
URL ever appears in any output line.
"""

import datetime
import importlib.util
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

_SPEC = importlib.util.spec_from_file_location(
    "conformance_run", REPO_ROOT / "scripts" / "conformance_run.py"
)
conformance = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(conformance)

# Sentinel values loud enough that any leak into output is unmissable.
FULL_ENV = {
    "MINING_WRITE_ENDPOINT": (
        "https://SENTINEL-endpoint.example/relay/mining/action"
    ),
    "MINING_WRITE_SHARED_SECRET": "SENTINEL-shared-secret-do-not-print",
}


# --- base-URL resolution ------------------------------------------------------


def test_explicit_base_url_wins_and_trailing_slash_is_stripped():
    env = dict(FULL_ENV, SHIM_CONFORMANCE_BASE_URL="https://SENTINEL-base.example/")
    base, detail = conformance.resolve_base_url(env)
    assert base == "https://SENTINEL-base.example"
    assert "SHIM_CONFORMANCE_BASE_URL is SET" in detail
    assert "SENTINEL" not in detail  # the detail line never carries a URL


def test_base_url_is_derived_from_the_write_endpoint():
    base, detail = conformance.resolve_base_url(dict(FULL_ENV))
    assert base == "https://SENTINEL-endpoint.example"
    assert "derived from MINING_WRITE_ENDPOINT" in detail
    assert conformance.ACTION_PATH in detail
    assert "SENTINEL" not in detail


def test_underivable_endpoint_is_reported_with_the_fix():
    env = {"MINING_WRITE_ENDPOINT": "https://SENTINEL.example/some/other/route"}
    base, detail = conformance.resolve_base_url(env)
    assert base is None
    assert "SHIM_CONFORMANCE_BASE_URL" in detail  # names the fix
    assert "SENTINEL" not in detail


def test_no_env_at_all_names_both_vars():
    base, detail = conformance.resolve_base_url({})
    assert base is None
    assert "SHIM_CONFORMANCE_BASE_URL" in detail
    assert "MINING_WRITE_ENDPOINT" in detail


# --- secret resolution + fingerprint ------------------------------------------


def test_secret_override_wins_over_the_canonical_name():
    env = dict(FULL_ENV, SHIM_CONFORMANCE_SECRET="SENTINEL-override")
    secret, source = conformance.resolve_secret(env)
    assert secret == "SENTINEL-override"
    assert source == "SHIM_CONFORMANCE_SECRET"


def test_canonical_secret_is_used_when_no_override():
    secret, source = conformance.resolve_secret(dict(FULL_ENV))
    assert secret == FULL_ENV["MINING_WRITE_SHARED_SECRET"]
    assert source == "MINING_WRITE_SHARED_SECRET"


def test_empty_string_secret_counts_as_unset():
    secret, source = conformance.resolve_secret(
        {"MINING_WRITE_SHARED_SECRET": "", "SHIM_CONFORMANCE_SECRET": ""}
    )
    assert secret is None and source is None


def test_fingerprint_never_contains_the_secret_and_is_deterministic():
    fp = conformance.secret_fingerprint("SENTINEL-shared-secret-do-not-print")
    assert "SENTINEL" not in fp
    assert fp.startswith("sha256:")
    assert "35 chars" in fp  # length only, never the value
    assert fp == conformance.secret_fingerprint(
        "SENTINEL-shared-secret-do-not-print"
    )


# --- the env report ------------------------------------------------------------


def test_full_env_report_is_ok_and_leaks_nothing():
    lines, base, ok = conformance.build_env_report(dict(FULL_ENV))
    output = "\n".join(lines)
    assert ok and base == "https://SENTINEL-endpoint.example"
    assert "SENTINEL" not in output  # no URL, no secret value
    assert "sha256:" in output  # fingerprint at most
    assert "MISSING" not in output


def test_missing_secret_report_is_not_ok_and_names_the_exports():
    env = {"MINING_WRITE_ENDPOINT": FULL_ENV["MINING_WRITE_ENDPOINT"]}
    lines, base, ok = conformance.build_env_report(env)
    output = "\n".join(lines)
    assert not ok and base is not None
    assert "signing secret: MISSING" in output
    assert "MINING_WRITE_SHARED_SECRET" in output
    assert "SHIM_CONFORMANCE_SECRET" in output
    assert "SENTINEL" not in output


# --- verdict formatting ---------------------------------------------------------


def test_pass_verdict_points_at_the_manual_audit_step():
    lines, code = conformance.format_verdict(0, Path("/x/conformance-1.log"))
    output = "\n".join(lines)
    assert code == conformance.EXIT_PASS == 0
    assert "VERDICT: PASS" in output
    assert "audit" in output  # the explicit next step
    assert "docs/live-prod-cutover.md §1" in output
    assert "reload data/sample_snapshot.json" in output  # re-run fine print
    assert "/x/conformance-1.log" in output


def test_pytest_exit_4_maps_to_the_missing_env_exit_code():
    lines, code = conformance.format_verdict(4, Path("/x/r.log"))
    output = "\n".join(lines)
    assert code == conformance.EXIT_MISSING_ENV == 3
    assert "MISCONFIGURED" in output
    assert "MINING_WRITE_SHARED_SECRET" in output


def test_ordinary_failure_verdict_carries_the_reload_hint():
    lines, code = conformance.format_verdict(1, Path("/x/r.log"))
    output = "\n".join(lines)
    assert code == conformance.EXIT_SWEEP_FAILED == 1
    assert "VERDICT: FAIL" in output
    assert "data/sample_snapshot.json" in output  # cutover §1 fine print


def test_exit_codes_are_distinct():
    codes = {
        conformance.EXIT_PASS,
        conformance.EXIT_SWEEP_FAILED,
        conformance.EXIT_PROBE_FAILED,
        conformance.EXIT_MISSING_ENV,
    }
    assert len(codes) == 4
    # never collide with the seam's own pytest.exit code (4) — a 4 from this
    # wrapper would read as the seam's abort
    assert conformance.PYTEST_EXIT_MISSING_SECRET == 4
    assert 4 not in codes


# --- results file ----------------------------------------------------------------


def test_results_path_is_timestamped_inside_the_given_dir():
    now = datetime.datetime(2026, 7, 13, 4, 5, 6, tzinfo=datetime.timezone.utc)
    path = conformance.results_path("/some/dir", now=now)
    assert path == Path("/some/dir/conformance-20260713T040506Z.log")


def test_default_results_dir_is_git_ignored():
    gitignore = (REPO_ROOT / ".gitignore").read_text()
    assert ".conformance-runs/" in gitignore
    assert conformance.RESULTS_DIR.name == ".conformance-runs"


# --- main(): the no-subprocess path ----------------------------------------------


def test_main_with_empty_env_exits_3_without_running_anything():
    out = io.StringIO()
    code = conformance.main([], environ={}, stdout=out)
    output = out.getvalue()
    assert code == 3
    assert "MISCONFIGURED" in output
    assert "SHIM_CONFORMANCE_BASE_URL" in output
    assert "MINING_WRITE_SHARED_SECRET" in output


def test_main_missing_env_output_never_leaks_values():
    out = io.StringIO()
    env = {"MINING_WRITE_ENDPOINT": FULL_ENV["MINING_WRITE_ENDPOINT"]}
    code = conformance.main([], environ=env, stdout=out)
    assert code == 3
    assert "SENTINEL" not in out.getvalue()
