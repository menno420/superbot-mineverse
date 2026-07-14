# substrate-kit upgrade report — v1.16.0 → v1.17.0

> Generated 2026-07-14 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 6 · unchanged: 19

| planted doc | class | note |
|---|---|---|
| CONSTITUTION.md | unchanged | template identical across versions |
| docs/decisions.md | unchanged | template identical across versions |
| docs/architecture.md | unchanged | template identical across versions |
| docs/ownership.md | unchanged | template identical across versions |
| docs/runtime_contracts.md | unchanged | template identical across versions |
| docs/repo-navigation-map.md | unchanged | template identical across versions |
| docs/helper-policy.md | unchanged | template identical across versions |
| docs/collaboration-model.md | unchanged | template identical across versions |
| docs/ai-project-workflow.md | unchanged | template identical across versions |
| docs/owner-profile.md | unchanged | template identical across versions |
| docs/AGENT_ORIENTATION.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/current-state.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/question-router.md | unchanged | template identical across versions |
| docs/CAPABILITIES.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/SKILLS.md | unchanged | template identical across versions |
| docs/ROUTINES.md | unchanged | template identical across versions |
| docs/reading-path.md | unchanged | template identical across versions |
| docs/ideas/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .session-journal.md | unchanged | template identical across versions |
| control/README.md | unchanged | template identical across versions |
| control/inbox.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/status.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/claims/README.md | unchanged | template identical across versions |
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
