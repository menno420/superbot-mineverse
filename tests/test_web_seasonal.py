"""Seasonal decorations (backlog item 6) — served-bytes pins.

Same style as tests/test_web_audio.py / test_web_fun.py: one real server,
substring asserts on the served files. Pins the static aria-hidden header
slot, the date-injection discipline (the seasonal layer never reads the
clock — only boot() does, once, and passes the date in), the reuse of the
hatSVGRects markup filter (one rect grammar, one junk gate), and the
no-new-motion rule: the seasonal CSS carries zero animation/transition,
the stylesheet's keyframe count is unchanged, and the single JS motion
gate stays single. The pure decision seams (date → season id, id → spec,
spec → SVG) are executed per-CI-run in tests/test_js_logic.py.
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
def html(base_url):
    return fetch_text(base_url, "/")


@pytest.fixture(scope="module")
def js(base_url):
    return fetch_text(base_url, "/app.js")


@pytest.fixture(scope="module")
def css(base_url):
    return fetch_text(base_url, "/style.css")


def seasonal_js_block(js):
    """The seasonal layer's source slice — SEASONAL_EVENTS up to the next
    unrelated function (bandLabel)."""
    assert "const SEASONAL_EVENTS = [" in js
    block = js.split("const SEASONAL_EVENTS = [", 1)[1]
    return block.split("function bandLabel", 1)[0]


# --- the static header slot ---------------------------------------------------


def test_header_slot_is_static_and_aria_hidden(html):
    # The ornament holder ships in the markup itself, aria-hidden from the
    # start — decoration is flavor here (like the diamond rain), never a
    # carrier of information, so assistive tech never sees it at all.
    assert ('<span id="seasonal-decor-slot" class="seasonal-decor" '
            'aria-hidden="true"></span>') in html


def test_slot_is_filled_by_js_only_through_the_pure_svg_seam(js):
    assert 'document.getElementById("seasonal-decor-slot")' in js
    assert "slot.innerHTML = seasonalDecorSVG(spec)" in js


# --- date injection: the seasonal layer never reads the clock ------------------


def test_pure_seams_exist(js):
    for fn in ("function seasonForDate", "function seasonalDecorSpec",
               "function seasonalDecorSVG", "function applySeasonalDecor"):
        assert fn in js, f"app.js missing {fn}"


def test_seasonal_layer_never_reads_the_clock(js):
    # The whole seasonal block is date-INJECTED: no Date construction, no
    # Date.now anywhere inside it — determinism lives in the seams, the
    # clock lives in boot().
    block = seasonal_js_block(js)
    assert "new Date(" not in block
    assert "Date.now(" not in block


def test_boot_injects_the_local_calendar_date_once(js):
    # Exactly two mentions: the definition and the single boot() call.
    assert js.count("applySeasonalDecor(") == 2
    boot = js.split("async function boot()", 1)[1]
    assert "applySeasonalDecor([" in boot
    # Local wall-calendar date, zero-padded to the injected ISO format.
    assert "today.getFullYear()" in boot
    assert 'String(today.getMonth() + 1).padStart(2, "0")' in boot
    assert 'String(today.getDate()).padStart(2, "0")' in boot


def test_season_decision_runs_only_inside_the_impure_caller(js):
    # seasonForDate is called exactly once, by applySeasonalDecor — no
    # second path can disagree with the injected date.
    assert js.count("seasonForDate(") == 2  # definition + the one call
    caller = js.split("function applySeasonalDecor", 1)[1].split(
        "function bandLabel", 1)[0]
    assert "seasonalDecorSpec(seasonForDate(isoDate))" in caller


# --- one rect grammar, one junk filter -----------------------------------------


def test_ornament_markup_reuses_the_hat_pixel_filter(js):
    # seasonalDecorSVG routes through hatSVGRects — the same validated
    # [x, y, w, h, "#hex"] grammar as the cosmetic hats, so no unvetted
    # string can land in seasonal markup either.
    assert "const rects = hatSVGRects(spec.pixels);" in js


def test_seasonal_layer_ships_no_asset_files(js, css):
    # Inline SVG/CSS only: the seasonal block references no files and no
    # URLs, and the stylesheet still loads nothing external.
    block = seasonal_js_block(js)
    for marker in (".png", ".gif", ".jpg", ".webp", "http", "url("):
        assert marker not in block, f"unexpected asset reference {marker}"
    assert "url(" not in css


# --- cosmetic only: no new motion, tint-only CSS -------------------------------


def test_seasonal_css_is_tint_only_no_animation(css):
    assert ".seasonal-decor {" in css
    seasonal = css.split(".seasonal-decor {", 1)[1].split("/* miner VS */", 1)[0]
    assert "animation" not in seasonal
    assert "transition" not in seasonal
    for season in ("winter", "spring", "summer", "autumn",
                   "founding-day", "new-year"):
        assert f"body.season-{season} {{ --glow:" in css, season
    # The season classes retint ONLY the existing lantern glow.
    for line in seasonal.splitlines():
        if line.startswith("body.season-"):
            assert "--glow:" in line and line.count(":") == 1, line


def test_stylesheet_keyframe_count_is_unchanged(css):
    # lantern-flicker, diamond-fall, sparkle-pop — and nothing new: the
    # seasonal layer adds zero motion for reduced-motion to even gate.
    assert css.count("@keyframes") == 3


def test_js_motion_gate_stays_single(js):
    assert js.count('window.matchMedia("(prefers-reduced-motion: reduce)")') \
        == 1


def test_seasonal_state_does_not_persist(js):
    assert "localStorage" not in js
    assert "sessionStorage" not in js
