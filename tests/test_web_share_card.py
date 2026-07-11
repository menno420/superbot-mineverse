"""Share-card + Konami-prefix pins for the static frontend (web/).

Same served-bytes style as tests/test_web_fun.py / test_web_a11y.py:
one real server, substring asserts on the served files. Pins the
canvas-drawn PNG share card (real button, honest aria-label, offscreen
canvas, toBlob/dataURL download, cave palette + oreIconSVG gem reuse,
no new animation), the Konami longest-prefix fallback fix, and the
shared tableHeadRow() column-header helper.

Known gap, stated on purpose: the repo has NO pytest harness that
EXECUTES frontend JS (all web tests are byte pins), so
konamiNextProgress() is kept a small pure function and pinned
structurally here; its behavior was exercised end-to-end in a real
browser during the PR's verification instead.
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


# --- share card: a real, honestly-labelled button --------------------------------


def test_share_button_is_a_real_button_with_honest_label(js):
    assert 'el("button", "share-button", "Download card (PNG)")' in js
    assert 'button.type = "button";' in js
    # Label-in-name: the accessible name STARTS with the visible text,
    # and says honestly that a PNG image gets downloaded.
    assert '`Download card (PNG) — save ${miner.display_name}\'s miner card `' \
        in js
    assert '"as a PNG image"' in js
    # The button ships on every rendered miner card (public cards AND the
    # my-miner view, which reuses renderMinerCard).
    assert "card.appendChild(shareCardButton(miner, world));" in js


def test_share_card_is_client_side_canvas_only(js):
    # Offscreen canvas — created, drawn, downloaded; never inserted.
    assert 'document.createElement("canvas"); // offscreen, never in DOM' in js
    assert "canvas.width = SHARE_CARD_WIDTH;" in js
    assert "canvas.height = SHARE_CARD_HEIGHT;" in js
    # Download path: toBlob first, dataURL fallback, temporary <a download>.
    assert 'typeof canvas.toBlob === "function"' in js
    assert 'canvas.toDataURL("image/png")' in js
    assert "link.download = fileName;" in js
    assert "URL.revokeObjectURL(href)" in js
    # No network anywhere in the share-card path: the only fetch()es in
    # app.js remain the three API reads/writes that predate this feature.
    assert js.count("fetch(") == 3


def test_share_card_mirrors_the_cave_theme_and_ore_gems(js):
    # Canvas twin of the style.css palette…
    for hex_pin in ('"#17141f"', '"#0e0c14"', '"#221d2e"', '"#3a3350"',
                    '"#e8e4f2"', '"#a79fc0"', '"#f5a83c"'):
        assert hex_pin in js, f"share-card theme missing {hex_pin}"
    # …and the gem flourish reuses the oreIconSVG geometry + tier colors.
    assert "function drawShareCardGem" in js
    assert "Same gem geometry as oreIconSVG" in js
    assert "Object.entries(ORE_TIER_COLORS)" in js


def test_share_card_content_lines_are_pure_and_pinned(js):
    # Pure text-shaping seam (name, depth/biome/record, level/XP/coins,
    # key gear) — emoji-free for reliable canvas glyphs.
    assert "function shareCardLines" in js
    assert "function shareCardGearLines" in js
    assert "function biomeName" in js  # plain name, no emoji, for canvas
    assert "record depth ${miner.record_depth}" in js
    assert '"(no gear equipped)"' in js
    assert "function shareCardFileName" in js
    assert "mineverse-${base || \"miner\"}-card.png" in js


def test_share_card_adds_no_animation_and_keeps_the_single_motion_gate(js, css):
    # One static frame: the share-card path never touches the animation
    # machinery, and the single JS motion gate stays single.
    assert js.count('window.matchMedia("(prefers-reduced-motion: reduce)")') \
        == 1
    share = css.split("button.share-button", 1)[1]
    assert "animation" not in share.split("}", 2)[0]


def test_share_button_keeps_the_cave_button_styling(css):
    assert "button.share-button {" in css
    share = css.split("button.share-button {", 1)[1]
    assert "cursor: pointer;" in share
    assert "border: 1px solid var(--edge);" in share


# --- Konami: longest-prefix fallback (no more lost progress) ----------------------


def test_konami_mismatch_falls_back_to_longest_prefix(js):
    assert "function konamiNextProgress" in js
    # The KMP-style contract, pinned in prose next to the code.
    assert "LONGEST prefix of the" in js
    assert "sequence that is a suffix of that input" in js
    # The detector routes through the pure function…
    assert "konamiProgress = konamiNextProgress(konamiProgress, key, " \
        "KONAMI_SEQUENCE);" in js
    # …and the old lossy reset is gone.
    assert "key === KONAMI_SEQUENCE[0] ? 1 : 0" not in js


# --- shared tableHeadRow helper -----------------------------------------------------


def test_table_head_row_helper_owns_all_three_tables(js):
    assert "function tableHeadRow" in js
    assert 'tableHeadRow(["#", "Miner", ...(board?.columns || [])])' in js
    assert 'tableHeadRow(["Item", "Total", ...matrix.columns])' in js
    assert 'tableHeadRow(["Stat", a.display_name, b.display_name])' in js
