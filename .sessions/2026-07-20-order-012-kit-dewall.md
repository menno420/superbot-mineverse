# Session — 2026-07-20 — ORDER 012: green the substrate-gate on kit v1.20.1 upgrade PR #138

> **Status:** `in-progress`
> **Branch:** `claude/kit-upgrade-v1.20.1`
> **Timestamp (UTC):** Mon Jul 20 2026

## ✅ What shipped

Additive doc-only commits on the kit-wave PR branch (`claude/kit-upgrade-v1.20.1`,
PR #138) that clear the two pre-existing false-wall findings the new v1.20.1
`substrate-gate` flags — the only thing keeping the upgrade red. No kit
distribution file, product code, test, or workflow is touched; the flagged
lines are resident-owned docs outside the kit lane.

- `docs/NEXT-TASKS.md:26` — `[false-wall:agent-negated-infra-mutation]`: the
  blanket "agents cannot set secrets" wall is rewritten as the scoped, dated
  (2026-07-20) fact the gate itself teaches — agents mutate Railway variables,
  env, and deploys as normal work via the documented paths; only the
  owner-console secret *values* stay owner-set. History preserved, wall gone.
- `docs/decisions.md:39` — `[false-wall:classifier-denied-standing]`: the
  quoted old-framing token "classifier denies" is reworded to the dated
  past-fact form "~2026-07-15 classifier refusal of …", which drops the
  standing-wall trigger while the surrounding block still labels the whole
  framing FALSE / not-carried-forward.

**Scope:** execute inbox ORDER 012 — additive-only commits on the foreign
kit-wave PR branch that flip its substrate-gate green by de-walling the two
resident-owned doc lines the gate names, mirroring fleet-manager PR #390 style
(dated past-tense rephrasing / scoped fact). No rebase, no force-push, no auth
/ secrets / env / kit-distribution change.

## 💡 Session idea

The gate's clearing model attaches a repudiation/date cue only to the SAME
physical line as the wall phrase (plus a one-line *backward* wrap-lookback). A
multi-line block that quotes an old wall and then labels it FALSE on the NEXT
line reads as fully repudiated to a human but stays red to the gate — a real
false-positive class. A cheap symmetric fix: extend the wrap-lookback one line
FORWARD too (guarded the same way the backward one is — no contrast-start, no
sentence-end between), so a `"…classifier denies\n … was FALSE"` quote-then-
repudiate spanning a line break clears without de-triggering the quoted token.

## ⟲ Previous-session review

`.sessions/2026-07-20-readiness-heartbeat.md` (`claude/readiness-heartbeat`)
did a clean docs+control-only readiness pass — advanced the truth-stamp, pruned
two terminal claims after verifying each PR closed/merged on live GitHub, and
re-stamped `control/status.md` neutral; solid heartbeat hygiene, though its own
model line (`… · docs-readiness`) is the very non-PL-004 task-class token the
gate now advises on — this card uses the taught `docs-only` class to stay clean.

- **📊 Model:** Opus 4.8 · normal · docs-only — land the kit v1.20.1 upgrade doc fix (ORDER 012 false-wall de-wall on PR #138)
