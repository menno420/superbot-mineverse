"""WRITE-contract v1 transport helpers — stdlib-only, TEST GUILD ONLY.

This module is the web side of docs/mining-write-contract.md: it holds the
host-env configuration for the bot-side action endpoint, the canonical HMAC
request-signing implementation (shared with the dev/test shim so both sides
of the contract sign and verify identically), and the one function that
relays a signed proposal to the executor.

The web app NEVER executes an action itself: everything here produces or
transports a *proposal*; the bot side (real endpoint, or the dev shim in
``tests/shim/shim_bot.py``) is the only executor.

Configuration comes from HOST environment variables ONLY (never files,
never the repo):

- ``MINING_WRITE_ENDPOINT``      — full URL of the bot-side action endpoint
- ``MINING_WRITE_SHARED_SECRET`` — HMAC-SHA256 key for request signing

With either absent the app runs in DEGRADED MODE: every read view works
exactly as before, the frontend renders disabled action buttons, and
``POST /api/action`` answers an honest ``503 {"error": "writes not
configured"}`` — the same pattern as the OAuth degraded mode (docs/auth.md).

Signing scheme (contract § "Transport auth"):

    string_to_sign = METHOD + "\\n" + PATH + "\\n" + TIMESTAMP + "\\n"
                     + sha256_hex(BODY)
    X-Mineverse-Signature: hex(HMAC_SHA256(secret, string_to_sign))
    X-Mineverse-Timestamp: unix epoch seconds, decimal string

Verification is constant-time and checks the signature BEFORE the ±300 s
timestamp skew window, so an unsigned probe learns nothing about the clock.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

ENV_ENDPOINT = "MINING_WRITE_ENDPOINT"
ENV_SECRET = "MINING_WRITE_SHARED_SECRET"

HEADER_SIGNATURE = "X-Mineverse-Signature"
HEADER_TIMESTAMP = "X-Mineverse-Timestamp"
SKEW_SECONDS = 300
HTTP_TIMEOUT_SECONDS = 10
CONTRACT_VERSION = "1"


class WriteConfig:
    """Write-endpoint configuration snapshot. ``None`` values = degraded."""

    def __init__(self, endpoint: str | None, secret: str | None) -> None:
        self.endpoint = endpoint
        self.secret = secret

    @classmethod
    def from_env(cls, environ=os.environ) -> "WriteConfig":
        return cls(
            endpoint=environ.get(ENV_ENDPOINT) or None,
            secret=environ.get(ENV_SECRET) or None,
        )

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.secret)


# --- canonical signing (web server signs; shim + real endpoint verify) -----


def string_to_sign(method: str, path: str, timestamp: str, body: bytes) -> str:
    return "\n".join(
        (method.upper(), path, timestamp, hashlib.sha256(body).hexdigest())
    )


def sign(secret: str, method: str, path: str, timestamp: str, body: bytes) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        string_to_sign(method, path, timestamp, body).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify(
    secret: str,
    method: str,
    path: str,
    timestamp: str,
    body: bytes,
    signature: str,
    *,
    now: float | None = None,
) -> str | None:
    """Return the contract reason_code for a transport-auth failure, or None.

    Signature first (constant-time), THEN the timestamp window — the
    timestamp is part of the signed string, so a valid signature with a
    bad/stale timestamp is ``stale_timestamp`` and everything else is
    ``invalid_signature``.
    """
    if not isinstance(signature, str) or not signature or not isinstance(
        timestamp, str
    ):
        return "invalid_signature"
    expected = sign(secret, method, path, timestamp, body)
    if not hmac.compare_digest(expected, signature.lower()):
        return "invalid_signature"
    try:
        signed_at = int(timestamp)
    except ValueError:
        return "stale_timestamp"
    current = time.time() if now is None else now
    if abs(current - signed_at) > SKEW_SECONDS:
        return "stale_timestamp"
    return None


# --- the relay call ----------------------------------------------------------


def propose(
    config: WriteConfig, proposal: dict, *, now: float | None = None
) -> tuple[int, bytes]:
    """Sign ``proposal`` and POST it to the configured executor.

    Returns ``(http_status, response_body_bytes)`` — the executor's answer
    verbatim, including contract rejections (4xx/5xx bodies conform to
    ``schemas/mining_action_response.v1.schema.json``). Network-level
    failures (endpoint unreachable, timeout) raise ``OSError``/``URLError``
    for the caller to translate into an honest 502.
    """
    if not config.configured:
        raise ValueError("writes are not configured")
    body = json.dumps(proposal, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    path = urllib.parse.urlsplit(config.endpoint).path or "/"
    timestamp = str(int(time.time() if now is None else now))
    request = urllib.request.Request(
        config.endpoint,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            HEADER_TIMESTAMP: timestamp,
            HEADER_SIGNATURE: sign(config.secret, "POST", path, timestamp, body),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as err:
        # Contract rejections arrive as HTTP errors — their bodies are
        # first-class response envelopes, not transport failures.
        return err.code, err.read()
