#!/usr/bin/env python3
"""One-command WRITE-contract conformance sweep — stdlib-only wrapper.

The operational form of docs/live-prod-cutover.md §1's first checkbox
(one page: docs/conformance-runbook.md). It wraps the opt-in pytest
seam in ``tests/test_actions.py`` — nothing here re-implements the
contract; the sweep IS the existing fixture suite pointed at the real
executor. What this wrapper adds, in order:

1. **Env resolution** (names only — a secret VALUE is never printed;
   at most a sha256 fingerprint + length, and endpoint URLs are never
   printed at all, matching ``scripts/readiness_check.py``):
   the sweep's base URL comes from ``SHIM_CONFORMANCE_BASE_URL``, or is
   DERIVED from ``MINING_WRITE_ENDPOINT`` by stripping the contract
   route (the endpoint the web host already carries is the same
   executor); the signing secret from ``SHIM_CONFORMANCE_SECRET`` or
   ``MINING_WRITE_SHARED_SECRET``.
2. **Unsigned reachability probe** (skippable with ``--skip-probe``) —
   the exact ``readiness_check.py --probe`` handshake, reused from that
   module: one UNSIGNED POST that must draw the contract's pre-auth
   401. Signature-first verification means it can never execute
   anything, is never audited, and needs no secret.
2b. **Opt-in ingest leg** (``--probe-ingest``) — the exact
   ``readiness_check.py --probe-ingest`` handshake, reused from the
   same module: one UNSIGNED POST to the FLAG-1 ingest route named by
   ``MINING_SNAPSHOT_RELAY_URL``. Honest answers are 401 (configured)
   or 503 (fail-closed); **HTTP 200 for an unsigned push is a security
   failure** and reds the run. With the URL unset the leg is skipped,
   never failed — the READ relay is optional at every stage
   (docs/live-prod-cutover.md §1), so the write sweep's semantics are
   untouched.
3. **The sweep**: ``python3 -m pytest tests/test_actions.py -q`` with
   the conformance env passed through, output tee'd to a timestamped
   results file under ``.conformance-runs/`` (git-ignored — results are
   NEVER committed).
4. **Verdict**: PASS/FAIL plus the explicit next step — the manual
   3-step audit-trail verification (docs/live-prod-cutover.md §1),
   which no automated sweep covers.

Exit codes: 0 PASS · 1 sweep FAILED · 2 probe failed · 3 required env
missing/underivable (pytest's own exit 4 — the seam's missing-secret
abort — maps here too). This script enables nothing: the live-prod
flag is the owner's alone (docs/live-prod-cutover.md §5).

Usage (on a shell carrying the owner-provisioned values):

    python3 scripts/conformance_run.py
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The contract route (docs/mining-write-contract.md § "Transport auth").
# The pytest seam wants scheme://host[:port] ONLY — the tests append this
# path themselves — while MINING_WRITE_ENDPOINT is the full action URL,
# hence the derivation in resolve_base_url.
ACTION_PATH = "/relay/mining/action"

ENV_BASE_URL = "SHIM_CONFORMANCE_BASE_URL"
ENV_ENDPOINT = "MINING_WRITE_ENDPOINT"
ENV_SECRET_OVERRIDE = "SHIM_CONFORMANCE_SECRET"
ENV_SECRET = "MINING_WRITE_SHARED_SECRET"

# The FLAG-1 ingest route for the opt-in --probe-ingest leg. NOT part of
# the required env: the READ relay is optional at every stage, so with
# the URL unset the leg is skipped — never failed (mirrors
# scripts/readiness_check.py, which owns the probe implementation).
ENV_INGEST_URL = "MINING_SNAPSHOT_RELAY_URL"

EXIT_PASS = 0
EXIT_SWEEP_FAILED = 1
EXIT_PROBE_FAILED = 2
EXIT_MISSING_ENV = 3

# tests/test_actions.py calls pytest.exit(..., returncode=4) when the base
# URL is set but no signing secret is available.
PYTEST_EXIT_MISSING_SECRET = 4

# Results live in a git-ignored directory INSIDE the repo (discoverable,
# survives /tmp cleanup) — never committed.
RESULTS_DIR = REPO_ROOT / ".conformance-runs"

SWEEP_CMD = ("-m", "pytest", "tests/test_actions.py", "-q")


def secret_fingerprint(secret: str) -> str:
    """A non-reversible identity for a secret so two hosts can compare
    WITHOUT ever printing the value: sha256 prefix + length only."""
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:8]
    return f"sha256:{digest}… ({len(secret)} chars)"


def resolve_base_url(environ) -> tuple[str | None, str]:
    """(base_url, detail). The detail line NEVER contains a URL."""
    explicit = (environ.get(ENV_BASE_URL) or "").rstrip("/")
    if explicit:
        return explicit, f"{ENV_BASE_URL} is SET (used as-is)"
    endpoint = (environ.get(ENV_ENDPOINT) or "").rstrip("/")
    if endpoint.endswith(ACTION_PATH):
        return endpoint[: -len(ACTION_PATH)], (
            f"derived from {ENV_ENDPOINT} by stripping {ACTION_PATH}"
        )
    if endpoint:
        return None, (
            f"{ENV_BASE_URL} is UNSET and {ENV_ENDPOINT} does not end with "
            f"{ACTION_PATH}, so no base URL can be derived — export "
            f"{ENV_BASE_URL} (scheme://host[:port] only) explicitly"
        )
    return None, f"neither {ENV_BASE_URL} nor {ENV_ENDPOINT} is SET"


def resolve_secret(environ) -> tuple[str | None, str | None]:
    """(secret, env name it came from). Override wins, matching the seam
    (tests/test_actions.py). Empty string counts as unset."""
    for name in (ENV_SECRET_OVERRIDE, ENV_SECRET):
        value = environ.get(name)
        if value:
            return value, name
    return None, None


def build_env_report(environ) -> tuple[list[str], str | None, bool]:
    """(lines, base_url, ok). Pure — inject any mapping. No URL and no
    secret value ever enters a line (fingerprint at most)."""
    lines = ["conformance env (names only — URLs and secret values are never printed):"]
    base_url, base_detail = resolve_base_url(environ)
    lines.append(f"  base URL: {'ok' if base_url else 'MISSING'} — {base_detail}")
    secret, secret_source = resolve_secret(environ)
    if secret:
        lines.append(
            f"  signing secret: SET via {secret_source} — {secret_fingerprint(secret)}"
        )
    else:
        lines.append(
            f"  signing secret: MISSING — export {ENV_SECRET} (or its override "
            f"{ENV_SECRET_OVERRIDE}) with the conformance target's test-guild secret"
        )
    ok = base_url is not None and secret is not None
    return lines, base_url, ok


def format_verdict(pytest_code: int, results_file) -> tuple[list[str], int]:
    """Map the sweep's pytest exit code to (lines, this script's exit code).
    Pure — tested without running pytest."""
    lines = [""]
    if pytest_code == 0:
        lines += [
            "VERDICT: PASS — the WRITE-contract conformance sweep is green "
            "against the external executor.",
            f"full output: {results_file}",
            "",
            "NEXT STEP (manual — no sweep covers it): the 3-step audit-trail "
            "verification in docs/live-prod-cutover.md §1 — (a) an accepted "
            "mine, (b) a 422 economy_rejection, (c) a byte-identical replay of "
            "(a) → replayed: true and NO new audit row.",
            "Fine print before any re-run: reload data/sample_snapshot.json "
            "into the test guild — the deterministic-delta assertions assume "
            "the committed snapshot's starting values (cutover §1).",
            "This verdict enables nothing: the live-prod flag is the owner's "
            "alone (docs/live-prod-cutover.md §5).",
        ]
        return lines, EXIT_PASS
    if pytest_code == PYTEST_EXIT_MISSING_SECRET:
        lines += [
            f"VERDICT: MISCONFIGURED — pytest exited {PYTEST_EXIT_MISSING_SECRET}: "
            "the conformance seam aborted because no signing secret reached it "
            f"(tests/test_actions.py). Export {ENV_SECRET} (or "
            f"{ENV_SECRET_OVERRIDE}) and re-run.",
            f"full output: {results_file}",
        ]
        return lines, EXIT_MISSING_ENV
    lines += [
        f"VERDICT: FAIL — the conformance sweep exited {pytest_code}; the "
        "executor's behavior diverges from the contract fixtures (or the run "
        "environment broke mid-sweep).",
        f"full output: {results_file}",
        "Common non-bug cause first (cutover §1 fine print): a test guild NOT "
        "freshly reloaded with data/sample_snapshot.json fails the "
        "deterministic-delta assertions — reload and re-run before filing "
        "anything against the executor.",
    ]
    return lines, EXIT_SWEEP_FAILED


def results_path(results_dir, now=None) -> Path:
    now = now or datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return Path(results_dir) / f"conformance-{stamp}.log"


def _load_readiness():
    """Reuse the readiness_check module — ONE probe implementation per
    seam (write + ingest), never two (scripts/ is not a package, hence
    importlib). Returns the module so callers pick their probe."""
    spec = importlib.util.spec_from_file_location(
        "readiness_check", Path(__file__).resolve().parent / "readiness_check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_ingest_probe(environ, stdout, prober=None) -> bool:
    """The opt-in FLAG-1 ingest leg (--probe-ingest). Returns False iff
    the probe FAILED.

    Mirrors ``readiness_check.py --probe-ingest`` exactly: one UNSIGNED
    POST to the route named by ``MINING_SNAPSHOT_RELAY_URL`` must draw
    401 (configured) or 503 (fail-closed) — an HTTP 200 is a SECURITY
    failure. URL unset → skipped, never failed (the READ relay is
    optional at every stage). The printed lines never contain the URL or
    any env value; ``prober`` is injectable for network-free tests and
    defaults to ``readiness_check.probe_ingest_endpoint``.
    """
    ingest_url = environ.get(ENV_INGEST_URL)
    if not ingest_url:
        print(
            f"ingest probe: skipped — {ENV_INGEST_URL} is UNSET (the READ "
            "relay is optional at every stage; the var is the bot-side "
            "pusher's).",
            file=stdout,
        )
        return True
    if prober is None:
        prober = _load_readiness().probe_ingest_endpoint
    ok, detail = prober(ingest_url)
    print(f"ingest probe: {'ok' if ok else 'FAILED'} — {detail}", file=stdout)
    if not ok:
        print(
            "Aborting before the sweep: the ingest route did not answer the "
            "unsigned probe with the contract's 401/503 (an unsigned 200 is "
            "a SECURITY failure — see detail above). "
            "scripts/readiness_check.py --probe-ingest is the same handshake.",
            file=stdout,
        )
    return ok


def run_sweep(base_url: str, environ, results_file: Path, stdout) -> int:
    """Exec the pytest sweep with the conformance env, tee output to the
    results file, return pytest's exit code."""
    child_env = dict(environ)
    child_env[ENV_BASE_URL] = base_url
    results_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, *SWEEP_CMD]
    with results_file.open("w", encoding="utf-8") as log:
        log.write(
            "# WRITE-contract conformance sweep (scripts/conformance_run.py)\n"
            f"# started: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
            f"# command: python3 {' '.join(SWEEP_CMD)}\n"
        )
        proc = subprocess.Popen(
            cmd,
            cwd=REPO_ROOT,
            env=child_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout:
            stdout.write(line)
            log.write(line)
        code = proc.wait()
        log.write(f"# pytest exit code: {code}\n")
    return code


def main(argv=None, environ=os.environ, stdout=sys.stdout, ingest_prober=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the WRITE-contract conformance sweep (tests/test_actions.py) "
            "against the real executor in ONE command: env check, unsigned "
            "reachability probe, pytest sweep, PASS/FAIL verdict. With "
            "--probe-ingest, also probe the FLAG-1 ingest route unsigned."
        )
    )
    parser.add_argument(
        "--skip-probe",
        action="store_true",
        help="skip the unsigned reachability probe and go straight to the sweep",
    )
    parser.add_argument(
        "--probe-ingest",
        action="store_true",
        help=(
            "also POST one UNSIGNED request to the FLAG-1 ingest route named "
            f"by {ENV_INGEST_URL} and expect 401 (configured) or 503 "
            "(fail-closed) — NEVER 200 (readiness_check.py --probe-ingest is "
            "the same handshake). Skipped when the var is unset — the READ "
            "relay is optional at every stage."
        ),
    )
    parser.add_argument(
        "--results-dir",
        default=str(RESULTS_DIR),
        help="where the timestamped output log lands (default: %(default)s — git-ignored; never commit results)",
    )
    args = parser.parse_args(argv)

    print("WRITE-contract conformance run (docs/conformance-runbook.md)", file=stdout)
    print("", file=stdout)
    lines, base_url, ok = build_env_report(environ)
    print("\n".join(lines), file=stdout)
    print("", file=stdout)
    if not ok:
        print(
            "MISCONFIGURED: required env is missing (detail above). Values are "
            "owner-provisioned host configuration — docs/live-prod-cutover.md §1.",
            file=stdout,
        )
        return EXIT_MISSING_ENV

    if args.skip_probe:
        print("probe: skipped (--skip-probe)", file=stdout)
    else:
        probe_endpoint = _load_readiness().probe_endpoint
        probe_ok, detail = probe_endpoint(base_url + ACTION_PATH)
        print(f"probe: {'ok' if probe_ok else 'FAILED'} — {detail}", file=stdout)
        if not probe_ok:
            print(
                "Aborting before the sweep: the executor is not answering the "
                "contract's unsigned-probe handshake. Fix reachability first "
                "(scripts/readiness_check.py --probe is the same handshake).",
                file=stdout,
            )
            return EXIT_PROBE_FAILED
    if args.probe_ingest:
        if not run_ingest_probe(environ, stdout, prober=ingest_prober):
            return EXIT_PROBE_FAILED
    print("", file=stdout)

    results_file = results_path(args.results_dir)
    print(f"sweep: python3 {' '.join(SWEEP_CMD)}  (tee → {results_file})", file=stdout)
    pytest_code = run_sweep(base_url, environ, results_file, stdout)
    lines, code = format_verdict(pytest_code, results_file)
    print("\n".join(lines), file=stdout)
    with results_file.open("a", encoding="utf-8") as log:
        log.write("\n".join(lines) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
