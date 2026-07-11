"""Tests for the deepened read views (server/views.py + GET /api/views).

Every new render path is data-shaped server-side in ``server/views.py``
so it is testable here; the frontend only paints what these functions
return.  The v1 schema stays the single source of truth: the wiring
tests below assert the module's slot list / xp fields / bounds are EQUAL
to what ``schemas/mining_snapshot.v1.schema.json`` declares, so a schema
edit breaks these tests before any hand-copied list could drift.
"""

import json
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import views  # noqa: E402
from server.app import WEB_ROOT, make_server  # noqa: E402

SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "mining_snapshot.v1.schema.json"

_SCHEMA = json.loads(SCHEMA_PATH.read_text())
_MINER_PROPS = _SCHEMA["$defs"]["miner"]["properties"]


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT_PATH.read_text())


@pytest.fixture(scope="module")
def built(snapshot):
    return views.build_views(snapshot)


# --- schema wiring: derived, never hand-copied --------------------------


def test_equipment_slots_come_from_the_schema():
    assert views.equipment_slots() == list(
        _MINER_PROPS["equipment"]["propertyNames"]["enum"]
    )
    # The contract's oracle-confirmed slot set, via the schema.
    assert "tool" in views.equipment_slots()
    assert "boots" in views.equipment_slots()


def test_xp_fields_come_from_the_schema():
    assert views.xp_fields() == list(_MINER_PROPS["xp"]["required"])
    assert "level" in views.xp_fields()


def test_position_fields_come_from_the_schema():
    assert views.position_fields() == list(_MINER_PROPS["position"]["required"])
    assert set(views.position_fields()) == {"x", "y"}


def test_energy_fields_come_from_the_schema():
    assert views.energy_fields() == list(_MINER_PROPS["energy"]["required"])
    assert "updated_at" in views.energy_fields()


def test_bounds_come_from_the_schema():
    assert views.vault_level_max() == _MINER_PROPS["vault_level"]["maximum"]
    assert views.depth_max() == _MINER_PROPS["depth"]["maximum"]
    assert (
        views.energy_max()
        == _MINER_PROPS["energy"]["properties"]["current"]["maximum"]
    )


# --- item grouping (inventory browser + pack/vault panels) --------------


def test_group_items_orders_ore_tiers_stone_to_diamond():
    store = {"diamond": 1, "wood": 5, "stone": 9, "gold": 2, "torch": 3}
    grouped = views.group_items(store)
    assert grouped["ores"] == [["stone", 9], ["gold", 2], ["diamond", 1]]
    assert grouped["other"] == [["torch", 3], ["wood", 5]]  # alphabetical


def test_group_items_unknown_items_never_dropped():
    grouped = views.group_items({"mystery relic": 1})
    assert grouped["ores"] == []
    assert grouped["other"] == [["mystery relic", 1]]


def test_group_items_empty_and_missing_stores():
    assert views.group_items({}) == {"ores": [], "other": []}
    assert views.group_items(None) == {"ores": [], "other": []}


# --- skills + structures panels (rank_counts) -----------------------------


def test_rank_counts_orders_by_value_then_name():
    ranked = views.rank_counts({"luck": 3, "mining": 5, "endurance": 3})
    assert ranked == [["mining", 5], ["endurance", 3], ["luck", 3]]


def test_rank_counts_unknown_names_never_dropped():
    assert views.rank_counts({"mystery skill": 1}) == [["mystery skill", 1]]


def test_rank_counts_empty_and_missing_stores():
    assert views.rank_counts({}) == []
    assert views.rank_counts(None) == []


def test_rank_counts_drops_only_non_integer_values():
    ranked = views.rank_counts({"mining": 2, "bogus": "three", "luck": 1})
    assert ranked == [["mining", 2], ["luck", 1]]


def test_shaped_miner_skills_and_structures(snapshot, built):
    delver = built["miners"][0]  # DeepDelver: mining 4, luck 2
    assert delver["skills"] == [["mining", 4], ["luck", 2]]
    maven = next(
        m for m in built["miners"] if m["display_name"] == "MagmaMaven"
    )
    assert maven["structures"] == [
        ["forge", 4], ["home", 2], ["campfire", 1], ["dock", 1],
    ]


def test_shaped_miner_empty_skills_and_structures(built):
    pebble = next(
        m for m in built["miners"] if m["display_name"] == "PebblePicker"
    )
    assert pebble["skills"] == []
    assert pebble["structures"] == []


