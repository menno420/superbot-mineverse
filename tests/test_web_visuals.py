"""Cave visual theme anchors for the static frontend (web/).

Byte-pins for the fun-&-visuals slice, in the ``test_web_a11y.py``
served-frontend style: biome-tinted depth bands, the lantern-flicker
keyframes (and the reduced-motion guard that statics them), the
mine-shaft cross-section hooks, ore rarity icons, the vault chest /
energy lantern / gear durability visuals and the leaderboard podium +
count-up. Every graphic here is decoration next to text — these tests
also pin the text equivalents so the visuals can never silently replace
the semantics.
"""

import sys
import threading
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app import make_server  # noqa: E402


@pytest.fixture(scope="module")
def base_url():
    """One real server for the whole module — these are read-only GETs."""
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    yield f"http://{host}:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def fetch_text(base_url, path):
    with urllib.request.urlopen(base_url + path) as res:
        assert res.status == 200
        return res.read().decode("utf-8")


@pytest.fixture(scope="module")
def js(base_url):
    return fetch_text(base_url, "/app.js")


@pytest.fixture(scope="module")
def css(base_url):
    return fetch_text(base_url, "/style.css")


# --- cave theme: biome tints + lantern flicker -------------------------------


def test_css_defines_a_biome_tint_per_depth_band(css):
    for var in ("--biome-0:", "--biome-1:", "--biome-2:", "--biome-3:"):
        assert var in css, f"style.css missing biome tint variable {var}"
    for hook in (".band-depth-0", ".band-depth-1",
                 ".band-depth-2", ".band-depth-3"):
        assert hook in css, f"style.css missing band tint hook {hook}"


def test_js_applies_band_tint_classes(js):
    assert "function bandTintClass" in js
    assert "band-depth-${Math.max(0, Math.min(depth, 3))}" in js
    # Both the ladder and the mini-map bands get the tint.
    assert "`ladder-band ${bandTintClass(band.depth)}`" in js
    assert "`minimap-band ${bandTintClass(panel.depth)}`" in js


def test_css_ships_lantern_flicker_keyframes(css):
    assert "@keyframes lantern-flicker" in css
    assert "animation: lantern-flicker" in css
    # The animated property sets a static base value too, so the
    # reduced-motion end state is a steady glow, not a pop.
    assert "text-shadow: 0 0 8px var(--glow); /* static base" in css


def test_reduced_motion_guard_survived_the_theme(css):
    # The flicker is pure CSS keyframes, so THIS block is what keeps it
    # static under reduced motion — re-pin it from the theme's side.
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "animation-duration: 0.01ms !important" in css
    assert "animation-iteration-count: 1 !important" in css
    assert "transition-duration: 0.01ms !important" in css


# --- mine-shaft cross-section (depth ladder) ---------------------------------


def test_css_fuses_ladder_bands_into_a_shaft(css):
    assert "#depth-ladder .ladder-band { margin: 0; border-radius: 0; }" in css
    assert "#depth-ladder .ladder-band + .ladder-band { border-top: 0; }" in css


def test_js_ships_avatar_and_record_flag_decoration(js):
    assert "function minerAvatarSVG" in js
    assert "function recordFlagSVG" in js
    assert 'svgSpan("miner-avatar", minerAvatarSVG(hat))' in js
    assert 'svgSpan("record-flag", recordFlagSVG())' in js
    # The chip TEXT stays the semantics: name, "· record", empty state.
    assert "`${name} · record`" in js
    assert '"(nobody here)"' in js


def test_svg_decoration_routes_through_decorative(js):
    # Every inline-SVG span is aria-hidden via the decorative() helper.
    assert "function svgSpan" in js
    assert "return decorative(span);" in js


# --- ore identity icons -------------------------------------------------------


