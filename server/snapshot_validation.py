"""Stdlib-only runtime validation of contract payloads against their v1 schemas.

WHY THIS EXISTS (and why it is not jsonschema): the web backend is stdlib-only
by contract (docs/architecture.md; ``jsonschema`` is a DEV/test dependency only
— see requirements-dev.txt and tests/test_schema_gate.py), so we cannot import
jsonschema at runtime. But the committed sample is not the only snapshot the
server will ever load: the future live bot→web relay pushes snapshots the CI
gate never saw. This module refuses a malformed relay payload AT INGESTION with
an honest 503 instead of serving corrupt data as 200. The same interpreter also
backs ``server/response_validation.py`` (the runtime check of the executor's
WRITE-contract response envelope): :func:`validate_value` is the generic
entrypoint, :func:`validate_snapshot` the snapshot-specific one.

HOW: a compact, schema-DERIVED interpreter. It reads the very same committed
schema file (``schemas/mining_snapshot.v1.schema.json`` here;
``schemas/mining_action_response.v1.schema.json`` via response_validation) and
enforces the JSON Schema keywords those contracts actually use — ``type``,
``const``, ``enum``, ``required``, ``properties``, ``additionalProperties``,
``items``, ``$ref``/``$defs``, ``minimum``, ``maximum``, ``pattern``,
``propertyNames``, the size/length bounds ``maxItems``/``minItems`` (arrays),
``maxLength``/``minLength`` (strings), ``maxProperties``/``minProperties``
(objects), and the applicators ``allOf``, ``if``/``then``/``else`` and ``not``
(the response schema's accept/reject cross-field rules) — so it cannot drift
from the schema file. It is intentionally a SUBSET of full Draft 2020-12 (it
does not, e.g., check ``format: date-time``); the authoritative conformance gate
remains the real jsonschema validator in tests/test_schema_gate.py. Required
fields + types + the ``schema_version`` version pin are all covered here.

DRIFT GUARD: ``_check`` fails LOUD on any *validation* keyword it does not
implement (logs a warning naming the keyword, then raises ``SnapshotInvalid`` →
honest 503). A future schema keyword can therefore never again be silently
ignored: it must be implemented (added to ``_HANDLED_KEYWORDS``) or explicitly
allow-listed as a no-op annotation (``_NOOP_KEYWORDS``) before it validates.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

LOGGER = logging.getLogger(__name__)

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "mining_snapshot.v1.schema.json"
)

# JSON Schema *validation* keywords ``_check`` actually enforces at runtime. If a
# schema node carries a validation keyword that is NOT in this set (and not in
# ``_NOOP_KEYWORDS`` below), ``_check`` fails LOUD — see the drift guard in
# ``_check``. This is deliberate: silently ignoring an unimplemented keyword let
# the runtime validator drift from the CI jsonschema gate (a snapshot the schema
# rejects would pass here). Any keyword added to the committed schema must be
# implemented here (or explicitly allow-listed) before it can validate.
_HANDLED_KEYWORDS = frozenset(
    {
        "type",
        "const",
        "enum",
        "minimum",
        "maximum",
        "pattern",
        "required",
        "properties",
        "additionalProperties",
        "propertyNames",
        "items",
        "maxItems",
        "minItems",
        "maxLength",
        "minLength",
        "maxProperties",
        "minProperties",
        "$ref",
        "allOf",
        "if",
        "then",
        "else",
        "not",
    }
)

# Annotation / structural keywords that legitimately have NO runtime assertion
# effect. Enumerated explicitly (not a blanket "ignore anything unknown") so that
# genuinely-unhandled *validation* keywords still fail loud. ``format`` is
# annotation-only here BY DESIGN: this module does not assert ``format:
# date-time`` (the authoritative jsonschema gate in tests/test_schema_gate.py
# does); ``$defs``/``definitions`` are subschema containers reached only via
# ``$ref``, never applied to a value directly.
_NOOP_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "$anchor",
        "$comment",
        "$defs",
        "definitions",
        "title",
        "description",
        "examples",
        "default",
        "readOnly",
        "writeOnly",
        "deprecated",
        "format",
    }
)

# JSON type name -> Python type(s). ``bool`` is a Python subclass of ``int``, so
# integer/number checks reject booleans explicitly below.
_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


class SnapshotInvalid(ValueError):
    """A value failed its v1 structural check (carries a locating message).

    Named for its original (snapshot) use; it is the interpreter's generic
    violation type — ``response_validation`` raises it for envelopes too.
    """


class _UnhandledKeyword(SnapshotInvalid):
    """Drift-guard failure: the schema uses a keyword this interpreter lacks.

    A distinct subclass so :func:`_passes` (the ``if``/``not`` applicators'
    boolean probe) can re-raise it instead of swallowing it as an ordinary
    "does not match" — the fail-loud drift guard must hold even inside
    conditional subschemas.
    """


def load_schema() -> dict:
    """Read + parse the committed v1 READ-contract schema."""
    return json.loads(SCHEMA_PATH.read_text())


def _resolve(root: dict, node: dict) -> dict:
    """Follow a single local ``$ref`` (e.g. ``#/$defs/miner``); else return node."""
    ref = node.get("$ref")
    if not ref:
        return node
    if not ref.startswith("#/"):
        raise SnapshotInvalid(f"unsupported $ref: {ref!r}")
    target: object = root
    for part in ref[2:].split("/"):
        if not isinstance(target, dict) or part not in target:
            raise SnapshotInvalid(f"unresolvable $ref: {ref!r}")
        target = target[part]
    if not isinstance(target, dict):
        raise SnapshotInvalid(f"$ref does not point at a schema: {ref!r}")
    return target


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check(root: dict, schema: dict, value: object, path: str) -> None:
    schema = _resolve(root, schema)

    # DRIFT GUARD (fail loud): refuse any *validation* keyword this interpreter
    # does not implement, so it can never silently pass a snapshot the schema
    # would reject. No-op annotation keywords ($schema, title, format, …) are
    # explicitly allow-listed and do not trip this.
    unhandled = set(schema) - _HANDLED_KEYWORDS - _NOOP_KEYWORDS
    if unhandled:
        keyword = sorted(unhandled)[0]
        LOGGER.warning(
            "snapshot validation: unimplemented schema keyword %r at %s — "
            "refusing snapshot (runtime/schema drift guard)",
            keyword,
            path,
        )
        raise _UnhandledKeyword(
            f"{path}: unimplemented schema keyword {keyword!r} "
            f"(runtime validator would drift from the schema)"
        )

    # Applicators (the response schema's accept/reject cross-field rules).
    for index, subschema in enumerate(schema.get("allOf", [])):
        _check(root, subschema, value, f"{path} (allOf[{index}])")
    if "not" in schema and _passes(root, schema["not"], value, path):
        raise SnapshotInvalid(f"{path}: matches a schema it must not match")
    if "if" in schema:
        if _passes(root, schema["if"], value, path):
            if "then" in schema:
                _check(root, schema["then"], value, f"{path} (then)")
        elif "else" in schema:
            _check(root, schema["else"], value, f"{path} (else)")

    declared = schema.get("type")
    if declared is not None:
        expected = _JSON_TYPES[declared]
        if declared in ("integer", "number") and isinstance(value, bool):
            raise SnapshotInvalid(f"{path}: expected {declared}, got boolean")
        if not isinstance(value, expected):
            raise SnapshotInvalid(f"{path}: expected {declared}")

    if "const" in schema and value != schema["const"]:
        raise SnapshotInvalid(f"{path}: must equal {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise SnapshotInvalid(f"{path}: {value!r} not in enum")

    if _is_number(value):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            raise SnapshotInvalid(f"{path}: {value} below minimum {minimum}")
        if maximum is not None and value > maximum:
            raise SnapshotInvalid(f"{path}: {value} above maximum {maximum}")

    if isinstance(value, str):
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise SnapshotInvalid(f"{path}: does not match pattern {schema['pattern']!r}")
        max_length = schema.get("maxLength")
        min_length = schema.get("minLength")
        if max_length is not None and len(value) > max_length:
            raise SnapshotInvalid(
                f"{path}: string length {len(value)} exceeds maxLength {max_length}"
            )
        if min_length is not None and len(value) < min_length:
            raise SnapshotInvalid(
                f"{path}: string length {len(value)} below minLength {min_length}"
            )

    if isinstance(value, dict):
        max_properties = schema.get("maxProperties")
        min_properties = schema.get("minProperties")
        if max_properties is not None and len(value) > max_properties:
            raise SnapshotInvalid(
                f"{path}: {len(value)} properties exceeds maxProperties {max_properties}"
            )
        if min_properties is not None and len(value) < min_properties:
            raise SnapshotInvalid(
                f"{path}: {len(value)} properties below minProperties {min_properties}"
            )
        for required in schema.get("required", []):
            if required not in value:
                raise SnapshotInvalid(f"{path}: missing required '{required}'")
        properties = schema.get("properties", {})
        property_names = schema.get("propertyNames")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if property_names is not None:
                _check(root, property_names, key, f"{path}/{key} (property name)")
            if key in properties:
                _check(root, properties[key], item, f"{path}/{key}")
            elif additional is False:
                raise SnapshotInvalid(f"{path}: unexpected property '{key}'")
            elif isinstance(additional, dict):
                _check(root, additional, item, f"{path}/{key}")

    if isinstance(value, list):
        max_items = schema.get("maxItems")
        min_items = schema.get("minItems")
        if max_items is not None and len(value) > max_items:
            raise SnapshotInvalid(
                f"{path}: array length {len(value)} exceeds maxItems {max_items}"
            )
        if min_items is not None and len(value) < min_items:
            raise SnapshotInvalid(
                f"{path}: array length {len(value)} below minItems {min_items}"
            )
        items = schema.get("items")
        if isinstance(items, dict):
            for index, element in enumerate(value):
                _check(root, items, element, f"{path}[{index}]")


def _passes(root: dict, schema: dict, value: object, path: str) -> bool:
    """Boolean probe for the ``if``/``not`` applicators: does ``value`` match?

    Ordinary violations mean "no"; a drift-guard failure inside the probed
    subschema is NOT a "no" — it re-raises, keeping fail-loud intact.
    """
    try:
        _check(root, schema, value, path)
    except _UnhandledKeyword:
        raise
    except SnapshotInvalid:
        return False
    return True


def validate_value(value: object, schema: dict) -> object:
    """Generic entrypoint: validate any ``value`` against ``schema``.

    Same interpreter, same fail-loud drift guard — used by
    ``server/response_validation.py`` for the WRITE-contract response
    envelope. Raises :class:`SnapshotInvalid` on the first violation.
    """
    _check(schema, schema, value, "<root>")
    return value


def validate_snapshot(snapshot: object, *, schema: dict | None = None) -> object:
    """Validate ``snapshot`` against the v1 READ contract; return it if valid.

    Raises :class:`SnapshotInvalid` (a ``ValueError`` subclass) with a locating
    message on the first violation.
    """
    root = schema if schema is not None else load_schema()
    return validate_value(snapshot, root)
