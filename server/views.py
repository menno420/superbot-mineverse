"""Read-only view shaping over the snapshot — stdlib-only, pure functions.

``GET /api/views`` (server/app.py) serves :func:`build_views` over the
same snapshot document ``GET /api/snapshot`` relays verbatim.  Everything
here is a DERIVED read projection for the frontend: no state, no writes,
no new contract — the READ contract v1 (docs/mining-data-contract.md +
schemas/mining_snapshot.v1.schema.json) stays the single source of truth.

Schema-derived, never hand-copied: the equipment slot list, the
xp/position/energy field lists and the vault/depth/energy bounds are
read from the committed v1 schema at import time — via the shared
``snapshot_validation.load_schema()`` cached loader (one schema, one
parse, one path constant), so this module cannot drift from the
contract (tests/test_views.py pins the wiring).  The loaded dict is the
CACHED shared instance: everything here reads it (``list(...)`` copies
or scalar lookups), never mutates it.

Every shaper tolerates missing or empty fields — a degraded snapshot
renders as honest empty structures, never a crash.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

try:
    from server import snapshot_validation
except ImportError:  # direct script execution: python3 server/app.py
    import snapshot_validation  # type: ignore[no-redef]

_MINER_PROPS = snapshot_validation.load_schema()["$defs"]["miner"]["properties"]

# Display-order hint only, from the contract PROSE ("Ore progression runs
# stone → diamond", docs/mining-data-contract.md §per-miner fields).  Item
# keys are contractually OPEN, so unknown items simply land in the
# "other" bucket — this tuple can lag game content without ever breaking
# conformance or hiding an item.
ORE_TIER_ORDER = ("stone", "bronze", "iron", "silver", "gold", "diamond")

# Delivery numbers from the contract PROSE (docs/mining-data-contract.md
# § Delivery expectations): the bot targets a fresh snapshot every 60 s,
# and the staleness threshold is 180 s — measured, not folklore: sim-lab
# VERDICT 056 (finalized APPROVE, sim-lab control/outbox.md L999-L1008
# @ 32ff5c3; sims/verdict-056-snapshot-stale-threshold/results.json +
# REPORT.md) prices FALSESTALE(180) ≈ 4.83e-4 ≤ 1/200 with 10× headroom
# and mean outage detection ≈ 145 s ≤ the 240 s cap, at the pinned
# 60 s-cadence model (invented-but-pinned disturbance widths, i.i.d.
# misses — boundaries recorded in the contract doc's Staleness bullet).
# The schema carries no delivery cadence, so — like ORE_TIER_ORDER —
# these are prose-sourced constants, not shape facts.
SNAPSHOT_CADENCE_SECONDS = 60
STALE_AFTER_SECONDS = 3 * SNAPSHOT_CADENCE_SECONDS


def equipment_slots() -> list[str]:
    """The closed slot enum, straight from the v1 schema."""
    return list(_MINER_PROPS["equipment"]["propertyNames"]["enum"])


def xp_fields() -> list[str]:
    """The xp projection's required field names, from the v1 schema."""
    return list(_MINER_PROPS["xp"]["required"])


def position_fields() -> list[str]:
    """The position object's required field names, from the v1 schema."""
    return list(_MINER_PROPS["position"]["required"])


def energy_fields() -> list[str]:
    """The energy object's required field names, from the v1 schema."""
    return list(_MINER_PROPS["energy"]["required"])


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


def rank_counts(store: dict | None) -> list:
    """A dynamic countMap as ``[name, value]`` pairs, highest value first.

    Ties break alphabetically.  Keys are contractually OPEN (skill and
    structure names are oracle-owned), so nothing is filtered by name —
    only non-integer values are dropped, since the schema forbids them.
    Pairs (not an object) so JSON preserves the ordering.
    """
    store = store if isinstance(store, dict) else {}
    entries = [
        (name, value)
        for name, value in store.items()
        if isinstance(value, int)
    ]
    return [
        [name, value]
        for name, value in sorted(entries, key=lambda kv: (-kv[1], kv[0]))
    ]


def shape_position(miner: dict) -> dict | None:
    """The schema-required coordinate fields, or None when unplottable.

    A missing position object, or one whose required fields are absent or
    non-integer, shapes to None so the frontend renders an honest
    "position unknown" instead of plotting garbage.
    """
    position = miner.get("position")
    if not isinstance(position, dict):
        return None
    shaped = {field: position.get(field) for field in position_fields()}
    if not all(isinstance(value, int) for value in shaped.values()):
        return None
    return shaped


