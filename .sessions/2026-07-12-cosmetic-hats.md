# Session — 2026-07-12 — cosmetic hats by miner id (backlog item 7)

> **Status:** `in-progress`
> **Branch:** `claude/cosmetic-hats`
> **Venue:** lane worker session (coordinator-delegated groomed-backlog slice).

**Goal:** ship groomed-backlog item 7
(`docs/ideas/founding-day-groomed-backlog-2026-07-11.md`): a deterministic
per-suid cosmetic hat on the pixel avatars. Server-derived and ADDITIVE,
following the achievements precedent — `server/views.py build_views` gains
a `hats` key (shared catalog + one per-miner row), derived from the miner's
suid via a stable `hashlib.sha256` digest (never Python's salted `hash()`).
The frontend draws the hat as extra pixels on the existing 8×N pixel-art
avatar SVG in the depth-ladder chips; the new drawing logic stays a PURE
function (hat pixel spec → `<rect>` markup) pinned per-CI-run through the
PR #48 `js_call` harness in `tests/test_js_logic.py`. Purely cosmetic — no
gameplay meaning, no state, no clock. `GET /api/snapshot` byte-identical;
a11y per the PR #32–35 pattern (SVG aria-hidden decoration, visually-hidden
text alternative carries the hat label).
