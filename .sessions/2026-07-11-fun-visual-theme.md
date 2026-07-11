# Session 2026-07-11 — cave visual theme (fun & visuals PR 1)

> **Status:** `in-progress`

## Plan

Frontend-only visual theme slice — vanilla HTML/JS/CSS + tests, no
contract, schema, server, write-path, or auth changes:

1. **Cave/mine theme** — richer dark palette via CSS variables plus
   biome-tinted accents per depth band (Surface = green/earth, Cavern =
   stone grey-blue, the Deep = crystal purple/teal, the Magma core =
   ember orange/red), and a CSS-only lantern-flicker glow on the header.
   The existing global `prefers-reduced-motion` guard already zeroes
   animation durations, so the pure-CSS keyframe flicker is static under
   reduced motion by construction.
2. **Mine-shaft depth cross-section** — `#depth-ladder-section` becomes
   a side-view shaft: stacked bands with layered gradient backgrounds
   (dirt lip → stone → biome tint), small aria-hidden pixel-style
   inline-SVG miner avatars on the `here` chips and a marker-flag SVG on
   `record_only` chips. All existing accessible text (band labels,
   names, "· record", "(nobody here)") is preserved — visuals are
   decoration layered onto the semantic list, never a replacement.
3. **Ore identity icons** — `oreIconSVG(name)` returns an aria-hidden
   inline-SVG gem per ore tier with distinct rarity colors (stone grey →
   bronze brown → iron silver-grey → silver white → gold yellow →
   diamond cyan); unknown items get no icon. Used in the inventory
   matrix row headers and the ore entries of miner pack/vault lists,
   with matching text-tint classes.
4. **Vault chest + energy lantern + gear durability** — an inline-SVG
   chest that fills stepwise by `vault_level` 0–6 (visually-hidden
   "vault level N of M" text equivalent kept alongside the pips); an
   inline-SVG lantern whose glow dims stepwise with the energy fraction
   (existing meter, "as of" line and `.low` behavior untouched); a
   per-gear-item wear bar colored green → amber → red as accumulated
   wear rises (contract: 0 = pristine, no schema max — 100 is a display
   cap), with a cracked/broken state at the cap and the "wear N" text
   kept visible.
5. **Leaderboard podium + count-up** — top-3 rows get aria-hidden medal
   marks with the rank number still in text; numeric score cells count
   up on render via a new shared `prefersReducedMotion()` helper
   (`window.matchMedia("(prefers-reduced-motion: reduce)")` — the first
   matchMedia use in app.js), rendering instantly under reduced motion
   and always ending at the exact server value (no drift).
6. **Regression net** — new `tests/test_web_visuals.py` pinning the
   served bytes for every anchor above, in the `tests/test_web_a11y.py`
   served-frontend style, including a re-pin that the reduced-motion
   guard block survived the theme work.

Constraints honored: no server/contract/schema changes; vanilla
HTML/JS/CSS, no build step, no new dependencies, no network calls;
`control/status.md` / `control/inbox.md` untouched; the reduced-motion
guard, `.visually-hidden`, `:focus-visible` and narrow-viewport blocks
pinned by tests/test_web_a11y.py stay byte-intact.

## 💡 Session idea

The inline-SVG helpers (`oreIconSVG`, `minerAvatarSVG`, `recordFlagSVG`,
`vaultChestSVG`, `lanternSVG`) all funnel through one `svgSpan(class,
markup)` decorator; PR 2 of this lane (achievements / easter eggs / VS
view / 404 page) should reuse that seam and `prefersReducedMotion()`
instead of growing a second animation-gating path — two gates is how one
of them forgets reduced motion.

## ⟲ Previous-session review

The web-a11y-responsive session's byte-pinning test style
(tests/test_web_a11y.py — one module-scoped real server, substring
asserts on `/`, `/app.js`, `/style.css`) is the template for
`tests/test_web_visuals.py`. Its decorative/text-alternative discipline
(`decorative()` + `visuallyHidden()` helpers, graphics never replace
text) is exactly the contract this visual slice must keep: every new
SVG routes through `decorative()`, and every graphic keeps or gains a
text equivalent. Its session idea (extract a `tablist()` helper before
a second tabbed widget lands) is untouched by this slice — no new tab
widget here — and still stands.

- **📊 Model:** fable-5 · standard effort · task-class: frontend visual theme (build)
