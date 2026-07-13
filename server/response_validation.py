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

Like snapshot validation, the schema file is re-read per validation call:
the server holds no mutable state (docs/architecture.md), and the write path
is low-volume by contract (per-actor rate limits), so honesty beats a cache.
"""

from __future__ import annotations

import json
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


def load_schema() -> dict:
    """Read + parse the committed v1 WRITE-contract response schema."""
    return json.loads(SCHEMA_PATH.read_text())


def envelope_error(body: bytes, *, schema: dict | None = None) -> str | None:
    """Why ``body`` is not a conformant v1 response envelope — or ``None``.

    ``body`` is the executor's raw response bytes. Returns a locating,
    log-safe message for the first violation (non-JSON counts), ``None``
    when the envelope conforms. Never raises on bad input: the caller
    translates any message into the honest 502.
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
    return None
