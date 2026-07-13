# superbot-mineverse · status
updated: 2026-07-13T15:08:30Z
phase: SEAT HEARTBEAT — control-only worker slice: heartbeat overwrite + registry-brief CI drift note (rides PR branch `claude/heartbeat-drift-note-0713`). Session type: worker, not a coordinator seat.
health: green
kit: v1.8.0
last-shipped: #78 — outbox: idle pytest owner ask + kit v1.15.0 upgrade report; merged 2026-07-13T14:59:00Z; current main bf9ee98.
blockers: none
orders: acked=001,002,003,004,005 done=001,002,003,004,005 (unchanged; no new ORDERs in control/inbox.md at HEAD bf9ee98)
⚑ needs-owner: pytest as a required check on superbot-idle main — full six-field OWNER-ACTION block: control/outbox.md entry 2026-07-13T14:56Z (VENUE: hub). Carried: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET pair — control/outbox.md 2026-07-12T21:05Z.
notes: control-only diff (status overwrite + outbox append + claim lifecycle) — CI control fast lane, no session card per convention.

## SEAT KIT STATE (facts, cited)

- idle: kit v1.15.0 — upgraded via superbot-idle PR #91, squash 96cd635.
- games: kit v1.15.0 @ games main d6a9526.
- mineverse: kit v1.8.0 — verified at HEAD bf9ee98 (`bootstrap.py` `KIT_VERSION = "1.8.0"` line 90; `substrate.config.json` `"kit_version": "1.8.0"`).

## SHIPPED TODAY (2026-07-13, seat-wide pointers)

- idle: #87, #89, #90, #91 — kit v1.7.1→v1.15.0; the new born-red HOLD verified live (pre-flip designed-red substrate-gate run 29259353167, post-flip green run 29259492736).
- games: #81 — current-state groom.
- mineverse: #75, #76, #77, #78 — records fix + outbox appends; all four API-verified merged (merged_by github-actions[bot]); main bf9ee98.

## OPEN PRS

- Zero open PRs on mineverse besides this heartbeat PR (open-PR list API-verified empty at 2026-07-13T15:05Z, before this branch's PR was opened).

## CI FACTS (verified live this session)

- Check contexts on merged PRs #77 (head 9db52dd) and #78 (head 68815c9): `substrate-gate`, `pytest`, `enable-auto-merge` — all SUCCESS.
- Required contexts on main per the enabler's server-side rules probe (run 29260140367, job 86850885591): `substrate-gate`, `pytest`.
- Registry-brief drift note filed: control/outbox.md entry 2026-07-13T15:08Z (brief says "substrate-gate + schema-gate"; no `schema-gate` check context exists — that workflow file's job reports as `pytest`).

## ROUTINES (neutral facts)

- Failsafe cron "SuperBot World failsafe wake" trig_01QctdbvhdcvuSFsCPxdseae (`15 1-23/2 * * *`), bound to the coordinator session; pacemaker chain coordinator-managed.

## NEXT-2 BATON

1. Owner ruleset answer on pytest-required for superbot-idle (control/outbox.md 2026-07-13T14:56Z, ⚑ above).
2. Manager routing of the kit v1.15.0 carve-out regeneration bug to kit-lab (already filed in control/outbox.md 2026-07-13T14:56Z kit-upgrade report).
