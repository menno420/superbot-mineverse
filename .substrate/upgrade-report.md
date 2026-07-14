# substrate-kit upgrade report — v1.15.0 → v1.16.0

> Generated 2026-07-14 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 4 · diverged: 2 · template-improved: 5 · unchanged: 14

| planted doc | class | note |
|---|---|---|
| CONSTITUTION.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/decisions.md | unchanged | template identical across versions |
| docs/architecture.md | unchanged | template identical across versions |
| docs/ownership.md | unchanged | template identical across versions |
| docs/runtime_contracts.md | unchanged | template identical across versions |
| docs/repo-navigation-map.md | unchanged | template identical across versions |
| docs/helper-policy.md | unchanged | template identical across versions |
| docs/collaboration-model.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/ai-project-workflow.md | unchanged | template identical across versions |
| docs/owner-profile.md | unchanged | template identical across versions |
| docs/AGENT_ORIENTATION.md | diverged | both the template and the doc moved — manual merge |
| docs/current-state.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/question-router.md | unchanged | template identical across versions |
| docs/CAPABILITIES.md | diverged | both the template and the doc moved — manual merge |
| docs/SKILLS.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/ROUTINES.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/reading-path.md | unchanged | template identical across versions |
| docs/ideas/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .session-journal.md | unchanged | template identical across versions |
| control/README.md | unchanged | template identical across versions |
| control/inbox.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/status.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/claims/README.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| scripts/env-setup.sh | unchanged | template identical across versions |
| .claude/CLAUDE.md | unchanged | template identical across versions |

## Carve-out scan

- carve-out scan: .github/workflows/substrate-gate.yml — ran, 0 found
- carve-out scan: .github/workflows/auto-merge-enabler.yml — ran, 0 found

## Capability-ledger seed refresh

- capability-seed: docs/CAPABILITIES.md fence already current — nothing to refresh.

This upgrade ships the venue-scoped capability ledger (grounded-skills §4.2): entries carry a venue token (owner-live · autonomous-project · routine-fired · subagent · any) and the ledger's kit-owned seed block carries the posture decision rule. If this repo carries a local prose copy of the boot-triad/venue-posture rule (superbot Q-0270), that copy is now superseded by docs/CAPABILITIES.md's posture rule — collapse the local copy into a pointer.

## Seat-digest refresh

- seat-digest: docs/seat-digest.md already current — nothing to refresh.

## Applied (--apply-docs)

- applied: CONSTITUTION.md (template@new, hash re-recorded)
- applied: docs/collaboration-model.md (template@new, hash re-recorded)
- applied: docs/SKILLS.md (template@new, hash re-recorded)
- applied: docs/ROUTINES.md (template@new, hash re-recorded)
- applied: control/claims/README.md (template@new, hash re-recorded)

## Template deltas for diverged docs

### docs/AGENT_ORIENTATION.md

```diff
--- docs/AGENT_ORIENTATION.md (template@old, current slots)
+++ docs/AGENT_ORIENTATION.md (template@new, current slots)
@@ -42,8 +42,9 @@
 `docs/repo-navigation-map.md` · `docs/ai-project-workflow.md` ·
 `docs/owner-profile.md` · `docs/current-state.md` · `docs/decisions.md` ·
 `docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/SKILLS.md` ·
-`docs/ROUTINES.md` · `docs/ideas/README.md` — plus the root
-`CONSTITUTION.md` (the working agreement) and `.session-journal.md`.
+`docs/ROUTINES.md` · `docs/reading-path.md` · `docs/ideas/README.md` —
+plus the root `CONSTITUTION.md` (the working agreement) and
+`.session-journal.md`.
 
 Recurring action? **`docs/SKILLS.md`** — the skill index — names every
 kit-shipped skill and when to reach for it; check it before improvising a
@@ -54,6 +55,11 @@
 probe-not-record, scheduler-health signatures, pacing — read it before
 touching the trigger registry.
 
+Reading or acting across sibling repos in a fleet? **`docs/reading-path.md`**
+— the standing read authorization, the one-command fleet orient, the
+sibling/truth-file map, tiered depth, truth rules — read it before burning
+turns re-discovering what you may read.
+
 ## Verifying any change
 
 See the working agreement (`.claude/CLAUDE.md`) and its verify guidance
```

### docs/CAPABILITIES.md

```diff
--- docs/CAPABILITIES.md (template@old, current slots)
+++ docs/CAPABILITIES.md (template@new, current slots)
@@ -5,7 +5,7 @@
 > Generated by substrate-kit. What agent sessions in THIS environment can and
 > cannot do — **verified findings, never assumptions**. Read at session start
 > (it is in the orientation reading order); append at session close. Fleet
-> master copy: `menno420/fleet-manager` → `docs/capabilities.md` — sync new
+> master copy: `menno420/fleet-manager` → `docs/CAPABILITIES.md` — sync new
 > fleet-wide findings there via the manager when cross-repo access allows.
 
 ## Why this file exists
```

