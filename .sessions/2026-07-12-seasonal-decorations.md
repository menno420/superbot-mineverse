# Session — 2026-07-12 — seasonal decorations (backlog item 6)

> **Status:** `in-progress`
> **Branch:** `claude/seasonal-decorations`
> **Venue:** lane worker session (coordinator-delegated groomed-backlog slice).

**Goal:** ship groomed-backlog item 6
(`docs/ideas/founding-day-groomed-backlog-2026-07-11.md`): seasonal
decorations — a small, tasteful, date-keyed cosmetic layer over the cave
theme. Core logic stays PURE with the date INJECTED
(`seasonForDate(isoDate)` → season/event id across a handful of calendar
windows incl. year wrap; `seasonalDecorSpec(seasonId)` → renderable spec
in the hat-pixel grammar), pinned per-CI-run via the PR #48 `js_call`
harness plus served-bytes pins; only the impure boot caller reads the
real clock, once. Purely cosmetic — no gameplay meaning, aria-hidden per
the `decorative()` route, NO new animation (the existing lantern-glow
keyframes + global reduced-motion guard stay the only motion), no
persistence, JSON API byte-identical, no new endpoints, no npm, no asset
files (inline SVG/CSS only).
