# Session — 2026-07-12 — substrate-gate fail-open root-cause finding (flip-race)

> **Status:** `in-progress`
> **Branch:** `claude/gate-fail-open-finding`
> **Venue:** lane worker session (coordinator-assigned investigation write-up).

**Goal:** commit the verified root-cause finding for why PRs #48/#49
auto-merged with in-progress session cards (the "flip-race"; records fixed
by PR #50): a finding doc under `docs/findings/` with exact code/workflow
citations and CI run IDs, plus a `control/outbox.md` note asking the
manager to route the minimal gate fix upstream to substrate-kit (both the
workflow and `bootstrap.py` are kit-regenerated — no hand-patch here).
Docs + control only; no runtime change.