# --- position shaping (mini-map input) -------------------------------------


def test_shape_position_carries_the_schema_fields(snapshot):
    position = views.shape_position(snapshot["miners"][0])
    assert position == {"x": 4, "y": -2}
    assert set(position) == set(views.position_fields())


def test_shape_position_missing_or_malformed_is_none():
    assert views.shape_position({}) is None
    assert views.shape_position({"position": "nowhere"}) is None
    assert views.shape_position({"position": {"x": 1}}) is None
    assert views.shape_position({"position": {"x": 1, "y": "two"}}) is None


def test_shape_position_ignores_extra_open_fields():
    # The contract keeps position OPEN beyond x/y — extras never break it.
    miner = {"position": {"x": 2, "y": 3, "discovered": 7}}
    assert views.shape_position(miner) == {"x": 2, "y": 3}


# --- energy shaping ---------------------------------------------------------


def test_shape_energy_carries_schema_fields_and_bound(snapshot):
    energy = views.shape_energy(snapshot["miners"][0])
    assert energy["current"] == 41
    assert energy["updated_at"] == 1783728000
    assert energy["max"] == views.energy_max()
    assert set(energy) == set(views.energy_fields()) | {"max"}


def test_shape_energy_tolerates_missing_meter():
    energy = views.shape_energy({})
    assert energy["max"] == views.energy_max()
    assert all(
        energy[field] is None for field in views.energy_fields()
    )


def test_shape_energy_ignores_extra_open_fields():
    # The contract keeps energy OPEN beyond current/updated_at — additive
    # regen fields must never leak into (or break) the shaped meter.
    miner = {
        "energy": {"current": 30, "updated_at": 1783728000, "regen_rate": 2}
    }
    energy = views.shape_energy(miner)
    assert set(energy) == set(views.energy_fields()) | {"max"}
    assert energy["current"] == 30


# --- identity + xp.game (card-face fields) ---------------------------------


def test_shaped_miner_carries_suid_and_xp_game(snapshot, built):
    # suid and xp.game paint on the card face — pin the passthrough.
    for raw, shaped in zip(snapshot["miners"], built["miners"]):
        assert shaped["suid"] == raw["suid"]
        assert shaped["xp"]["game"] == raw["xp"]["game"]


def test_shaped_miner_xp_ignores_extra_open_fields():
    # xp is PERMISSIVE beyond the required quartet — additive extras must
    # never leak into (or break) the shaped projection.
    miner = {
        "xp": {
            "game": "mining",
            "game_total": 5,
            "shared_total": 9,
            "level": 1,
            "prestige": 3,
        }
    }
    shaped = views.shape_miner(miner)
    assert set(shaped["xp"]) == set(views.xp_fields())
    assert shaped["xp"]["game"] == "mining"


# --- position mini-map ------------------------------------------------------


def test_minimap_has_a_panel_per_depth(snapshot, built):
    minimap = built["minimap"]
    assert [panel["depth"] for panel in minimap] == [0, 1, 2, 3]
    assert [panel["biome"] for panel in minimap] == snapshot["biomes"]


def test_minimap_plots_miners_at_their_band(built):
    by_depth = {panel["depth"]: panel for panel in built["minimap"]}
    deep = by_depth[3]  # DeepDelver (4,-2) + MagmaMaven (-6,-6)
    assert {p["name"] for p in deep["points"]} == {"DeepDelver", "MagmaMaven"}
    delver = next(p for p in deep["points"] if p["name"] == "DeepDelver")
    assert (delver["x"], delver["y"]) == (4, -2)
    assert deep["bounds"] == {
        "min_x": -6, "max_x": 4, "min_y": -6, "max_y": -2,
    }
    assert deep["unplotted"] == []


def test_minimap_lists_unplottable_miners_honestly():
    miners = [
        {"display_name": "Lost", "depth": 1, "position": {"x": "?", "y": 0}},
        {"display_name": "Found", "depth": 1, "position": {"x": 5, "y": 5}},
    ]
    panel = views.build_minimap(miners, 1, [])[1]
    assert panel["unplotted"] == ["Lost"]
    assert [p["name"] for p in panel["points"]] == ["Found"]
    assert panel["bounds"] == {
        "min_x": 5, "max_x": 5, "min_y": 5, "max_y": 5,
    }


