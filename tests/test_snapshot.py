"""Payload sanity for the committed sample snapshot (READ contract v1).

The v1 JSON Schema (schemas/mining_snapshot.v1.schema.json) is the single
source of truth for required fields — REQUIRED_MINER_FIELDS below is DERIVED
from it, never hand-copied, so this test and the schema cannot drift.
Full conformance lives in tests/test_schema_gate.py; this module keeps the
cheap semantic checks the frontend relies on.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "mining_snapshot.v1.schema.json"

_SCHEMA = json.loads(SCHEMA_PATH.read_text())

# Derived from the schema — the contract's per-miner required list.
REQUIRED_MINER_FIELDS = tuple(_SCHEMA["$defs"]["miner"]["required"])
REQUIRED_ENVELOPE_FIELDS = tuple(_SCHEMA["required"])


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT_PATH.read_text())


def test_required_fields_come_from_the_schema():
    """Guard the single-source-of-truth wiring itself."""
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
