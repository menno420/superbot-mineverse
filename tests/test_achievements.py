"""Tests for the achievements derivation (server/views.py, fun layer).

``build_achievements`` is a pure function over the snapshot's miners:
same data in, same badges out — no clock, no randomness, no state.
These tests pin every achievement's boundary, the honest handling of
missing/malformed fields, the exact winners the committed sample
snapshot yields, and that the ``achievements`` key on ``build_views``
is purely ADDITIVE (no existing key changes shape).
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import views  # noqa: E402

SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"

MAX_DEPTH = 3  # the sample world's max_depth


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT_PATH.read_text())


@pytest.fixture(scope="module")
def built(snapshot):
    return views.build_views(snapshot)


def earned(miner, max_depth=MAX_DEPTH):
    return views.earned_achievements(miner, max_depth)


# --- catalog -----------------------------------------------------------------


def test_catalog_ids_are_ordered_and_unique():
    ids = [entry["id"] for entry in views.ACHIEVEMENT_CATALOG]
    assert ids == [
        "deep_diver", "packrat", "coin_magnate", "fully_geared",
        "tool_breaker", "balanced_build", "the_answer",
    ]
    assert len(set(ids)) == len(ids)


def test_catalog_entries_carry_name_emoji_and_description():
    for entry in views.ACHIEVEMENT_CATALOG:
        assert set(entry) == {"id", "name", "emoji", "description"}
        assert entry["name"] and entry["emoji"] and entry["description"]


def test_thresholds_are_the_documented_values():
    # The thresholds are code-documented constants — pin them so a silent
    # rebalance shows up here (and in the sample-winner pins below).
    assert views.PACKRAT_THRESHOLD == 200
    assert views.COIN_MAGNATE_THRESHOLD == 10_000
    assert views.TOOL_BREAKER_WEAR == 100
    assert views.BALANCED_BUILD_MIN_SKILLS == 2
    assert views.BALANCED_BUILD_MAX_SPREAD == 1
    assert views.THE_ANSWER_COUNT == 42


# --- Deep Diver: record_depth == max_depth ------------------------------------


def test_deep_diver_boundary():
    assert "deep_diver" in earned({"record_depth": 3})
    assert "deep_diver" not in earned({"record_depth": 2})
    # Beyond max_depth is not "at" it — no badge for impossible data.
    assert "deep_diver" not in earned({"record_depth": 4})


def test_deep_diver_missing_or_malformed_record():
    assert "deep_diver" not in earned({})
    assert "deep_diver" not in earned({"record_depth": "3"})
    assert "deep_diver" not in earned({"record_depth": None})


# --- Packrat: pack total ≥ threshold -------------------------------------------


def test_packrat_boundary():
    at = {"mining_inventory": {"stone": views.PACKRAT_THRESHOLD}}
    below = {"mining_inventory": {"stone": views.PACKRAT_THRESHOLD - 1}}
    assert "packrat" in earned(at)
    assert "packrat" not in earned(below)


def test_packrat_sums_across_items():
    split = {"mining_inventory": {"stone": 150, "wood": 50}}
    assert "packrat" in earned(split)


def test_packrat_empty_or_missing_inventory():
    assert "packrat" not in earned({"mining_inventory": {}})
    assert "packrat" not in earned({})
    assert "packrat" not in earned({"mining_inventory": "lots"})


def test_packrat_ignores_non_integer_counts():
    miner = {"mining_inventory": {"stone": 100, "bogus": "many", "wood": 100}}
    assert "packrat" in earned(miner)
    miner = {"mining_inventory": {"stone": 100, "bogus": "many"}}
    assert "packrat" not in earned(miner)


# --- Coin Magnate: coins ≥ threshold -------------------------------------------


def test_coin_magnate_boundary():
    assert "coin_magnate" in earned({"coins": views.COIN_MAGNATE_THRESHOLD})
    assert "coin_magnate" not in earned(
        {"coins": views.COIN_MAGNATE_THRESHOLD - 1})


def test_coin_magnate_missing_or_malformed_coins():
    assert "coin_magnate" not in earned({})
    assert "coin_magnate" not in earned({"coins": "10000"})


# --- Fully Geared: all 9 schema slots filled ------------------------------------


def test_fully_geared_needs_every_schema_slot():
    full = {"equipment": {slot: f"iron {slot}"
                          for slot in views.equipment_slots()}}
    assert "fully_geared" in earned(full)
    # Any one slot missing (or empty) breaks it.
    for missing in views.equipment_slots():
        partial = dict(full["equipment"])
        del partial[missing]
        assert "fully_geared" not in earned({"equipment": partial}), missing
    empty_value = dict(full["equipment"], boots="")
    assert "fully_geared" not in earned({"equipment": empty_value})


def test_fully_geared_empty_or_missing_equipment():
    assert "fully_geared" not in earned({"equipment": {}})
    assert "fully_geared" not in earned({})
    assert "fully_geared" not in earned({"equipment": "everything"})


def _sample_miner(snapshot, name):
    return next(
        m for m in snapshot["miners"] if m["display_name"] == name
    )


def test_gear_goblin_is_the_only_fully_geared_sample_miner(snapshot):
    # GearGoblin was added so this badge has a live earner; everyone
    # else still has open slots.
    for miner in snapshot["miners"]:
        expected = miner["display_name"] == "GearGoblin"
        assert ("fully_geared" in earned(miner)) is expected, \
            miner["display_name"]


def test_gear_goblin_fills_exactly_the_nine_schema_slots(snapshot):
    goblin = _sample_miner(snapshot, "GearGoblin")
    assert set(goblin["equipment"]) == set(views.equipment_slots())
    assert all(goblin["equipment"].values())


def test_gear_goblin_boundary_any_slot_emptied_loses_the_badge(snapshot):
    goblin = _sample_miner(snapshot, "GearGoblin")
    assert earned(goblin) == ["fully_geared"]  # that badge, and only it
    for slot in views.equipment_slots():
        stripped = dict(goblin, equipment={
            k: v for k, v in goblin["equipment"].items() if k != slot
        })
        assert "fully_geared" not in earned(stripped), slot


# --- Tool Breaker: any gear_wear at/over the display cap -------------------------


def test_tool_breaker_boundary():
    assert "tool_breaker" in earned(
        {"gear_wear": {"pickaxe": views.TOOL_BREAKER_WEAR}})
    assert "tool_breaker" in earned(
        {"gear_wear": {"pickaxe": views.TOOL_BREAKER_WEAR + 50}})
    assert "tool_breaker" not in earned(
        {"gear_wear": {"pickaxe": views.TOOL_BREAKER_WEAR - 1}})


def test_tool_breaker_empty_missing_or_malformed_wear():
    assert "tool_breaker" not in earned({"gear_wear": {}})
    assert "tool_breaker" not in earned({})
    assert "tool_breaker" not in earned({"gear_wear": {"pickaxe": "worn"}})


def test_rusty_relic_is_the_only_tool_breaker_sample_miner(snapshot):
    # RustyRelic was added so this badge has a live earner; everyone
    # else's gear stays under the 100-wear display cap.
    for miner in snapshot["miners"]:
        expected = miner["display_name"] == "RustyRelic"
        assert ("tool_breaker" in earned(miner)) is expected, \
            miner["display_name"]


def test_rusty_relic_wear_is_at_or_over_the_cap(snapshot):
    relic = _sample_miner(snapshot, "RustyRelic")
    assert max(relic["gear_wear"].values()) >= views.TOOL_BREAKER_WEAR
    assert earned(relic) == ["tool_breaker"]  # that badge, and only it


def test_rusty_relic_boundary_one_below_the_cap_loses_the_badge(snapshot):
    relic = _sample_miner(snapshot, "RustyRelic")
    capped = dict(relic, gear_wear={
        item: min(wear, views.TOOL_BREAKER_WEAR - 1)
        for item, wear in relic["gear_wear"].items()
    })
    assert "tool_breaker" not in earned(capped)


# --- Balanced Build: ≥2 skills, spread ≤ 1 ---------------------------------------


def test_balanced_build_boundary():
    assert "balanced_build" in earned({"skills": {"mining": 2, "luck": 1}})
    assert "balanced_build" in earned({"skills": {"mining": 2, "luck": 2}})
    assert "balanced_build" not in earned({"skills": {"mining": 3, "luck": 1}})


def test_balanced_build_needs_at_least_two_skills():
    assert "balanced_build" not in earned({"skills": {"mining": 1}})
    assert "balanced_build" not in earned({"skills": {}})
    assert "balanced_build" not in earned({})


def test_balanced_build_three_skills_use_full_spread():
    assert "balanced_build" in earned(
        {"skills": {"mining": 3, "luck": 2, "endurance": 3}})
    assert "balanced_build" not in earned(
        {"skills": {"mining": 3, "luck": 1, "endurance": 3}})


def test_balanced_build_ignores_non_integer_levels():
    # Dropping the bogus value leaves one skill — not enough.
    assert "balanced_build" not in earned(
        {"skills": {"mining": 2, "bogus": "two"}})


# --- The Answer: exactly 42 of one pack item --------------------------------------


def test_the_answer_boundary():
    assert "the_answer" in earned({"mining_inventory": {"stone": 42}})
    assert "the_answer" not in earned({"mining_inventory": {"stone": 41}})
    assert "the_answer" not in earned({"mining_inventory": {"stone": 43}})


def test_the_answer_any_single_item_counts():
    miner = {"mining_inventory": {"stone": 7, "towel": 42}}
    assert "the_answer" in earned(miner)


def test_the_answer_is_pack_only_not_vault():
    # Documented scope: mining_inventory only — the vault doesn't count.
    assert "the_answer" not in earned({"vault": {"gold": 42}})


# --- degraded miners earn nothing, never crash -------------------------------------


def test_empty_miner_earns_nothing():
    assert earned({}) == []


def test_malformed_miner_earns_nothing():
    miner = {
        "record_depth": "deep",
        "mining_inventory": "lots",
        "coins": None,
        "equipment": 7,
        "gear_wear": [100],
        "skills": "many",
    }
    assert earned(miner) == []


# --- the committed sample: pinned winners ------------------------------------------


SAMPLE_WINNERS = {
    "DeepDelver": ["deep_diver", "coin_magnate", "the_answer"],
    "SilverSeeker": ["packrat", "balanced_build"],
    "CavernCrawler": ["packrat"],
    "PebblePicker": [],  # honest zero-state
    "MagmaMaven": ["deep_diver", "coin_magnate"],
    "GearGoblin": ["fully_geared"],
    "RustyRelic": ["tool_breaker"],
}


def test_sample_snapshot_winners_are_pinned(built):
    by_name = {
        row["display_name"]: row["earned"]
        for row in built["achievements"]["miners"]
    }
    assert by_name == SAMPLE_WINNERS


def test_sample_result_is_varied_and_non_empty(built):
    rows = built["achievements"]["miners"]
    earned_sets = [tuple(row["earned"]) for row in rows]
    assert any(earned_sets), "sample snapshot must yield some badges"
    assert len(set(earned_sets)) > 1, "sample badges must vary across miners"


def test_every_catalog_achievement_has_a_sample_earner(built):
    # The demo guarantee this slice exists for: every badge in the
    # catalog is earned by at least one committed sample miner, so the
    # achievements panel never shows an earner-less row.
    earned_union = {
        badge
        for row in built["achievements"]["miners"]
        for badge in row["earned"]
    }
    assert earned_union == {e["id"] for e in views.ACHIEVEMENT_CATALOG}


def test_earned_lists_follow_catalog_order(built):
    catalog_order = [e["id"] for e in views.ACHIEVEMENT_CATALOG]
    for row in built["achievements"]["miners"]:
        indices = [catalog_order.index(a) for a in row["earned"]]
        assert indices == sorted(indices), row["display_name"]


# --- build_views wiring: purely additive --------------------------------------------


def test_achievements_key_is_additive(snapshot, built):
    without = {k: v for k, v in built.items() if k != "achievements"}
    assert set(built) == set(without) | {"achievements"}
    # Every pre-existing key keeps its exact shape (same snapshot in →
    # same value out — the fun layer added, never altered).
    for key in ("schema_version", "generated_at", "guild_id", "world",
                "slots", "miners", "staleness", "ladder", "minimap",
                "leaderboards", "inventory"):
        assert key in built, key


def test_achievements_rows_align_with_shaped_miners(built):
    achieved = built["achievements"]["miners"]
    assert [row["suid"] for row in achieved] == \
        [m["suid"] for m in built["miners"]]
    assert [row["display_name"] for row in achieved] == \
        [m["display_name"] for m in built["miners"]]


def test_build_achievements_empty_guild():
    doc = views.build_achievements([], MAX_DEPTH)
    assert doc["miners"] == []
    assert [e["id"] for e in doc["catalog"]] == \
        [e["id"] for e in views.ACHIEVEMENT_CATALOG]


def test_achievements_survive_garbage_miners():
    built = views.build_views({"miners": [None, 42, {}]})
    rows = built["achievements"]["miners"]
    assert len(rows) == 1  # only the dict survives, like miners itself
    assert rows[0]["earned"] == []


def test_achievements_are_json_serializable(built):
    json.dumps(built["achievements"])
