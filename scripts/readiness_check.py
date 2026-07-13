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

``--probe-ingest`` is the FLAG-1 READ-relay twin: one deliberately
UNSIGNED POST to the snapshot-ingest route named by
``MINING_SNAPSHOT_RELAY_URL`` (the exact env var the bot-side pusher,
superbot #2058, POSTs to — provisioned bot-host-side, exportable ad hoc
wherever the leg is run). The receive side (``POST /api/snapshot/ingest``,
server/app.py) is fail-closed by contract, so the only honest answers are
**401** (configured — signature is verified over the raw bytes before
anything is parsed or persisted) or **503** (unconfigured —
``snapshot ingest not configured``). **HTTP 200 for an unsigned push is a
security failure** and this check reds loudly on it. The ingest relay is
optional at every stage (docs/live-prod-cutover.md §1), so with the URL
unset the leg is skipped, never failed.

Exit status: 0 iff every required env var is SET (and each probe, when
requested, passed); 1 otherwise, with a plain-language report of what is
missing.

This script only ever READS the environment and (opt-in) performs one
loopback-grade POST per probe. It enables nothing: the live-prod flag is
the owner's alone (docs/live-prod-cutover.md §5).

Usage:

    python3 scripts/readiness_check.py                 # env presence only
    python3 scripts/readiness_check.py --probe         # + write-endpoint probe
    python3 scripts/readiness_check.py --probe-ingest  # + ingest-route probe
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

# The FLAG-1 ingest-route leg (--probe-ingest). NOT one of the six required
# vars: the READ relay is optional at every stage, so the leg is skipped —
# never failed — when the URL is unset. The name is the bot-side pusher's
# own (superbot #2058 POSTs to MINING_SNAPSHOT_RELAY_URL every ~60 s).
INGEST_RELAY_URL_ENV = "MINING_SNAPSHOT_RELAY_URL"

# The receive side's honest unsigned answers (server/app.py
# _serve_snapshot_ingest): 401 carries the canonical transport-auth reason
# (server/actions.verify), 503 the fail-closed unconfigured error.
INGEST_401_REASONS = ("invalid_signature", "stale_timestamp")
INGEST_503_ERROR = "snapshot ingest not configured"


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


def probe_ingest_endpoint(
    endpoint: str, *, timeout: float = PROBE_TIMEOUT_SECONDS
) -> tuple[bool, str]:
    """One UNSIGNED empty-body POST to the ingest route. Returns (ok, detail).

    The FLAG-1 receive side is fail-closed (server/ingest.py doctrine), so
    exactly two answers are honest for an unsigned push:

    - **401** with the canonical transport-auth reason
      (``invalid_signature`` / ``stale_timestamp``) — configured; the
      signature is checked over the raw bytes before anything is parsed
      or persisted, so the probe can never place data.
    - **503** ``snapshot ingest not configured`` — unconfigured; the
      endpoint refuses everything rather than accept unsigned data.

    **HTTP 200 means the endpoint accepted an UNSIGNED snapshot — a
    security failure**, reported in those words. Anything else is
    reported honestly. The detail string never contains the endpoint URL
    or any env value.
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
        # 401/503 arrive as HTTP errors — the expected paths.
        status, body = err.code, err.read()
    except (urllib.error.URLError, OSError) as err:
        reason = getattr(err, "reason", err)
        return False, f"ingest route unreachable ({type(err).__name__}: {reason})"
    if status == 200:
        return False, (
            "SECURITY FAILURE: the ingest route accepted an UNSIGNED "
            "snapshot push (HTTP 200) — it must answer 401 (configured) "
            "or 503 (unconfigured), never 200"
        )
    if status not in (401, 503):
        return False, (
            f"expected HTTP 401 or 503 for an unsigned ingest probe, got {status}"
        )
    try:
        payload = json.loads(body)
    except ValueError:
        return False, "ingest response body is not JSON"
    if not isinstance(payload, dict):
        return False, "ingest response body is not a JSON object"
    error = payload.get("error")
    if status == 401:
        if error not in INGEST_401_REASONS:
            return False, (
                "expected the canonical transport-auth reason for an "
                f"unsigned ingest probe, got {error!r}"
            )
        return True, (
            f"ingest route is up, configured, and rejected the unsigned probe ({error})"
        )
    if error != INGEST_503_ERROR:
        return False, f"expected the fail-closed 503 error, got {error!r}"
    return True, (
        "ingest route is up and fail-closed (snapshot ingest not configured "
        "— MINING_SNAPSHOT_RELAY_SHARED_SECRET and/or MINING_SNAPSHOT_PATH "
        "unset on the serving host)"
    )


def build_report(
    environ,
    *,
    probe: bool = False,
    prober=probe_endpoint,
    probe_ingest: bool = False,
    ingest_prober=probe_ingest_endpoint,
):
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

    ingest_probe_failed = False
    ingest_probe_ran = False
    if probe_ingest:
        ingest_endpoint = environ.get(INGEST_RELAY_URL_ENV)
        if not ingest_endpoint:
            lines.append(
                f"ingest probe: skipped — {INGEST_RELAY_URL_ENV} is UNSET "
                "(the READ relay is optional at every stage; the var is "
                "the bot-side pusher's)."
            )
        else:
            ok, detail = ingest_prober(ingest_endpoint)
            ingest_probe_ran = True
            ingest_probe_failed = not ok
            lines.append(f"ingest probe: {'ok' if ok else 'FAILED'} — {detail}")
        lines.append("")

    if missing or probe_failed or ingest_probe_failed:
        if missing:
            lines.append(
                "NOT READY: "
                f"{len(missing)} of {len(REQUIRED_ENV_VARS)} required env "
                "vars unset: " + ", ".join(missing)
            )
        if probe_failed:
            lines.append("NOT READY: the endpoint probe failed (detail above).")
        if ingest_probe_failed:
            lines.append(
                "NOT READY: the ingest-route probe failed (detail above)."
            )
        lines.append(
            "Provisioning is owner-side (host environment) — see "
            "docs/live-prod-cutover.md §1. This script never enables "
            "anything; the live-prod flag is the owner's alone (§5)."
        )
        return lines, 1

    lines.append(
        "READY (mechanical checks only): all six env vars are SET"
        + (" and the endpoint answered the probe correctly" if probe else "")
        + (
            " and the ingest route answered its probe correctly"
            if ingest_probe_ran
            else ""
        )
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
            "never values), with --probe one unsigned probe of "
            "MINING_WRITE_ENDPOINT, and with --probe-ingest one unsigned "
            "probe of the FLAG-1 ingest route (MINING_SNAPSHOT_RELAY_URL)."
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
    parser.add_argument(
        "--probe-ingest",
        action="store_true",
        help=(
            "POST one UNSIGNED request to the FLAG-1 ingest route named by "
            "MINING_SNAPSHOT_RELAY_URL and expect 401 (configured) or 503 "
            "(unconfigured) — NEVER 200 (safe: signature-first means an "
            "unsigned probe can never place data). Skipped when the var "
            "is unset — the READ relay is optional at every stage."
        ),
    )
    args = parser.parse_args(argv)
    lines, code = build_report(
        environ, probe=args.probe, probe_ingest=args.probe_ingest
    )
    print("\n".join(lines), file=stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
