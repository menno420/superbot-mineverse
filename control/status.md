# superbot-mineverse · status
updated: 2026-07-14T18:59:20Z
phase: HEARTBEAT — fleet-seat relay (games worker session): games preflight-path fix parked as games PR #143; this repo untouched beyond this heartbeat (mineverse HEAD `419d559`, kit v1.16.0 via #110).
health: green
kit: v1.16.0
last-shipped: #110 — kit upgrade v1.15.0 → v1.16.0 (squash 419d559). This heartbeat rides its own control-only PR.
blockers: none
orders: acked=001,002,003,004,005,006,007,008 done=001,002,003,004,005,006,007,008
⚑ needs-owner: unchanged — the four pending clicks remain consolidated in docs/eap-closeout-walkthrough-2026-07-14.md §C (superbot #2058 draft flip + sender-side HMAC · six host env vars · env-gated conformance e2e · carried OA-003), each with a bolded recommendation + VERIFY step; full six-field blocks in the 2026-07-14T11:34:32Z heartbeat (git history of this file) and control/outbox.md.
notes: this stamp is a cross-seat heartbeat relay from a superbot-games worker session (games/idle status files are frozen archives; this file is the live heartbeat). Facts below; no orders served or filed in this repo.

## GAMES SLICE — preflight path fix (2026-07-14, facts + pointers)

- games PR #143 (`claude/preflight-path-fix`, head `790d2aa`, base main @ `8c9c320`): plants `scripts/preflight.py` — `substrate.config.json` `preflight_scripts` named the kit-default path but the file was absent, so every `bootstrap.py check --strict` full-lane run self-skipped the preflight leg with a not-found NOTE; the wrapper delegates to the existing gate-parity `tools/preflight.py` (games #128), mirroring idle PR #137 (squash `8ff9f59`).
- Verified locally at `790d2aa`: `python3 -m pytest -q` → 810 passed in 42.50s · `python3 scripts/preflight.py` → preflight GREEN, all three gates, exit 0 · `check --strict` → NOTE gone; sole red = the branch's own designed born-red card hold · failure propagation proven by a temporary injected exit 42 surfacing as an exit-affecting `[preflight-script]` finding.
- CI at first push: tests SUCCESS · reconcile SUCCESS · enable-auto-merge SUCCESS · substrate-gate FAILURE = the designed `[session-card-hold]` born-red hold only (job log carries the "Designed hold — not a CI failure to investigate" notice); no `[preflight-script]` finding in the gate venue.
- games inbox at `8c9c320`: ORDERs 001–009 present, none newer than 009 (games #139/#140 record 009 done); ORDER 008 verdict-gated, untouched.

## OPEN PRS (this repo)

- none at stamp time (this heartbeat's own control-only PR lands after this stamp).

## SIBLING LANES

- games: PR #143 as above; last main merge #142 (`8c9c320`, host card-guard split mirroring idle #137).
- idle: HEAD `c31251e` (#138, claim release after idle #137's preflight plant + card-guard split).
- seat-wide EAP record: docs/audits/eap-project-audit-2026-07-14.md.

## ROUTINES (neutral facts)

- Failsafe cron trig_01QctdbvhdcvuSFsCPxdseae bound to the coordinator session; pacemaker chain coordinator-managed.

## NEXT-2 BATON (carried)

1. Serve the games SIM-REQUEST `fishing-full-roster-economy` (29 not-yet-pinned species, filed in games control/outbox.md via games PR #92 squash 21937f3) when the sim verdict returns — first full-content-wave batch under ORDER 007's bigger-batches rule.
2. Verdict-gated waits as before — fishing cook-leg economy SIM-REQUEST (folded by reference into the full-roster batch) + PRESTIGE tuning ruling. Consumer-side snapshot-parity work (3 flavor requireds + slot-map) stays gated on the pending seam ruling (option A) and lands producer-side in product-forge.
