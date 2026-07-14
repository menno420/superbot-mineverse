# Session — 2026-07-14 — mini-map co-location badge

> **Status:** `complete`
> **Branch:** `claude/improve-minimap-colocation`
> **Venue:** improvement-wave lane G (owner directive 2026-07-14; wave
> claim `control/claims/claude-improvement-wave-2026-07-14.md`, #95).

**Goal:** `build_minimap` (server/views.py) emits one point PER MINER,
so two miners at the same (x, y) in a band render as invisibly
overlapping dots (web/app.js `minimapPlot` — later dots simply paint
over earlier ones; the hidden alt list is the only place the second
name survives). Change: group same-(x, y) miners into ONE entry
`{x, y, names: [...]}` (snapshot order preserved); frontend renders one
dot with a visible `×N` badge when N > 1 and ALL names in the dot
title, hover label and the accessible hidden list. The committed sample
currently has NO collision, so the demo can't show the feature — move
ONE sample miner (MagmaMaven, depth 3, (-6, -6) → (4, -2)) to share
coordinates with DeepDelver; MagmaMaven's pinned badges
(tests/test_achievements.py: `deep_diver`, `coin_magnate`) are
depth/coin-derived, position-independent — verified before choosing it.
Keep the sample schema-valid (re-validate with
`server.snapshot_validation.validate_snapshot`). Pins to keep:
tests/test_web_a11y.py `at (${point.x}, ${point.y})` alt-list template.

## Close-out

Shipped on `claude/improve-minimap-colocation` (base: main @ `a0b66e6`,
the #100 sample-stale-ux squash):

- server/views.py `build_minimap`: per-band `occupied` dict keys cells
  by `(x, y)` (safe to hash — `shape_position` int-checks both fields);
  first miner in a cell creates `{x, y, names: []}`, later ones append.
  Point shape changed `{name, x, y}` → `{x, y, names: [...]}`; panel
  keys (`depth`/`biome`/`unplotted`/`bounds`) untouched, bounds math
  unchanged (grouping can only DEDUPE identical coordinates).
- web/app.js `minimapPlot`: one dot per cell; `who =
  point.names.join(", ")` feeds title + hover label; `names.length > 1`
  adds a visible `×N` badge (`.minimap-count`, accent-colored, in
  web/style.css). The hidden alt list (`renderMinimap`) lists every
  co-located name; the a11y pin `at (${point.x}, ${point.y})`
  (tests/test_web_a11y.py:110) still matches both templates.
- data/sample_snapshot.json: MagmaMaven (depth 3) moved (-6, -6) →
  (4, -2) to share DeepDelver's cell, so the demo actually SHOWS the
  badge. Re-validated with `server.snapshot_validation.validate_snapshot`
  (clean). Chosen because MagmaMaven's pinned achievement set
  (tests/test_achievements.py:297 `deep_diver` + `coin_magnate`) and
  every threshold comment naming it (Packrat 80, coins 25990, skill
  spread 3) are position-independent — no pin adjusted, none needed.
- Tests (rewrites + 3 new, suite 594 → 597): sample-pinned band test now
  asserts the grouped depth-3 point + tightened bounds and the
  no-collision depth-2 band; new colliding fixture (grouping + snapshot
  order + bounds), new cross-band non-collision case; unplottable test
  updated to the names shape; test_web_visuals.py pins the badge
  markup + CSS hook.

Verified pre-flip in this container: `python3 -m pytest -q` →
**597 passed, 1 skipped**; `python3 bootstrap.py check --strict` exit 0
(tails in the PR body).

## 💡 Session idea

The `×N` badge and the dot are the only VISIBLE collision cues, and
both live inside `decorative(minimapPlot(panel))` — aria-hidden. A
screen-reader user gets the names from the alt list but never the
"co-located" fact itself ("A, B at (1, 2)" reads as one line, fine —
but nothing says these two share a cell versus merely being adjacent
list entries; sighted users get the explicit ×2). Follow-up: append a
plain-text count to grouped alt-list items — `A, B at (1, 2) (2 miners
here)` — one template edit. Guard recipe: web/app.js `renderMinimap`
alt-list loop (the `point.names.join` li) + the pinned template in
tests/test_web_a11y.py `test_minimap_and_race_ship_text_alternatives`
and the new badge pin test in tests/test_web_visuals.py. Dedupe
checked: no session card, docs/ideas entry, or test comment mentions
alt-list collision phrasing (greps for "minimap" across .sessions/ and
docs/ideas/ come back structural only).

## ⟲ Previous-session review

`2026-07-14-improve-sample-stale-ux` (this lane's previous session,
merged #100) replays clean at `a0b66e6`: the additive `source` key is
in `build_staleness` exactly as described, both js source checks
short-circuit ABOVE the age math, and its "every pinned substring
still matches" claim held through THIS session's suite runs untouched.
Two dings: (1) its close-out says the notice covers "the demo" but
never states the interaction with the sibling boot-loading banner
(#97) it merged in mid-flight — the merge commit records "both
telemetry rows kept" and a green 594 suite, yet the card's close-out
was written BEFORE that merge and never amended, so the card
undersells what the branch actually shipped (a merge resolution is
work; cards should absorb late-breaking scope). (2) Its 💡 (append the
sample's generated_at to the neutral notice) names a guard recipe but
no consumer session — the same watcher-less-idea pattern the lane keeps
flagging; this card's idea has the same weakness and says so honestly
rather than pretending otherwise.

- **📊 Model:** fable-5 · standard effort · task-class: mini-map co-location grouping — same-(x,y) miners as one {x,y,names} point + ×N badge, sample gains a real collision (build)
