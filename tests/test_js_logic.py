"""JS logic harness — execute the REAL shipped web/app.js pure functions.

Closes the JS-logic-test gap (groomed backlog 2026-07-11, item 2): until
now no JavaScript ever EXECUTED in CI — pytest pinned served bytes only,
and ``konamiNextProgress`` (the PR #40 longest-prefix fix) was verified
once via Playwright, never per-CI-run.

How it works (zero new CI infrastructure):

* Each test shells out to ``node`` (preinstalled on GitHub ubuntu
  runners). If ``node`` is not on PATH locally, the whole module SKIPS
  with a clear reason — same conditional-skip pattern as the
  conformance tests in ``tests/test_actions.py``.
* A small embedded runner script (``_RUNNER_JS``) loads the ACTUAL
  ``web/app.js`` source into a ``vm`` context whose globals carry the
  minimal browser shims the file's top level touches (``document``,
  ``window``, a forever-pending ``fetch`` so ``boot()`` suspends without
  rendering anything). Top-level ``function`` declarations become
  properties of that context, so named pure functions are callable with
  JSON-serializable arguments — the same bytes the browser runs, not a
  copy-pasted twin.
* The harness is reusable: ``js_call(fn, *args)`` for one call,
  ``js_fold(fn, init, stream, *extra)`` to thread state through a key
  stream (returns the whole trace), ``run_js_ops(...)`` to batch many
  operations into ONE node process. New pure functions in web/ can be
  pinned by adding vectors here — no npm, no package.json.
"""

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_JS = REPO_ROOT / "web" / "app.js"

NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(
    NODE is None,
    reason="node not on PATH; JS logic tests skipped (GitHub ubuntu "
    "runners preinstall node, so these always run in CI)",
)

# The runner: reads {"source_path", "ops"} JSON on stdin, loads the real
# JS source into a vm context with minimal browser-global shims, executes
# the ops against the context's top-level functions, writes a JSON array
# of results to stdout. Ops:
#   {"type": "call", "fn": name, "args": [...]}          -> fn(*args)
#   {"type": "fold", "fn": name, "init": x,
#    "stream": [...], "extra": [...]}                    -> trace of
#        acc = fn(acc, item, *extra) for each item (whole trace back)
_RUNNER_JS = r"""
"use strict";
const fs = require("fs");
const vm = require("vm");

const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const source = fs.readFileSync(payload.source_path, "utf8");

const noop = () => {};
const stubElement = () => ({
  className: "", textContent: "", hidden: false, style: {},
  setAttribute: noop, appendChild: noop, remove: noop,
  addEventListener: noop,
  classList: { add: noop, remove: noop, toggle: noop },
});
const sandbox = {
  document: {
    addEventListener: noop,
    getElementById: () => stubElement(),
    createElement: () => stubElement(),
    createTextNode: () => ({}),
    body: stubElement(),
  },
  window: { matchMedia: () => ({ matches: false }) },
  // Forever-pending fetch: boot() suspends at its first await and never
  // renders, rejects, or keeps the event loop alive. No network ever.
  fetch: () => new Promise(noop),
  console: { log: noop, warn: noop, error: noop },
  setTimeout: () => 0,
  clearTimeout: noop,
};
vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: payload.source_path });

const results = payload.ops.map((op) => {
  const fn = sandbox[op.fn];
  if (typeof fn !== "function") {
    throw new Error(
      "no top-level function '" + op.fn + "' in " + payload.source_path);
  }
  if (op.type === "call") return fn(...op.args);
  if (op.type === "fold") {
    const extra = op.extra || [];
    const trace = [];
    let acc = op.init;
    for (const item of op.stream) {
      acc = fn(acc, item, ...extra);
      trace.push(acc);
    }
    return trace;
  }
  throw new Error("unknown op type '" + op.type + "'");
});
process.stdout.write(JSON.stringify(results === undefined ? null : results));
"""


