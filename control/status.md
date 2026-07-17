# SuperBot World seat heartbeat · 2026-07-16T00:55Z · v3.6 coordinator reboot (first rebooted wake)
updated: 2026-07-16T00:55:09Z
phase: EAP-extension ack slice — ORDER 009 acked in control/outbox.md + this heartbeat re-stamped wholesale; control-only traffic, no product code touched.
health: green
kit: v1.17.0 · check: green · engaged: yes
last-shipped: #116 — EAP ORDER 009 ack claim (squash 141373d); the outbox ack + this heartbeat ride branch `claude/eap-ack-2`.
blockers: none
orders: acked=001,002,003,004,005,006,007,008,009 done=001,002,003,004,005,006,007,008
⚑ needs-owner: unchanged — the pending clicks stay consolidated in docs/eap-closeout-walkthrough-2026-07-14.md §C (incl. OA-003), each with a bolded recommendation + VERIFY step.
notes: RETIRED heartbeat — EAP autonomy wind-down 2026-07-17. This control/ message bus is deprecated (see the DEPRECATED banner at the end of this file); it is kept as history, not a live surface. Live status: docs/current-state.md; forward plan: docs/NEXT-TASKS.md.

## REPO STATE (live main shas at stamp)

- mineverse `141373d` green (610 passed + 1 skipped, verified 2026-07-15 @b9ade33)
- games `5db902a` green (810 passed @446a84e)
- idle `25d34f1` green (1381 passed + 1 skipped @8a7275d)

## ROUTINES (RETIRED — autonomy wind-down 2026-07-17)

- **No live routines for this seat.** The failsafe cron
  (trig_01RwQK2cBpgvY2xc2LZPSNtQ · `15 1-23/2 * * *`, coordinator-bound) and
  the pacemaker wake chain were EAP autonomy apparatus and are being wound
  down. Do NOT re-arm them: the owner is recreating this project fresh and the
  EAP goes read-only 2026-07-21. Any trigger still armed for this seat is the
  owner's to delete; agents do not re-arm. Historical doctrine (deprecated):
  `docs/ROUTINES.md`.

## ORDERS (fleet view at stamp)

- mineverse ORDER 009 acked — claim PR #116 MERGED + the outbox ack/this heartbeat
  on branch `claude/eap-ack-2` (this PR).
- games ORDER 010 acked — PR #148 MERGED.
- idle ORDER 010 acked — claim PR #143 + outbox PR #144, both MERGED.
- games ORDER 008 gated on the sim-verdict relay (V075/V076 finalized at sim-lab
  per coordinator, fm relay pending).

## PRS (live state at write time)

- truth-refresh: games #147 / idle #141 / mineverse #115 — MERGED 2026-07-15.
- idle reconcile-race fix #142 — MERGED.
- EAP acks: games #148 MERGED + idle #143/#144 MERGED (2026-07-16); this PR pending.

## SECURITY

- SECURITY-BEFORE-SECRETS satisfied (CSRF #42 merged 2026-07-12); six OAuth env
  vars owner-pending → docs/eap-closeout-walkthrough-2026-07-14.md §C (incl. OA-003).

## NEXT-2 BATON (RETIRED)

The wake-chain baton is retired with the autonomy wind-down. The forward plan
for this repo now lives in `docs/NEXT-TASKS.md` (owner-driven; no wake chain).

---

> ## ⚠️ DEPRECATED — retired EAP-era heartbeat (2026-07-17)
>
> This `control/status.md` seat heartbeat is part of the retired coordinator/
> worker message bus. The Claude Code Projects EAP goes **read-only
> 2026-07-21**; the owner is winding down agent autonomy and **recreating this
> project fresh**. Treat this file as history, not a live surface — do not
> re-stamp it, act on its ⚑ needs-owner asks, or re-arm its routines. Live
> status: `docs/current-state.md`; forward plan: `docs/NEXT-TASKS.md`.