def test_minimap_empty_band_has_no_bounds():
    # No points → bounds None (the frontend shows an empty state instead
    # of inventing a grid), and the biome label falls back like the ladder.
    empty = views.build_minimap([], 3, [])
    assert all(p["bounds"] is None and p["points"] == [] for p in empty)
    assert [p["biome"] for p in empty] == [
        "depth 0", "depth 1", "depth 2", "depth 3",
    ]


# --- snapshot staleness ------------------------------------------------------


def test_parse_generated_at_utc_z_form(snapshot):
    expected = int(
        datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    )
    assert views.parse_generated_at("2026-07-11T12:00:00Z") == expected
    assert views.parse_generated_at(snapshot["generated_at"]) == expected


def test_parse_generated_at_offset_and_naive_forms_agree():
    z = views.parse_generated_at("2026-07-11T12:00:00Z")
    assert views.parse_generated_at("2026-07-11T12:00:00+00:00") == z
    # No offset → read as UTC, per the contract ("ISO 8601 UTC instant").
    assert views.parse_generated_at("2026-07-11T12:00:00") == z


def test_parse_generated_at_unknown_is_none():
    assert views.parse_generated_at(None) is None
    assert views.parse_generated_at(1783728000) is None
    assert views.parse_generated_at("not a timestamp") is None


def test_staleness_block_ships_prose_thresholds(snapshot, built):
    staleness = built["staleness"]
    assert staleness["generated_at"] == snapshot["generated_at"]
    assert staleness["generated_at_epoch"] == views.parse_generated_at(
        snapshot["generated_at"]
    )
    assert staleness["cadence_seconds"] == views.SNAPSHOT_CADENCE_SECONDS == 60
    assert (
        staleness["stale_after_seconds"]
        == views.STALE_AFTER_SECONDS
        == 3 * views.SNAPSHOT_CADENCE_SECONDS
    )


def test_staleness_block_unknown_timestamp_is_honest():
    staleness = views.build_staleness({})
    assert staleness["generated_at"] is None
    assert staleness["generated_at_epoch"] is None
    garbled = views.build_staleness({"generated_at": "yesterday-ish"})
    assert garbled["generated_at"] == "yesterday-ish"  # shown verbatim
    assert garbled["generated_at_epoch"] is None  # but age stays unknown


# --- gear panel ----------------------------------------------------------


def test_shape_gear_covers_every_schema_slot(snapshot):
    miner = snapshot["miners"][0]
    gear = views.shape_gear(miner)
    assert [row["slot"] for row in gear] == views.equipment_slots()


def test_shape_gear_joins_wear_and_keeps_empty_slots_honest(snapshot):
    miner = snapshot["miners"][0]  # DeepDelver: tool/light/charm equipped
    gear = {row["slot"]: row for row in views.shape_gear(miner)}
    assert gear["tool"]["item"] == "diamond pickaxe"
    assert gear["tool"]["wear"] == miner["gear_wear"]["diamond pickaxe"]
    assert gear["charm"]["item"] == "lucky charm"
    assert gear["charm"]["wear"] is None  # equipped but no wear entry
    assert gear["boots"]["item"] is None  # unequipped slot stays visible
    assert gear["boots"]["wear"] is None


def test_shape_gear_tolerates_missing_maps():
    gear = views.shape_gear({})
    assert len(gear) == len(views.equipment_slots())
    assert all(row["item"] is None and row["wear"] is None for row in gear)


# --- vault panel ---------------------------------------------------------


def test_shape_vault_level_and_grouping(snapshot):
    miner = snapshot["miners"][0]  # vault_level 3, gold/diamond/silver
    vault = views.shape_vault(miner)
    assert vault["level"] == 3
    assert vault["level_max"] == views.vault_level_max()
    assert [name for name, _ in vault["ores"]] == ["silver", "gold", "diamond"]


def test_shape_vault_empty_vault_is_an_empty_state(snapshot):
    pebble = next(
        m for m in snapshot["miners"] if m["display_name"] == "PebblePicker"
    )
    vault = views.shape_vault(pebble)
    assert vault["level"] == 0
    assert vault["ores"] == [] and vault["other"] == []


def test_shape_vault_tolerates_missing_fields():
    vault = views.shape_vault({})
    assert vault["level"] == 0
    assert vault["ores"] == [] and vault["other"] == []


# --- depth/biome ladder --------------------------------------------------


def test_ladder_has_a_band_per_depth(snapshot):
    ladder = views.build_ladder(
        snapshot["miners"], snapshot["max_depth"], snapshot["biomes"]
    )
    assert [band["depth"] for band in ladder] == [0, 1, 2, 3]
    assert [band["biome"] for band in ladder] == snapshot["biomes"]


