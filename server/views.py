"""Read-only view shaping over the snapshot — stdlib-only, pure functions.

``GET /api/views`` (server/app.py) serves :func:`build_views` over the
same snapshot document ``GET /api/snapshot`` relays verbatim.  Everything
here is a DERIVED read projection for the frontend: no state, no writes,
no new contract — the READ contract v1 (docs/mining-data-contract.md +
schemas/mining_snapshot.v1.schema.json) stays the single source of truth.

Schema-derived, never hand-copied: the equipment slot list, the xp field
list and the vault/depth/energy bounds are read from the committed v1
schema file at import time, so this module cannot drift from the
contract (tests/test_views.py pins the wiring).

Every shaper tolerates missing or empty fields — a degraded snapshot
renders as honest empty structures, never a crash.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "mining_snapshot.v1.schema.json"

_SCHEMA = json.loads(SCHEMA_PATH.read_text())
_MINER_PROPS = _SCHEMA["$defs"]["miner"]["properties"]

# Display-order hint only, from the contract PROSE ("Ore progression runs
# stone → diamond", docs/mining-data-contract.md §per-miner fields).  Item
# keys are contractually OPEN, so unknown items simply land in the
# "other" bucket — this tuple can lag game content without ever breaking
# conformance or hiding an item.
ORE_TIER_ORDER = ("stone", "bronze", "iron", "silver", "gold", "diamond")


def equipment_slots() -> list[str]:
    """The closed slot enum, straight from the v1 schema."""
    return list(_MINER_PROPS["equipment"]["propertyNames"]["enum"])


def xp_fields() -> list[str]:
    """The xp projection's required field names, from the v1 schema."""
    return list(_MINER_PROPS["xp"]["required"])


def vault_level_max() -> int:
    return _MINER_PROPS["vault_level"]["maximum"]


def depth_max() -> int:
    return _MINER_PROPS["depth"]["maximum"]


def energy_max() -> int:
    return _MINER_PROPS["energy"]["properties"]["current"]["maximum"]


def group_items(store: dict | None) -> dict:
    """Split an item→count map into ordered ``ores`` and ``other`` lists.

    Ores come first in tier order (stone → diamond); everything else
    follows alphabetically.  Entries are ``[name, count]`` pairs so JSON
    preserves the ordering (objects would not).
    """
    store = store if isinstance(store, dict) else {}
    ores = [
        [name, store[name]]
        for name in ORE_TIER_ORDER
        if name in store
    ]
    other = [
        [name, count]
        for name, count in sorted(store.items())
        if name not in ORE_TIER_ORDER
    ]
    return {"ores": ores, "other": other}


def shape_gear(miner: dict) -> list[dict]:
    """One row per schema slot: ``{slot, item|None, wear|None}``.

    Unequipped slots stay present with ``item: None`` so the frontend
    renders an honest empty slot instead of hiding it.  ``wear`` joins
    from the miner's ``gear_wear`` map when the equipped item has an
    entry there.
    """
    equipment = miner.get("equipment") or {}
    gear_wear = miner.get("gear_wear") or {}
    rows = []
    for slot in equipment_slots():
        item = equipment.get(slot)
        rows.append({
            "slot": slot,
            "item": item,
            "wear": gear_wear.get(item) if item is not None else None,
        })
    return rows


def shape_vault(miner: dict) -> dict:
    """Vault panel data: tier level (bounded by the schema max) + items."""
    level = miner.get("vault_level")
    return {
        "level": level if isinstance(level, int) else 0,
        "level_max": vault_level_max(),
        **group_items(miner.get("vault")),
    }


def shape_miner(miner: dict) -> dict:
    """The per-miner card projection the frontend renders."""
    xp = miner.get("xp") or {}
    energy = miner.get("energy") or {}
    return {
        "suid": miner.get("suid"),
        "display_name": miner.get("display_name") or f"miner {miner.get('suid')}",
        "depth": miner.get("depth", 0),
        "record_depth": miner.get("record_depth", 0),
        "position": miner.get("position"),
        "coins": miner.get("coins", 0),
        "energy": {"current": energy.get("current"), "max": energy_max()},
        "xp": {field: xp.get(field) for field in xp_fields()},
        "gear": shape_gear(miner),
        "pack": group_items(miner.get("mining_inventory")),
        "vault": shape_vault(miner),
    }