def test_ore_icons_cover_all_six_tiers_with_distinct_colors(js):
    assert "function oreIconSVG" in js
    for pin in (
        'stone: "#9aa0a6"',
        'bronze: "#c07f45"',
        'iron: "#aeb6c2"',
        'silver: "#eceff4"',
        'gold: "#f5c842"',
        'diamond: "#7de8e0"',
    ):
        assert pin in js, f"app.js ORE_TIER_COLORS missing {pin}"
    # Item names are contractually open — unknown items get no icon.
    assert "if (!color) return null;" in js


def test_ore_icons_reach_packs_and_inventory_headers(js, css):
    assert 'svgSpan("ore-icon", icon)' in js
    assert "`ore tier-${name}`" in js  # pack/vault ore entries
    assert "`item-name tier-${cell}`" in js  # inventory matrix row headers
    for tier in ("stone", "bronze", "iron", "silver", "gold", "diamond"):
        assert f".tier-{tier}" in css, f"style.css missing text tint .tier-{tier}"


# --- vault chest / energy lantern / gear durability ---------------------------


def test_vault_chest_keeps_a_text_equivalent(js):
    assert "function vaultChestSVG" in js
    assert 'svgSpan("vault-chest", vaultChestSVG(vaultLevel, vaultLevelMax))' in js
    # AT-facing equivalent of the chest fill + pips.
    assert "` vault level ${vaultLevel} of ${vaultLevelMax}`" in js


def test_energy_lantern_dims_and_keeps_meter_semantics(js):
    assert "function lanternSVG" in js
    assert 'svgSpan("energy-lantern",' in js
    # Stepped glow, no ticking; the meter text + as-of line + low state
    # all survive the lantern.
    assert "Math.round(fraction * 4)" in js
    assert "`⚡ ${current ?? \"?\"}/${max ?? \"?\"}`" in js
    assert "as of ${formatEpochUTC(energy.updated_at)}" in js
    assert 'classList.add("low")' in js


def test_gear_wear_bar_is_honest_about_direction(js, css):
    # Contract: gear_wear is ACCUMULATED wear (0 = pristine, no schema
    # max) — the bar fills toward broken, capped for display only.
    assert "const WEAR_DISPLAY_MAX = 100;" in js
    assert "function wearBar" in js
    assert "ACCUMULATED wear (0 = pristine" in js
    # The exact wear number stays visible as text.
    assert "· wear ${wear}" in js
    # Green → amber → red thresholds + broken state with cracked icon.
    assert '"wear-critical" : wear >= 50 ? "wear-worn" : "wear-ok"' in js
    assert "function crackedIconSVG" in js
    assert 'svgSpan("cracked-icon", crackedIconSVG())' in js
    for hook in (".wear-track", ".wear-bar.wear-ok",
                 ".wear-bar.wear-worn", ".wear-bar.wear-critical"):
        assert hook in css, f"style.css missing durability hook {hook}"


# --- leaderboard podium + count-up --------------------------------------------


def test_podium_medals_are_decorative_and_rank_stays_text(js, css):
    assert 'const MEDALS = ["🥇", "🥈", "🥉"]' in js
    assert "`podium podium-${rank + 1}`" in js
    # Medal span is aria-hidden; the rank number is re-appended as text.
    assert 'decorative(el("span", "medal", `${MEDALS[rank]} `))' in js
    assert "document.createTextNode(String(cell))" in js
    for hook in (".podium-1", ".podium-2", ".podium-3"):
        assert hook in css, f"style.css missing podium hook {hook}"


def test_prefers_reduced_motion_helper_gates_the_count_up(js):
    assert "function prefersReducedMotion" in js
    assert 'window.matchMedia("(prefers-reduced-motion: reduce)")' in js
    assert "function countUpCell" in js
    # Reduced motion (or a non-numeric cell) renders instantly.
    assert "prefersReducedMotion() ||" in js


def test_count_up_always_lands_on_the_exact_value(js):
    assert "cell.textContent = finalText; // exact final value — no drift" in js
    # Only score columns animate — rank and name cells stay static text.
    assert "countUpCell(td, cell); // score columns count up" in js