def run_js_ops(ops, source=APP_JS):
    """Run a batch of ops against `source` in one node process."""
    payload = json.dumps({"source_path": str(source), "ops": ops})
    proc = subprocess.run(
        [NODE, "-e", _RUNNER_JS],
        input=payload,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"node runner failed (exit {proc.returncode}):\n{proc.stderr}"
        )
    return json.loads(proc.stdout)


def js_call(fn, *args):
    """Call one named top-level pure function from web/app.js."""
    return run_js_ops([{"type": "call", "fn": fn, "args": list(args)}])[0]


def js_fold(fn, init, stream, *extra):
    """acc = fn(acc, item, *extra) over `stream`; returns the full trace."""
    return run_js_ops(
        [{"type": "fold", "fn": fn, "init": init,
          "stream": list(stream), "extra": list(extra)}]
    )[0]


# --- the shipped Konami sequence, read from the real source ----------------

# The tests below pass `sequence` explicitly (it is a parameter of the pure
# function); this extraction pins that the vectors exercise the SEQUENCE THE
# BROWSER ACTUALLY USES, not a stale copy in this file.
def shipped_konami_sequence():
    src = APP_JS.read_text(encoding="utf-8")
    match = re.search(r"const KONAMI_SEQUENCE = \[(.*?)\];", src, re.DOTALL)
    assert match, "KONAMI_SEQUENCE literal not found in web/app.js"
    return re.findall(r'"([^"]+)"', match.group(1))


KONAMI = shipped_konami_sequence()

UP, DOWN, LEFT, RIGHT = "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"


def test_shipped_sequence_is_the_konami_code():
    assert KONAMI == [UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, "b", "a"]


# --- konamiNextProgress: the PR #40 longest-prefix automaton ----------------


def reference_progress(history, sequence):
    """Gold standard: the longest prefix of `sequence` that is a suffix of
    the ENTIRE key history. A correct KMP-style step function folded over
    the stream must agree with this at every step."""
    for length in range(min(len(history), len(sequence)), 0, -1):
        if history[-length:] == sequence[:length]:
            return length
    return 0


def reference_trace(stream, sequence):
    return [
        reference_progress(stream[: i + 1], sequence)
        for i in range(len(stream))
    ]


def test_konami_full_sequence_reaches_ten():
    assert js_fold("konamiNextProgress", 0, KONAMI, KONAMI) == list(
        range(1, 11)
    )


def test_konami_third_arrowup_keeps_progress_two():
    # THE PR #40 fix: after ↑↑ a third ArrowUp must keep progress 2 (the
    # last two keys are still a valid prefix), not fall back to 1 or 0.
    assert js_fold("konamiNextProgress", 0, [UP, UP, UP], KONAMI) == [1, 2, 2]


