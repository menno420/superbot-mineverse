# superbot-mineverse · status
updated: 2026-07-13T18:45:43Z
phase: HEARTBEAT — end-of-day control-only worker slice: wholesale status refresh (shipped record, kit state, order service, routines, baton). Session type: worker, not a coordinator seat.
health: green
kit: v1.15.0 · check: green
last-shipped: #82 — kit v1.15.0 lane-owed template deltas (CAPABILITIES + AGENT_ORIENTATION); merged 2026-07-13T16:34:58Z; current main f79d0ae.
blockers: none
orders: acked=001,002,003,004,005 done=001,002,003,004,005 (no new ORDERs in control/inbox.md at HEAD f79d0ae)
⚑ needs-owner: pytest as required check on superbot-idle main (OA-003) — full six-field OWNER-ACTION block: this repo's control/outbox.md entry 2026-07-13T14:56Z (VENUE: hub). Carried: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET pair — control/outbox.md entry 2026-07-12T21:05Z.
notes: control-only diff (status overwrite + claim lifecycle) — CI control fast lane, no session card per convention. Tree verified this slice: pytest 551 passed / 1 skipped; bootstrap check --strict exit 0.

## SHIPPED 2026-07-13 (verified live at GitHub, per-repo merged-PR record)

- mineverse: 28 PRs merged today — #55–#82 (squash SHAs, ascending: be916c8, 6fd8145, b2b41c3, 7f33c2b, 9746389, 9ee2707, 2d05628, bf93786, 79a4018, f9261a2, 35f147a, 3fe538e, 9809c2a, 5a14f03, 5a12fee, dc320bf, 234e8f7, f206bf1, e44a80c, a84b3d0, bcef4b2, 8088d67, f89c04e, bf9ee98, d2925e2, 1520e05, e81c9ff, f79d0ae). Day-wave subset since the 11:47Z heartbeat: #75–#82.
- superbot-idle: 25 PRs merged today — #75–#99 (squash SHAs, ascending: 86f631d, ac0af23, 457407c, 497db5a, 7af705c, 4af4338, c925a45, c735075, 161bc7d, d992c56, 3e22f69, b03cc96, 3a4fa5f, 05a99f5, e740810, 675c347, 96cd635, 26b7eaa, cf59d02, 4ebe037, 2ac6c5d, 70b2e8d, 3c295ef, 53edf18, 4c31a2c). idle main at 4c31a2c.
- superbot-games: 27 PRs merged today — #65–#91 (squash SHAs, ascending: 64b3371, 60b2773, dd867c8, 1b09a03, 7c13166, da0e47e, c491bd3, ef18b4e, 6ecd579, 0e62ee3, 0ee7482, 425a3d7, 5aec110, dabba30, 57f69be, 156e2de, d6a9526, 739c571, 72a94bb, 9caf1b6, ae4beff, c629577, 67de572, 0ffd3cc, ab442e7, 52eb8b2, ce70d9e). games main at ce70d9e.
- Narrative context per repo: each repo's docs/current-state.md at its HEAD (mineverse f79d0ae, idle 4c31a2c, games ce70d9e).

## KIT STATE (facts, cited)

- Seat kit v1.15.0 on all three repos, verified in-tree:
  - mineverse: `bootstrap.py` line 93 `KIT_VERSION = "1.15.0"` @ f79d0ae (upgraded via PR #80, squash 1520e05).
  - superbot-idle: `bootstrap.py` line 93 `KIT_VERSION = "1.15.0"` @ 4c31a2c (upgraded via idle PR #91, squash 96cd635). idle's own heartbeat kit line self-reports v1.7.1 — tree wins per protocol (self-report lag class).
  - superbot-games: `bootstrap.py` line 93 `KIT_VERSION = "1.15.0"` @ ce70d9e.
- mineverse lane-owed post-upgrade docs deltas shipped in #82 (squash f79d0ae).

## ORDER SERVICE (sibling repos, cited at their HEADs)

- games ORDER 007 done — games control/status.md @ ce70d9e orders line: `acked=001,002,003,004,005,006,007 done=001,002,003,005,006,007` with `007 = ORDER 007 section` (served via games PRs #82–#85, squashes 739c571/72a94bb/9caf1b6/ae4beff).
- idle ORDER 005 done — idle control/status.md @ 4c31a2c orders line: `acked=000-005 done=000-005 (… 005 done-when met atomically … graduation PR #93 …)` (idle #93 squash cf59d02).
- mineverse ORDERs 001–005: done (unchanged; see orders line above).

## OPEN PRS

- Zero open PRs on mineverse (open-PR list API-verified empty at 2026-07-13T18:41Z, before this branch's PR was opened).

## ROUTINES (neutral facts)

- Failsafe cron "SuperBot World failsafe wake" trig_01QctdbvhdcvuSFsCPxdseae (`15 1-23/2 * * *`), bound to the coordinator session; pacemaker chain coordinator-managed, idles when the backlog is dry.

## OPEN OWNER ASKS (pointers only)

- idle pytest-required (OA-003): six-field block in this repo's control/outbox.md @ 2026-07-13T14:56Z; also carried in idle control/status.md + outbox @ 4c31a2c.
- mineverse write-pair secrets (MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET): control/outbox.md @ 2026-07-12T21:05Z.
- games D2 ratification / packaging / standalone-CLI persistence decisions: games control/outbox.md @ ce70d9e (D1/D2 decision-note + OWNER-QUEUE persistence entry).

## NEXT-2 BATON

1. Verdict-gated waits — fishing cook-leg economy SIM-REQUEST (games control/outbox.md @ ce70d9e, filed via games #89 squash ab442e7) + PRESTIGE tuning ruling.
2. games truth-stamp anchor idea — see the games .sessions card for #90 (squash 52eb8b2).
