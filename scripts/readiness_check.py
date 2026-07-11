#!/usr/bin/env python3
"""Live-prod readiness check — stdlib-only, SAFE TO RUN ANYWHERE.

The mechanical slice of docs/live-prod-cutover.md §1: reports which of the
six host env vars are provisioned (SET/UNSET — a value is NEVER printed,
not even a prefix or a length) and, with ``--probe``, sends one
deliberately UNSIGNED request to ``MINING_WRITE_ENDPOINT`` expecting the
WRITE contract's pre-auth rejection (401 ``invalid_signature`` —
docs/mining-write-contract.md § "Transport auth"). Signature-first
verification means the probe can never execute anything, is never audited,
and needs no secret.

Exit status: 0 iff every required env var is SET (and the probe, when
requested, passed); 1 otherwise, with a plain-language report of what is
missing.

This script only ever READS the environment and (opt-in) performs one
loopback-grade POST. It enables nothing: the live-prod flag is the owner's
alone (docs/live-prod-cutover.md §5).

Usage:

    python3 scripts/readiness_check.py           # env presence only
    python3 scripts/readiness_check.py --probe   # + endpoint probe
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# The six prod prerequisites, exactly as documented (docs/auth.md +
# docs/mining-write-contract.md § "Degraded mode").
REQUIRED_ENV_VARS = (
    "DISCORD_OAUTH_CLIENT_ID",
    "DISCORD_OAUTH_CLIENT_SECRET",
    "OAUTH_REDIRECT_URI",
    "WEB_SESSION_SIGNING_KEY",
    "MINING_WRITE_ENDPOINT",
    "MINING_WRITE_SHARED_SECRET",
)

# The response-envelope fields every contract answer carries
# (schemas/mining_action_response.v1.schema.json — checked structurally
# here because this script must stay stdlib-only; the full jsonschema gate
# lives in tests/).
RESPONSE_REQUIRED_FIELDS = (
    "contract_version",
    "action_id",
    "status",
    "reason_code",
    "message",
    "replayed",
)

PROBE_TIMEOUT_SECONDS = 10


def check_env(environ) -> list[tuple[str, bool]]:
    """(name, is_set) for each required var. Empty string counts as UNSET
    (mirrors ``server/actions.WriteConfig.from_env``'s ``or None``)."""
    return [(name, bool(environ.get(name))) for name in REQUIRED_ENV_VARS]


def probe_endpoint(
    endpoint: str, *, timeout: float = PROBE_TIMEOUT_SECONDS
) -> tuple[bool, str]:
    """One UNSIGNED empty-body POST to the executor. Returns (ok, detail).

    Expected answer: HTTP 401 with a contract response envelope whose
    ``reason_code`` is ``invalid_signature`` (or ``stale_timestamp`` —
    some executors may classify a missing timestamp there). Anything else
    is reported honestly. The detail string never contains the endpoint
    URL or any env value.
    """
    request = urllib.request.Request(
        endpoint,
        data=b"{}",
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as res:
            status, body = res.status, res.read()
    except urllib.error.HTTPError as err:
        # Contract rejections arrive as HTTP errors — that is the
        # expected path for an unsigned probe.
        status, body = err.code, err.read()
    except (urllib.error.URLError, OSError) as err:
        reason = getattr(err, "reason", err)
        return False, f"endpoint unreachable ({type(err).__name__}: {reason})"
    if status != 401:
        return False, f"expected HTTP 401 for an unsigned probe, got {status}"
    try:
        payload = json.loads(body)
    except ValueError:
        return False, "response body is not JSON"
    if not isinstance(payload, dict):
        return False, "response body is not a JSON object"
    missing = [f for f in RESPONSE_REQUIRED_FIELDS if f not in payload]
    if missing:
        return False, (
            "response envelope is missing contract fields: "
            + ", ".join(sorted(missing))
        )
    if payload.get("status") != "rejected":
        return False, f"expected status 'rejected', got {payload.get('status')!r}"
    reason_code = payload.get("reason_code")
    if reason_code not in ("invalid_signature", "stale_timestamp"):
        return False, (
            "expected reason_code 'invalid_signature' for an unsigned "
            f"probe, got {reason_code!r}"
        )
    return True, f"executor is up and rejected the unsigned probe ({reason_code})"


def build_report(environ, *, probe: bool = False, prober=probe_endpoint):
    """Compute the full readiness verdict → (lines, exit_code).

    Pure apart from the injected ``prober`` — everything printable is
    assembled here so tests can assert on it without touching the real
    process environment or the network. No env VALUE ever enters a line.
    """
    lines: list[str] = ["live-prod readiness check (docs/live-prod-cutover.md)", ""]
    results = check_env(environ)
    missing = [name for name, is_set in results if not is_set]
    width = max(len(name) for name in REQUIRED_ENV_VARS)
    lines.append("host env vars (presence only — values are never shown):")
    for name, is_set in results:
        lines.append(f"  {name.ljust(width)}  {'SET' if is_set else 'UNSET'}")
    lines.append("")

    probe_failed = False
    if probe:
        endpoint = environ.get("MINING_WRITE_ENDPOINT")
        if not endpoint:
            lines.append("probe: skipped — MINING_WRITE_ENDPOINT is UNSET.")
        else:
            ok, detail = prober(endpoint)
            probe_failed = not ok
            lines.append(f"probe: {'ok' if ok else 'FAILED'} — {detail}")
        lines.append("")

    if missing or probe_failed:
        if missing:
            lines.append(
                "NOT READY: "
                f"{len(missing)} of {len(REQUIRED_ENV_VARS)} required env "
                "vars unset: " + ", ".join(missing)
            )
        if probe_failed:
            lines.append("NOT READY: the endpoint probe failed (detail above).")
        lines.append(
            "Provisioning is owner-side (host environment) — see "
            "docs/live-prod-cutover.md §1. This script never enables "
            "anything; the live-prod flag is the owner's alone (§5)."
        )
        return lines, 1

    lines.append(
        "READY (mechanical checks only): all six env vars are SET"
        + (" and the endpoint answered the probe correctly" if probe else "")
        + "."
    )
    lines.append(
        "NOT covered from here: bot-side allowlist, Discord redirect "
        "registration, audit-trail verification, branch-ruleset checks — "
        "see docs/live-prod-cutover.md §6. The flag stays the owner's (§5)."
    )
    return lines, 0


def main(argv=None, environ=os.environ, stdout=sys.stdout) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report live-prod readiness: env-var presence (SET/UNSET only, "
            "never values) and, with --probe, one unsigned probe of "
            "MINING_WRITE_ENDPOINT."
        )
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help=(
            "POST one UNSIGNED request to MINING_WRITE_ENDPOINT and expect "
            "the contract's 401 invalid_signature rejection (safe: an "
            "unsigned probe can never execute anything)."
        ),
    )
    args = parser.parse_args(argv)
    lines, code = build_report(environ, probe=args.probe)
    print("\n".join(lines), file=stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
