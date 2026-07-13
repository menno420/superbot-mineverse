"""Payload sanity for the committed sample snapshot (READ contract v1).

The v1 JSON Schema (schemas/mining_snapshot.v1.schema.json) is the single
source of truth for required fields — REQUIRED_MINER_FIELDS is DERIVED
from it, never hand-copied, so this test and the schema cannot drift. The
derivation lives in the importable ``snapshot_contract`` module (repo
root) so the FLAG-1 exporter can vendor-pin the same artifact; this test
imports it and guards the wiring. Full conformance lives in
tests/test_schema_gate.py; this module keeps the cheap semantic checks
the frontend relies on.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from snapshot_contract import (  # noqa: E402
    REQUIRED_ENVELOPE_FIELDS,
    REQUIRED_MINER_FIELDS,
    SCHEMA_PATH,
    SCHEMA_VERSION,
)

SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT_PATH.read_text())


def test_required_fields_come_from_the_schema():
    """Guard the single-source-of-truth wiring itself."""
    # The module's constants must be exactly the committed schema's lists —
    # a fresh, independent derivation here so snapshot_contract.py can
    # never drift from schemas/mining_snapshot.v1.schema.json.
    schema = json.loads(SCHEMA_PATH.read_text())
    assert SCHEMA_PATH.name == "mining_snapshot.v1.schema.json"
    assert REQUIRED_MINER_FIELDS == tuple(schema["$defs"]["miner"]["required"])
    assert REQUIRED_ENVELOPE_FIELDS == tuple(schema["required"])
    assert SCHEMA_VERSION == schema["properties"]["schema_version"]["const"]
    assert "mining_inventory" in REQUIRED_MINER_FIELDS
    assert set(REQUIRED_ENVELOPE_FIELDS) == {
        "schema_version", "generated_at", "guild_id", "miners",
    }


def test_snapshot_has_contract_envelope(snapshot):
    for field in REQUIRED_ENVELOPE_FIELDS:
        assert field in snapshot, f"envelope missing {field}"
    assert snapshot["schema_version"] == "1"
    assert isinstance(snapshot["guild_id"], str)
    assert snapshot["generated_at"].endswith("Z")
    # Optional world-shape hints: the sample ships them, and when present
    # they must agree with each other.
    assert isinstance(snapshot["max_depth"], int)
    assert len(snapshot["biomes"]) == snapshot["max_depth"] + 1


def test_snapshot_has_several_miners(snapshot):
    assert len(snapshot["miners"]) >= 3


def test_every_miner_has_required_fields(snapshot):
    for miner in snapshot["miners"]:
        missing = [f for f in REQUIRED_MINER_FIELDS if f not in miner]
        assert not missing, f"miner {miner.get('suid')} missing {missing}"


def test_miner_field_shapes(snapshot):
    max_depth = snapshot["max_depth"]
    for miner in snapshot["miners"]:
        assert isinstance(miner["suid"], str)
        assert isinstance(miner["guild_id"], str)
        assert 0 <= miner["depth"] <= max_depth
        assert miner["record_depth"] >= miner["depth"] or miner["record_depth"] >= 0
        assert {"x", "y"} <= set(miner["position"])
        assert isinstance(miner["energy"]["current"], int)
        for store in ("mining_inventory", "vault", "equipment", "gear_wear",
                      "skills", "structures"):
            assert isinstance(miner[store], dict)
        for qty in miner["mining_inventory"].values():
            assert isinstance(qty, int) and qty >= 0
        assert isinstance(miner["vault_level"], int)
        assert isinstance(miner["xp"]["level"], int)
        assert isinstance(miner["xp"]["game_total"], int)


def test_leaderboard_orderable(snapshot):
    """The frontend sorts by depth then mining XP — both must be numeric."""
    miners = snapshot["miners"]
    ranked = sorted(
        miners,
        key=lambda m: (m["depth"], m["xp"]["game_total"]),
        reverse=True,
    )
    assert len(ranked) == len(miners)
    depths = [m["depth"] for m in ranked]
    assert depths == sorted(depths, reverse=True)
    # A useful race needs miners at different depths.
    assert len(set(depths)) > 1
