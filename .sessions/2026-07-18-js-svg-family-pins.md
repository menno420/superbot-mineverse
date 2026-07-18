# Session — 2026-07-18 — JS-exec pins for the last three unpinned pure SVG helpers

> **Status:** `complete`
> **Branch:** `claude/js-svg-family-pins`
> **Timestamp (UTC):** Sat Jul 18 2026

**Scope:** execution-pin the final three pure SVG-markup helpers in
`web/app.js` that still had PRESENCE-ONLY grep coverage in
`tests/test_web_visuals.py` (their branches ran in no executed test). Add real
vm-executed vector tests to `tests/test_js_logic.py` using the module's
existing node `vm` harness (`run_js_ops` / `js_call`) and its node-absent skip
guard, mirroring the exec pins from PR #124 and PR #125:

1. `minerAvatarSVG(hat)` (`web/app.js` :498) — pure (JSON hat → markup). Base
   helmet/face/overalls rects render FIRST; the optional server-derived
   cosmetic hat (`hatSVGRects(hat ? hat.pixels : null)`) is appended AFTER so
   its pixels layer ON TOP. Vectors pin: a valid hat rect present AND ordered
   after the five base rects (substring `.index()` order), plus `null`, `{}`,
   and a junk-`pixels` hat all rendering base-only with no extra rect and no
   throw.
2. `crackedIconSVG()` (`web/app.js` :557) — pure, constant markup; the ONLY
   caller of `pixelSVGShell(..., crisp=false)`. Vector pins that
   `shape-rendering="crispEdges"` is ABSENT (the crisp=false proof), the smooth
   `<polyline>` stroke bytes, and `focusable="false"` present.
3. `recordFlagSVG()` (`web/app.js` :513) — pure, constant. Vector pins the
   pole `<rect>` and pennant `<polygon>` exact bytes plus crispEdges present.

Test-only, zero runtime change — no `web/`, `server/`, or `data/` bytes move.

## What shipped

Three vm-executed vector tests added to `tests/test_js_logic.py` (PR #126):

- `test_miner_avatar_svg_layers_hat_after_the_base_rects` — pins the shared
  shell header (8×10 grid, crispEdges, focusable), all five base rects present
  in shipped order, and the cosmetic hat rect present AND positioned strictly
  after every base rect (substring `.index()`), with the total `<rect>` count
  = base + 1.
- `test_miner_avatar_svg_renders_base_only_for_missing_or_junk_hat` — pins that
  `null`, `{}`, and a junk-`pixels` hat all render byte-identical base-only
  markup (five rects, no extra hat rect) with no throw — the `hat ? hat.pixels
  : null` short-circuit and the hatSVGRects validity filter both exercised.
- `test_cracked_icon_svg_is_the_crisp_false_smooth_stroke` — pins
  `shape-rendering="crispEdges"` ABSENT (the crisp=false proof) while
  `focusable="false"` stays present, plus the exact smooth `<polyline>` stroke
  bytes.
- `test_record_flag_svg_pole_and_pennant_bytes` — pins crispEdges present plus
  the pole `<rect>` and pennant `<polygon>` exact shipped bytes/colors.

Source behavior matched every approximation in the order; no surprises, no
`web/app.js` changes needed — this drains the presence-only SVG helpers to
zero. `test_js_logic.py` alone: 54 passed. Full suite: 645 passed, 1 skipped.

Born-red HOLD flipped to `complete` at end of session; the green enabler
(`.github/workflows/auto-merge-enabler.yml`) lands PR #126 — never a manual
merge.

## 💡 Session idea

With `minerAvatarSVG` now pinned for the hat-layering ORDER, a natural next
step is a single exec vector that threads a REAL shipped catalog hat
(`server.views.HAT_CATALOG`) through `minerAvatarSVG` — the same contract seam
`test_hat_svg_rects_accepts_shipped_server_catalog` already guards for
`hatSVGRects` in isolation — so a future catalog edit that yields a hat which
survives the filter but mis-layers on the avatar base would fail loudly at the
composed level, not just the helper level.

## ⟲ Previous-session review

`.sessions/2026-07-18-js-svg-pins.md` (PR #125, `claude/js-svg-pins`) added
vm-executed vectors for `vaultChestSVG`, `lanternSVG`, and `oreIconSVG` —
pinning the chest fill-height clamp and `levelMax == 0` div-by-zero guard, the
lantern glow-step array index/clamp, and the ore-tier color map with its
unknown-name `null` branch. Sound and well-scoped; it establishes the exact
vector-test shape this session mirrors, and this lane finishes the same job it
started — draining the residual presence-only SVG helpers down to zero. Its 💡
(an SVG well-formedness parse in the same harness) is orthogonal to this lane
and remains open.

- **📊 Model:** Claude Opus 4.x · medium · test writing — vm-exec pins for the last three pure SVG helpers
