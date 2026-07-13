# Session — 2026-07-13 — minigame section spec (ORDER 004 item 4)

> **Status:** `in-progress`
> **Branch:** `claude/minigame-section-spec`
> **Venue:** lane worker session (coordinator-delegated ORDER 004 item 4).

**Goal:** land `docs/design/minigame-section-spec-2026-07-13.md` — the
cross-repo minigame inventory + section spec for SuperBot 2.0 per ORDER 004
item 4 (`control/inbox.md`, claim `control/claims/minigame-section-spec.md`
merged via #56). Inputs are four read-only inventories pinned at
superbot-next@`7330bc1` (PR #313 merged post-HEAD noted), superbot-games@
`64b3371`, superbot-idle@`457407c`, superbot-mineverse@`18f1fb3`. The spec
carries: the repos' own game groups (🏆 Competitive / 🎲 Activities hub
sections, world hub, BTD6 own-category, plugin lanes), enable-all-or-pick
semantics grounded in what exists (`capability_execution_overrides`, `!setup`
channel-access modes, per-channel message-game opt-in, idle setup codes,
plugin pinning, mineverse env tiers), a dynamic-panel model, a per-game
readiness table with file@sha / PR# citations, and an honest-nulls section.
Docs-only in this repo; a separate control-only PR posts the outbox pointer
and closes the claim. Flip-race interim rule in force: full stack incl. the
flip pushed BEFORE the PR opens.

## Close-out

(to be written at session close)

## 💡 Session idea

The spec's readiness table hand-carries file@sha citations from four sibling
repos with no machine check that the pinned SHAs still describe reality — a
tiny `tools/`-style staleness probe (read the four pinned SHAs out of the
spec's provenance block, compare against each repo's current origin/main via
the MCP API, emit an advisory "spec pinned N commits behind" line) would let
any future session know at a glance whether the section spec needs a re-pin
pass before building panels against it. Guard recipe: provenance block in
`docs/design/minigame-section-spec-2026-07-13.md` § Provenance (four
backticked 7-char SHAs), compare via GitHub MCP `list_commits` per repo;
verify by running the probe once against the four pinned SHAs and once
against a deliberately stale pin.

## ⟲ Previous-session review

The `2026-07-12-seasonal-decorations` card is a strong build close-out: the
shipped-surface paragraph names every seam with file anchors, the
judgment-call block records *why* (lexicographic MM-DD compares, LOCAL vs UTC
date flagged honestly, aria-hidden-with-no-text-twin justified by the
diamond-rain precedent) rather than just *what*, and its 💡 idea ships a real
guard recipe (the four `<svg viewBox=` literals → one `pixelSVGShell` helper,
named test target). It also demonstrably obeyed the flip-race interim rule
and watched the born-red hold work locally. Two nits: the promised
`pixelSVGShell` dedup idea is now the second consecutive idea aimed at
`web/app.js` internals while the older bare-`📊 Model:`-line housekeeping
sweep (flagged in ITS previous-session review, three reviews running by its
own count) still hasn't landed or been explicitly dropped — the review chain
keeps re-carrying that item instead of resolving it; and the close-out cites
"437 passed + 1 conditional skip" without naming the skip reason, which the
reader must dig out of `pytest -rs` (it's the `SHIM_CONFORMANCE_BASE_URL`
conformance seam).

- **📊 Model:** fable-5 · standard effort · task-class: cross-repo minigame inventory + section spec (research+docs)
