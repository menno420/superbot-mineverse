# Session — 2026-07-12 — substrate-gate fail-open root-cause finding (flip-race)

> **Status:** `complete`
> **Branch:** `claude/gate-fail-open-finding`
> **Venue:** lane worker session (coordinator-assigned investigation write-up).

**Goal:** commit the verified root-cause finding for why PRs #48/#49
auto-merged with in-progress session cards (the "flip-race"; records fixed
by PR #50): a finding doc under `docs/findings/` with exact code/workflow
citations and CI run IDs, plus a `control/outbox.md` note asking the
manager to route the minimal gate fix upstream to substrate-kit (both the
workflow and `bootstrap.py` are kit-regenerated — no hand-patch here).
Docs + control only; no runtime change.

## Close-out

Shipped on `claude/gate-fail-open-finding` → main.
`docs/findings/substrate-gate-born-red-fail-open-2026-07-12.md` (new dir)
records the full mechanism: the kit gate's three diff routes (MODIFIED →
locked door; ADDED → advisory nonexistent sentinel, real card never
evaluated; none → advisory), the engine one-card-per-run contract with
line citations at `0417fc0`, the empirical run evidence (PR #48
`3f84068` → run 29211118886; PR #49 `24c818e` → run 29211563277; no run
for stranded flip `12b4045`), verdict (b) — kit fail-open BY DESIGN
(workflow byte-identical to `_live_ci_workflow`, gba-homebrew PR #2
rationale), the minimal upstream fix (locked door when an added-card PR
carries non-coordination changes), the `tail -1` multi-card residual gap,
the two repo-local fallbacks with costs, and the interim full-stack-push
practice. `control/outbox.md` gained the lane→manager routing note (the
kit owns both the workflow and the template — no hand-patch here);
`docs/current-state.md` links the finding from its CI paragraph (known
gap) + Recently shipped. Verified: `bootstrap.py check --strict` exit 0,
`python3 -m pytest -q` = 415 passed + 1 skipped (baseline unchanged —
docs/control only). This PR itself follows the interim rule: full stack
pushed, flip included, BEFORE the PR was opened.

## 💡 Session idea

The finding's fix keeps heartbeat-only PRs advisory by classifying paths
with a hardcoded grep list (`.sessions/`, `control/`, `telemetry/`) — but
the kit ALREADY has a coordination-surface definition: the control fast
lane at the top of the same workflow. If the kit instead extracted one
shell function (or a `bootstrap.py classify-diff` subcommand) used by BOTH
the fast lane and the added-card route, the two path lists could never
drift apart — guard recipe: fast-lane path filter in
`_live_ci_workflow` (bootstrap.py 9688–9750) vs the proposed
`non_heartbeat` grep; pin with a kit test asserting the two filters accept
identical path sets.

## ⟲ Previous-session review

The `2026-07-12-webaudio-cave-toggle` card is a model build close-out:
the judgment calls are recorded WITH their rejected alternatives
(synthesized-over-assets, non-persistence as pattern-avoidance, the
structural reduced-motion argument), the pure-seam/impure-interpreter
split is named per function, and its 💡 conftest fixture-dedup idea ships
a proper guard recipe (anchors + the 415+1 invariant). It also followed
the flip-race rule this session's finding formalizes — full stack pushed
before PR. One nit inherited forward: the housekeeping sweep for the bare
`📊 Model:` lines on other 2026-07-12 cards, flagged two reviews running,
still hasn't landed.

- **📊 Model:** fable-5 · standard effort · task-class: substrate-gate born-red fail-open root-cause finding — flip-race PRs #48/#49 (control/docs)
