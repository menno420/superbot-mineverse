# superbot-mineverse · status
updated: 2026-07-13T09:28:00Z
phase: heartbeat — ORDER 005 night report (owner ask 2026-07-13, fm relay); the ORDER 004 morning-tally content below is PRESERVED. COORDINATOR-DELEGATED heartbeat write.
health: green
kit: v1.8.0
last-shipped: #63 — tests+server: shared served-bytes fixtures + views uses cached schema loader; merged 2026-07-13T02:21Z.
blockers: none
orders: acked=001,002,003,004,005 done=001,002,003,004,005 (005 = NIGHT REPORT section below)
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

## NIGHT REPORT 2026-07-13T09:28Z (ORDER 005 — owner ask 2026-07-13, fm relay)

Window: 2026-07-12T22:30Z → 2026-07-13T09:28Z. ORDER 005 verified binding at HEAD
(control/inbox.md, landed via PR #66 MERGED 2026-07-13T09:11:56Z — API-verified).
Supersedes nothing — the ORDER 004 tally above is preserved; this section extends it
to the full requested window (which opens earlier, 22:30Z, and closes later).

### SHIPPED (this repo; ALL merges API-verified; squash SHA on main · merged_at UTC)
- #50 stranded close-out flips for #48/#49 — 0417fc0 · 22:41:38Z
- #51 ambient cave audio (backlog item 5) — 10942ea · 23:05:25Z
- #52 born-red fail-open finding + kit ask — 6a73ca3 · 23:16:12Z
- #53 seasonal decorations (backlog item 6) — 030a3e9 · 23:29:14Z
- #54 heartbeat 23:41Z — 18f1fb3 · 23:44:35Z
- #55 ORDER 004 landing (verbatim owner directive) — be916c8 · 00:48:50Z
- #56 minigame-spec claim — 6fd8145 · 00:51:25Z
- #57 FLAG-1 consume seam (MINING_SNAPSHOT_PATH) — b2b41c3 · 01:02:06Z
- #59 minigame-spec outbox pointer + claim close — 9746389 · 01:08:04Z
- #58 minigame section spec (ORDER 004 item 4) — 7f33c2b · 01:18:38Z
- #60 FLAG-2 write-path hardening (response-envelope validation) — 9ee2707 · 01:54:07Z
- #61 one-command conformance runner + runbook — 2d05628 · 01:58:40Z
- #62 server internals dedupe — bf93786 · 02:04:24Z
- #63 test-infra dedupe — 79a4018 · 02:21:34Z
- #64 ORDER 004 morning tally — f9261a2 · 04:14:37Z
- #65 ORDER 038 adoption — 35f147a · 05:29:43Z
- #66 ORDER 005 landing (manager-written) — 3fe538e · 09:11:56Z
- Suite 437 → **522 passed, 1 skipped** — VERIFIED locally at HEAD 3fe538e (`python3 -m pytest -q`).

### Cross-repo seat work in superbot-next (ALL LANE-REPORTED — superbot-next is not
reachable from this reporting session: GitHub API access denied, repo not in session
scope; states below are as verified by the ORDER 004 tally session at 04:12Z)
- Fishing port COMPLETE: #324/#313/#330/#342/#350 merged (+ re-scoped #338); `_unmapped` 15→0, goldens 484, full-corpus report job SUCCESS.
- Write-parity lane: #306 (WP-1) merged; stack #312 → #317 → #335 → #344 parked OPEN + green for owner sweep.
- Stale-duplicate item resolved pre-window-close: #328 closed unmerged (superseded by #330/#342); #338 re-scoped after #342 and merged.
- Energy slice 0 #320 OPEN, not merged (correction stands from the 04:12Z tally); dig-gating A/B/C ask lives in its body.

### OPEN PRs + check states
- This repo: none (API-verified 2026-07-13T09:15Z).
- superbot-next write-parity stack #312→#317→#335→#344 + #320 — OPEN (lane-reported, see above).

### ORDERS served + outstanding
- 001–004 done (004 tally posted via #64, merged 04:14:37Z); 005 = this report. Outstanding: none.

### Asks pending
- ⚑ MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET pair — conformance is then one command: `python3 scripts/conformance_run.py` (outbox 2026-07-12T21:05Z; docs/conformance-runbook.md).
- substrate-kit born-red fail-open gate fix — outbox 2026-07-12T22:10Z; finding docs/findings/substrate-gate-born-red-fail-open-2026-07-12.md.
- dig-gating A/B/C energy decision — superbot-next #320 body (open PR; lane-reported).

### STALLS / denials (verbatim)
- None this window in this repo.

### Wake-chain health (SEAT-LEVEL — one chain serves games/idle/mineverse; the order asks per-repo, the chain is per-seat)
- Failsafe cron `trig_0131tbQZs8HKmxKR4u5ZD1Hb` "SuperBot World failsafe wake", cron `15 1-23/2 * * *` — API-verified live 2026-07-13T09:16Z: enabled, last fired 09:15:25Z, next 11:15:00Z. Overnight fires 01:15/03:15/05:15/07:15 on schedule (lane-reported; the API exposes only the last fire).
- send_later pacemaker chain continuous through the night; current tick `trig_01K5pWUeY1YEM6taMeWmHvG8` fires 09:19Z (API-verified live, bound to the seat coordinator session).
- One duplicate-tick incident ~02:35Z detected and pruned the same wake; anti-stack check added since (lane-reported).

### Next-3
1. Run the conformance sweep the moment the write secret pair lands (`python3 scripts/conformance_run.py`).
2. Kit-lab response on the born-red fail-open ask (outbox 2026-07-12T22:10Z) — adopt the fixed gate when it ships.
3. Backlog trigger probes (groomed-backlog items 3/4) next generative wave.