def test_ladder_places_current_and_record_depths(snapshot):
    ladder = views.build_ladder(
        snapshot["miners"], snapshot["max_depth"], snapshot["biomes"]
    )
    by_depth = {band["depth"]: band for band in ladder}
    # CavernCrawler: depth 1, record_depth 2 — current chip at 1,
    # record-only marker at 2.
    assert "CavernCrawler" in by_depth[1]["here"]
    assert "CavernCrawler" in by_depth[2]["record_only"]
    # PebblePicker: depth 0, record 1.
    assert "PebblePicker" in by_depth[0]["here"]
    assert "PebblePicker" in by_depth[1]["record_only"]
    # A miner at their record depth appears once, as current only.
    assert "DeepDelver" in by_depth[3]["here"]
    assert "DeepDelver" not in by_depth[3]["record_only"]


def test_ladder_biome_fallback_when_hints_absent():
    ladder = views.build_ladder([], 3, [])
    assert [band["biome"] for band in ladder] == [
        "depth 0", "depth 1", "depth 2", "depth 3",
    ]


# --- leaderboards ---------------------------------------------------------


def test_leaderboards_ship_all_three_boards(built):
    assert set(built["leaderboards"]) == {"depth", "xp_level", "coins"}


def test_depth_board_matches_existing_ordering(snapshot, built):
    ranked = [row[1] for row in built["leaderboards"]["depth"]["rows"]]
    expected = [
        m["display_name"]
        for m in sorted(
            snapshot["miners"],
            key=lambda m: (m["depth"], m["xp"]["game_total"]),
            reverse=True,
        )
    ]
    assert ranked == expected


def test_xp_level_board_sorted_by_level(snapshot, built):
    rows = built["leaderboards"]["xp_level"]["rows"]
    levels = [row[2] for row in rows]
    assert levels == sorted(levels, reverse=True)
    assert rows[0][1] == "MagmaMaven"  # level 16 in the sample
    assert [row[0] for row in rows] == list(range(1, len(rows) + 1))


def test_coins_board_sorted_by_coins(built):
    rows = built["leaderboards"]["coins"]["rows"]
    coins = [row[2] for row in rows]
    assert coins == sorted(coins, reverse=True)
    assert rows[0][1] == "MagmaMaven"  # 25990 coins in the sample
    assert rows[-1][1] == "PebblePicker"  # 480 coins


def test_leaderboards_tolerate_malformed_miners():
    boards = views.build_leaderboards([{}, {"coins": 5, "display_name": "x"}])
    assert boards["coins"]["rows"][0][1] == "x"
    assert boards["coins"]["rows"][1][2] == 0  # missing coins ranks as 0


# --- inventory browser (guild matrix) ------------------------------------


def test_inventory_matrix_totals_and_columns(snapshot, built):
    matrix = built["inventory"]
    assert matrix["columns"] == [
        m["display_name"] for m in snapshot["miners"]
    ]
    by_item = {row[0]: row for row in matrix["rows"]}
    stone = by_item["stone"]
    expected_total = sum(
        m["mining_inventory"].get("stone", 0) for m in snapshot["miners"]
    )
    assert stone[1] == expected_total
    assert sum(stone[2:]) == expected_total


def test_inventory_matrix_orders_ores_first(built):
    items = [row[0] for row in built["inventory"]["rows"]]
    present_ores = [t for t in views.ORE_TIER_ORDER if t in items]
    assert items[: len(present_ores)] == present_ores
    rest = items[len(present_ores):]
    assert rest == sorted(rest)  # then the rest, alphabetical


def test_inventory_matrix_empty_guild():
    assert views.build_inventory_matrix([]) == {"columns": [], "rows": []}


# --- the whole document ----------------------------------------------------


def test_build_views_envelope(snapshot, built):
    assert built["schema_version"] == snapshot["schema_version"]
    assert built["generated_at"] == snapshot["generated_at"]
    assert built["guild_id"] == snapshot["guild_id"]
    assert built["world"] == {
        "max_depth": snapshot["max_depth"],
        "biomes": snapshot["biomes"],
    }
    assert built["slots"] == views.equipment_slots()
    assert len(built["miners"]) == len(snapshot["miners"])


