"""Fun-layer anchors for the static frontend (web/) — served-bytes pins.

Same style as tests/test_web_a11y.py / test_web_visuals.py: one real
server, substring asserts on the served files. Pins the achievements
section, the Konami diamond rain (and its reduced-motion gate), the
Tool Fondler toast + live region, the idle 💤 state, the miner VS view,
the console greeting and the cave-art 404 page — plus the rule that
every JS-driven animation routes through the ONE prefersReducedMotion()
gate.
"""

import sys
import threading
import urllib.error
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
def html(base_url):
    return fetch_text(base_url, "/")


@pytest.fixture(scope="module")
def js(base_url):
    return fetch_text(base_url, "/app.js")


@pytest.fixture(scope="module")
def css(base_url):
    return fetch_text(base_url, "/style.css")


@pytest.fixture(scope="module")
def not_found_page(base_url):
    """The served cave-art 404 body (any unknown non-API path)."""
    try:
        urllib.request.urlopen(base_url + "/definitely-not-here")
    except urllib.error.HTTPError as err:
        assert err.code == 404
        return err.read().decode("utf-8")
    pytest.fail("expected a 404 for an unknown path")


# --- achievements section ------------------------------------------------------


def test_achievements_section_is_wired(html, js):
    assert 'id="achievements-section" aria-labelledby="achievements-heading"' \
        in html
    assert 'id="achievements-rollup"' in html
    assert 'id="achievements-miners"' in html
    assert "function renderAchievements" in js
    assert "renderAchievements(views.achievements)" in js


def test_achievement_badges_keep_text_labels(js):
    # Emoji are aria-hidden decoration; the badge NAME is the text.
    assert 'decorative(el("span", "badge-emoji", `${entry.emoji} `))' in js
    assert "document.createTextNode(entry.name)" in js
    # Honest empty states, both directions.
    assert '"(no achievements yet)"' in js
    assert '" · nobody yet"' in js


# --- Konami code → diamond rain --------------------------------------------------


def test_konami_sequence_is_pinned(js):
    assert "const KONAMI_SEQUENCE = [" in js
    assert '"ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown",' in js
    assert '"ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight",' in js
    assert '"b", "a",' in js
    assert 'document.addEventListener("keydown", onKonamiKeydown)' in js


def test_diamond_rain_reuses_the_diamond_ore_svg(js):
    assert 'svgSpan("diamond-drop", oreIconSVG("diamond"))' in js


def test_diamond_rain_is_reduced_motion_aware(js):
    # The JS gate: reduced motion gets a static flash, never .falling.
    assert "const reduced = prefersReducedMotion();" in js
    assert 'drop.classList.add("falling")' in js
    assert "reduced ? DIAMOND_FLASH_MS : DIAMOND_RAIN_MS" in js


def test_diamond_rain_cleans_up_and_escape_dismisses(js):
    assert "function dismissDiamondRain" in js
    assert "setTimeout(\n    dismissDiamondRain" in js  # auto-clean
    assert 'if (event.key === "Escape")' in js
    # Deterministic scatter — no randomness in the shower.
    assert "(i * 37) % 100" in js


def test_diamond_rain_overlay_cannot_shift_layout(css):
    rain = css.split(".diamond-rain", 1)[1]
    assert "position: fixed;" in rain
    assert "pointer-events: none;" in rain
    assert "@keyframes diamond-fall" in css


# --- Tool Fondler (hidden achievement) --------------------------------------------


def test_toast_is_a_polite_live_region(html, js):
    assert '<p id="toast" class="toast" role="status" hidden></p>' in html
    assert "function showToast" in js


def test_tool_row_is_a_real_button_with_a_per_miner_counter(js):
    assert "const TOOL_FONDLER_CLICKS = 10;" in js
    assert 'el("button", "tool-row")' in js
    assert 'button.type = "button";' in js
    assert "toolClicks" in js  # per-miner (suid-keyed) counter
    assert "Tool Fondler" in js


def test_tool_fondler_sparkle_is_reduced_motion_gated(js, css):
    assert 'if (!prefersReducedMotion()) sparkle.classList.add("sparkle-pop")' \
        in js
    assert "@keyframes sparkle-pop" in css


# --- idle miners (stale snapshot → 💤) ---------------------------------------------


def test_idle_state_pins(js):
    assert "function snapshotIsStale" in js
    # Same thresholds the header staleness line uses.
    assert "staleness?.stale_after_seconds ?? 180" in js
    assert 'decorative(el("span", "idle-mark", " 💤"))' in js
    assert 'visuallyHidden("span", " (idle)")' in js


# --- miner VS view ------------------------------------------------------------------


def test_vs_selects_are_labelled_and_native(html):
    assert 'id="vs-section" aria-labelledby="vs-heading"' in html
    assert '<label for="vs-a">Miner A</label>' in html
    assert '<label for="vs-b">Miner B</label>' in html
    assert '<select id="vs-a"' in html
    assert '<select id="vs-b"' in html


def test_vs_stats_and_pure_helpers_are_pinned(js):
    assert "const VS_STATS = [" in js
    for label in ('"depth"', '"record depth"', '"level"', '"mining XP"',
                  '"coins"', '"energy"', '"vault level"', '"pack total"',
                  '"skill ranks"'):
        assert f"[{label}," in js, f"VS_STATS missing {label}"
    assert "function packTotal" in js
    assert "function skillRankTotal" in js


def test_vs_bars_are_decorative_and_values_stay_text(js):
    assert 'el("span", "vs-value", String(value))' in js
    assert 'decorative(el("span", "vs-track"))' in js
    assert "const peak = Math.max(value, other, 1);" in js


def test_vs_honest_states(js):
    assert '"Pick two miners above to compare them."' in js
    assert "a miner always ties with themself" in js


# --- console greeting -----------------------------------------------------------------


def test_console_greeting_is_pinned(js):
    assert "const CONSOLE_GREETING = [" in js
    assert "M I N E V E R S E" in js
    assert "console.log(CONSOLE_GREETING)" in js


# --- cave-art 404 page ------------------------------------------------------------------


def test_404_page_markers(not_found_page):
    assert "404 — you dug too deep" in not_found_page
    assert '<pre class="cave" aria-hidden="true">' in not_found_page
    assert 'href="/"' in not_found_page
    assert "climb back to the surface" in not_found_page


# --- the a11y ground rules survived the fun layer ------------------------------------------


def test_new_sections_keep_the_labelled_section_pattern(html):
    for section, heading in (
        ("achievements-section", "achievements-heading"),
        ("vs-section", "vs-heading"),
    ):
        assert f'id="{section}" aria-labelledby="{heading}"' in html
        assert f'id="{heading}"' in html


def test_the_single_js_motion_gate_still_stands(js):
    # One JS gate for everything script-driven: count-up (PR 1), the
    # diamond rain and the sparkle (this PR). No second matchMedia path.
    assert js.count('window.matchMedia("(prefers-reduced-motion: reduce)")') \
        == 1
    assert js.count("prefersReducedMotion()") >= 3
