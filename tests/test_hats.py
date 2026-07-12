"""Tests for the cosmetic-hats derivation (server/views.py, fun layer).

Groomed-backlog item 7: a deterministic per-suid cosmetic hat on the
pixel avatars. ``hat_index``/``build_hats`` are pure functions — same
suid in, same hat out, on every call, process and machine (sha256, never
the salted builtin ``hash()``). These tests pin the catalog's shape and
pixel bounds, determinism, distribution sanity, the exact hats the
committed sample snapshot yields, and that the ``hats`` key on
``build_views`` is purely ADDITIVE (no existing key changes shape).
"""

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import views  # noqa: E402

SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT_PATH.read_text())


@pytest.fixture(scope="module")
def built(snapshot):
    return views.build_views(snapshot)


# --- catalog -----------------------------------------------------------------


def test_catalog_ids_are_ordered_and_unique():
    ids = [entry["id"] for entry in views.HAT_CATALOG]
    assert ids == [
        "miners_helmet", "hard_hat", "lantern_cap", "bandana",
        "tin_crown", "green_beanie", "top_hat", "mushroom_cap",
    ]
    assert len(set(ids)) == len(ids)


def test_catalog_entries_carry_id_label_and_pixels():
    for entry in views.HAT_CATALOG:
        assert set(entry) == {"id", "label", "pixels"}
        assert entry["id"] and entry["label"] and entry["pixels"]


def test_catalog_pixels_are_valid_rects_inside_the_avatar_grid():
    # Every pixel is [x, y, w, h, "#rrggbb"] and stays inside the 8×10
    # grid the frontend's minerAvatarSVG draws (rows 0–1 headroom, row 2
    # base-helmet overlay) — the frontend's hatSVGRects validity filter
    # must never drop a SHIPPED catalog pixel.
    for entry in views.HAT_CATALOG:
        for pixel in entry["pixels"]:
            x, y, w, h, color = pixel
            assert all(isinstance(v, int) for v in (x, y, w, h)), pixel
            assert w > 0 and h > 0, pixel
            assert 0 <= x and x + w <= views.HAT_GRID_WIDTH, pixel
            assert 0 <= y and y + h <= views.HAT_GRID_HEIGHT, pixel
            assert HEX_COLOR.match(color), pixel


# --- derivation: deterministic, stable, distributed --------------------------


def test_hat_index_is_stable_across_calls():
    for suid in ("100000000000000001", "7", None, "", 42):
        assert views.hat_index(suid) == views.hat_index(suid)


def test_hat_index_pinned_vectors():
    # Literal pins: if the digest recipe (sha256, str(suid), first 8
    # bytes big-endian, mod catalog size) OR the catalog size silently
    # changes, every miner's hat changes — these vectors make that a
    # loud test failure instead of a quiet cosmetic reshuffle.
    assert len(views.HAT_CATALOG) == 8
    assert views.hat_index("100000000000000001") == 6  # top_hat
    assert views.hat_index("100000000000000002") == 1  # hard_hat
    assert views.hat_index("100000000000000003") == 4  # tin_crown
    assert views.hat_index(None) == 5  # degraded miner: stable too


def test_hat_index_distribution_covers_the_whole_catalog():
    # Distribution sanity: 200 sequential suids must reach every hat —
    # deterministic (fixed inputs, stable digest), so never flaky.
    indices = {views.hat_index(str(n)) for n in range(1, 201)}
    assert indices == set(range(len(views.HAT_CATALOG)))


def test_build_hats_same_input_same_output():
    miners = json.loads(SNAPSHOT_PATH.read_text())["miners"]
    assert views.build_hats(miners) == views.build_hats(miners)


def test_sample_snapshot_hats_are_pinned_and_varied(built):
    rows = built["hats"]["miners"]
    assert [(r["display_name"], r["hat"]) for r in rows] == [
        ("DeepDelver", "top_hat"),
        ("SilverSeeker", "hard_hat"),
        ("CavernCrawler", "tin_crown"),
        ("PebblePicker", "bandana"),
        ("MagmaMaven", "hard_hat"),
        ("GearGoblin", "green_beanie"),
        ("RustyRelic", "bandana"),
    ]
    # Different suids can land different hats (5 distinct across 7).
    assert len({r["hat"] for r in rows}) == 5


# --- the additive key on build_views -----------------------------------------


def test_build_views_hats_is_additive(snapshot, built):
    assert "hats" in built
    assert set(built["hats"]) == {"catalog", "miners"}
    # Additive means additive: dropping the key restores a document
    # whose other keys are untouched by the hats derivation.
    without = {k: v for k, v in built.items() if k != "hats"}
    rebuilt = views.build_views(snapshot)
    rebuilt.pop("hats")
    assert without == rebuilt


def test_hats_rows_align_with_shaped_miners(built):
    assert [r["suid"] for r in built["hats"]["miners"]] == [
        m["suid"] for m in built["miners"]
    ]
    catalog_ids = {entry["id"] for entry in built["hats"]["catalog"]}
    for row in built["hats"]["miners"]:
        assert set(row) == {"suid", "display_name", "hat"}
        assert row["hat"] in catalog_ids


def test_hats_display_name_matches_the_ladder_fallback():
    # The frontend joins hats onto ladder chips by display_name, so the
    # fallback expression must match build_ladder's exactly.
    miners = [
        {"suid": "9", "display_name": "Steve"},
        {"suid": "9"},          # no name → suid
        {},                     # nothing → "?"
    ]
    rows = views.build_hats(miners)["miners"]
    assert [r["display_name"] for r in rows] == ["Steve", "9", "?"]


def test_build_hats_never_crashes_on_degraded_miners():
    rows = views.build_hats([{}, {"suid": None}])["miners"]
    assert rows[0]["hat"] == rows[1]["hat"]  # both derive from str(None)
    assert rows[0]["hat"] == views.HAT_CATALOG[views.hat_index(None)]["id"]


def test_build_hats_is_json_serializable_and_copies_the_catalog(built):
    json.dumps(built["hats"])
    # The served catalog is a copy — mutating it must not poison the
    # module-level table for later requests.
    built["hats"]["catalog"][0]["pixels"][0][0] = 99
    assert views.HAT_CATALOG[0]["pixels"][0][0] != 99
