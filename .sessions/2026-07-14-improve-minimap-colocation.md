# Session — 2026-07-14 — mini-map co-location badge

> **Status:** `in-progress`
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

- **📊 Model:** fable-5 · standard effort · task-class: mini-map co-location grouping — same-(x,y) miners as one {x,y,names} point + ×N badge, sample gains a real collision (build)
