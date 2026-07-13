# superbot-mineverse · status
updated: 2026-07-13T22:22:30Z
phase: HEARTBEAT — control-only worker slice: owner bigger-batches/production-grade directive landed as ORDER 007 in control/inbox.md + wholesale status refresh. Session type: worker, not a coordinator seat.
health: green
kit: v1.15.0 · check: green
last-shipped: #84 — ORDER 006 (EAP final-night worklist, fm ORDER 045 relay) appended to control/inbox.md; merged 2026-07-13T22:19:15Z; current main 5856a54.
blockers: none
orders: acked=001,002,003,004,005,006,007 done=001,002,003,004,005 (006 EAP worklist + 007 owner bigger-batches are status: new, unclaimed — execution belongs to the seat's next wake, not this control-only worker slice)
⚑ needs-owner: pytest as required check on superbot-idle main (OA-003) — full six-field OWNER-ACTION block: this repo's control/outbox.md entry 2026-07-13T14:56Z (VENUE: hub). Carried: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET pair — control/outbox.md entry 2026-07-12T21:05Z.
notes: control-only diff (inbox ORDER append + status overwrite + claim lifecycle) — CI control fast lane, no session card per convention. inbox one-writer exception: ORDER 007 relays a live owner turn via coordinator dispatch (sanctioned exception, stated inside the ORDER per doctrine). Tree verified this slice: bootstrap check --strict exit 0.

## OWNER DIRECTIVE 2026-07-13 ~21:59Z (bigger batches / production-grade) — landed in all three inboxes

- games ORDER 008 — PR menno420/superbot-games#92, merged 2026-07-13T22:09:21Z, squash 21937f3 (games main since advanced to e2f6699 via claim-release #93).
- idle ORDER 006 — PR menno420/superbot-idle#101, merged 2026-07-13T22:05:45Z, squash 58061e8 (idle main since advanced to 952aa9e via #102 claim prune + #103 EAP ORDER 007).
- mineverse ORDER 007 — this PR (branch claude/owner-order-batch-sim), appended after ORDER 006.
- Separately landed, distinct directive: mineverse ORDER 006 — EAP final-night worklist (fm ORDER 045 relay) via PR #84, merged 2026-07-13T22:19:15Z, squash 5856a54.

## SHIPPED 2026-07-13 (verified live at GitHub, per-repo merged-PR record)

- mineverse: 30 PRs merged today — #55–#82 (squash SHAs, ascending: be916c8, 6fd8145, b2b41c3, 7f33c2b, 9746389, 9ee2707, 2d05628, bf93786, 79a4018, f9261a2, 35f147a, 3fe538e, 9809c2a, 5a14f03, 5a12fee, dc320bf, 234e8f7, f206bf1, e44a80c, a84b3d0, bcef4b2, 8088d67, f89c04e, bf9ee98, d2925e2, 1520e05, e81c9ff, f79d0ae) plus #83 (heartbeat, ae98dd0) and #84 (ORDER 006, 5856a54). mineverse main at 5856a54.
- superbot-idle: 29 PRs merged today — #75–#103; the 18:45Z record listed #75–#99 (squash SHAs ascending: 86f631d, ac0af23, 457407c, 497db5a, 7af705c, 4af4338, c925a45, c735075, 161bc7d, d992c56, 3e22f69, b03cc96, 3a4fa5f, 05a99f5, e740810, 675c347, 96cd635, 26b7eaa, cf59d02, 4ebe037, 2ac6c5d, 70b2e8d, 3c295ef, 53edf18, 4c31a2c); since then #100 (1f4d774), #101 (58061e8), #102 (95bd3cf), #103 (952aa9e). idle main at 952aa9e.
- superbot-games: 29 PRs merged today — #65–#93; the 18:45Z record listed #65–#91 (squash SHAs ascending: 64b3371, 60b2773, dd867c8, 1b09a03, 7c13166, da0e47e, c491bd3, ef18b4e, 6ecd579, 0e62ee3, 0ee7482, 425a3d7, 5aec110, dabba30, 57f69be, 156e2de, d6a9526, 739c571, 72a94bb, 9caf1b6, ae4beff, c629577, 67de572, 0ffd3cc, ab442e7, 52eb8b2, ce70d9e); since then #92 (21937f3), #93 (e2f6699). games main at e2f6699.
- Narrative context per repo: each repo's docs/current-state.md at its HEAD (mineverse 5856a54, idle 952aa9e, games e2f6699).

## KIT STATE (facts, cited)

- Seat kit v1.15.0 on all three repos, verified in-tree:
  - mineverse: `bootstrap.py` line 93 `KIT_VERSION = "1.15.0"` @ 5856a54 (upgraded via PR #80, squash 1520e05).
  - superbot-idle: `bootstrap.py` line 93 `KIT_VERSION = "1.15.0"` @ 4c31a2c (upgraded via idle PR #91, squash 96cd635). idle's own heartbeat kit line self-reports v1.7.1 — tree wins per protocol (self-report lag class).
  - superbot-games: `bootstrap.py` line 93 `KIT_VERSION = "1.15.0"` @ ce70d9e.
- mineverse lane-owed post-upgrade docs deltas shipped in #82 (squash f79d0ae).

## ORDER SERVICE (sibling repos, cited at their HEADs)

- games ORDER 007 done — games control/status.md @ ce70d9e orders line: `acked=001,002,003,004,005,006,007 done=001,002,003,005,006,007` with `007 = ORDER 007 section` (served via games PRs #82–#85, squashes 739c571/72a94bb/9caf1b6/ae4beff). games ORDER 008 (owner bigger-batches) landed via #92 — status: new.
- idle ORDER 005 done — idle control/status.md @ 4c31a2c orders line: `acked=000-005 done=000-005 (… 005 done-when met atomically … graduation PR #93 …)` (idle #93 squash cf59d02). idle ORDER 006 (owner bigger-batches, #101) + ORDER 007 (EAP worklist, #103) landed — status: new.
- mineverse ORDERs 001–005: done (unchanged; see orders line above). ORDERs 006 + 007: new, unclaimed.

## OPEN PRS

- Zero open PRs on mineverse (open-PR list API-verified empty at 2026-07-13T22:19Z, after #84 merged and before this branch's PR was opened). The 18:45Z heartbeat's zero-open-PRs line had gone stale in the interim (#84 was open 22:14–22:19Z).

## ROUTINES (neutral facts)

- Failsafe cron "SuperBot World failsafe wake" trig_01QctdbvhdcvuSFsCPxdseae (`15 1-23/2 * * *`), bound to the coordinator session; pacemaker chain coordinator-managed, idles when the backlog is dry.

## OPEN OWNER ASKS (pointers only)

- idle pytest-required (OA-003): six-field block in this repo's control/outbox.md @ 2026-07-13T14:56Z; also carried in idle control/status.md + outbox @ 4c31a2c.
- mineverse write-pair secrets (MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET): control/outbox.md @ 2026-07-12T21:05Z. Standing ORDER 003 ordering rule unchanged: security merges before anything secrets-adjacent; the OAuth six-env-var provisioning ask stays subordinate per that rule.
- games D2 ratification / packaging / standalone-CLI persistence decisions: games control/outbox.md @ ce70d9e (D1/D2 decision-note + OWNER-QUEUE persistence entry; games main has since advanced to e2f6699 — entries are append-only, pointer remains valid).

## NEXT-2 BATON

1. Serve the games SIM-REQUEST `fishing-full-roster-economy` (29 not-yet-pinned species, filed in games control/outbox.md via PR #92 squash 21937f3) when the sim verdict returns — first full-content-wave batch under ORDER 007's bigger-batches rule.
2. Verdict-gated waits as before — fishing cook-leg economy SIM-REQUEST (folded by reference into the full-roster batch; originally filed via games #89 squash ab442e7) + PRESTIGE tuning ruling.
