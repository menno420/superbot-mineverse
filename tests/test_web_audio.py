"""Ambient cave audio anchors (backlog item 5) — served-bytes pins.

Same style as tests/test_web_a11y.py / test_web_fun.py: one real server,
substring asserts on the served files. Pins the muted-by-default honest
toggle (aria-pressed + visible label, real button), the no-autoplay
discipline (the AudioContext constructor is looked up exactly once, inside
startCaveAmbience, which only the toggle's click handler calls), the
synthesized-no-assets rule, the no-persistence choice, and the rule that
the audio adds NO animation and leaves the single motion gate single. The
pure decision seams (graph spec, drip rhythm, toggle face) are executed
per-CI-run in tests/test_js_logic.py.
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


# --- the honest toggle -------------------------------------------------------


def test_toggle_is_a_real_button_muted_by_default(html):
    # Static markup already carries the muted default — the honest state
    # exists even before (or without) any JS running.
    assert ('<button id="cave-audio-toggle" class="audio-toggle" '
            'type="button" aria-pressed="false">🔇 Cave sounds off</button>'
            ) in html


def test_toggle_face_comes_from_the_pure_state_function(js):
    assert "function caveSoundsButtonState" in js
    assert '{ pressed: "true", label: "🔊 Cave sounds on" }' in js
    assert '{ pressed: "false", label: "🔇 Cave sounds off" }' in js
    # The painter applies BOTH halves — aria-pressed and label never split.
    assert 'button.setAttribute("aria-pressed", state.pressed)' in js
    assert "button.textContent = state.label" in js


def test_page_boots_muted_always(js):
    # The JS re-asserts the muted default at load — never the reverse.
    assert ("paintCaveSoundsToggle(caveSoundsButton, false); "
            "// muted by default, always") in js


def test_toggle_state_does_not_persist(html, js):
    # Deliberate: nothing in web/ persists UI state, and the audio choice
    # follows suit — every page load starts muted.
    assert "localStorage" not in js
    assert "sessionStorage" not in js
    assert "localStorage" not in html


# --- no-autoplay discipline --------------------------------------------------


def test_audio_context_is_born_inside_the_toggle_gesture(js):
    # The constructor lookup exists exactly once, inside
    # startCaveAmbience()...
    ctor = "window.AudioContext || window.webkitAudioContext"
    assert js.count(ctor) == 1
    assert ctor in js.split("function startCaveAmbience", 1)[1]
    # ...and the ONLY caller of startCaveAmbience is the toggle handler:
    # exactly two occurrences — the definition and that single call site.
    assert js.count("startCaveAmbience()") == 2
    assert ("startCaveAmbience()"
            in js.split("function onCaveSoundsToggle", 1)[1])
    assert 'caveSoundsButton.addEventListener("click", onCaveSoundsToggle)' \
        in js


def test_missing_webaudio_keeps_the_button_honestly_off(js):
    # No constructor → startCaveAmbience reports false → the face stays
    # "off"; aria-pressed never claims sound that does not exist.
    assert 'if (typeof Ctor !== "function") return false;' in js
    assert "paintCaveSoundsToggle(button, startCaveAmbience())" in js


def test_toggle_off_cleans_up_completely(js):
    assert "function stopCaveAmbience" in js
    assert "clearTimeout(caveDripTimer)" in js
    assert "caveAudioCtx.close()" in js


# --- synthesized, subtle, deterministic ---------------------------------------


def test_ambience_is_synthesized_not_asset_files(html, js):
    # WebAudio primitives only — no audio files anywhere in the frontend.
    for anchor in ("ctx.createBuffer(", "ctx.createBufferSource()",
                   "ctx.createBiquadFilter()", "ctx.createOscillator()",
                   "ctx.createGain()"):
        assert anchor in js, f"app.js missing WebAudio primitive {anchor}"
    for page in (html, js):
        for ext in (".mp3", ".ogg", ".wav", ".m4a", "<audio"):
            assert ext not in page, f"unexpected audio asset marker {ext}"


def test_wiring_is_a_thin_interpreter_of_the_pure_spec(js):
    # The graph the browser builds IS the pure spec — one source of truth,
    # pinned per-CI-run through the js_call harness.
    assert "function caveAmbienceGraphSpec" in js
    assert "const spec = caveAmbienceGraphSpec();" in js
    assert "function buildCaveAudioNode" in js
    assert "caveDripDelaySeconds(caveDripIndex) * 1000" in js


def test_drips_and_wind_are_deterministic_no_randomness(js):
    # Same house rule as the diamond rain: no Math.random in the ambience.
    assert "Math.random" not in js
    assert "function caveDripDelaySeconds" in js


# --- reduced motion: nothing pulses with the audio ----------------------------


def test_audio_adds_no_animation_and_keeps_the_single_motion_gate(js, css):
    # Sound is not motion: nothing on the page animates with the audio, so
    # the single JS motion gate stays single (the test_web_fun.py pin) and
    # the toggle's CSS block carries no animation at all.
    assert js.count('window.matchMedia("(prefers-reduced-motion: reduce)")') \
        == 1
    toggle_block = css.split("button.audio-toggle {", 1)[1].split("}", 1)[0]
    assert "animation" not in toggle_block
    assert "transition" not in toggle_block


def test_toggle_keeps_the_cave_button_styling(css):
    assert "button.audio-toggle {" in css
    toggle = css.split("button.audio-toggle {", 1)[1]
    assert "cursor: pointer;" in toggle
    # Pressed state is visible (accent), matching the board-tab pattern.
    assert 'button.audio-toggle[aria-pressed="true"]' in css
