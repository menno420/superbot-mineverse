# Session — 2026-07-14 — pixelSVGShell dedupe (refactor)

> **Status:** `in-progress`
> **Branch:** `claude/improve-svg-shell-dedupe`
> **Venue:** improvement-wave lane G (owner directive 2026-07-14; wave
> claim `control/claims/claude-improvement-wave-2026-07-14.md`, #95).

**Goal:** cash in the 💡 from
`.sessions/2026-07-12-seasonal-decorations.md`: web/app.js
hand-concatenates the same `<svg viewBox=... width=... height=...
[shape-rendering="crispEdges" ]focusable="false">` shell in four places
(`minerAvatarSVG`, `recordFlagSVG`, `crackedIconSVG`,
`seasonalDecorSVG`) — the shell attributes can silently drift on a
fifth icon. Change: ONE shared `pixelSVGShell(viewBox, w, h, inner)`
helper used by all four; byte-output equivalence REQUIRED (zero visual
change) — nuance found up front: `crackedIconSVG` alone ships NO
`shape-rendering="crispEdges"`, so the helper takes an optional
trailing `crisp = true` flag rather than forcing a byte change on the
crack mark. Verify before committing: node-vm byte-diff of all four
functions' outputs old-vs-new, plus the pinned substrings in
tests/test_web_visuals.py + tests/test_js_logic.py
(`test_seasonal_decor_svg_draws_every_shipped_pixel` executes the real
markup). Locate call sites by content — sibling merges shifted line
numbers from the harvest's :486/:499/:545/:687.

- **📊 Model:** fable-5 · standard effort · task-class: pixelSVGShell dedupe — four hand-rolled SVG shells behind one helper, byte-identical output (refactor)