def build_ladder(miners: list, max_depth: int, biomes: list) -> list[dict]:
    """Depth bands 0..max_depth, each with its biome and its miners.

    ``here`` lists display names currently AT the band; ``record_only``
    lists names whose record_depth is the band but who are elsewhere now.
    """
    bands = []
    for depth in range(max_depth + 1):
        biome = biomes[depth] if depth < len(biomes) else f"depth {depth}"
        here, record_only = [], []
        for miner in miners:
            name = miner.get("display_name") or miner.get("suid") or "?"
            if miner.get("depth") == depth:
                here.append(name)
            elif miner.get("record_depth") == depth:
                record_only.append(name)
        bands.append({
            "depth": depth,
            "biome": biome,
            "here": here,
            "record_only": record_only,
        })
    return bands


def _board(miners: list, key, columns: list[str]) -> dict:
    ranked = sorted(miners, key=key, reverse=True)
    return {
        "columns": columns,
        "rows": [
            [i + 1, m.get("display_name") or m.get("suid") or "?", *key(m)]
            for i, m in enumerate(ranked)
        ],
    }


def build_leaderboards(miners: list) -> dict:
    """Depth (the existing board), XP-level and coins rankings."""
    def _xp(miner: dict, field: str) -> int:
        xp = miner.get("xp") or {}
        value = xp.get(field)
        return value if isinstance(value, int) else 0

    def _int(miner: dict, field: str) -> int:
        value = miner.get(field)
        return value if isinstance(value, int) else 0

    return {
        "depth": _board(
            miners,
            lambda m: (_int(m, "depth"), _xp(m, "game_total")),
            ["depth", "mining XP"],
        ),
        "xp_level": _board(
            miners,
            lambda m: (_xp(m, "level"), _xp(m, "game_total"), _xp(m, "shared_total")),
            ["level", "mining XP", "shared XP"],
        ),
        "coins": _board(
            miners,
            lambda m: (_int(m, "coins"),),
            ["coins"],
        ),
    }


def build_inventory_matrix(miners: list) -> dict:
    """Guild inventory browser: item rows × miner columns, ores first.

    ``rows`` are ``[item, total, count-per-miner...]`` with per-miner
    counts in ``columns`` order; items order matches :func:`group_items`
    (ore tiers stone → diamond, then the rest alphabetically).
    """
    combined: dict[str, int] = {}
    for miner in miners:
        store = miner.get("mining_inventory")
        if not isinstance(store, dict):
            continue
        for name, count in store.items():
            if isinstance(count, int):
                combined[name] = combined.get(name, 0) + count
    grouped = group_items(combined)
    ordered_items = [name for name, _ in grouped["ores"] + grouped["other"]]
    columns = [m.get("display_name") or m.get("suid") or "?" for m in miners]
    rows = []
    for item in ordered_items:
        counts = [
            (m.get("mining_inventory") or {}).get(item, 0) or 0
            for m in miners
        ]
        rows.append([item, combined[item], *counts])
    return {"columns": columns, "rows": rows}


def build_views(snapshot: dict) -> dict:
    """The whole derived read projection served by ``GET /api/views``."""
    miners_raw = snapshot.get("miners")
    miners = [m for m in miners_raw if isinstance(m, dict)] \
        if isinstance(miners_raw, list) else []
    max_depth = snapshot.get("max_depth")
    if not isinstance(max_depth, int):
        max_depth = depth_max()  # schema fallback when the hint is absent
    biomes = snapshot.get("biomes")
    if not isinstance(biomes, list):
        biomes = []
    return {
        "schema_version": snapshot.get("schema_version"),
        "generated_at": snapshot.get("generated_at"),
        "guild_id": snapshot.get("guild_id"),
        "world": {"max_depth": max_depth, "biomes": biomes},
        "slots": equipment_slots(),
        "miners": [shape_miner(m) for m in miners],
        "ladder": build_ladder(miners, max_depth, biomes),
        "leaderboards": build_leaderboards(miners),
        "inventory": build_inventory_matrix(miners),
    }
