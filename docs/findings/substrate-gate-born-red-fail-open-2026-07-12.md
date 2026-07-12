# Finding — substrate-gate fail-open on PR-added session cards (the flip-race)

> **Status:** `audit`
>
> Root-cause finding for why PRs #48/#49 auto-merged with `in-progress`
> session cards. Records were repaired by PR #50; this doc is the WHY plus
> the routing decision for the fix. Every citation below was verified at
> `origin/main` commit `0417fc0`; line numbers refer to that tree's
> `bootstrap.py`.

## Symptom

PRs #48 (JS logic test harness) and #49 (cosmetic hats) auto-merged while
their session cards (`.sessions/2026-07-12-js-logic-test-harness.md`,
`.sessions/2026-07-12-cosmetic-hats.md`) still carried
`> **Status:** `in-progress``. The close-out flips were stranded on their
branches post-merge (the "flip-race") and had to be landed separately by
PR #50. This finding establishes the mechanism and the correct home for
the fix.

## Root cause — how the gate routes the card in a PR diff

CI's `substrate-gate` workflow (`.github/workflows/substrate-gate.yml` —
carrying the KIT-OWNED header: "adopt/upgrade regenerates this file in
place … hand edits are OVERWRITTEN") gates the single session card in the
PR diff via three routes:

1. **Card MODIFIED by the PR** → locked door:
   `bootstrap.py check --strict --require-session-log --session-log "$card"`.
   An in-progress card reds the run.
2. **Card ADDED by the PR** → advisory sentinel:
   `bootstrap.py check --strict --session-log .sessions/__born-red-card-added__.md`
   — a deliberately NONEXISTENT file, with no `--require-session-log`. The
   real added card is never evaluated.
3. **No card in the diff** → advisory sentinel (same shape).

Engine contract (`bootstrap.py`, `cmd_check`): exactly ONE card is
validated per run (lines 12676–12684); an explicitly-passed nonexistent
`--session-log` is an advisory pass (lines 12732–12735); with no flag the
newest-by-mtime card is picked (`latest_session_log`, lines 1698–1705).
An in-progress Status badge reds a card via `check_log` lines 1773–1774
(`IN_PROGRESS_TOKENS`, line 1716).

So a single-PR work session — card ADDED + work + flip-as-last-commit, all
in one PR — takes route 2 for its entire life: CI is green from the first
push, before the flip exists. The auto-merge enabler is gated only on the
required `substrate-gate` context (`substrate.config.json` →
`"required_context": "substrate-gate"`) and merges at first green —
pre-flip. That is the flip-race.

## Empirical evidence

- PR #48, head `3f84068` → substrate-gate run **29211118886**, SUCCESS,
  log lines: "card .sessions/2026-07-12-js-logic-test-harness.md is newly
  ADDED by this PR (born-red heartbeat) — advisory sentinel gate" /
  "check: --session-log .sessions/__born-red-card-added__.md does not
  exist (advisory — not a failure)."
- PR #49, head `24c818e` → run **29211563277**, SUCCESS, same pattern.
- No CI run exists for the stranded flip commit `12b4045` — it was pushed
  post-merge, and the workflow triggers only on `pull_request` + `push`
  to `main`.

## Verdict — (b) kit fail-open by design, no local divergence

The installed workflow is byte-identical to the kit template embedded in
`bootstrap.py` (`_live_ci_workflow`, lines 9688–9750; the advisory
added-card branch at 9742–9746). The advisory branch exists for a real
reason — gba-homebrew PR #2: a heartbeat-only PR that ADDS the born-red
card (first-commit convention REQUIRES an in-progress card at birth)
could never merge under a locked door. But the kit's design makes EVERY
added card advisory, so single-PR work sessions have no born-red hold in
CI at all. (The template does tighten one special case — a PR that also
touches the gate workflow itself keeps the locked door on an added card —
but that does not cover the ordinary work PR.)

## Minimal fix — belongs in substrate-kit, NOT this repo

In the added-card branch of the template, apply the locked door when the
diff contains anything beyond coordination surfaces:

```sh
non_heartbeat="$(git diff --name-only "$range" | grep -v -e '^\.sessions/' -e '^control/' -e '^telemetry/' | head -1)"
```

→ if non-empty, run `--strict --require-session-log --session-log "$card"`;
else keep the advisory sentinel. With this, flip-last is safe again (CI
stays red until the flip ⇒ the auto-merge enabler cannot merge pre-flip);
heartbeat-only PRs still merge born-red by design.

**Residual kit-level gap (separate follow-up):** the routing's `tail -1`
gates only ONE card in multi-card PRs.

## Why NOT hand-patched here

Both the workflow file (KIT-OWNED header above) and `bootstrap.py`'s
embedded template are regenerated in place by `bootstrap.py`
adopt/upgrade — a local edit is silently overwritten on the next upgrade,
turning the fix into a regression trap. The fix is routed upstream via
`control/outbox.md` (2026-07-12 entry) for the manager to relay to
substrate-kit.

## Repo-local alternatives (if the kit declines) — both have costs

1. **Separate workflow** implementing the added-card locked door, made a
   SECOND required context. Survives kit upgrades (the KIT-OWNED header
   itself says host customizations go in a separate workflow file), but
   requires a ruleset edit — owner/console-adjacent, not agent-doable.
2. **Process-only:** split the session-opening heartbeat PR from the work
   PR, so the work PR always MODIFIES the card and hits the existing
   locked door. No config change, but doubles PR traffic per session and
   relies on discipline rather than mechanism.

## Interim lane practice (recorded, in force)

Push the FULL commit stack — including the completeness flip — BEFORE
opening the PR (PR #50's process inversion). First green then coincides
with flipped, so auto-merge cannot strand the close-out.
