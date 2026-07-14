"""Fun-layer anchors for the static frontend (web/) — served-bytes pins.

Same style as tests/test_web_a11y.py / test_web_visuals.py: one real
server, substring asserts on the served files. Pins the achievements
section, the Konami diamond rain (and its reduced-motion gate), the
Tool Fondler toast + live region, the idle 💤 state, the miner VS view,
the console greeting, the boot loading banner and the cave-art 404
page — plus the rule that
every JS-driven animation routes through the ONE prefersReducedMotion()
gate.
"""

import urllib.error
import urllib.request

import pytest

# The served-bytes fixture stack (base_url server, fetch_text, html/js/css)
# is shared in tests/conftest.py.


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


def test_sample_source_gets_neutral_notice_not_the_stale_alarm(js):
    # staleness.source === "sample" (committed demo file) → a neutral
    # notice instead of the permanent false STALE alarm, and the 💤 idle
    # marks stay off (snapshotIsStale short-circuits false). BOTH
    # consumers must check the source — header line + card idle check.
    assert js.count('staleness?.source === "sample"') == 2
    assert "committed sample data — live relay not connected" in js
    assert 'line.classList.add("sample");' in js


def test_staleness_fallbacks_match_views_constants(js):
    # Drift guard: the frontend's `?? N` staleness fallbacks (header
    # staleness line + snapshotIsStale card idle check) carry the SAME
    # numbers as the server constants they shadow (server/views.py
    # STALE_AFTER_SECONDS / SNAPSHOT_CADENCE_SECONDS, the measured
    # VERDICT-056 values). Extracted from the served bytes by regex —
    # same pattern as shipped_konami_sequence in tests/test_js_logic.py
    # — so retuning one side without the other reds here, wherever the
    # literal moves inside app.js.
    import re
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from server import views  # noqa: E402

    stale_fallbacks = re.findall(r"stale_after_seconds \?\? (\d+)", js)
    cadence_fallbacks = re.findall(r"cadence_seconds \?\? (\d+)", js)
    # Both consumers of the stale threshold, one of the cadence — a
    # dropped fallback (?? gone entirely) is drift too.
    assert len(stale_fallbacks) >= 2
    assert len(cadence_fallbacks) >= 1
    assert {int(n) for n in stale_fallbacks} == {views.STALE_AFTER_SECONDS}
    assert {int(n) for n in cadence_fallbacks} == {
        views.SNAPSHOT_CADENCE_SECONDS
    }


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


# --- boot loading state ----------------------------------------------------------------


def test_boot_raises_a_loading_banner_before_the_snapshot_fetch(js):
    # Until /api/views resolves the page is header-only (every section
    # ships hidden) — boot() must say so through the status banner.
    assert 'showBanner("Loading snapshot…", false);' in js
    assert js.index('showBanner("Loading snapshot…", false);') \
        < js.index('fetch("/api/views")')


def test_loading_banner_clears_before_render_raises_its_own(js):
    assert "function hideBanner" in js
    # Cleared once the snapshot is in hand, BEFORE render() — whose
    # no-miners banner must not be clobbered by the teardown.
    assert "hideBanner();\n    render(views);" in js
    assert 'showBanner("Snapshot loaded, but it contains no miners.", false);' \
        in js


# --- 429 backoff hint (Retry-After → rejection line) ------------------------------------


def test_send_action_reads_retry_after_on_429(js):
    # The relay forwards Retry-After on 429 (tests/test_actions.py pins
    # the allowlist); sendAction must actually READ it — gated on the
    # status so no other rejection ever grows a header-derived suffix.
    assert "function retryAfterText" in js
    assert "res.status === 429" in js
    assert 'retryAfterText(res.headers.get("Retry-After"))' in js
    assert "`✗ ${data.reason_code}: ${data.message}${hint}`" in js


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
