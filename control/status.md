# superbot-mineverse · status
updated: 2026-07-13T16:15:03Z
phase: HEARTBEAT — control-only worker slice: status overwrite (kit line v1.8.0 → v1.15.0 post-#80) + outbox kit-lab relay append (rides PR branch `claude/status-kit-v1150`). Session type: worker, not a coordinator seat.
health: green
kit: v1.15.0
last-shipped: #80 — kit upgrade v1.8.0 → v1.15.0 (substrate-gate gains the --added-card born-red HOLD; required check contexts survive unchanged); merged 2026-07-13T16:05:32Z by github-actions[bot]; current main 1520e05.
blockers: none
orders: acked=001,002,003,004,005 done=001,002,003,004,005 (unchanged; no new ORDERs in control/inbox.md at HEAD 1520e05)
⚑ needs-owner: pytest as a required check on superbot-idle main — full six-field OWNER-ACTION block: control/outbox.md entry 2026-07-13T14:56Z (VENUE: hub). Carried: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET pair — control/outbox.md 2026-07-12T21:05Z.
notes: control-only diff (status overwrite + outbox append + claim lifecycle) — CI control fast lane, no session card per convention. Outbox relays pending manager sweep: born-red gate routing (2026-07-12T22:10Z), registry-brief corrections (2026-07-13T13:48Z / 14:16Z / 15:08Z), kit upgrade-report sha256-pair relay (this session, addressed for kit-lab).

## KIT STATE (facts, cited)

- mineverse: kit v1.15.0 — verified at HEAD 1520e05 (`bootstrap.py` line 93 `KIT_VERSION = "1.15.0"`; `substrate.config.json` `"kit_version": "1.15.0"`). Upgraded via PR #80 (head c1905de), merged 2026-07-13T16:05:32Z.
- Lane-owed post-upgrade deltas still open (PR #80 card `.sessions/2026-07-13-kit-upgrade-v1150.md`): diverged `docs/CAPABILITIES.md` template delta + the remaining `docs/AGENT_ORIENTATION.md` template delta (only the minimal read-path hunk was merged in #80).

## OPEN PRS

- Zero open PRs (open-PR list API-verified empty at 2026-07-13T16:13Z, before this branch's PR was opened).

## ROUTINES (neutral facts)

- Failsafe cron "SuperBot World failsafe wake" trig_01QctdbvhdcvuSFsCPxdseae (`15 1-23/2 * * *`), bound to the coordinator session; pacemaker chain coordinator-managed.

## NEXT-2 BATON

1. Kit v1.15.0 remaining docs deltas — `docs/CAPABILITIES.md` template delta + `docs/AGENT_ORIENTATION.md` remaining delta (lane-owed per the #80 card) — being shipped in a sibling docs PR this session.
2. Owner provisioning of the MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET pair (control/outbox.md 2026-07-12T21:05Z, ⚑ above; also waits on the bot lane's write endpoint, FLAG 2) — then run `python3 scripts/conformance_run.py` per docs/conformance-runbook.md.
