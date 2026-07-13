"""Importable READ-contract constants — one artifact for both sides of FLAG 1.

``schemas/mining_snapshot.v1.schema.json`` stays the single source of truth:
every constant below is DERIVED from the committed schema at import time,
never hand-copied, so this module and the schema cannot drift (the same
derivation ``tests/test_snapshot.py`` carried at lines 22-23 before it was
promoted here — idea-engine
``ideas/superbot-mineverse/snapshot-contract-shared-constant-2026-07-11.md``).

Web side: import it (``tests/test_snapshot.py`` does; the CI gate proves the
promotion). Bot side: the FLAG-1 exporter vendor-pins this file TOGETHER
WITH the schema file and asserts byte-equality of both in its own CI —
then a field rename on either side goes red at PR time, not at relay
cadence. Stdlib-only and free of repo-internal imports on purpose, so the
file is vendorable as-is.
"""

from __future__ import annotations

import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "mining_snapshot.v1.schema.json"

_SCHEMA = json.loads(SCHEMA_PATH.read_text())

#: Contract major version — v1 is exactly the string "1" (schema const).
SCHEMA_VERSION: str = _SCHEMA["properties"]["schema_version"]["const"]

#: The envelope's required keys (4 at v1).
REQUIRED_ENVELOPE_FIELDS: tuple[str, ...] = tuple(_SCHEMA["required"])

#: The contract's per-miner required field list (16 at v1).
REQUIRED_MINER_FIELDS: tuple[str, ...] = tuple(_SCHEMA["$defs"]["miner"]["required"])