def test_build_views_shaped_miner_carries_all_panels(built):
    miner = built["miners"][0]
    for panel in ("gear", "pack", "vault", "xp", "energy",
                  "skills", "structures", "position"):
        assert panel in miner
    assert miner["energy"]["max"] == views.energy_max()
    assert set(miner["xp"]) == set(views.xp_fields())


def test_build_views_carries_minimap_and_staleness(built):
    assert "minimap" in built
    assert "staleness" in built
    assert len(built["minimap"]) == len(built["ladder"])


def test_build_views_empty_snapshot_renders_empty_states():
    built = views.build_views(
        {
            "schema_version": "1",
            "generated_at": "2026-07-11T12:00:00Z",
            "guild_id": "1",
            "miners": [],
        }
    )
    assert built["miners"] == []
    assert built["inventory"] == {"columns": [], "rows": []}
    assert all(
        band["here"] == [] and band["record_only"] == []
        for band in built["ladder"]
    )
    # No max_depth hint → the schema's depth bound backstops the ladder.
    assert len(built["ladder"]) == views.depth_max() + 1
    for board in built["leaderboards"].values():
        assert board["rows"] == []


def test_build_views_never_crashes_on_garbage():
    built = views.build_views({"miners": "not-a-list"})
    assert built["miners"] == []
    assert built["staleness"]["generated_at_epoch"] is None
    built = views.build_views({"miners": [None, 42, {}]})
    assert len(built["miners"]) == 1  # only the dict survives, shaped
    assert built["miners"][0]["coins"] == 0
    assert built["miners"][0]["position"] is None
    assert built["miners"][0]["skills"] == []
    assert built["miners"][0]["structures"] == []


def test_build_views_is_json_serializable(built):
    json.dumps(built)


# --- GET /api/views over real HTTP -----------------------------------------


@pytest.fixture()
def serve():
    servers = []

    def _start(**kwargs):
        server = make_server(port=0, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        host, port = server.server_address[:2]
        return f"http://{host}:{port}"

    yield _start
    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def fetch(url):
    with urllib.request.urlopen(url) as res:
        return res.status, res.headers, res.read()


def test_views_route_serves_shaped_document(serve, built):
    status, headers, body = fetch(serve() + "/api/views")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    assert json.loads(body) == built


def test_views_route_missing_snapshot_is_honest_503(serve, tmp_path):
    base = serve(snapshot_path=tmp_path / "gone.json", web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/views")
    assert excinfo.value.code == 503
    assert json.loads(excinfo.value.read())["error"] == "snapshot unavailable"


def test_views_route_corrupt_snapshot_is_honest_503(serve, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2,")
    base = serve(snapshot_path=bad, web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/views")
    assert excinfo.value.code == 503


def test_views_route_empty_guild_still_200(serve, tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({
        "schema_version": "1",
        "generated_at": "2026-07-11T12:00:00Z",
        "guild_id": "1",
        "miners": [],
    }))
    base = serve(snapshot_path=empty, web_root=WEB_ROOT)
    status, _, body = fetch(base + "/api/views")
    assert status == 200
    assert json.loads(body)["miners"] == []


def test_frontend_wires_the_new_sections(serve):
    """Smoke: the served frontend carries the new views' anchors."""
    base = serve()
    _, _, html = fetch(base + "/")
    for anchor in (b"depth-ladder", b"inventory-browser", b"board-tabs"):
        assert anchor in html, f"index.html missing {anchor}"
    _, _, js = fetch(base + "/app.js")
    assert b"/api/views" in js


def test_frontend_wires_the_slice2_sections(serve):
    """Smoke: mini-map, staleness line, skills/structures/energy anchors."""
    base = serve()
    _, _, html = fetch(base + "/")
    for anchor in (b"minimap", b"snapshot-staleness"):
        assert anchor in html, f"index.html missing {anchor}"
    _, _, js = fetch(base + "/app.js")
    for anchor in (b"renderMinimap", b"renderStaleness", b"energyMeter",
                   b"Skills", b"Structures", b"stale_after_seconds",
                   b"generated_at_epoch"):
        assert anchor in js, f"app.js missing {anchor}"


def test_frontend_paints_identity_and_xp_game(serve):
    """Smoke: suid identity line, header guild id, xp.game on the card."""
    base = serve()
    _, _, js = fetch(base + "/app.js")
    for anchor in (b"identity-line", b"miner.suid", b"views.guild_id",
                   b"xp.game"):
        assert anchor in js, f"app.js missing {anchor}"
    _, _, css = fetch(base + "/style.css")
    assert b"identity-line" in css, "style.css missing identity-line"
