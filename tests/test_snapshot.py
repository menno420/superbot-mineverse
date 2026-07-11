"""Payload sanity for the committed stage-1 sample snapshot."""

import json
from pathlib import Path

import pytest

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_snapshot.json"

# Oracle-derived per-miner fields (menno420/superbot mining_player_state via
# disbot/services/mining_workflow.py + disbot/utils/; xp via game_xp_service).
REQUIRED_MINER_FIELDS = (
    "suid",
    "guild_id",
    "display_name",
    "depth",
    "record_depth",
    "position",
    "energy",
    "coins",
    "xp",
    "equipment",
    "gear_wear",
    "mining_inventory",
    "vault",
    "vault_level",
    "skills",
    "structures",
)


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT_PATH.read_text())


def test_snapshot_loads_and_has_envelope(snapshot):
    assert snapshot["schema"] == "mineverse.snapshot"
    assert snapshot["schema_version"] == 1
    assert snapshot["generated_at"]
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
