"""Stdlib-only runtime validation of the executor's action-response envelope.

The mineverse side of the WRITE contract (docs/mining-write-contract.md)
relays the executor's answer to ``POST /api/action`` to the browser. Until
this module existed, that relay was VERBATIM with no runtime check — response
conformance to ``schemas/mining_action_response.v1.schema.json`` was asserted
only by the dev/test jsonschema validators (tests/test_actions.py), so a
buggy or half-deployed executor answering 200 with a malformed or non-JSON
body would reach the browser unchecked. A lying 200 is worse than a clean
failure.

This is NOT a second ad-hoc validator: it loads the committed response schema
and runs it through the same schema-derived interpreter that already guards
snapshot ingestion (``server/snapshot_validation.py`` — see that module's
docstring for the keyword coverage and the fail-loud drift guard). The
failure semantics live in ``server/app.py``'s ``_serve_action``: a
non-conformant envelope on ANY executor HTTP status is never relayed; the
web server answers ``502 {"error": "invalid executor response"}`` instead.
Conformant envelopes — including contract rejections — relay verbatim,
exactly as before.

On top of schema conformance sits a COHERENCE layer: the contract's "HTTP
status mapping" table pairs every reason_code in the closed taxonomy with
exactly one HTTP status, so a schema-conformant envelope arriving under the
WRONG status (``ok`` under a 4xx/5xx, a rejection reason_code under 200) is
just as much a lying answer as a malformed body — same 502, never relayed.
``EXPECTED_HTTP_STATUS`` below is that table, transcribed; pass the
executor's status to ``envelope_error(..., http_status=...)`` to apply it.

Like snapshot validation, the parsed schema is cached (``lru_cache`` on
``load_schema``): the schema is a COMMITTED file, immutable under a running
server, so parsing it once is honest — the statelessness contract
(docs/architecture.md) is about the DATA being validated (the executor's
response, the live-fed snapshot), which is never cached.
``load_schema.cache_clear()`` is the explicit reload seam.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

try:
    from server import snapshot_validation
except ImportError:  # direct script execution: python3 server/app.py
    import snapshot_validation  # type: ignore[no-redef]

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "mining_action_response.v1.schema.json"
)

# The contract's "HTTP status mapping" table (docs/mining-write-contract.md),
# verbatim: each reason_code in the CLOSED v1 taxonomy pairs with exactly one
# HTTP status. Idempotent replays repeat the ORIGINAL response's status
# ("An idempotent replay repeats the original response's HTTP status"), so a
# replayed envelope obeys the same row as the original did — `replayed` never
# changes the expected status. A test pins this table to the schema's
# reason_code enum so an additive taxonomy change cannot silently skip the
# coherence check.
EXPECTED_HTTP_STATUS = {
    "ok": 200,
    "malformed_request": 400,
    "unsupported_contract_version": 400,
    "unknown_action": 400,
    "invalid_params": 400,
    "invalid_signature": 401,
    "stale_timestamp": 401,
    "guild_not_allowed": 403,
    "actor_not_found": 404,
    "replayed_action": 409,
    "economy_rejection": 422,
    "rate_limited": 429,
    "internal_error": 500,
}


@lru_cache(maxsize=None)
def load_schema() -> dict:
    """Read + parse the committed v1 WRITE-contract response schema (parsed once).

    Cached for the same reason as ``snapshot_validation.load_schema``: a
    committed schema file cannot change under a running server, and the
    cache never touches the validated payloads themselves.
    ``load_schema.cache_clear()`` is the explicit reload seam.
    """
    return json.loads(SCHEMA_PATH.read_text())


def envelope_error(
    body: bytes, *, http_status: int | None = None, schema: dict | None = None
) -> str | None:
    """Why ``body`` is not a relayable v1 response envelope — or ``None``.

    ``body`` is the executor's raw response bytes. Returns a locating,
    log-safe message for the first violation (non-JSON counts), ``None``
    when the envelope conforms. Never raises on bad input: the caller
    translates any message into the honest 502.

    When ``http_status`` is given, a second layer runs ON TOP of schema
    conformance: the executor's HTTP status must cohere with the envelope's
    ``reason_code`` per the contract's "HTTP status mapping" table
    (``EXPECTED_HTTP_STATUS``). ``ok: true`` under a 4xx/5xx, a rejection
    reason_code under 200, or any other off-table pairing is refused —
    a conformant body under a lying status is still a lying answer. Pass
    ``http_status=None`` (the default) for the schema-only verdict.
    """
    try:
        envelope = json.loads(body)
    except ValueError:
        return "executor body is not valid JSON"
    try:
        snapshot_validation.validate_value(
            envelope, schema if schema is not None else load_schema()
        )
    except snapshot_validation.SnapshotInvalid as exc:
        return str(exc)
    if http_status is not None:
        # reason_code is inside the closed enum here (conformance passed);
        # a code missing from the table would mean the table drifted from
        # the schema — refuse loudly rather than skip the check (same
        # fail-loud posture as the interpreter's drift guard).
        reason_code = envelope["reason_code"]
        expected = EXPECTED_HTTP_STATUS.get(reason_code)
        if expected is None:
            return (
                f"reason_code {reason_code!r} has no contract HTTP status "
                "mapping (EXPECTED_HTTP_STATUS drifted from the schema enum)"
            )
        if http_status != expected:
            return (
                f"HTTP {http_status} is incoherent with reason_code "
                f"{reason_code!r} (the contract maps it to {expected})"
            )
    return None
