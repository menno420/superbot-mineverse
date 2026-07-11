"""Stdlib-only runtime validation of a mining snapshot against READ contract v1.

WHY THIS EXISTS (and why it is not jsonschema): the web backend is stdlib-only
by contract (docs/architecture.md; ``jsonschema`` is a DEV/test dependency only
— see requirements-dev.txt and tests/test_schema_gate.py), so we cannot import
jsonschema at runtime. But the committed sample is not the only snapshot the
server will ever load: the future live bot→web relay pushes snapshots the CI
gate never saw. This module refuses a malformed relay payload AT INGESTION with
an honest 503 instead of serving corrupt data as 200.

HOW: a compact, schema-DERIVED interpreter. It reads the very same committed
``schemas/mining_snapshot.v1.schema.json`` and enforces the JSON Schema keywords
that contract actually uses — ``type``, ``const``, ``enum``, ``required``,
``properties``, ``additionalProperties``, ``items``, ``$ref``/``$defs``,
``minimum``, ``maximum``, ``pattern`` and ``propertyNames`` — so it cannot drift
from the schema file. It is intentionally a SUBSET of full Draft 2020-12 (it
does not, e.g., check ``format: date-time``); the authoritative conformance gate
remains the real jsonschema validator in tests/test_schema_gate.py. Required
fields + types + the ``schema_version`` version pin are all covered here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "mining_snapshot.v1.schema.json"
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
    """A snapshot failed the v1 structural check (carries a locating message)."""


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

    if isinstance(value, str) and "pattern" in schema:
        if re.search(schema["pattern"], value) is None:
            raise SnapshotInvalid(f"{path}: does not match pattern {schema['pattern']!r}")

    if isinstance(value, dict):
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
        items = schema.get("items")
        if isinstance(items, dict):
            for index, element in enumerate(value):
                _check(root, items, element, f"{path}[{index}]")


def validate_snapshot(snapshot: object, *, schema: dict | None = None) -> object:
    """Validate ``snapshot`` against the v1 READ contract; return it if valid.

    Raises :class:`SnapshotInvalid` (a ``ValueError`` subclass) with a locating
    message on the first violation.
    """
    root = schema if schema is not None else load_schema()
    _check(root, root, snapshot, "<root>")
    return snapshot
