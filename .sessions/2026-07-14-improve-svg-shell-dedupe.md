# Session — 2026-07-14 — pixelSVGShell dedupe (refactor)

> **Status:** `complete`
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

## Close-out

Shipped on `claude/improve-svg-shell-dedupe` (base: main @ `0f3a520`,
the #101 minimap-colocation squash):

- web/app.js: new `pixelSVGShell(viewBox, width, height, inner,
  crisp = true)` placed directly above `minerAvatarSVG`; all four
  hand-rolled shells now route through it (`minerAvatarSVG`,
  `recordFlagSVG`, `seasonalDecorSVG` with the default crisp shell;
  `crackedIconSVG` with `crisp=false` because its smooth-stroke crack
  never shipped crispEdges — forcing it would have been a real, if
  subtle, visual change, and byte-equivalence was the bar).
- Byte-equivalence PROVEN before commit, not assumed: a node-vm
  harness (same sandbox as tests/test_js_logic.py's runner) loaded
  `git show HEAD:web/app.js` and the edited file side by side and
  compared all four functions' outputs — `minerAvatarSVG(null)`,
  `minerAvatarSVG(hat)`, `recordFlagSVG()`, `crackedIconSVG()`,
  `seasonalDecorSVG(spec)` and the junk-spec empty case — every one
  BYTE-IDENTICAL. Pinned substrings in tests/test_web_visuals.py and
  tests/test_js_logic.py (incl.
  `test_seasonal_decor_svg_draws_every_shipped_pixel`, which executes
  the real markup) all pass untouched.
- Out of scope, deliberately: `oreIconSVG`, `vaultChestSVG`,
  `lanternSVG` also hand-roll `focusable="false"` shells (no
  crispEdges) — the harvested 💡 named exactly four; see this card's
  idea.
- Tests (+1, suite 601 → 602): tests/test_js_logic.py
  `test_pixel_svg_shell_is_the_one_shared_icon_shell` executes the
  helper in node and pins both byte-forms (crisp default + crisp=false).

Verified pre-flip in this container: `python3 -m pytest -q` →
**602 passed, 1 skipped**; `python3 bootstrap.py check --strict` exit 0
(tails in the PR body).

## 💡 Session idea

Three hand-rolled shells remain — `oreIconSVG`, `vaultChestSVG`,
`lanternSVG` all concatenate `<svg viewBox=... focusable="false">`
(no crispEdges, smooth geometry) — exactly the drift surface this
session closed for the pixel four: a sixth icon copied from THOSE
templates can still forget `focusable="false"`. They fold into
`pixelSVGShell(..., false)` byte-identically (same shape as the
crackedIconSVG call this session landed). Guard recipe: the three
remaining `` `<svg viewBox=`` template literals in web/app.js (locate
by content), replay the node-vm old-vs-new byte diff this session used,
extend `test_pixel_svg_shell_is_the_one_shared_icon_shell`
(tests/test_js_logic.py) with nothing — it already pins both
byte-forms. Dedupe checked: the seasonal-decorations 💡 (harvested
here) named only the four crisp shells; no card, docs/ideas entry, or
test comment proposes folding the remaining three.

## ⟲ Previous-session review

`2026-07-14-improve-minimap-colocation` (this lane's previous session,
merged #101) replays clean at `0f3a520`: rebuilding the views over the
committed sample yields exactly the grouped depth-3 point it claims
(`[{x: 4, y: -2, names: ["DeepDelver", "MagmaMaven"]}]` — re-executed,
not trusted), the a11y template pin survived, and its
position-independence argument for MagmaMaven held through TWO sibling
merges (#99's Homesteader badge is structure-derived and didn't touch
the moved coordinates). Two dings: (1) it repeated the exact
unamended-close-out failure it dinged the PR-1 card for — its
close-out was written before the mid-flight merge of #99/#102
(telemetry keep-all resolution, suite 597 → 601) and never absorbed
it; diagnosing a disease in the review section while committing it two
sections up is the lane's clearest recursion yet. (2) Its "no pin
adjusted, none needed" claim about achievements is true but was only
HALF verified in the card (badge ids checked; the Homesteader badge
that landed mid-flight was never re-checked against the moved miner —
it happens to be structure-based, but the card records no such check;
this review closes that gap).

- **📊 Model:** fable-5 · standard effort · task-class: pixelSVGShell dedupe — four hand-rolled SVG shells behind one helper, byte-identical output (refactor)