def test_konami_up_up_up_then_rest_still_fires():
    # ...and because progress stayed 2, finishing the code after the
    # stutter still reaches 10 without re-entering the first two keys.
    stream = [UP, UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, "b", "a"]
    trace = js_fold("konamiNextProgress", 0, stream, KONAMI)
    assert trace == [1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_konami_mismatch_that_restarts_at_one():
    # ↑↑↓↓ then ↑: the ↑ breaks the run but IS the first key of the code.
    assert js_fold("konamiNextProgress", 0, [UP, UP, DOWN, DOWN, UP], KONAMI) == [
        1, 2, 3, 4, 1,
    ]


def test_konami_mismatch_that_resets_to_zero():
    # ↑↓ — the ↓ is neither a continuation nor a restart.
    assert js_fold("konamiNextProgress", 0, [UP, DOWN], KONAMI) == [1, 0]


def test_konami_garbage_key_resets_to_zero():
    assert js_call("konamiNextProgress", 7, "Escape", KONAMI) == 0
    assert js_call("konamiNextProgress", 9, "x", KONAMI) == 0


def test_konami_single_step_vectors():
    vectors = [
        # (progress, key, expected)
        (0, UP, 1),
        (0, DOWN, 0),
        (0, "a", 0),
        (1, UP, 2),
        (2, UP, 2),  # longest-prefix hold — the PR #40 case
        (2, DOWN, 3),
        (4, LEFT, 5),
        (7, RIGHT, 8),
        (8, "b", 9),
        (8, "a", 0),  # right letter family, wrong order
        (9, "a", 10),
        (9, "b", 0),  # "b" repeated: no prefix of the code ends ...bb
    ]
    ops = [
        {"type": "call", "fn": "konamiNextProgress",
         "args": [progress, key, KONAMI]}
        for progress, key, _ in vectors
    ]
    results = run_js_ops(ops)
    for (progress, key, expected), got in zip(vectors, results):
        assert got == expected, f"progress={progress} key={key!r}"


def test_konami_case_sensitive_letters():
    # onKonamiKeydown lowercases single-char keys BEFORE calling the pure
    # step; the step itself is exact-match. Pin that division of labor.
    assert js_call("konamiNextProgress", 8, "B", KONAMI) == 0
    assert js_call("konamiNextProgress", 8, "b", KONAMI) == 9


def test_konami_agrees_with_longest_prefix_reference_on_key_streams():
    # Deterministic pseudo-random streams over the code's own alphabet
    # (plus a noise key), checked step-by-step against the brute-force
    # longest-prefix reference. One node process for all streams.
    import random

    rng = random.Random(40)  # nod to PR #40; fixed seed, deterministic
    alphabet = KONAMI + ["x"]
    streams = [
        [rng.choice(alphabet) for _ in range(40)] for _ in range(12)
    ]
    # Include the adversarial classics explicitly.
    streams.append([UP] * 8 + KONAMI)
    streams.append(KONAMI[:7] + KONAMI)
    ops = [
        {"type": "fold", "fn": "konamiNextProgress", "init": 0,
         "stream": stream, "extra": [KONAMI]}
        for stream in streams
    ]
    results = run_js_ops(ops)
    for stream, got in zip(streams, results):
        assert got == reference_trace(stream, KONAMI), f"stream={stream}"


# --- other cleanly-pure web/app.js functions worth pinning ------------------


def test_biome_name_fallbacks_and_clamping():
    ops = [
        {"type": "call", "fn": "biomeName", "args": args}
        for args in [
            [0, None], [1, None], [2, None], [3, None],
            [99, None],   # clamps high
            [-5, None],   # clamps low
            [0, []],      # empty list -> fallback names
            [0, "nope"],  # non-array -> fallback names
            [1, ["Top", "Bottom"]],
            [9, ["Top", "Bottom"]],  # clamps against the CUSTOM list
        ]
    ]
    assert run_js_ops(ops) == [
        "Surface", "Cavern", "the Deep", "the Magma core",
        "the Magma core", "Surface", "Surface", "Surface",
        "Bottom", "Bottom",
    ]


def test_biome_label_emoji_and_trim():
    ops = [
        {"type": "call", "fn": "biomeLabel", "args": args}
        for args in [
            [0, None],
            [3, None],
            [99, None],
            # index beyond BIOME_ICONS: icon is "" and the label trims.
            [5, ["a", "b", "c", "d", "e", "Frontier"]],
        ]
    ]
    assert run_js_ops(ops) == [
        "\U0001f333 Surface",        # 🌳
        "\U0001f30b the Magma core",  # 🌋
        "\U0001f30b the Magma core",
        "Frontier",
    ]


def test_format_age_unit_boundaries():
    vectors = [
        (0, "0s"), (59, "59s"),
        (60, "1m"), (3599, "59m"),
        (3600, "1h"), (86399, "23h"),
        (86400, "1d"), (172800, "2d"), (863999, "9d"),
    ]
    ops = [
        {"type": "call", "fn": "formatAge", "args": [seconds]}
        for seconds, _ in vectors
    ]
    assert run_js_ops(ops) == [expected for _, expected in vectors]


def test_format_epoch_utc():
    epochs = [0, 1752278400, 1699999999]
    ops = [
        {"type": "call", "fn": "formatEpochUTC", "args": [epoch]}
        for epoch in epochs
    ]
    expected = [
        datetime.fromtimestamp(epoch, timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        )
        + " UTC"
        for epoch in epochs
    ]
    assert run_js_ops(ops) == expected
    assert expected[0] == "1970-01-01 00:00 UTC"  # anchor one literally


def test_share_card_file_name_sanitization():
    ops = [
        {"type": "call", "fn": "shareCardFileName", "args": [miner]}
        for miner in [
            {"display_name": "Steve"},
            {"display_name": "Herr Ober!! 99"},
            {"display_name": "--Alex--"},
            {"display_name": "!!!"},   # all symbols -> generic fallback
            {},                        # missing name -> generic fallback
        ]
    ]
    assert run_js_ops(ops) == [
        "mineverse-steve-card.png",
        "mineverse-herr-ober-99-card.png",
        "mineverse-alex-card.png",
        "mineverse-miner-card.png",
        "mineverse-miner-card.png",
    ]


def test_pack_total_and_skill_rank_total():
    ops = [
        {"type": "call", "fn": "packTotal", "args": [
            {"ores": [["iron", 3], ["gold", 2]], "other": [["torch", 5]]}]},
        {"type": "call", "fn": "packTotal", "args": [
            {"ores": [["iron", "many"], ["gold", 2]]}]},  # non-numeric skipped
        {"type": "call", "fn": "packTotal", "args": [None]},
        {"type": "call", "fn": "packTotal", "args": [{}]},
        {"type": "call", "fn": "skillRankTotal", "args": [
            [["mining", 4], ["luck", 2]]]},
        {"type": "call", "fn": "skillRankTotal", "args": [
            [["mining", "four"]]]},
        {"type": "call", "fn": "skillRankTotal", "args": [None]},
    ]
    assert run_js_ops(ops) == [10, 2, 0, 0, 6, 0, 0]


def test_share_card_gear_lines_filter_cap_and_wear():
    gear = [
        {"slot": "pick", "item": "Iron Pick", "wear": 42},
        {"slot": "boots", "item": None},          # empty slot filtered out
        None,                                     # junk entry filtered out
        {"slot": "helm", "item": "Cap"},          # no wear -> no wear suffix
        {"slot": "chest", "item": "Plate", "wear": 0},  # wear 0 still shown
        {"slot": "ring", "item": "Band", "wear": 7},
        {"slot": "belt", "item": "Sash", "wear": 8},    # 5th kept item: capped
    ]
    assert js_call("shareCardGearLines", gear) == [
        "pick: Iron Pick · wear 42",
        "helm: Cap",
        "chest: Plate · wear 0",
        "ring: Band · wear 7",
    ]
    assert js_call("shareCardGearLines", None) == []


def test_share_card_lines_text_shaping():
    miner = {
        "display_name": "Steve",
        "suid": 7,
        "depth": 2,
        "record_depth": 3,
        "coins": 5,
        "xp": {"level": 4, "game_total": 100, "game": "mining"},
        "gear": [{"slot": "pick", "item": "Iron Pick", "wear": 42}],
    }
    world = {"max_depth": 4, "biomes": None}
    lines = js_call("shareCardLines", miner, world)
    assert lines == {
        "title": "Steve",
        "subtitle": "suid 7",
        "stats": [
            "Depth 2/4 — the Deep · record depth 3",
            "Level 4 · 100 mining XP · 5 coins",
        ],
        "gear": ["pick: Iron Pick · wear 42"],
        "footer": "Mineverse — read-only mining economy viewer",
    }
    # Defaults when fields are absent: unknown suid, "?" placeholders.
    bare = js_call("shareCardLines", {"display_name": "X", "depth": 0,
                                      "record_depth": 0}, None)
    assert bare["subtitle"] == "suid unknown"
    assert bare["stats"][0] == "Depth 0/? — Surface · record depth 0"
    assert bare["stats"][1] == "Level ? · 0 ? XP · 0 coins"


# --- cosmetic hats: hatSVGRects + hatsByName (backlog item 7) ---------------
#
# The hat pipeline is server-derived (server/views.py build_hats,
# pytest-covered in tests/test_hats.py); these two pure functions are the
# ONLY new frontend logic — spec → markup, and views.hats → name join.


def test_hat_svg_rects_renders_valid_pixels_in_order():
    pixels = [[2, 1, 4, 1, "#f5c842"], [1, 2, 6, 1, "#f5c842"]]
    assert js_call("hatSVGRects", pixels) == (
        '<rect x="2" y="1" width="4" height="1" fill="#f5c842"/>'
        '<rect x="1" y="2" width="6" height="1" fill="#f5c842"/>'
    )


def test_hat_svg_rects_rejects_junk_specs_and_entries():
    ops = [
        {"type": "call", "fn": "hatSVGRects", "args": [spec]}
        for spec in [
            None,                                   # no hat
            "hat",                                  # non-array spec
            {},                                     # non-array spec
            [],                                     # empty spec
            [[1, 2, 3, 4]],                         # missing color
            [[1, 2, 3, 4, 5, 6]],                   # wrong arity
            [["a", 2, 3, 4, "#fff"]],               # non-numeric coord
            [[1, 2, 3, 4, "red"]],                  # non-hex color
            [[1, 2, 3, 4, '"><script>x</script>']],  # markup never lands
            [None, 7],                              # junk entries
        ]
    ]
    assert run_js_ops(ops) == [""] * len(ops)


def test_hat_svg_rects_keeps_valid_entries_when_junk_is_mixed_in():
    pixels = [[4, 0, 1, 1, "#f5c842"], None, [1, 2, 3, 4, "red"]]
    assert js_call("hatSVGRects", pixels) == (
        '<rect x="4" y="0" width="1" height="1" fill="#f5c842"/>'
    )


def test_hat_svg_rects_accepts_shipped_server_catalog():
    # Contract seam: every pixel the server actually ships must survive
    # the frontend validity filter — a filtered SHIPPED pixel would be a
    # silently half-drawn hat.
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from server import views  # noqa: E402

    ops = [
        {"type": "call", "fn": "hatSVGRects", "args": [entry["pixels"]]}
        for entry in views.HAT_CATALOG
    ]
    for entry, markup in zip(views.HAT_CATALOG, run_js_ops(ops)):
        assert markup.count("<rect") == len(entry["pixels"]), entry["id"]


def test_hats_by_name_joins_rows_to_catalog():
    hats = {
        "catalog": [
            {"id": "top_hat", "label": "top hat", "pixels": []},
            {"id": "bandana", "label": "bandana", "pixels": []},
        ],
        "miners": [
            {"suid": "1", "display_name": "DeepDelver", "hat": "top_hat"},
            {"suid": "2", "display_name": "RustyRelic", "hat": "bandana"},
            {"suid": "3", "display_name": "Ghost", "hat": "no_such_hat"},
            {"suid": "4", "hat": "top_hat"},   # nameless: can't reach a chip
            None,                              # junk row
        ],
    }
    assert js_call("hatsByName", hats) == {
        "DeepDelver": {"id": "top_hat", "label": "top hat", "pixels": []},
        "RustyRelic": {"id": "bandana", "label": "bandana", "pixels": []},
    }


def test_hats_by_name_tolerates_missing_or_junk_views_key():
    ops = [
        {"type": "call", "fn": "hatsByName", "args": [spec]}
        for spec in [None, {}, {"catalog": "x", "miners": "y"},
                     {"catalog": [None, {"label": "no id"}], "miners": []}]
    ]
    assert run_js_ops(ops) == [{}] * len(ops)


# --- ambient cave audio (backlog item 5): pure spec/label seams -------------
#
# The WebAudio wiring (startCaveAmbience/buildCaveAudioNode) is a thin
# interpreter needing a real AudioContext; ALL the decisions live in these
# pure functions — graph spec from config, deterministic drip rhythm, and
# the honest toggle face — so they are what CI pins.


def test_cave_sounds_button_state_is_honest_both_ways():
    on, off = run_js_ops([
        {"type": "call", "fn": "caveSoundsButtonState", "args": [True]},
        {"type": "call", "fn": "caveSoundsButtonState", "args": [False]},
    ])
    assert on == {"pressed": "true", "label": "🔊 Cave sounds on"}
    assert off == {"pressed": "false", "label": "🔇 Cave sounds off"}
    # aria-pressed always mirrors the label — no state where they disagree.
    assert (on["pressed"] == "true") == ("on" in on["label"])
    assert (off["pressed"] == "false") == ("off" in off["label"])


def test_cave_ambience_graph_spec_shape_and_chain():
    # No argument → the SHIPPED ambience (CAVE_AUDIO), exactly what the
    # browser's interpreter builds.
    spec = js_call("caveAmbienceGraphSpec")
    by_id = {node["id"]: node for node in spec["nodes"]}
    assert set(by_id) == {"master", "wind-noise", "wind-filter"}
    assert by_id["master"]["type"] == "gain"
    assert by_id["wind-filter"]["type"] == "biquad"
    assert by_id["wind-noise"]["type"] == "noise"
    assert by_id["wind-noise"]["loop"] is True  # the wind never runs out
    # The chain reaches the speakers: noise → filter → master → destination.
    assert spec["connections"] == [
        ["wind-noise", "wind-filter"],
        ["wind-filter", "master"],
        ["master", "destination"],
    ]
    # Every connection endpoint is a declared node (or the destination).
    for src, dst in spec["connections"]:
        assert src in by_id
        assert dst in by_id or dst == "destination"


def test_cave_ambience_is_subtle_by_construction():
    spec = js_call("caveAmbienceGraphSpec")
    by_id = {node["id"]: node for node in spec["nodes"]}
    # Whisper-quiet master gain — ambience, never music.
    assert 0 < by_id["master"]["gain"] <= 0.1
    # Wind is a low-pass rumble, not white-noise hiss.
    assert by_id["wind-filter"]["filterType"] == "lowpass"
    assert 0 < by_id["wind-filter"]["frequencyHz"] <= 400


def test_cave_ambience_graph_spec_reads_the_given_config():
    custom = {
        "masterGain": 0.02,
        "wind": {"noiseSeconds": 1, "filterType": "lowpass",
                 "frequencyHz": 120, "q": 1.5},
    }
    spec = js_call("caveAmbienceGraphSpec", custom)
    by_id = {node["id"]: node for node in spec["nodes"]}
    assert by_id["master"]["gain"] == 0.02
    assert by_id["wind-filter"]["frequencyHz"] == 120
    assert by_id["wind-filter"]["q"] == 1.5
    assert by_id["wind-noise"]["seconds"] == 1


def test_cave_drip_delay_is_deterministic_and_bounded():
    # Shipped config: gaps live in [4, 9] s and cycle deterministically —
    # the same rhythm every visit (diamond-rain-style scatter, no RNG).
    ops = [
        {"type": "call", "fn": "caveDripDelaySeconds", "args": [i]}
        for i in range(24)
    ]
    delays = run_js_ops(ops)
    assert all(4 <= d <= 9 for d in delays)
    assert set(delays) == {4, 5, 6, 7, 8, 9}  # full range, no dead gap
    assert delays[:6] == delays[6:12] == delays[12:18]  # period = span
    assert delays == run_js_ops(ops)  # bit-identical on a re-run


def test_cave_drip_delay_respects_custom_gap_bounds():
    config = {"drip": {"minGapSeconds": 2, "maxGapSeconds": 4}}
    delays = run_js_ops([
        {"type": "call", "fn": "caveDripDelaySeconds", "args": [i, config]}
        for i in range(9)
    ])
    assert all(2 <= d <= 4 for d in delays)
    assert set(delays) == {2, 3, 4}


# --- seasonal decorations (backlog item 6): date-keyed pure seams -----------
#
# The DOM caller (applySeasonalDecor) is a three-liner; ALL the decisions
# live in seasonForDate (injected ISO date → season/event id, calendar
# windows + fixed dates), seasonalDecorSpec (id → renderable spec) and
# seasonalDecorSVG (spec → pixel-SVG markup through the hatSVGRects
# filter) — so those are what CI pins, across every window boundary and
# the year wrap.

SEASON_IDS = {"winter", "spring", "summer", "autumn"}
EVENT_IDS = {"founding-day", "new-year"}
ALL_SEASONAL_IDS = SEASON_IDS | EVENT_IDS


def test_season_for_date_window_boundaries():
    vectors = [
        # every inclusive window edge, both sides
        ("2026-02-28", "winter"),
        ("2028-02-29", "winter"),   # leap day: still winter
        ("2026-03-01", "spring"),
        ("2026-05-31", "spring"),
        ("2026-06-01", "summer"),
        ("2026-08-31", "summer"),
        ("2026-09-01", "autumn"),
        ("2026-11-30", "autumn"),
        ("2026-12-01", "winter"),
        # mid-window sanity
        ("2026-01-15", "winter"),
        ("2026-04-10", "spring"),
        ("2026-07-12", "summer"),   # this session's date
        ("2026-10-31", "autumn"),
    ]
    ops = [
        {"type": "call", "fn": "seasonForDate", "args": [iso]}
        for iso, _ in vectors
    ]
    assert run_js_ops(ops) == [expected for _, expected in vectors]


def test_season_for_date_wraps_the_year_end():
    # Winter is one window spanning the year boundary: late December and
    # early January agree, across DIFFERENT years.
    ops = [
        {"type": "call", "fn": "seasonForDate", "args": [iso]}
        for iso in ["2026-12-30", "2027-01-02", "2030-12-25", "2031-02-10"]
    ]
    assert run_js_ops(ops) == ["winter"] * 4


def test_fixed_dates_override_their_surrounding_season():
    ops = [
        {"type": "call", "fn": "seasonForDate", "args": [iso]}
        for iso in [
            "2026-07-11",  # founding day beats summer...
            "2026-07-10", "2026-07-12",  # ...but only on the day itself
            "2026-12-31", "2027-01-01",  # new year beats winter, both sides
            "2026-12-30", "2027-01-02",  # neighbors stay winter
        ]
    ]
    assert run_js_ops(ops) == [
        "founding-day", "summer", "summer",
        "new-year", "new-year", "winter", "winter",
    ]


def test_season_for_date_repeats_identically_every_year():
    ops = [
        {"type": "call", "fn": "seasonForDate", "args": [f"{year}-07-11"]}
        for year in (2026, 2027, 2099)
    ]
    assert run_js_ops(ops) == ["founding-day"] * 3


def test_season_for_date_accepts_datetime_strings():
    # boot() passes a bare date, but a full timestamp maps the same way.
    ops = [
        {"type": "call", "fn": "seasonForDate", "args": [iso]}
        for iso in ["2026-07-11T12:00:00Z", "2026-10-05 08:30"]
    ]
    assert run_js_ops(ops) == ["founding-day", "autumn"]


def test_season_for_date_rejects_junk_with_null_never_a_throw():
    ops = [
        {"type": "call", "fn": "seasonForDate", "args": [junk]}
        for junk in [
            None, 123, [], {}, "", "not-a-date",
            "07-11",          # missing year
            "2026-13-01",     # impossible month
            "2026-00-10",     # month zero
            "2026-07-00",     # day zero
            "2026-07-32",     # impossible day
            "2026-7-1",       # unpadded (not the injected format)
            "2026-07-11x",    # trailing junk that isn't a time separator
        ]
    ]
    assert run_js_ops(ops) == [None] * len(ops)


def test_every_calendar_day_maps_to_exactly_one_seasonal_id():
    # Exhaustive: all 365 days of 2026 plus all 366 of leap-year 2028 —
    # never null, never an unknown id, and the fixed dates land exactly
    # where they should. One node process for the whole sweep.
    from datetime import date as _date, timedelta

    days = []
    for year in (2026, 2028):
        day = _date(year, 1, 1)
        while day.year == year:
            days.append(day)
            day += timedelta(days=1)
    ops = [
        {"type": "call", "fn": "seasonForDate", "args": [day.isoformat()]}
        for day in days
    ]
    results = run_js_ops(ops)
    for day, got in zip(days, results):
        assert got in ALL_SEASONAL_IDS, f"{day} -> {got!r}"
        mmdd = day.strftime("%m-%d")
        if mmdd == "07-11":
            assert got == "founding-day", day
        elif mmdd in ("12-31", "01-01"):
            assert got == "new-year", day


def test_seasonal_decor_spec_is_renderable_for_every_id():
    ops = []
    for season_id in sorted(ALL_SEASONAL_IDS):
        ops.append({"type": "call", "fn": "seasonalDecorSpec",
                    "args": [season_id]})
    specs = run_js_ops(ops)
    for season_id, spec in zip(sorted(ALL_SEASONAL_IDS), specs):
        assert spec["id"] == season_id
        assert spec["cssClass"] == f"season-{season_id}"
        assert isinstance(spec["label"], str) and spec["label"]
        assert isinstance(spec["pixels"], list) and spec["pixels"]
        for pixel in spec["pixels"]:
            x, y, w, h, color = pixel
            # every pixel sits inside the 10×10 avatar-grammar grid
            assert 0 <= x and 0 <= y and w > 0 and h > 0, pixel
            assert x + w <= 10 and y + h <= 10, pixel
            assert re.fullmatch(r"#[0-9a-fA-F]{6}", color), pixel


def test_seasonal_decor_svg_draws_every_shipped_pixel():
    # Same contract seam as the hat catalog test: every shipped pixel
    # must survive the hatSVGRects validity filter — a filtered SHIPPED
    # pixel would be a silently half-drawn ornament.
    spec_ops = [
        {"type": "call", "fn": "seasonalDecorSpec", "args": [season_id]}
        for season_id in sorted(ALL_SEASONAL_IDS)
    ]
    specs = run_js_ops(spec_ops)
    svg_ops = [
        {"type": "call", "fn": "seasonalDecorSVG", "args": [spec]}
        for spec in specs
    ]
    for spec, markup in zip(specs, run_js_ops(svg_ops)):
        assert markup.startswith('<svg viewBox="0 0 10 10"'), spec["id"]
        assert 'shape-rendering="crispEdges"' in markup, spec["id"]
        assert markup.count("<rect") == len(spec["pixels"]), spec["id"]


def test_seasonal_decor_spec_and_svg_reject_junk_quietly():
    ops = [
        {"type": "call", "fn": "seasonalDecorSpec", "args": [None]},
        {"type": "call", "fn": "seasonalDecorSpec", "args": ["mars-storm"]},
        {"type": "call", "fn": "seasonalDecorSVG", "args": [None]},
        {"type": "call", "fn": "seasonalDecorSVG", "args": [{}]},
        {"type": "call", "fn": "seasonalDecorSVG",
         "args": [{"pixels": "junk"}]},
        # pixels present but all invalid -> hatSVGRects filters them all
        # -> no rects -> no <svg> shell either
        {"type": "call", "fn": "seasonalDecorSVG",
         "args": [{"pixels": [[1, 2, 3, 4, "red"], None]}]},
    ]
    assert run_js_ops(ops) == [None, None, "", "", "", ""]


def test_harness_reports_missing_function_clearly():
    with pytest.raises(RuntimeError, match="no top-level function"):
        js_call("noSuchFunctionAnywhere")
