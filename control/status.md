# superbot-mineverse · status
updated: 2026-07-13T04:12:00Z
phase: heartbeat — ORDER 004 morning tally (night-run ~2026-07-13T00:40–04:05Z, whole SuperBot World seat). COORDINATOR-DELEGATED heartbeat write — the coordinator seat authorized this status overwrite.
health: green
kit: v1.8.0
last-shipped: #63 — tests+server: shared served-bytes fixtures + views uses cached schema loader; merged 2026-07-13T02:21Z.
blockers: none
orders: acked=001,002,003,004 done=001,002,003,004
⚑ needs-owner: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET pair (conformance is then one command: `python3 scripts/conformance_run.py`, docs/conformance-runbook.md) — full OWNER-ACTION block (WHAT/WHERE/HOW/WHY-IT-MATTERS/UNBLOCKS/VERIFIED-NEEDED/RISK): control/outbox.md entry 2026-07-12T21:05Z. Owner-decision queue: § QUEUED below.
practice (2026-07-13T05:27:28Z): ORDER 038 adopted (fm inbox, standing, 2026-07-13): VERDICT 016 authenticity gate applied to every cross-agent reviewer reply before acting (cited line ranges must be ≤ EOF at the reviewed head; failed reply = fabricated, discarded with citation) — Q-0120 still governs replies that pass.
notes: ORDER 004 done-when met — tally posted here, per-game state table below, minigame section spec at docs/design/minigame-section-spec-2026-07-13.md (landed #58, outbox pointer #59). Verification labels: mineverse PR states API-verified at this stamp; games/idle/next merge states verified against each repo's main history at HEAD; suite counts, goldens, and run details are lane-reported (sources cited).

## ORDER 004 NIGHT-RUN TALLY (2026-07-13, ~00:40–04:05Z)

### SHIPPED (merged)

- **superbot-games** (suite 310→516, lane-reported per PR bodies; merges verified in main): #68 mining seam · #69 fishing seam · #70 mining CLI · #71 fishing CLI · #72 hub launcher · #73 persistence owner-queue · #74 docs · #75 D&D · #77 exploration · #76 fm-ORDER-037 stamp fix. All four world games reviewed/standalone/hub-integrated ✅ (`python -m games`).
- **superbot-idle** (suite →1260, 15 packs; lane-reported per PR bodies; merges verified in main): #75 adapter inc1 · #76 wave-4 packs · #78 adapter inc2 (settings/events/render-forwarding) · #79 milestones skinned · #80 playability + tools/play.py REPL · #81 docs truth-fix · #82 outbox entries. Idle reviewed/standalone/hub-adapter ✅.
- **superbot-mineverse** (suite 437→522 per #63 body; all merges API-verified): #55 ORDER 004 landing · #56/#59 spec claim+outbox · #57 FLAG-1 consume seam (MINING_SNAPSHOT_PATH) · #58 minigame section spec · #60 FLAG-2 write-path hardening · #61 conformance runner+runbook · #62/#63 generative dedupe. FLAG consume-side + conformance prep ✅.
- **superbot-next** — FISHING PORT COMPLETE (merges verified in main): #324 claim, #313 slice-1 (sibling), #330 rods, #342 bait, #350 curios/structures; plus #338 re-scoped bait-leg tests (merged 6d74fff). Lane-reported: fishing `_unmapped` 15→0, directory retired repo-wide, goldens 484, full-corpus report job SUCCESS; one real codex P1 (coral double-spend) fixed stricter-than-oracle. WRITE-PARITY lane: #306 merged (WP-1). Lane-reported: deep-mining WP goldens ~18 minted, all 8 guard-only-capture exemptions retired, 5 PG concurrency regression tests (red-without-lock proven).

### OPEN PRs (parked per tonight's rule, one-pass sweep; API-verified open at this stamp)

- superbot-next write-parity stack: #312 → #317 → #335 → #344 (order in each body; green per lane report).
- superbot-next #320 — mining energy pure domain core (slice 0) — **OPEN, not merged** (earlier lane report said merged; corrected against the API). Carries the dig-gating A/B/C energy decision ask in its body.
- Stale-duplicate item RESOLVED, no owner action needed: #328 closed unmerged 02:19Z (superseded by slices #330/#342); #338 was re-scoped after #342 and merged.

### QUEUED (owner decisions / asks — homes cited)

- D1/D2 audit-schema D2 ratification + 4 SIM-REQUESTs (mining/fishing/dnd/exploration economies) + persistence governance + rung-3 packaging — superbot-games control/outbox.md.
- idle SIM-001 economy-feel + A10-fail evidence + 2 Q-blocks needing fleet Q-numbers — superbot-idle control/outbox.md.
- mining dig-gating A/B/C energy decision — superbot-next #320 body (open PR).
- six-secret pair MINING_WRITE_ENDPOINT/MINING_WRITE_SHARED_SECRET → conformance is one command: `python3 scripts/conformance_run.py` (docs/conformance-runbook.md).
- substrate-kit born-red fail-open fix ask — this repo control/outbox.md; finding docs/findings/substrate-gate-born-red-fail-open-2026-07-12.md.
- Named follow-ups: wood-vs-mining cross-domain race · fish-pool sibling · check_money_race mis-classification at mining/ops.py:598 (fishing lane PR bodies).

### STALLED-with-error

- None. (The permission-walled fishing session was superseded by the rebuild lane — its container-local build is now redundant; recommend owner archive it.)

## PER-GAME STATE TABLE (owner deliverable; reviewed/standalone/integrated)

| game | state |
| --- | --- |
| mining (games) | ✅ / ✅ / ✅ |
| fishing (games) | ✅ / ✅ / ✅ |
| dnd (games) | ✅ / ✅ / ✅ |
| exploration (games) | ✅ / ✅ / ✅ |
| idle | ✅ / ✅ / adapter ✅ |
| fishing (next) | ported 20/20 ✅ |
| deep-mining (next) | write-parity complete pending stack sweep (#312→#317→#335→#344) |
| mineverse | read ✅ / write-ready (conformance one command; needs secret pair) |

Improvements lists live in the lane PRs + games control/outbox.md.

## ROUTINE RECORD (Q-0265)

- Failsafe cron "SuperBot World failsafe wake": id trig_0131tbQZs8HKmxKR4u5ZD1Hb, cron `15 1-23/2 * * *`, live.
- send_later pacemaker chain (one-tick); anti-stack check added after one duplicate incident, pruned same wake.

## Externally pending (pointers, unchanged)

- Owner secrets block (six names, write pair outstanding): control/outbox.md entry 2026-07-12T21:05Z; docs/live-prod-cutover.md.
- Bot-lane FLAG 1 (READ relay) + FLAG 2 (WRITE endpoint) — consume-side seams now merged here (#57, #60); full verbatim specs preserved at control/status.md@52fe2ca (git history), summarized in docs/current-state.md § Externally pending.
- Stage-(d) live-prod flag — owner-only, via a control/inbox.md ORDER.
- Groomed backlog: docs/ideas/founding-day-groomed-backlog-2026-07-11.md.
