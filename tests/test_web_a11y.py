"""Accessibility + responsive anchors for the static frontend (web/).

The frontend is vanilla HTML/JS/CSS with no build step, so these tests
pin the served bytes: semantic landmarks and ARIA wiring in
``index.html``, the tab/table/decoration semantics the JS paints, and
the focus-visible / reduced-motion / narrow-viewport rules in the CSS.
A regression that drops a landmark, a role, or the responsive media
query goes red here before it ships.
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


# --- landmarks (index.html) -------------------------------------------------


def test_html_has_semantic_landmarks(html):
    for anchor in ("<header>", "<main>", "<footer>", "<nav"):
        assert anchor in html, f"index.html missing landmark {anchor}"


def test_nav_landmark_is_named(html):
    assert 'aria-label="Account"' in html


def test_every_section_has_an_accessible_name(html):
    # Each <section> is labelled by its own heading via aria-labelledby.
    for section, heading in (
        ("my-miner-section", "my-miner-heading"),
        ("depth-ladder-section", "depth-ladder-heading"),
        ("depth-race-section", "depth-race-heading"),
        ("minimap-section", "minimap-heading"),
        ("leaderboard-section", "leaderboard-heading"),
        ("inventory-browser-section", "inventory-browser-heading"),
        ("miners-section", "miners-heading"),
    ):
        assert f'id="{section}" aria-labelledby="{heading}"' in html
        assert f'id="{heading}"' in html


def test_status_lines_are_live_regions(html):
    # Banner, staleness and action-result update after load — role=status
    # lets screen readers announce them without stealing focus.
    assert html.count('role="status"') >= 3


# --- leaderboard tabs (WAI-ARIA tabs pattern) -------------------------------


def test_tablist_and_tabpanel_are_declared(html):
    assert 'role="tablist"' in html
    assert 'aria-label="Leaderboard type"' in html
    assert 'id="leaderboard-panel"' in html
    assert 'role="tabpanel"' in html
    # The scrollable panel is keyboard-reachable.
    assert 'role="tabpanel" tabindex="0"' in html


def test_tabs_get_full_aria_wiring_in_js(js):
    for anchor in (
        '.setAttribute("role", "tab")',
        '.setAttribute("aria-controls", "leaderboard-panel")',
        '.setAttribute("aria-selected", String(selected))',
        "b.tabIndex = selected ? 0 : -1",  # roving tabindex
        'panel.setAttribute("aria-labelledby", `board-tab-${active}`)',
    ):
        assert anchor in js, f"app.js missing tab wiring {anchor}"


def test_tabs_support_arrow_key_navigation(js):
    for key in ("ArrowRight", "ArrowLeft", '"Home"', '"End"'):
        assert key in js, f"app.js tab keyboard support missing {key}"
    assert 'addEventListener("keydown", onTabKeydown)' in js


# --- tables: captions + header scope ----------------------------------------


def test_leaderboard_table_has_visually_hidden_caption(html, js):
    assert '<caption id="leaderboard-caption" class="visually-hidden">' in html
    # The JS keeps the caption in sync with the selected board.
    assert "caption.textContent" in js


def test_inventory_table_gets_caption_and_scoped_headers(js):
    assert '"Inventory browser — quantity of each item carried, per miner"' in js
    # Column headers on both tables + row headers on the inventory matrix.
    assert js.count('scope = "col"') >= 2
    assert 'scope = "row"' in js


# --- decorative graphics carry text alternatives ----------------------------


def test_decorative_parts_are_aria_hidden(js):
    assert 'setAttribute("aria-hidden", "true")' in js
    # Race bars, energy bars, the mini-map plot and biome icons all route
    # through the decorative() helper.
    assert js.count("decorative(") >= 4


def test_minimap_and_race_ship_text_alternatives(js):
    assert "visuallyHidden(" in js
    assert "position unknown" in js  # unplotted miners stay listed as text
    assert "at (${point.x}, ${point.y})" in js  # plot alternative list
    assert "depth ${miner.depth} of ${world.max_depth}" in js  # race bars


# --- CSS: focus, reduced motion, screen-reader utility, responsive ----------


def test_css_ships_visually_hidden_utility(css):
    assert ".visually-hidden" in css
    assert "clip-path: inset(50%)" in css


def test_css_ships_visible_focus_states(css):
    assert ":focus-visible" in css
    assert "outline: 2px solid var(--accent)" in css


def test_css_respects_prefers_reduced_motion(css):
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "animation-duration: 0.01ms !important" in css
    assert "transition-duration: 0.01ms !important" in css


def test_css_reflows_panels_on_narrow_viewports(css):
    assert "@media (max-width: 30rem)" in css
    narrow = css.split("@media (max-width: 30rem)", 1)[1]
    for selector in (".cards", ".race-row", ".ladder-band", ".minimap-band"):
        assert selector in narrow, f"narrow-viewport block missing {selector}"
    assert "grid-template-columns: 1fr" in narrow