def shape_energy(miner: dict) -> dict:
    """Energy meter: the schema-required fields + the schema's 0–60 bound.

    ``updated_at`` (unix epoch seconds of the last bot-side recalculation)
    passes through so the frontend can say "as of <when>" honestly — the
    value is snapshot data, never something to tick forward client-side.
    """
    energy = miner.get("energy") or {}
    shaped = {field: energy.get(field) for field in energy_fields()}
    shaped["max"] = energy_max()
    return shaped


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
    return {
        "suid": miner.get("suid"),
        "display_name": miner.get("display_name") or f"miner {miner.get('suid')}",
        "depth": miner.get("depth", 0),
        "record_depth": miner.get("record_depth", 0),
        "position": shape_position(miner),
        "coins": miner.get("coins", 0),
        "energy": shape_energy(miner),
        "xp": {field: xp.get(field) for field in xp_fields()},
        "gear": shape_gear(miner),
        "pack": group_items(miner.get("mining_inventory")),
        "vault": shape_vault(miner),
        "skills": rank_counts(miner.get("skills")),
        "structures": rank_counts(miner.get("structures")),
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


def build_minimap(miners: list, max_depth: int, biomes: list) -> list[dict]:
    """Position mini-map: one panel per depth band 0..max_depth.

    Each panel carries ``points`` (``{name, x, y}`` for every miner at the
    band whose position shapes cleanly), ``unplotted`` (names at the band
    whose position is missing or malformed — listed honestly, never
    silently dropped) and integer plot ``bounds`` (min/max of x and y over
    the band's points; None when nothing plots, so the frontend shows an
    empty state instead of inventing a grid).
    """
    panels = []
    for depth in range(max_depth + 1):
        biome = biomes[depth] if depth < len(biomes) else f"depth {depth}"
        points, unplotted = [], []
        for miner in miners:
            if miner.get("depth") != depth:
                continue
            name = miner.get("display_name") or miner.get("suid") or "?"
            position = shape_position(miner)
            if position is None:
                unplotted.append(name)
            else:
                points.append({"name": name, **position})
        if points:
            xs = [p["x"] for p in points]
            ys = [p["y"] for p in points]
            bounds = {
                "min_x": min(xs),
                "max_x": max(xs),
                "min_y": min(ys),
                "max_y": max(ys),
            }
        else:
            bounds = None
        panels.append({
            "depth": depth,
            "biome": biome,
            "points": points,
            "unplotted": unplotted,
            "bounds": bounds,
        })
    return panels


# --- achievements (fun layer) — deterministic badges over snapshot data ----
#
# Every threshold is documented here, next to the check that uses it.
# Achievements are a pure derivation: same snapshot in, same badges out —
# no state, no clock, no randomness.

# Packrat: total mining_inventory count at/above this. Chosen against the
# committed sample so some miners hit it (SilverSeeker 212, CavernCrawler
# 227) and some don't (DeepDelver 193, MagmaMaven 80, PebblePicker 51).
PACKRAT_THRESHOLD = 200

# Coin Magnate: coins at/above this. Sample: DeepDelver 18450 and
# MagmaMaven 25990 hit; SilverSeeker 7320 and below don't.
COIN_MAGNATE_THRESHOLD = 10_000

# Tool Breaker: any gear_wear entry at/over the frontend's wear display
# cap (web/app.js WEAR_DISPLAY_MAX = 100). The contract gives accumulated
# wear no schema maximum, so the display cap is the "visibly broken" line.
# Sample: RustyRelic's battered pickaxe sits at 117; nobody else is close.
TOOL_BREAKER_WEAR = 100

# Balanced Build: at least this many skills, with the max−min level
# spread at most this. Sample: SilverSeeker (mining 2, endurance 1) hits;
# DeepDelver (spread 2) and MagmaMaven (spread 3) don't.
BALANCED_BUILD_MIN_SKILLS = 2
BALANCED_BUILD_MAX_SPREAD = 1

# The Answer: exactly this count of any single mining_inventory item —
# the easter-egg badge. Sample: DeepDelver carries exactly 42 stone.
THE_ANSWER_COUNT = 42

# The full catalog, in display order. The frontend renders emoji badges
# aria-hidden with the name as the text label.
ACHIEVEMENT_CATALOG = (
    {"id": "deep_diver", "name": "Deep Diver", "emoji": "🌋",
     "description": "record depth equals the world's max depth"},
    {"id": "packrat", "name": "Packrat", "emoji": "🎒",
     "description": f"carrying {PACKRAT_THRESHOLD}+ items in the pack"},
    {"id": "coin_magnate", "name": "Coin Magnate", "emoji": "💰",
     "description": f"holding {COIN_MAGNATE_THRESHOLD:,}+ coins"},
    {"id": "fully_geared", "name": "Fully Geared", "emoji": "🛡️",
     "description": "every equipment slot filled"},
    {"id": "tool_breaker", "name": "Tool Breaker", "emoji": "🔨",
     "description": f"any gear at {TOOL_BREAKER_WEAR}+ wear"},
    {"id": "balanced_build", "name": "Balanced Build", "emoji": "⚖️",
     "description": (f"{BALANCED_BUILD_MIN_SKILLS}+ skills within "
                     f"{BALANCED_BUILD_MAX_SPREAD} level of each other")},
    {"id": "the_answer", "name": "The Answer", "emoji": "🐬",
     "description": f"exactly {THE_ANSWER_COUNT} of one pack item"},
)


def _int_values(store) -> list[int]:
    """The integer values of a countMap — anything else is ignored.

    Mirrors :func:`rank_counts`'s tolerance: the schema forbids
    non-integer values, so they never count toward an achievement.
    """
    if not isinstance(store, dict):
        return []
    return [value for value in store.values() if isinstance(value, int)]


def earned_achievements(miner: dict, max_depth) -> list[str]:
    """Achievement ids the miner earned, in catalog order.

    Pure snapshot math — every check tolerates missing or malformed
    fields (a degraded miner simply earns nothing, never crashes).
    """
    inventory = _int_values(miner.get("mining_inventory"))
    skills = _int_values(miner.get("skills"))
    wears = _int_values(miner.get("gear_wear"))
    equipment = miner.get("equipment")
    equipment = equipment if isinstance(equipment, dict) else {}
    earned = []
    if isinstance(miner.get("record_depth"), int) \
            and miner["record_depth"] == max_depth:
        earned.append("deep_diver")
    if sum(inventory) >= PACKRAT_THRESHOLD:
        earned.append("packrat")
    if isinstance(miner.get("coins"), int) \
            and miner["coins"] >= COIN_MAGNATE_THRESHOLD:
        earned.append("coin_magnate")
    if all(equipment.get(slot) for slot in equipment_slots()):
        earned.append("fully_geared")
    if any(wear >= TOOL_BREAKER_WEAR for wear in wears):
        earned.append("tool_breaker")
    if len(skills) >= BALANCED_BUILD_MIN_SKILLS \
            and max(skills) - min(skills) <= BALANCED_BUILD_MAX_SPREAD:
        earned.append("balanced_build")
    if any(count == THE_ANSWER_COUNT for count in inventory):
        earned.append("the_answer")
    return earned


def build_achievements(miners: list, max_depth) -> dict:
    """Per-miner achievement badges + the shared catalog.

    An ADDITIVE key on :func:`build_views` — no existing key changes
    shape. ``catalog`` is the ordered badge definitions (id, name,
    emoji, description with the threshold baked into the prose);
    ``miners`` is one ``{suid, display_name, earned}`` row per miner
    with ``earned`` in catalog order (possibly empty — honest zero
    state, e.g. the sample's PebblePicker).
    """
    return {
        "catalog": [dict(entry) for entry in ACHIEVEMENT_CATALOG],
        "miners": [
            {
                "suid": miner.get("suid"),
                "display_name": (miner.get("display_name")
                                 or f"miner {miner.get('suid')}"),
                "earned": earned_achievements(miner, max_depth),
            }
            for miner in miners
        ],
    }


# --- cosmetic hats (fun layer) — deterministic per-suid avatar cosmetic ----
#
# Purely cosmetic: no gameplay meaning, no thresholds, nothing earned —
# a hat is a stable visual identity derived from the miner's suid alone.
# Derivation uses hashlib.sha256 (stable across processes, machines and
# Python versions), NEVER the builtin hash() (salted per process since
# PEP 456 — the same suid would change hats on every restart).
#
# Each catalog entry carries `pixels`: [x, y, w, h, "#rrggbb"] rects on
# the frontend avatar's 8×10 pixel grid (web/app.js minerAvatarSVG).
# Rows 0–1 are hat headroom above the head; row 2 is the base helmet
# row, which a hat may overlay. The frontend's pure hatSVGRects()
# turns these into aria-hidden <rect> markup layered over the avatar.

HAT_CATALOG = (
    {"id": "miners_helmet", "label": "miner's helmet",
     "pixels": [[2, 1, 4, 1, "#f5a83c"], [3, 1, 1, 1, "#fff7d6"]]},
    {"id": "hard_hat", "label": "hard hat",
     "pixels": [[2, 1, 4, 1, "#f5c842"], [1, 2, 6, 1, "#f5c842"]]},
    {"id": "lantern_cap", "label": "lantern cap",
     "pixels": [[2, 1, 4, 1, "#3a3350"], [4, 0, 1, 1, "#f5c842"]]},
    {"id": "bandana", "label": "bandana",
     "pixels": [[2, 2, 4, 1, "#e2543e"], [6, 2, 1, 1, "#e2543e"],
                [6, 3, 1, 1, "#e2543e"]]},
    {"id": "tin_crown", "label": "tin crown",
     "pixels": [[2, 2, 4, 1, "#eceff4"], [2, 1, 1, 1, "#eceff4"],
                [5, 1, 1, 1, "#eceff4"], [3, 2, 1, 1, "#7de8e0"]]},
    {"id": "green_beanie", "label": "green beanie",
     "pixels": [[2, 1, 4, 1, "#5aa85a"], [2, 2, 4, 1, "#5aa85a"],
                [4, 0, 1, 1, "#8fd18f"]]},
    {"id": "top_hat", "label": "top hat",
     "pixels": [[2, 0, 4, 1, "#221d2e"], [2, 1, 4, 1, "#221d2e"],
                [1, 2, 6, 1, "#221d2e"]]},
    {"id": "mushroom_cap", "label": "mushroom cap",
     "pixels": [[1, 2, 6, 1, "#e2543e"], [2, 1, 4, 1, "#e2543e"],
                [2, 2, 1, 1, "#ffffff"], [5, 1, 1, 1, "#ffffff"]]},
)

# The avatar pixel grid the catalog draws on (web/app.js minerAvatarSVG
# viewBox) — pinned here so tests can bound-check every catalog rect.
HAT_GRID_WIDTH = 8
HAT_GRID_HEIGHT = 10


def hat_index(suid) -> int:
    """Deterministic HAT_CATALOG index for a miner suid.

    sha256 of the suid's string form, first 8 digest bytes read as a
    big-endian integer, modulo the catalog size. Same suid → same hat,
    on every call, process and machine — no state, no clock, no
    randomness. A missing suid still derives (from ``str(None)``), so a
    degraded miner keeps a stable hat instead of crashing.
    """
    digest = hashlib.sha256(str(suid).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % len(HAT_CATALOG)


def build_hats(miners: list) -> dict:
    """Per-miner deterministic cosmetic hats + the shared catalog.

    An ADDITIVE key on :func:`build_views` — no existing key changes
    shape (the achievements precedent). ``catalog`` is the ordered hat
    definitions (id, label, pixels); ``miners`` is one
    ``{suid, display_name, hat}`` row per miner, where ``hat`` is a
    catalog id. ``display_name`` uses the SAME fallback expression as
    :func:`build_ladder`, so the frontend can join hats onto ladder
    chips by name.
    """
    return {
        "catalog": [
            {"id": entry["id"], "label": entry["label"],
             "pixels": [list(pixel) for pixel in entry["pixels"]]}
            for entry in HAT_CATALOG
        ],
        "miners": [
            {
                "suid": miner.get("suid"),
                "display_name": (miner.get("display_name")
                                 or miner.get("suid") or "?"),
                "hat": HAT_CATALOG[hat_index(miner.get("suid"))]["id"],
            }
            for miner in miners
        ],
    }


def parse_generated_at(value) -> int | None:
    """``generated_at`` (ISO 8601 UTC) → unix epoch seconds, or None.

    None means "unknown" — missing field, non-string, or an unparseable
    timestamp — so the frontend can say so instead of guessing an age.
    A timestamp without an explicit offset is read as UTC, per the
    contract ("ISO 8601 UTC instant").
    """
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def build_staleness(snapshot: dict, source: str = "sample") -> dict:
    """Staleness metadata for the header — age math stays CLIENT-side.

    The server only translates ``generated_at`` to epoch seconds and ships
    the contract-prose thresholds; the frontend compares against its own
    clock at render time (no live ticking).  ``generated_at_epoch`` is
    None when the timestamp is unknown, and the frontend must say so.

    ``source`` names where the snapshot bytes came from — ``"sample"``
    (the committed demo file, the default) or ``"live"`` (a
    host-configured relay path; server/app.py decides by comparing its
    snapshot path against the committed sample's). The frontend uses it
    to tell "demo data is old by design" apart from "the live relay went
    quiet" — only the latter deserves the STALE alarm.
    """
    generated_at = snapshot.get("generated_at")
    return {
        "generated_at": generated_at if isinstance(generated_at, str) else None,
        "generated_at_epoch": parse_generated_at(generated_at),
        "cadence_seconds": SNAPSHOT_CADENCE_SECONDS,
        "stale_after_seconds": STALE_AFTER_SECONDS,
        "source": source,
    }


def build_views(snapshot: dict, source: str = "sample") -> dict:
    """The whole derived read projection served by ``GET /api/views``.

    ``source`` is threaded into the staleness block untouched — see
    :func:`build_staleness`.
    """
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
        "staleness": build_staleness(snapshot, source),
        "ladder": build_ladder(miners, max_depth, biomes),
        "minimap": build_minimap(miners, max_depth, biomes),
        "leaderboards": build_leaderboards(miners),
        "inventory": build_inventory_matrix(miners),
        "achievements": build_achievements(miners, max_depth),
        "hats": build_hats(miners),
    }
